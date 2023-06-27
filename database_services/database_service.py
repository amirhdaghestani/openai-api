"""This module handles operations of database"""
import datetime
import nest_asyncio
nest_asyncio.apply()
import asyncio

import motor.motor_asyncio
from pymongo.errors import CollectionInvalid

from logger.ve_logger import VeLogger
from configs.database_config import DatabaseConfig, User
from utils.database_utils import generate_api_key, hash_api_key


class DatabaseService:
    """Class to handle database operations."""

    # Initialize logger
    logger = VeLogger()

    def __init__(self, database_config: DatabaseConfig=None) -> None:
        """Initializer of database.
        
        Args:
            database_config (DatabaseConfig): Config of database.

        Returns:
            None

        Raises:
            ValueError: When database_config is not provided.
        """
        # Check Arguments
        if database_config is None:
            self.logger.error("database config is None.")
            raise ValueError("Provide database_config when initializing class.")

        if database_config.db_url is None:
            self.logger.error("Database URL is None.")
            raise ValueError(
                "Provide Database URL when initializing class. You can set the " \
                "enviroment variable `DB_URL` to your URL endpoint.")

        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            database_config.db_url)
        self.db_name = database_config.db_name
        self.db_user_collection = database_config.db_user_collection
        self.db_admin_collection = database_config.db_admin_collection
        self.db_ts_collection = database_config.db_ts_collection
        self.db = self.client[self.db_name]
        self.user_collection = self.db.get_collection(
            self.db_user_collection
        )
        self.admin_collection = self.db.get_collection(
            self.db_admin_collection
        )
        asyncio.run(self._create_ts_collection(self.db_ts_collection))
        self.ts_collection = self.db.get_collection(
            self.db_ts_collection
        )

    async def _create_ts_collection(self, collection_name):
        """Create a time-series collection."""
        try:
            await self.db.create_collection(
                collection_name,
                timeseries = {
                    "timeField": "timestamp",
                    "metaField": "metadata",
                    "granularity": "seconds"
                },
                expireAfterSeconds=5184000
            )
        except CollectionInvalid as exception:
            self.logger.warning(f"Creating time series with {exception}")

    async def _get_doc(self, collection, dict_find: dict):
        """Check if value for key already exists in the database or not"""
        doc = await collection.find_one(dict_find)
        return doc

    async def _update_doc(self, collection, dict_find: dict, dict_update: dict):
        """Update if value for key already exists in the database or not"""
        doc = await collection.update_one(
            dict_find,
            {"$set": dict_update})
        return doc

    async def _add_doc(self, collection, dict_add: dict):
        """Check if value for key already exists in the database or not"""
        doc = await collection.insert_one(dict_add)
        return doc

    async def _delete_doc(self, collection, dict_find: dict):
        """Check if value for key already exists in the database or not"""
        doc = await collection.delete_one(dict_find)
        return doc

    async def check_limit(self, hashed_api_key: str, limit_key: str,
                          cost: int):
        """Check limit"""
        doc = await self._get_doc(self.user_collection,
                                  {"api_key": hashed_api_key})
        request_limit = int(doc[limit_key])
        if request_limit < cost:
            return {"message": "Limit has been surpassed. "\
                               "Contact adminstration.",
                    "acknowledged": False,
                    "status_code": 429}
        else:
            return {"message": f"Limit is {request_limit}",
                    "acknowledged": True,
                    "status_code": 200}

    async def check_request_limit(self, hashed_api_key: str, cost: int=1):
        """Check request limit"""
        return await self.check_limit(hashed_api_key=hashed_api_key,
                                      limit_key="request_limit",
                                      cost=cost)

    async def check_finetune_limit(self, hashed_api_key: str, cost: int=1):
        """Check request limit"""
        return await self.check_limit(hashed_api_key=hashed_api_key,
                                      limit_key="fine_tune_limit",
                                      cost=cost)

    async def update_limit(self, hashed_api_key: str, limit_key: str,
                           cost: int):
        """Update request limit"""
        doc = await self._get_doc(self.user_collection,
                                  {"api_key": hashed_api_key})
        request_limit = int(doc[limit_key])
        result = await self._update_doc(
            self.user_collection,
            {"api_key": hashed_api_key},
            {limit_key: request_limit - cost}
        )
        return {"message": "Limit has been updated. "\
                          f"Limit: {doc[limit_key]}",
                "acknowledged": result.acknowledged,
                "status_code": 200}

    async def update_request_limit(self, hashed_api_key: str, cost: int=1):
        """Check request limit"""
        return await self.update_limit(hashed_api_key=hashed_api_key,
                                       limit_key="request_limit",
                                       cost=cost)

    async def update_finetune_limit(self, hashed_api_key: str, cost: int=1):
        """Check request limit"""
        return await self.update_limit(hashed_api_key=hashed_api_key,
                                       limit_key="fine_tune_limit",
                                       cost=cost)

    async def verify_api_key(self, token: str):
        """Verify API key."""
        hashed_token = hash_api_key(token)
        doc = await self._get_doc(self.user_collection,
                                  {'api_key': hashed_token})
        if bool(doc):
            doc['acknowledged'] = True
            doc.pop('_id')
            return doc
        else:
            return {"message": "API key is not valid",
                    "acknowledged": False,
                    "status_code": 401}

    async def verify_admin(self, username: str, password: str):
        """Verify API key."""
        hashed_password = hash_api_key(password)
        doc = await self._get_doc(self.admin_collection,
                                  {'username': username})

        if bool(doc) and doc['password'] == hashed_password:
            doc['acknowledged'] = True
            doc['_id'] = ""
            return doc
        else:
            return {"message": "Username is not valid",
                    "acknowledged": False,
                    "status_code": 401}

    async def add_new_user(self, user: User):
        """Add new user to database
        
        Args:
            user (User): Input data of user.

        Returns:
            None

        """
        # Check arguments
        check_exists = await self._get_doc(self.user_collection,
                                           {'user_id': user.user_id})
        if bool(check_exists):
            return {"message": "User already exists.",
                    "acknowledged": False,
                    "status_code": 409}

        api_key = generate_api_key(user.user_id)
        hashed_api_key = hash_api_key(api_key)

        user_dict = user.dict()
        user_dict['api_key'] = hashed_api_key

        result = await self._add_doc(self.user_collection, user_dict)

        return {
            "API_key": api_key,
            "acknowledged": result.acknowledged,
            "status_code": 201
        }

    async def edit_user(self, user: User):
        """Edit user in database
        
        Args:
            user (User): Edited data of user.

        Returns:
            None

        """
        # Check arguments
        check_exists = await self._update_doc(self.user_collection,
                                              {'user_id': user.user_id},
                                              user.dict(exclude_unset=True))
        if check_exists.matched_count == 0 and check_exists.modified_count == 0:
            return {"message": "User does not exists.",
                    "acknowledged": False,
                    "status_code": 404}

        if check_exists.matched_count > 0 and check_exists.modified_count == 0:
            return {"message": "User did not update. User's data is the same.",
                    "acknowledged": False,
                    "status_code": 200}

        return {"message": "User updated.",
                "acknowledged": True,
                "status_code": 200}

    async def retrieve_user(self, search_value, search_key: str):
        """Get user in database
        
        Args:
            user_id (str): ID of the user to retrive.
            search_key (str): Key of column to search in database.

        Returns:
            None

        """
        # Check arguments
        check_exists = await self._get_doc(self.user_collection,
                                           {search_key: search_value})
        if not bool(check_exists):
            return {"message": "User did not exists.",
                    "acknowledged": False,
                    "status_code": 404}

        check_exists.pop('_id')
        check_exists.pop('api_key')

        return {"message": "User found.",
                "data": check_exists,
                "acknowledged": True,
                "status_code": 200}

    async def delete_user(self, search_value, search_key: str):
        """Delete user in database
        
        Args:
            user_id (str): ID of the user to delete.
            search_key (str): Key of column to search in database.

        Returns:
            None

        """
        # Check arguments
        check_exists = await self._get_doc(self.user_collection,
                                           {search_key: search_value})
        if not bool(check_exists):
            return {"message": "User did not exists.",
                    "acknowledged": False,
                    "status_code": 404}

        check_exists.pop('_id')
        check_exists.pop('api_key')

        check_deleted = await self._delete_doc(self.user_collection,
                                               {search_key: search_value})

        if check_deleted.deleted_count == 0:
            return {"message": "Couldn't delete the user.",
                    "acknowledged": False,
                    "status_code": 409}

        return {"message": "User deleted successfully.",
                "data": check_exists,
                "acknowledged": True,
                "status_code": 200}

    async def _add_time_series(self, collection, user_id: str, endpoint: str,
                               cost: int):
        """Insert time-series"""
        result = await collection.insert_one({
                "metadata": { "user_id": user_id, "endpoint": endpoint },
                "timestamp": datetime.datetime.now(),
                "request": cost
            }
        )
        return {"message": "Record has been added.",
                "acknowledged": result.acknowledged,
                "status_code": 200}

    async def _delete_time_series(self, collection, user_id: str):
        """Delete time-series"""
        result = await collection.delete_many({
            "metadata.user_id": user_id
        })
        return {"message": "Record has been added.",
                "acknowledged": result.acknowledged,
                "status_code": 200}

    async def delete_request_ts_record(self, user_id: str):
        """Delete time-series"""
        return await self._delete_time_series(collection=self.ts_collection,
                                              user_id=user_id)

    async def add_request_ts_record(self, user_id: str, endpoint: str,
                                    cost: int=1):
        """Add time series record"""
        return await self._add_time_series(collection=self.ts_collection,
                                           user_id=user_id,
                                           endpoint=endpoint,
                                           cost=cost)

    async def get_ts_dates(self, user_id: str, endpoint: str, day_from: float,
                           day_to: float=None, slice: str="hour"):
        """Get results of ts between two dates"""
        delta_from = datetime.datetime.now() - datetime.timedelta(days=day_from)
        match_filter_dict =  {"$gte":delta_from}

        if day_to:
            delta_to = datetime.datetime.now() - datetime.timedelta(days=day_to)
            match_filter_dict =  {**match_filter_dict, "$lte":delta_to}

        date_limiter = {
            "year": {"year": "$date.year"},
            "month": {"year": "$date.year", "month": "$date.month"},
            "day": {"year": "$date.year", "month": "$date.month",
                    "day": "$date.day"},
            "hour": {"year": "$date.year", "month": "$date.month",
                     "day": "$date.day", "hour": "$date.hour"},
            "minute": {"year": "$date.year", "month": "$date.month",
                     "day": "$date.day", "hour": "$date.hour",
                     "minute": "$date.minute"},
            "second": {"year": "$date.year", "month": "$date.month",
                     "day": "$date.day", "hour": "$date.hour",
                     "minute": "$date.minute", "second": "$date.second"}
        }

        pipeline = [
            {
                "$match": {
                    "timestamp": match_filter_dict,
                    "metadata.user_id": user_id,
                    "metadata.endpoint": endpoint
                }
            },
            {
                "$project": {
                    "date": {
                        "$dateToParts": { "date": "$timestamp" }
                    },
                    "request": "$request"
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": date_limiter[slice]
                    },
                    "sum_request": { "$sum": "$request" }
                }
            }
        ]

        dataset = self.ts_collection.aggregate(pipeline)
        return await dataset.to_list(length=None)

    async def find_all_property(self, collection, key: str):
        """Find all properties in a collection"""
        dataset = collection.find({}, {key:1})
        return await dataset.to_list(length=None)

    async def find_all_users(self):
        """Find all users in the users collection"""
        user_list = await self.find_all_property(self.user_collection, "user_id")
        user_id_list = []
        for user in user_list:
            user_id_list.append(user['user_id'])

        return user_id_list
