"""This module handles schemas for input API call"""
from typing import Union, Optional, Dict
from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError
from bson import ObjectId


PERMISSION_KEYS_LIST = ["text_completion_models",
                        "chat_completion_models",
                        "embeddings",
                        "fine_tune"]

PRIVILEGE_LIST = ["owner",
                  "admin",
                  "user"]

ADMIN_LIST = ["owner", "admin"]


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


# User class defined in Pydantic
class User(BaseModel):
    """Custom class for User data"""
    user_id: str
    password: str
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
    privilege: Optional[str]="user"
    @validator('privilege', pre=True)
    def privilege_check(cls, v):
        if v not in PRIVILEGE_LIST:
            raise ValidationError
        return v


# UserUpdate class defined in Pydantic
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
    privilege: Optional[str]=None
    @validator('privilege', pre=True)
    def privilege_check(cls, v):
        if v not in PRIVILEGE_LIST:
            raise ValidationError
        return v


# UserUpdatePass class defined in Pydantic
class UserUpdatePass(BaseModel):
    """Custom class for User data"""
    user_id: str
    password: str

# Password class defined in Pydantic
class Password(BaseModel):
    """Custom class for Password"""
    password: str
    old_password: str



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
