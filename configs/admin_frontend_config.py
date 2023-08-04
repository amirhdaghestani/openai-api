"""This module contains configs for admin frontend"""
import os


class AdminFronendConfig:
    """Necessary configs for admin frontend."""
    host = str(os.getenv("ADMIN_HOST")) \
           if os.getenv("ADMIN_HOST") else "0.0.0.0"
    port = int(os.getenv("ADMIN_PORT")) \
           if os.getenv("ADMIN_PORT") else 5010
    cdn = bool(os.getenv("ADMIN_CDN") != 'false') \
          if os.getenv("ADMIN_CDN") else True
    token_url = str(os.getenv("ADMIN_TOKEN_URL")) \
                if os.getenv("ADMIN_TOKEN_URL") else None
    add_user_url = str(os.getenv("ADMIN_ADD_USER_URL")) \
                   if os.getenv("ADMIN_ADD_USER_URL") else None
    edit_user_url = str(os.getenv("ADMIN_EDIT_USER_URL")) \
                    if os.getenv("ADMIN_EDIT_USER_URL") else None
    delete_user_url = str(os.getenv("ADMIN_DELETE_USER_URL")) \
                      if os.getenv("ADMIN_DELETE_USER_URL") else None
    get_user_url = str(os.getenv("ADMIN_GET_USER_URL")) \
                   if os.getenv("ADMIN_GET_USER_URL") else None
    init_url = str(os.getenv("ADMIN_INIT_URL")) \
                   if os.getenv("ADMIN_INIT_URL") else None
    get_record_user_url = str(os.getenv("ADMIN_GET_RECORD_USER_URL")) \
                          if os.getenv("ADMIN_GET_RECORD_USER_URL") else None
    request_timeout = int(os.getenv("ADMIN_REQUEST_TIMEOUT")) \
                      if os.getenv("ADMIN_REQUEST_TIMEOUT") else 10
    init_api_key = str(os.getenv("ADMIN_INIT_API_KEY")) \
                   if os.getenv("ADMIN_INIT_API_KEY") else None

    def __init__(self, host: str=None, port: str=None, cdn: bool=None,
                 token_url: str=None, add_user_url: str=None,
                 edit_user_url: str=None, delete_user_url: str=None,
                 get_user_url: str=None, get_record_user_url: str=None,
                 request_timeout: int=None, init_api_key: str=None) -> None:
        if host:
            self.host = host
        if port:
            self.port = port
        if cdn:
            self.cdn = cdn
        if token_url:
            self.token_url = token_url
        if add_user_url:
            self.add_user_url = add_user_url
        if edit_user_url:
            self.edit_user_url = edit_user_url
        if delete_user_url:
            self.delete_user_url = delete_user_url
        if get_user_url:
            self.get_user_url = get_user_url
        if get_record_user_url:
            self.get_record_user_url = get_record_user_url
        if request_timeout:
            self.request_timeout = request_timeout
        if init_api_key:
            self.init_api_key = init_api_key
