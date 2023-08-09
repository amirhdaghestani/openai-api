"""This is the main module."""
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sse_starlette.sse import EventSourceResponse
import json

from configs.database_config import DatabaseConfig
from configs.service_config import ServiceConfig
from configs.openai_config import OpenAIConfig
from configs.authentication_config import AuthenticationConfig
from database_services.database_service import DatabaseService
from openai_services.openai_service import OpenAIService
from schema.schema import (User, UserUpdate, UserUpdatePass, Password,
                           Completions, ChatCompletions,
                           Embeddings, FineTunes, ADMIN_LIST)

from authentication_services.authentication_service import AuthenticationService
from utils.http_exceptions import (limit_exception, forbidden_exception,
                                   owner_removal_exception,
                                   self_removal_exception,
                                   admin_remove_admin_exception,
                                   admin_add_owner_exception,
                                   admin_add_admin_exception,
                                   admin_update_owner_exception,
                                   admin_update_admin_exception,
                                   wrong_password_exception)


service_config = ServiceConfig()
database_config = DatabaseConfig()
database = DatabaseService(database_config=database_config)

openai_config = OpenAIConfig()
openai_service = OpenAIService(openai_config=openai_config)

auth_config = AuthenticationConfig()
auth_service = AuthenticationService(database_service=database,
                                     auth_config=auth_config)
app = FastAPI(docs_url=service_config.url_swagger,
              redoc_url=service_config.url_redoc)


@app.post("/admin/token", include_in_schema=False)
async def login(form_data: OAuth2PasswordRequestForm=Depends()):
    """Login endpoint"""
    result = await database.verify_admin(form_data.username, form_data.password)
    if result['acknowledged'] is False:
        raise wrong_password_exception

    result.pop("_id")
    result.pop("password")
    result.pop("api_key")
    result.pop("acknowledged")

    return {
        "access_token": auth_service.generate_access_token(result),
        "refresh_token": auth_service.generate_refresh_token(result)
    }

@app.post("/admin/users", include_in_schema=False)
async def add(user: User,  user_info: str=Depends(auth_service.validate_token)):
    """Add new user to database
    
    Args:
        user (User): Input user data.
        
    Returns:
        dict: result of adding data to database.
    
    """
    if user_info['sub']['privilege'] not in ADMIN_LIST:
        raise forbidden_exception

    if user_info['sub']['privilege'] == "admin":
        if user.privilege == "owner":
            raise admin_add_owner_exception
        if user.privilege == "admin":
            raise admin_add_admin_exception

    result = await database.add_new_user(user)
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return HTTPException(status_code=result['status_code'],
                             detail=result['API_key'])

@app.put("/admin/users", include_in_schema=False)
async def update(user: UserUpdate,
                 user_info: str=Depends(auth_service.validate_token)):
    """Update user in database
    
    Args:
        user (User): Input user data.
        
    Returns:
        dict: result of updating data in database.
    
    """
    if user_info['sub']['privilege'] not in ADMIN_LIST:
        raise forbidden_exception

    result = await database.retrieve_user(user.user_id, 'user_id')
    if result['acknowledged']:
        if user_info['sub']['privilege'] == "admin":
            if result['data']['privilege'] == "owner":
                raise admin_update_owner_exception
            if result['data']['privilege'] == "admin":
                raise admin_update_admin_exception

    result = await database.edit_user(user)
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return await database.retrieve_user(user.user_id, 'user_id')

@app.delete("/admin/users/{user_id}", include_in_schema=False)
async def delete_user(user_id: str,
                      user_info: str=Depends(auth_service.validate_token)):
    """Delete user in database

    Args:
        user_id (str): ID of the user data.

    Returns:
        dict: result of user data in database.

    """
    if user_info['sub']['privilege'] not in ADMIN_LIST:
        raise forbidden_exception

    if user_info['sub']['user_id'] == user_id:
        raise self_removal_exception

    result = await database.retrieve_user(user_id, 'user_id')
    if result['acknowledged']:
        if result['data']['privilege'] == "owner":
            raise owner_removal_exception
        if user_info['sub']['privilege'] == "admin" and \
            result['data']['privilege'] == "admin":
            raise admin_remove_admin_exception

    result = await database.delete_user(user_id, 'user_id')
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        await database.delete_request_ts_record(user_id)
        return result['data']

@app.put("/admin/users/me/password", include_in_schema=False)
async def change_password(password: Password,
                          user_info: str=Depends(auth_service.validate_token)):
    """Update user password

    Args:
        user_id (str): ID of the user data.

    Returns:
        dict: result of user data in database.

    """

    result = await database.verify_admin(username=user_info['sub']['user_id'],
                                         password=password.old_password)
    if result['acknowledged'] is False:
        raise wrong_password_exception

    user = UserUpdatePass(user_id=user_info['sub']['user_id'],
                          password=password.password)

    result = await database.edit_user(user)
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return await database.retrieve_user(user.user_id, 'user_id')

