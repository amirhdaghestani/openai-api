"""This module handles request to admin API"""
import json

import requests

from configs.admin_frontend_config import AdminFronendConfig
from logger.ve_logger import VeLogger


class AdminRequest:
    """This class handles requests to Admin API"""

    # Initialize logger
    logger = VeLogger()

    def __init__(self, admin_frontend_config: AdminFronendConfig=None) -> None:
        """Initializer of class
        
        Args:
            admin_frontend_config (AdminFrontendConfig): Necessary Configs.

        Returns:
            None
        
        Raises:
            ValueError: If admin_frontend_config is not provided.

        """
        # Check Arguments
        if admin_frontend_config is None:
            self.logger.error("admin frontend config is None.")
            raise ValueError(
                "Provide admin_frontend_config when initializing class.")

        # Set attributes
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        self.is_init = False
        self.init_api_key = admin_frontend_config.init_api_key
        self.token_url = admin_frontend_config.token_url
        self.add_user_url = admin_frontend_config.add_user_url
        self.edit_user_url = admin_frontend_config.edit_user_url
        self.delete_user_url = admin_frontend_config.delete_user_url
        self.get_user_url = admin_frontend_config.get_user_url
        self.get_record_user_url = admin_frontend_config.get_record_user_url
        self.init_url = admin_frontend_config.init_url
        self.timeout = admin_frontend_config.request_timeout

    def get_token(self, data: dict):
        """Get token from token endpoint

        Args:
            data (dict): User login information.

        Returns:
            dict: Result of API call.

        """
        results = requests.post(self.token_url,
                                data=data, timeout=self.timeout)

        if results.status_code == 200:
            content = json.loads(results.content)
            self.access_token = content['access_token']
            self.refresh_token = content['refresh_token']
            self.get_current_user()

        return results

    def is_db_init(self):
        """Get token from token endpoint

        Args:
            None

        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.init_api_key}
        results = requests.get(self.init_url, headers=headers,
                               timeout=self.timeout)

        if results.status_code == 200:
            content = json.loads(results.content)
            self.is_init = content

        return results

    def db_init(self, data: dict):
        """Get token from token endpoint

        Args:
            data (dict): Admin user information.

        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.init_api_key}
        results = requests.post(self.init_url, json=data, headers=headers,
                                timeout=self.timeout)

        if results.status_code == 200 or results.status_code == 201:
            self.is_init = True

        return results


    def add_user(self, data):
        """Add user

        Args:
            data (dict): User to create information.

        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.access_token}
        results = requests.post(self.add_user_url, json=data, headers=headers,
                                timeout=self.timeout)

        return results

    def update_user(self, data):
        """Update user

        Args:
            data (dict): User to update information.

        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.access_token}
        results = requests.put(self.edit_user_url, json=data, headers=headers,
                               timeout=self.timeout)

        return results

    def get_user(self, user_id: str):
        """Get user
        
        Args:
            user_id (str): ID of the user to retrieve.
        
        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.access_token}
        results = requests.get(self.get_user_url + "/" + user_id,
                               headers=headers, timeout=self.timeout)

        return results

    def get_current_user(self):
        """Get current user
        
        Args:
            None
        
        Returns:
            dict: Result of API call.

        """
        results = self.get_user("me")

        if results.status_code == 200:
            content = json.loads(results.content)
            self.user_info = content

        return results

    def get_all_user(self):
        """Get all user
        
        Args:
            None
        
        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.access_token}
        results = requests.get(self.get_user_url,
                               headers=headers, timeout=self.timeout)

        return results

    def delete_user(self, user_id: str):
        """Delete user
        
        Args:
            user_id (str): ID of the user to retrieve.
        
        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.access_token}
        results = requests.delete(self.delete_user_url + "/" + user_id,
                                  headers=headers, timeout=self.timeout)

        return results

    def change_password(self, data):
        """Delete user
        
        Args:
            data (dict): User to update password.
        
        Returns:
            dict: Result of API call.

        """
        headers = {"Authorization": "Bearer " + self.access_token}
        results = requests.put(self.get_user_url + "/me/password",
                               json=data, headers=headers,
                               timeout=self.timeout)

        return results

    def get_record(self, user_id: str, endpoint: str, day_from: float,
                   day_to: float=None, slice: str=None):
        """Get user record

        Args:
            user_id (str): ID of the user to retrieve.
        
        Returns:
            dict: Result of API call.

        """
        params = {'endpoint': endpoint, 'day_from': day_from,
                    'day_to': day_to, 'slice': slice}
        headers = {"Authorization": "Bearer " + self.access_token}
        results = requests.get(self.get_record_user_url.format(user_id),
                                params=params, headers=headers,
                                timeout=self.timeout)

        return results
