"""This module contains configs for authentication"""
import os


class AuthenticationConfig:
    """Necessary configs for Authentication.

    Attributes:

    """
    jwt_secret_key = str(os.getenv("JWT_SECRET_KEY")) \
                     if os.getenv("JWT_SECRET_KEY") else None
    jwt_refresh_secret_key = str(os.getenv("JWT_REFRESH_SECRET_KEY")) \
                             if os.getenv("JWT_REFRESH_SECRET_KEY") else None
    jwt_algorithm = str(os.getenv("JWT_ALGORITHM")) \
                    if os.getenv("JWT_ALGORITHM") else "HS256"
    access_token_expire_minute = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTE")) \
                                 if os.getenv("ACCESS_TOKEN_EXPIRE_MINUTE") \
                                 else 30
    refresh_token_expire_minute = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTE")) \
                                  if os.getenv("REFRESH_TOKEN_EXPIRE_MINUTE") \
                                  else 60*24*7
    initialization_token = str(os.getenv("AUTH_INIT_TOKEN")) \
                           if os.getenv("AUTH_INIT_TOKEN") \
                           else "admin"

    def __init__(self, jwt_secret_key: str=None,
                 jwt_refresh_secret_key: str=None,
                 jwt_algorithm: str=None,
                 access_token_expire_minute: int=None,
                 refresh_token_expire_minute: int=None,
                 initialization_token: str=None) -> None:
        if jwt_secret_key:
            self.jwt_secret_key = jwt_secret_key
        if jwt_refresh_secret_key:
            self.jwt_refresh_secret_key = jwt_refresh_secret_key
        if jwt_algorithm:
            self.jwt_algorithm = jwt_algorithm
        if access_token_expire_minute:
            self.access_token_expire_minute = access_token_expire_minute
        if refresh_token_expire_minute:
            self.refresh_token_expire_minute = refresh_token_expire_minute
        if initialization_token:
            self.initialization_token = initialization_token
