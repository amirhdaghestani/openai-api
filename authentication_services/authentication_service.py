"""This module handles authentication."""
from datetime import datetime
import json

from fastapi.security.api_key import APIKeyHeader
from fastapi.security import OAuth2PasswordBearer
from fastapi import Security, HTTPException
from jose import jwt
from pydantic import ValidationError

from logger.ve_logger import VeLogger
from configs.authentication_config import AuthenticationConfig
from utils.database_utils import create_access_token, create_refresh_token


class AuthenticationService:
    """Class for authentications."""

    # Initialize logger
    ve_logger = VeLogger()

    api_key_header = APIKeyHeader(name="Authorization", auto_error=False,
                                  scheme_name="API Key")
    init_token_header = APIKeyHeader(name="Authorization", auto_error=False,
                                     scheme_name="Init API Key")

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/token",
                                         scheme_name="JWT")

    def __init__(self, database_service, auth_config: AuthenticationConfig) -> None:
        """Initializer of class"""
        self.database = database_service

        self.auth_config = auth_config

    def _get_api_key(self, authorization: str):
        """Get the API key"""
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        token = authorization.split(" ")[1]
        return token

    async def api_key_auth(self, api_key: str=Security(api_key_header)):
        """Validate API key provided

        Args:
            api_key: API key provided in the header.

        """
        api_key = self._get_api_key(api_key)
        result = await self.database.verify_api_key(token=api_key)
        if result['acknowledged'] is False:
            raise HTTPException(status_code=result['status_code'],
                                detail=result['message'])
        else:
            result.pop('acknowledged')
            result.pop('password')
            return result

    async def init_key_auth(self, init_token: str=Security(init_token_header)):
        """Validate API key provided

        Args:
            api_key: API key provided in the header.

        """
        init_token = self._get_api_key(init_token)
        result = init_token == self.auth_config.initialization_token
        if result is False:
            raise HTTPException(status_code=401,
                                detail="Init token is not valid.")
        else:
            return result

    async def validate_token(self, token: str=Security(oauth2_scheme)):
        """Validate API key provided"""
        try:
            payload = jwt.decode(
                token, self.auth_config.jwt_secret_key,
                algorithms=[self.auth_config.jwt_algorithm]
            )

            if datetime.fromtimestamp(payload['exp']) < datetime.now():
                raise HTTPException(
                    status_code = 401,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            for key, value in payload.items():
                if isinstance(value, str):
                    payload[key] = eval(value)
            return payload
        except(jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=403,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def generate_access_token(self, subject: str):
        """Generate access token."""
        return create_access_token(
            jwt_secret_key=self.auth_config.jwt_secret_key,
            algorithm=self.auth_config.jwt_algorithm,
            access_token_expire_minutes=self.auth_config.access_token_expire_minute,
            subject=subject)

    def generate_refresh_token(self, subject: str):
        """Generate refresh access token."""
        return create_refresh_token(
            jwt_refresh_secret_key=self.auth_config.jwt_refresh_secret_key,
            algorithm=self.auth_config.jwt_algorithm,
            refresh_token_expire_minutes=self.auth_config.refresh_token_expire_minute,
            subject=subject)
