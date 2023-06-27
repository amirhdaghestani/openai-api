"""This module sets configs for database."""
import os
from typing import Union, Optional, Dict
from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError
from bson import ObjectId


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
    db_admin_collection = str(os.getenv("DB_ADMIN_COLLECTION")) \
                         if os.getenv("DB_ADMIN_COLLECYION") else "Admin"
    db_ts_collection = str(os.getenv("DB_TS_COLLECTION")) \
                       if os.getenv("DB_TS_COLLECYION") else "ts"

    def __init__(self, db_url: str=None, db_name: str=None,
                 db_user_collection: str=None,
                 db_admin_collection: str=None,
                 db_ts_collection: str=None) -> None:
        if db_url:
            self.db_url = db_url
        if db_name:
            self.db_name = db_name
        if db_user_collection:
            self.db_user_collection = db_user_collection
        if db_admin_collection:
            self.db_admin_collection = db_admin_collection
        if db_ts_collection:
            self.db_ts_collection = db_ts_collection


class PyObjectId(ObjectId):
    """Custom Type for reading MongoDB IDs"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Validator function"""
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid object_id")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Permissions(BaseModel):
    """Custom class for permissions"""
    text_completion_models: bool=True
    chat_completion_models: bool=True
    embeddings: bool=True
    fine_tunes: bool=False

PERMISSION_KEYS_LIST = ["text_completion_models",
                        "chat_completion_models",
                        "embeddings",
                        "fine_tune"]
# Message class defined in Pydantic
class User(BaseModel):
    """Custom class for User data"""
    user_id: str
    name: str
    request_limit: Optional[int]=1000
    fine_tune_limit: Optional[int]=2
    permissions: Optional[Dict]={
        "text_completion_models": True,
        "chat_completion_models": True,
        "embeddings": True,
        "fine_tune": False
    }
    @validator('permissions', pre=True)
    def permissions_check(cls, v):
        if set(PERMISSION_KEYS_LIST) != set(v.keys()):
            raise ValidationError

        return v

# Message class defined in Pydantic
class UserUpdate(BaseModel):
    """Custom class for User data"""
    user_id: str
    name: Optional[str]=None
    request_limit: Optional[int]=None
    fine_tune_limit: Optional[int]=None
    permissions: Optional[dict]=None
    @validator('permissions', pre=True)
    def permissions_check(cls, v):
        if v is None:
            return v
        if set(PERMISSION_KEYS_LIST) != set(v.keys()):
            raise ValidationError

        return v

class Completions(BaseModel):
    """Custom class for Completions data"""
    model: str="text-davinci-003"
    prompt: Union[str, list]="Hey, How are you?"
    suffix: Optional[str]=None
    max_tokens: Optional[int]=None
    temperature: Optional[float]=None
    top_p: Optional[float]=None
    n: Optional[int]=None
    stream: Optional[bool]=None
    logprobs: Optional[int]=None
    echo: Optional[bool]=None
    stop: Optional[Union[str, list]]=None
    presence_penalty: Optional[float]=None
    frequency_penalty: Optional[float]=None
    best_of: Optional[int]=None
    logit_bias: Optional[dict]=None
    user: Optional[str]=None


class ChatCompletions(BaseModel):
    """Custom class for Chat Completions data"""
    model: str="gpt-3.5-turbo"
    messages: list=[{"role": "user", "content": "Hey, How are you?"}]
    temperature: Optional[float]=None
    top_p: Optional[float]=None
    n: Optional[int]=None
    stream: Optional[bool]=None
    stop: Optional[Union[str, list]]=None
    max_tokens: Optional[int]=None
    presence_penalty: Optional[float]=None
    frequency_penalty: Optional[float]=None
    logit_bias: Optional[dict]=None
    user: Optional[str]=None


class Embeddings(BaseModel):
    """Custom class for Chat Completions data"""
    model: str="text-embedding-ada-002"
    input: Union[str, list]="Random text to test embedding"
    user: Optional[str]=None


class FineTunes(BaseModel):
    """Custom class for Fine Tuning"""
    training_file: str
    validation_file: Optional[str]=None
    model: Optional[str]=None
    n_epochs: Optional[int]=None
    batch_size: Optional[int]=None
    learning_rate_multiplier: Optional[float]=None
    prompt_loss_weight: Optional[float]=0.01
    compute_classification_metrics: Optional[bool]=None
    classification_n_classes: Optional[int]=None
    classification_positive_class: Optional[str]=None
    classification_betas: Optional[list]=None
    suffix: Optional[str]=None
