"""Watchlist Routes"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.utils.rate_limiting import get_client_identifier
from app.services.watchlist_manager import WatchlistManager
from app.utils.input_validation import validate_symbol, sanitize_user_id, sanitize_error_message
from app.core.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
import logging

logger = logging.getLogger(__name__)

# Initialize service
watchlist_manager = WatchlistManager()

@router.get("/api/watchlist")
@limiter.limit("60/minute")
async def get_watchlist(request: Request):
    """Get user's watchlist"""
    try:
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        watchlist = watchlist_manager.get_watchlist(user_id)
        return JSONResponse(content={
            "stocks": watchlist,
            "count": len(watchlist)
        })
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@router.post("/api/watchlist/add")
@limiter.limit("30/minute")
async def add_to_watchlist(request: Request):
    """Add stock to watchlist"""
    try:
        data = await request.json()
        symbol = data.get("symbol", "").strip()
        asset_type = data.get("asset_type", "stock")
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        
        # Validate symbol
        is_valid, error_msg = validate_symbol(symbol, asset_type)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg or "Invalid symbol")
        
        symbol = symbol.upper()
        
        # Limit watchlist size
        current_watchlist = watchlist_manager.get_watchlist(user_id)
        if len(current_watchlist) >= 50:  # Max 50 stocks
            raise HTTPException(status_code=400, detail="Watchlist is full (maximum 50 stocks)")
        
        success = watchlist_manager.add_stock(user_id, symbol)
        watchlist = watchlist_manager.get_watchlist(user_id)
        
        response = JSONResponse(content={
            "success": success,
            "message": f"{symbol} added to watchlist" if success else f"{symbol} already in watchlist",
            "watchlist": watchlist
        })
        
        # Set user_id cookie if not exists (with security flags)
        if not request.cookies.get("user_id"):
            response.set_cookie(
                "user_id", 
                user_id, 
                max_age=31536000,  # 1 year
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite="strict"
            )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@router.post("/api/watchlist/remove")
@limiter.limit("30/minute")
async def remove_from_watchlist(request: Request):
    """Remove stock from watchlist"""
    try:
        data = await request.json()
        symbol = data.get("symbol", "").strip()
        asset_type = data.get("asset_type", "stock")
        user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
        
        # Validate symbol
        is_valid, error_msg = validate_symbol(symbol, asset_type)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg or "Invalid symbol")
        
        symbol = symbol.upper()
        
        success = watchlist_manager.remove_stock(user_id, symbol)
        watchlist = watchlist_manager.get_watchlist(user_id)
        
        return JSONResponse(content={
            "success": success,
            "message": f"{symbol} removed from watchlist" if success else f"{symbol} not in watchlist",
            "watchlist": watchlist
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )
