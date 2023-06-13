"""Utils functions for database."""
import os
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Union, Any

from jose import jwt

def gen_random_string():
    """Generate a random string"""
    return ''.join(
        random.choices(string.ascii_lowercase, k=random.randint(5, 10))
    )

def hash_api_key(api_key):
    """Hash input api key"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_hashed_key(api_key, hashed_api_key):
    """Validate hashed key with the original key"""
    return hash_api_key(api_key) == hashed_api_key

def generate_api_key(user_id: str) -> str:
    """Generate API key"""
    try:
        salt = str(os.getenv("API_SALT")) \
               if os.getenv("API_SALT") else gen_random_string()
        key = user_id + salt
        generated_key = hash_api_key(key)

        # Format the key to your needs
        formated_key = f"mci-{generated_key}"
        return formated_key

    except Exception as exception:
        raise exception

def create_access_token(jwt_secret_key: str,
                        algorithm: str,
                        access_token_expire_minutes: int,
                        subject: Union[str, Any],
                        expires_delta: int = None) -> str:
    """Generate JWT access token"""
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=access_token_expire_minutes)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, jwt_secret_key, algorithm)
    return encoded_jwt

def create_refresh_token(jwt_refresh_secret_key: str,
                         algorithm: str,
                         refresh_token_expire_minutes: int,
                         subject: Union[str, Any],
                         expires_delta: int = None) -> str:
    """Generate refresh JWT token"""
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=refresh_token_expire_minutes)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, jwt_refresh_secret_key, algorithm)
    return encoded_jwt
