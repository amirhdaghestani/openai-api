"""This module sets configs for database."""
import os


class DatabaseConfig:
    """Necessary configs for database.

    Attributes:
        url [required] (str): Database URL.
        db_name (str): Database name.
        db_user_collection (str): Collection name for users.

    """
    db_url = str(os.getenv("DB_URL")) \
              if os.getenv("DB_URL") else None
    db_name = str(os.getenv("DB_NAME")) \
              if os.getenv("DB_NAME") else "OPENAI_API"
    db_user_collection = str(os.getenv("DB_USER_COLLECTION")) \
                         if os.getenv("DB_USER_COLLECYION") else "Users"
    db_ts_collection = str(os.getenv("DB_TS_COLLECTION")) \
                       if os.getenv("DB_TS_COLLECYION") else "ts"

    def __init__(self, db_url: str=None, db_name: str=None,
                 db_user_collection: str=None,
                 db_ts_collection: str=None) -> None:
        if db_url:
            self.db_url = db_url
        if db_name:
            self.db_name = db_name
        if db_user_collection:
            self.db_user_collection = db_user_collection
        if db_ts_collection:
            self.db_ts_collection = db_ts_collection
