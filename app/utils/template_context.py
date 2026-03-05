"""
Template Context Helper
Provides common context data for all templates
"""
from app.services.chatbot_providers import ChatbotManager
from app.services.user_api_keys import UserAPIKeyManager
from app.services.watchlist_manager import WatchlistManager


# Initialize services (singleton pattern)
_chatbot_manager = None
_user_api_key_manager = None
_watchlist_manager = None


def get_services():
    """Get initialized services"""
    global _chatbot_manager, _user_api_key_manager, _watchlist_manager
    
    if _chatbot_manager is None:
        _chatbot_manager = ChatbotManager()
    if _user_api_key_manager is None:
        _user_api_key_manager = UserAPIKeyManager()
    if _watchlist_manager is None:
        _watchlist_manager = WatchlistManager()
    
    return _chatbot_manager, _user_api_key_manager, _watchlist_manager


def get_common_context(request, user_id: str, page: str, **extra_context):
    """
    Get common template context with chatbot providers, watchlist, etc.
    
    Args:
        request: FastAPI Request object
        user_id: User identifier
        page: Page identifier
        **extra_context: Additional context variables
    
    Returns:
        dict: Template context
    """
    chatbot_manager, user_api_key_manager, watchlist_manager = get_services()
    
    # Get user API keys and chatbot providers
    user_api_keys = user_api_key_manager.get_all_keys(user_id)
    try:
        chatbot_providers = chatbot_manager.get_available_providers(user_api_keys)
    except Exception:
        chatbot_providers = []
    
    # Get watchlist
    watchlist = watchlist_manager.get_watchlist(user_id)
    
    # Build base context
    from app.core.config import settings
    context = {
        "request": request,
        "page": page,
        "app_name": settings.APP_NAME,
        "chatbot_providers": chatbot_providers,
        "watchlist": watchlist,
        "user_id": user_id,
        **extra_context
    }
    
    return context