@app.get("/admin/users", include_in_schema=False)
async def get_all_user(user_info: str=Depends(auth_service.validate_token)):
    """Get all users in database

    Args:
        None

    Returns:
        dict: result of user data in database.

    """
    if user_info['sub']['privilege'] not in ADMIN_LIST:
        raise forbidden_exception
    result = await database.find_all_users()

    return result

@app.get("/admin/users/me", include_in_schema=False)
async def get_current_user(user_info: str=Depends(auth_service.validate_token)):
    """Get the current user in database

    Args:
        None

    Returns:
        dict: result of user data in database.

    """
    return user_info['sub']

@app.get("/admin/users/{user_id}", include_in_schema=False)
async def get_user(user_id: str,
                   user_info: str=Depends(auth_service.validate_token)):
    """Get user in database

    Args:
        user_id (str): ID of the user data.

    Returns:
        dict: result of user data in database.

    """
    if user_info['sub']['privilege'] not in ADMIN_LIST and \
        user_info['sub']['user_id'] != user_id:
        raise forbidden_exception

    result = await database.retrieve_user(user_id, 'user_id')
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return result['data']

@app.get("/admin/users/{user_id}/records", include_in_schema=False)
async def get_record(user_id: str, endpoint: str, day_from: float,
                     day_to: float=0.0, slice: str="hour",
                     user_info: str=Depends(auth_service.validate_token)):
    """Get ts record in database

    Args:
        user_id (str): ID of the user data.
        endpoint (str): Endpoint to get the data for.
        day_from (float): Start date to collect data.
        day_to (float): End date to collect data.
        slice (str): year, month, day, hour, minute, or second slice.

    Returns:
        list: result of ts data in database.

    """
    if user_info['sub']['privilege'] not in ADMIN_LIST and \
        user_info['sub']['user_id'] != user_id:
        raise forbidden_exception

    result = await database.get_ts_dates(user_id, endpoint=endpoint,
                                         day_from=day_from, day_to=day_to,
                                         slice=slice)

    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])

    return result["data"]

@app.get("/admin/init", dependencies=[Depends(auth_service.init_key_auth)],
         include_in_schema=False)
async def is_initialized():
    """Check if initialized

    Args:
        None

    Returns:
        bool: if database is intialized.

    """
    result = await database.is_init()

    return result

@app.post("/admin/init", dependencies=[Depends(auth_service.init_key_auth)],
          include_in_schema=False)
async def initialize(user: User):
    """Initialize database

    Args:
        user (User): Input owner data.

    Returns:
        dict: result of owner data in database.

    """
    result = await database.init(user=user)
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return HTTPException(status_code=result['status_code'],
                             detail=result['API_key'])

@app.get("/get")
async def retrieve_user(user_info: str=Depends(auth_service.api_key_auth)):
    """Get user in database
    
    Args:
        user_info (str): user data.
        
    Returns:
        dict: result of user data in database.
    
    """
    user_info.pop("api_key")
    return user_info

@app.post("/v1/completions")
async def completions(completions_args: Completions, request: Request,
                      user_info: str=Depends(auth_service.api_key_auth)):
    """Get completions API

    Args:
        completions_args (Completion): Input Completion data.

    Returns:
        OpenAIResult.
    
    """
    if user_info['request_limit'] == 0:
        raise limit_exception

    if not user_info['permissions']['text_completion_models']:
        raise forbidden_exception

    try:
        openai_result = openai_service.completions(
            **completions_args.dict(exclude_unset=True))
        await database.update_request_limit(hashed_api_key=user_info['api_key'])
        await database.add_request_ts_record(user_info['user_id'],
                                             endpoint="completions")
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception

    async def event_generator(messages):
        # If client closes connection, stop sending events
        for message in messages:
            if await request.is_disconnected():
                break
            # Checks for new messages and return them to client if any
            if message:
                yield {
                    "data": json.dumps(message)
                }

    if completions_args.stream:
        return EventSourceResponse(event_generator(openai_result))
    return openai_result

@app.post("/v1/chat/completions")
async def chat_completions(chat_completions_args: ChatCompletions, request: Request,
                           user_info: str=Depends(auth_service.api_key_auth)):
    """Get completions API

    Args:
        chat_completions_args (ChatCompletions): Input ChatCompletions data.

    Returns:
        OpenAIResult.
    
    """
    if user_info['request_limit'] == 0:
        raise limit_exception

    if not user_info['permissions']['chat_completion_models']:
        raise forbidden_exception

    try:
        openai_result = openai_service.chat_completions(
            **chat_completions_args.dict(exclude_unset=True))
        await database.update_request_limit(hashed_api_key=user_info['api_key'])
        await database.add_request_ts_record(user_info['user_id'],
                                             endpoint="chat_completions")
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception

    async def event_generator(messages):
        # If client closes connection, stop sending events
        for message in messages:
            if await request.is_disconnected():
                break

            # Checks for new messages and return them to client if any
            if message:
                yield {
                    "data": json.dumps(message)
                }

    if chat_completions_args.stream:
        return EventSourceResponse(event_generator(openai_result))
    return openai_result

