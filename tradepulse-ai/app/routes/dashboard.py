"""
Dashboard Routes - Center of Intelligence for Stock Analysts
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import logging
import traceback

from app.core.config import settings
from app.utils.rate_limiting import get_client_identifier
from app.utils.template_context import get_common_context
from app.services.dashboard_service import DashboardService
from app.services.news_analyzer import NewsAnalyzer
from app.services.ai_stock_assistant import AIStockAssistant
from app.services.chatbot_providers import ChatbotManager
from app.services.user_api_keys import UserAPIKeyManager
from app.utils.input_validation import (
    validate_symbol, sanitize_user_id, sanitize_error_message,
    validate_asset_type, sanitize_string
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

# Initialize services
dashboard_service = DashboardService()
news_analyzer = NewsAnalyzer()
ai_stock_assistant = AIStockAssistant()
chatbot_manager = ChatbotManager()
user_api_key_manager = UserAPIKeyManager()


@router.get("/dashboard", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def dashboard_page(request: Request):
    """Dashboard page - Center of Intelligence"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
    
    # Get watchlist
    from app.services.watchlist_manager import WatchlistManager
    watchlist_manager = WatchlistManager()
    watchlist = watchlist_manager.get_watchlist(user_id)
    
    context = get_common_context(
        request,
        user_id,
        "dashboard",
        watchlist=watchlist
    )
    
    # Get dashboard data (with individual error handling to prevent one failure from breaking everything)
    try:
        # KPIs for watchlist stocks
        try:
            kpis_data = dashboard_service.get_watchlist_kpis(watchlist)
        except Exception as e:
            logger.error(f"Error getting KPIs: {e}")
            kpis_data = {'total_stocks': 0, 'kpis': [], 'summary': {'avg_price_change': 0, 'bullish_count': 0, 'bearish_count': 0, 'neutral_count': 0, 'total_volume': 0}}
        
        # Market overview
        try:
            market_overview = dashboard_service.get_market_overview()
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            market_overview = {'indices': []}
        
        # Top movers
        try:
            top_movers = dashboard_service.get_top_movers(watchlist)
        except Exception as e:
            logger.error(f"Error getting top movers: {e}")
            top_movers = {'gainers': [], 'losers': []}
        
        # Real-time news feed
        try:
            realtime_news = news_analyzer.get_realtime_news_feed(watchlist, hours_back=24, limit_per_symbol=3)
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            realtime_news = []
        
        context.update({
            'kpis_data': kpis_data,
            'market_overview': market_overview,
            'top_movers': top_movers,
            'realtime_news': realtime_news
        })
    except Exception as e:
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        logger.error(f"Error loading dashboard data: {error_msg}")
        if settings.DEBUG:
            logger.error(traceback.format_exc())
        context['error'] = error_msg
        # Set defaults to prevent template errors
        context.setdefault('kpis_data', {
            'total_stocks': 0, 
            'kpis': [], 
            'summary': {
                'avg_price_change': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0,
                'total_volume': 0
            }
        })
        context.setdefault('market_overview', {'indices': []})
        context.setdefault('top_movers', {'gainers': [], 'losers': []})
        context.setdefault('realtime_news', [])
    
    try:
        return templates.TemplateResponse("dashboard.html", context)
    except Exception as e:
        logger.error(f"Error rendering dashboard template: {e}")
        logger.error(traceback.format_exc())
        # Return a simple error page
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content=f"<h1>Error</h1><p>An error occurred: {str(e)}</p><pre>{traceback.format_exc()}</pre>",
            status_code=500
        )


@router.get("/api/dashboard/kpis")
@limiter.limit("60/minute")
async def get_dashboard_kpis(request: Request):
    """Get dashboard KPIs"""
    try:
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        from app.services.watchlist_manager import WatchlistManager
        watchlist_manager = WatchlistManager()
        watchlist = watchlist_manager.get_watchlist(user_id)
        
        kpis_data = dashboard_service.get_watchlist_kpis(watchlist)
        return JSONResponse(content=kpis_data)
    except Exception as e:
        logger.error(f"Error getting dashboard KPIs: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/api/dashboard/news")
@limiter.limit("60/minute")
async def get_dashboard_news(request: Request, hours_back: int = 24):
    """Get real-time news feed"""
    try:
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        from app.services.watchlist_manager import WatchlistManager
        watchlist_manager = WatchlistManager()
        watchlist = watchlist_manager.get_watchlist(user_id)
        
        news = news_analyzer.get_realtime_news_feed(watchlist, hours_back=hours_back)
        return JSONResponse(content={"news": news})
    except Exception as e:
        logger.error(f"Error getting dashboard news: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.post("/api/dashboard/ai-chat")
@limiter.limit("30/minute")
async def dashboard_ai_chat(request: Request):
    """AI chat with stock analysis context"""
    try:
        data = await request.json()
        messages = data.get("messages", [])
        symbol = data.get("symbol")  # Optional: if provided, adds context
        asset_type = data.get("asset_type", "stock")
        provider_name = data.get("provider", "openai")
        model = data.get("model")
        
        # Validate inputs
        if not messages:
            return JSONResponse(
                status_code=400,
                content={"error": "Messages are required"}
            )
        
        # Validate symbol if provided
        if symbol:
            is_valid, error_msg = validate_symbol(symbol, asset_type)
            if not is_valid:
                return JSONResponse(
                    status_code=400,
                    content={"error": error_msg or "Invalid symbol"}
                )
            symbol = symbol.upper().strip()
        
        # Validate asset type
        is_valid, error_msg = validate_asset_type(asset_type)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": error_msg or "Invalid asset type"}
            )
        
        # Validate message count and length
        if len(messages) > 100:
            return JSONResponse(
                status_code=400,
                content={"error": "Too many messages"}
            )
        
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "")
                if len(str(content)) > 10000:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Message content too long"}
                    )
        
        # Get user ID and API keys
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        user_api_keys = user_api_key_manager.get_all_keys(user_id)
        
        # Chat with context
        result = ai_stock_assistant.chat_with_context(
            messages=messages,
            symbol=symbol,
            asset_type=asset_type,
            provider_name=provider_name,
            model=model,
            user_api_keys=user_api_keys
        )
        
        if not result.get("success"):
            return JSONResponse(
                status_code=500,
                content=result
            )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error in dashboard AI chat: {e}")
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )


@router.get("/api/dashboard/market-overview")
@limiter.limit("60/minute")
async def get_market_overview(request: Request):
    """Get market overview"""
    try:
        overview = dashboard_service.get_market_overview()
        return JSONResponse(content=overview)
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/api/dashboard/top-movers")
@limiter.limit("60/minute")
async def get_top_movers(request: Request):
    """Get top movers"""
    try:
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        from app.services.watchlist_manager import WatchlistManager
        watchlist_manager = WatchlistManager()
        watchlist = watchlist_manager.get_watchlist(user_id)
        
        movers = dashboard_service.get_top_movers(watchlist)
        return JSONResponse(content=movers)
    except Exception as e:
        logger.error(f"Error getting top movers: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
