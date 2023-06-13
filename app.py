"""This is the main module."""
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Body
from fastapi.security import OAuth2PasswordRequestForm

from configs.database_config import (DatabaseConfig, User, UserUpdate,
                                     Completions, ChatCompletions,
                                     Embeddings, FineTunes)
from configs.service_config import ServiceConfig
from configs.openai_config import OpenAIConfig
from database_services.database_service import DatabaseService
from openai_services.openai_service import OpenAIService

from authentication_services.authentication_service import AuthenticationService
from utils.http_exceptions import limit_exception, forbidden_exception

service_config = ServiceConfig()
database_config = DatabaseConfig()
database = DatabaseService(database_config=database_config)

openai_config = OpenAIConfig()
openai_service = OpenAIService(openai_config=openai_config)

auth_service = AuthenticationService(database_service=database)
app = FastAPI(docs_url=service_config.url_swagger,
              redoc_url=service_config.url_redoc)

@app.post("/admin/token")
async def login(form_data: OAuth2PasswordRequestForm=Depends()):
    """Login endpoint"""
    result = await database.verify_admin(form_data.username, form_data.password)
    if result['acknowledged'] is False:
        raise HTTPException(status_code=401,
                            detail="Incorrect username or password")
    return {
        "access_token": auth_service.generate_access_token(result['username']),
        "refresh_token": auth_service.generate_refresh_token(result['username'])
    }

@app.post("/admin/add", dependencies=[Depends(auth_service.validate_token)])
async def add(user: User):
    """Add new user to database
    
    Args:
        user (User): Input user data.
        
    Returns:
        dict: result of adding data to database.
    
    """
    result = await database.add_new_user(user)
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return HTTPException(status_code=result['status_code'],
                             detail=result['API_key'])

@app.put("/admin/update", dependencies=[Depends(auth_service.validate_token)])
async def update(user: UserUpdate):
    """Update user in database
    
    Args:
        user (User): Input user data.
        
    Returns:
        dict: result of updating data in database.
    
    """
    result = await database.edit_user(user)
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return await database.retrieve_user(user.user_id, 'user_id')

@app.get("/admin/get/{user_id}", 
         dependencies=[Depends(auth_service.validate_token)])
async def get_user(user_id: str):
    """Get user in database

    Args:
        user_id (str): ID of the user data.

    Returns:
        dict: result of user data in database.

    """
    result = await database.retrieve_user(user_id, 'user_id')
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return result['data']

@app.delete("/admin/delete/{user_id}", 
            dependencies=[Depends(auth_service.validate_token)])
async def delete_user(user_id: str):
    """Delete user in database

    Args:
        user_id (str): ID of the user data.

    Returns:
        dict: result of user data in database.

    """
    result = await database.delete_user(user_id, 'user_id')
    if result['acknowledged'] is False:
        raise HTTPException(status_code=result['status_code'],
                            detail=result['message'])
    else:
        return result['data']

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
async def completions(completions_args: Completions,
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
    except Exception as exception:
        raise HTTPException(status_code=503, detail=str(exception))
    return openai_result

@app.post("/v1/chat/completions")
async def chat_completions(chat_completions_args: ChatCompletions,
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
    except Exception as exception:
        raise HTTPException(status_code=503, detail=str(exception))
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
    except Exception as exception:
        raise HTTPException(status_code=503, detail=str(exception))
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
        raise HTTPException(status_code=503, detail=str(exception))
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
        raise HTTPException(status_code=503, detail=str(exception))
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
    except Exception as exception:
        raise HTTPException(status_code=503, detail=str(exception))
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
        raise HTTPException(status_code=503, detail=str(exception))
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
    except Exception as exception:
        raise HTTPException(status_code=503, detail=str(exception))
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
        raise HTTPException(status_code=503, detail=str(exception))
    return openai_result


if __name__ == "__main__":
   uvicorn.run("app:app", host="127.0.0.1", port=service_config.port,
               reload=True)