@app.post("/v1/embeddings")
async def embeddings(embeddings_args: Embeddings,
                     user_info: str=Depends(auth_service.api_key_auth)):
    """Get completions API

    Args:
        embeddings_args (Embeddings): Input Embeddings data.

    Returns:
        OpenAIResult.

    """
    if user_info['request_limit'] == 0:
        raise limit_exception

    if not user_info['permissions']['embeddings']:
        raise forbidden_exception

    try:
        openai_result = openai_service.embeddings(
            **embeddings_args.dict(exclude_unset=True))
        await database.update_request_limit(hashed_api_key=user_info['api_key'])
        await database.add_request_ts_record(user_info['user_id'],
                                             endpoint="embeddings")
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception
    return openai_result

@app.post("/v1/files")
async def upload_files(purpose: str=Body(..., embed=True),
                       file: UploadFile = File(...),
                       user_info: str=Depends(auth_service.api_key_auth)):
    """Upload File API

    Args:
        upload_files_args (UploadFiles): Input UploadFiles data.

    Returns:
        OpenAIResult.

    """
    if not user_info['permissions']['fine_tune']:
        raise forbidden_exception

    try:
        upload_files_dict = {}
        upload_files_dict['file'] = file.file.read()
        upload_files_dict['user_provided_filename'] = file.filename
        upload_files_dict['purpose'] = purpose
        openai_result = openai_service.upload_files(**upload_files_dict)
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception
    return openai_result

@app.get("/v1/files")
async def list_files(user_info: str=Depends(auth_service.api_key_auth)):
    """Get list of uploaded files API

    Args:
        None

    Returns:
        OpenAIResult.

    """
    if not user_info['permissions']['fine_tune']:
        raise forbidden_exception

    try:
        openai_result = openai_service.list_files()
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception
    return openai_result

@app.post("/v1/fine-tunes")
async def fine_tunes(fine_tunes_args: FineTunes,
                     user_info: str=Depends(auth_service.api_key_auth)):
    """Fine-tune model via uploaded file API.

    Args:
        fine_tunes_args (FineTunes): Input FineTunes data.

    Returns:
        OpenAIResult.

    """
    if user_info['fine_tune_limit'] == 0:
        raise limit_exception

    if not user_info['permissions']['fine_tune']:
        raise forbidden_exception

    try:
        openai_result = openai_service.fine_tunes(
            **fine_tunes_args.dict(exclude_unset=True))
        await database.update_finetune_limit(hashed_api_key=user_info['api_key'])
        await database.add_request_ts_record(user_info['user_id'],
                                             endpoint="fine_tunes")
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception
    return openai_result

@app.get("/v1/fine-tunes/{fine_tune_id}")
async def retrieve_fine_tune(fine_tune_id: str,
                             user_info: dict=Depends(auth_service.api_key_auth)):
    """Retrieve a finetuning process API

    Args:
        fine_tune_id (str): id of the fine-tuning process.

    Returns:
        OpenAIResult.

    """
    if not user_info['permissions']['fine_tune']:
        raise forbidden_exception

    try:
        openai_result = openai_service.retrieve_fine_tune(fine_tune_id)
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception
    return openai_result

@app.get("/v1/fine-tunes/{fine_tune_id}/cancel")
async def cancel_fine_tune(fine_tune_id: str,
                           user_info: dict=Depends(auth_service.api_key_auth)):
    """Cancel a fine-tuning process API

    Args:
        fine_tune_id (str): id of the fine-tuning process.

    Returns:
        OpenAIResult.

    """
    if not user_info['permissions']['fine_tune']:
        raise forbidden_exception

    try:
        openai_result = openai_service.cancel_fine_tune(fine_tune_id)
        await database.update_finetune_limit(hashed_api_key=user_info['api_key'],
                                             cost=-1)
        await database.add_request_ts_record(user_id=user_info['user_id'],
                                             endpoint="fine_tunes",
                                             cost=-1)
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception
    return openai_result

@app.get("/v1/fine-tunes")
async def list_fine_tunes(user_info: str=Depends(auth_service.api_key_auth)):
    """Get list of fine-tuned models API

    Args:
        None

    Returns:
        OpenAIResult.

    """
    if not user_info['permissions']['fine_tune']:
        raise forbidden_exception

    try:
        openai_result = openai_service.list_fine_tunes()
    except Exception as exception:
        raise HTTPException(status_code=exception.http_status,
                            detail=str(exception)) from exception
    return openai_result


if __name__ == "__main__":
    uvicorn.run("app:app", host=service_config.host, port=service_config.port)
