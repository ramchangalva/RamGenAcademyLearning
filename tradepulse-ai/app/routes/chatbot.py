"""Chatbot Routes"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from app.core.config import settings
from app.utils.rate_limiting import get_client_identifier
from app.services.chatbot_providers import ChatbotManager
from app.services.user_api_keys import UserAPIKeyManager
from app.utils.input_validation import sanitize_user_id, sanitize_error_message

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

# Initialize services
chatbot_manager = ChatbotManager()
user_api_key_manager = UserAPIKeyManager()

@router.get("/api/chatbot/providers")
@limiter.limit("60/minute")
async def get_providers(request: Request):
    """Get available chatbot providers and their models"""
    try:
        user_id = request.cookies.get("user_id") or get_client_identifier(request)
        user_api_keys = user_api_key_manager.get_all_keys(user_id)
        providers = chatbot_manager.get_available_providers(user_api_keys)
        return JSONResponse(content={"providers": providers})
    except Exception as e:
        logger.error(f"Error getting chatbot providers: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error fetching providers"}
        )

@router.post("/api/chatbot/chat")
@limiter.limit("30/minute")
async def chatbot_chat(request: Request):
    """Chat with AI using configured provider"""
    try:
        data = await request.json()
        provider_name = data.get("provider", "openai")
        model = data.get("model")
        messages = data.get("messages", [])
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens", 1000)
        
        if not messages:
            raise HTTPException(
                status_code=400,
                detail="Messages are required"
            )
        
        # Validate messages format
        if not isinstance(messages, list):
            raise HTTPException(
                status_code=400,
                detail="Messages must be a list"
            )
        
        # Validate message count and content length
        if len(messages) > 100:  # Limit conversation history
            raise HTTPException(
                status_code=400,
                detail="Too many messages in conversation"
            )
        
        # Validate each message
        for msg in messages:
            if not isinstance(msg, dict):
                raise HTTPException(
                    status_code=400,
                    detail="Each message must be a dictionary"
                )
            content = msg.get("content", "")
            if len(str(content)) > 10000:  # Limit message length
                raise HTTPException(
                    status_code=400,
                    detail="Message content too long"
                )
        
        # Validate temperature and max_tokens
        if temperature < 0 or temperature > 2:
            temperature = 0.7
        if max_tokens < 1 or max_tokens > 4000:
            max_tokens = 1000
        
        # Get user ID and API keys
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        user_api_keys = user_api_key_manager.get_all_keys(user_id)
        
        # Get available models if model not specified
        if not model:
            models = chatbot_manager.get_provider_models(provider_name)
            if models:
                model = models[0]  # Use first available model
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"No models available for provider {provider_name}"
                )
        
        result = chatbot_manager.chat(
            provider_name=provider_name,
            messages=messages,
            model=model,
            user_api_keys=user_api_keys,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Chatbot error")
            )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@router.get("/api/chatbot/models/{provider}")
@limiter.limit("60/minute")
async def get_provider_models(request: Request, provider: str):
    """Get available models for a provider"""
    try:
        models = chatbot_manager.get_provider_models(provider)
        return JSONResponse(content={"models": models})
    except Exception as e:
        logger.error(f"Error getting models for {provider}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error fetching models"}
        )

@router.post("/api/chatbot/keys")
@limiter.limit("30/minute")
async def save_api_key(request: Request):
    """Save API key for a provider"""
    try:
        data = await request.json()
        provider = data.get("provider", "").strip()
        api_key = data.get("api_key", "").strip()
        base_url = data.get("base_url", "").strip() if data.get("base_url") else None
        
        # Validate inputs
        if not provider or not api_key:
            return JSONResponse(
                status_code=400,
                content={"error": "Provider and API key are required"}
            )
        
        # Validate provider name
        from app.utils.input_validation import validate_provider_name, sanitize_user_id, sanitize_error_message
        is_valid, error_msg = validate_provider_name(provider)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": error_msg or "Invalid provider"}
            )
        
        # Validate API key length
        if len(api_key) > 500:
            return JSONResponse(
                status_code=400,
                content={"error": "API key too long"}
            )
        
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        
        try:
            user_api_key_manager.set_api_key(user_id, provider, api_key, base_url)
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"error": str(e)}
            )
        
        return JSONResponse(content={
            "success": True,
            "message": f"API key saved for {provider}"
        })
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@router.get("/api/chatbot/keys")
@limiter.limit("60/minute")
async def get_api_keys(request: Request):
    """Get all API keys for the user (masked)"""
    try:
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        keys = user_api_key_manager.get_all_keys(user_id)
        
        # Mask API keys for security (show only last 4 characters)
        masked_keys = {}
        for provider, key_data in keys.items():
            api_key = key_data.get('api_key', '')
            if api_key:
                masked_key = '*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '****'
                masked_keys[provider] = {
                    'api_key': masked_key,
                    'base_url': key_data.get('base_url'),
                    'has_key': True
                }
            else:
                masked_keys[provider] = {'has_key': False}
        
        return JSONResponse(content={"keys": masked_keys})
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.delete("/api/chatbot/keys/{provider}")
@limiter.limit("30/minute")
async def delete_api_key(request: Request, provider: str):
    """Delete API key for a provider"""
    try:
        user_id = request.cookies.get("user_id") or get_client_identifier(request)
        success = user_api_key_manager.delete_api_key(user_id, provider)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"API key deleted for {provider}"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"error": f"No API key found for {provider}"}
            )
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
