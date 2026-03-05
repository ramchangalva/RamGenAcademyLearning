"""Market Scanner Routes"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from app.core.config import settings
from app.services.ai_market_scanner import AIMarketScanner
from app.utils.rate_limiting import get_client_identifier
from app.utils.template_context import get_common_context

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

# Initialize service
market_scanner = AIMarketScanner()

@router.get("/market-scanner", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def market_scanner_page(request: Request):
    """Market scanner page"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = request.cookies.get("user_id") or get_client_identifier(request)
    context = get_common_context(request, user_id, "market-scanner")
    
    return templates.TemplateResponse("market_scanner.html", context)

@router.get("/api/market/scan")
@limiter.limit("30/minute")
async def scan_market(request: Request, scan_type: str = "all", timeframe: str = "swing", asset_type: str = "all", signal_type: str = "all"):
    """AI Market Scanner endpoint"""
    try:
        # Map signal_type to scan_type
        scan_type_map = {
            "all": "all",
            "breakout": "breakouts",
            "reversal": "reversals",
            "volume": "volume_spikes",
            "trend": "trend_changes"
        }
        actual_scan_type = scan_type_map.get(signal_type, scan_type)
        
        filters = {
            'timeframe': timeframe,
            'asset_type': asset_type
        }
        results = market_scanner.scan_market(scan_type=actual_scan_type, filters=filters)
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Error in market scan: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
