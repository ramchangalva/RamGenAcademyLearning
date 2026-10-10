"""
Portfolio Management Routes
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from app.core.config import settings
from app.utils.rate_limiting import get_client_identifier
from app.services.portfolio_manager import PortfolioManager
from app.services.multi_asset_fetcher import MultiAssetFetcher
from app.models.portfolio import Holding
from app.utils.template_context import get_common_context

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize services
portfolio_manager = PortfolioManager()
asset_fetcher = MultiAssetFetcher()

@router.get("/portfolio", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def portfolio_page(request: Request):
    """Portfolio management page"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = request.cookies.get("user_id") or get_client_identifier(request)
    portfolio = portfolio_manager.get_portfolio(user_id)
    performance = portfolio_manager.get_performance(user_id)
    
    # Update current prices
    prices = {}
    for holding in portfolio.holdings:
        try:
            asset_info = asset_fetcher.get_asset_info(holding.symbol, holding.asset_type)
            if asset_info and 'current_price' in asset_info and asset_info['current_price']:
                prices[f"{holding.symbol}_{holding.asset_type}"] = asset_info['current_price']
        except Exception:
            # Keep existing price if fetch fails
            continue
    
    if prices:
        portfolio_manager.update_holding_prices(user_id, prices)
        portfolio = portfolio_manager.get_portfolio(user_id)
        performance = portfolio_manager.get_performance(user_id)
    
    context = get_common_context(
        request, 
        user_id, 
        "portfolio",
        portfolio=portfolio,
        performance=performance
    )
    return templates.TemplateResponse("portfolio.html", context)

@router.get("/api/portfolio", response_class=JSONResponse)
@limiter.limit("60/minute")
async def get_portfolio_api(request: Request):
    """Get portfolio as JSON"""
    user_id = request.cookies.get("user_id") or get_client_identifier(request)
    portfolio = portfolio_manager.get_portfolio(user_id)
    performance = portfolio_manager.get_performance(user_id)
    
    return JSONResponse(content={
        "portfolio": portfolio.dict(),
        "performance": performance.dict()
    })

@router.post("/api/portfolio/add", response_class=JSONResponse)
@limiter.limit("30/minute")
async def add_holding(request: Request):
    """Add holding to portfolio"""
    try:
        data = await request.json()
        user_id = request.cookies.get("user_id") or get_client_identifier(request)
        
        holding = Holding(
            symbol=data.get("symbol", "").upper(),
            asset_type=data.get("asset_type", "stock"),
            quantity=float(data.get("quantity", 0)),
            purchase_price=float(data.get("purchase_price", 0)),
            current_price=float(data.get("current_price", 0)),
            notes=data.get("notes")
        )
        
        success = portfolio_manager.add_holding(user_id, holding)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"{holding.symbol} added to portfolio"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Failed to add holding"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/api/portfolio/remove", response_class=JSONResponse)
@limiter.limit("30/minute")
async def remove_holding(request: Request):
    """Remove holding from portfolio"""
    try:
        data = await request.json()
        user_id = request.cookies.get("user_id") or get_client_identifier(request)
        symbol = data.get("symbol", "").upper()
        asset_type = data.get("asset_type", "stock")
        
        success = portfolio_manager.remove_holding(user_id, symbol, asset_type)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"{symbol} removed from portfolio"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Holding not found"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
