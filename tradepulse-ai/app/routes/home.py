"""
Home Route
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.utils.rate_limiting import get_client_identifier
from app.utils.template_context import get_common_context
from app.services.portfolio_manager import PortfolioManager

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize services
portfolio_manager = PortfolioManager()

@router.get("/", response_class=HTMLResponse)
@router.get("/home", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def home_page(request: Request):
    """Home page with all features"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = request.cookies.get("user_id") or get_client_identifier(request)
    portfolio = portfolio_manager.get_portfolio(user_id)
    
    context = get_common_context(
        request, 
        user_id, 
        "home",
        portfolio_count=len(portfolio.holdings),
        current_year=2024
    )
    return templates.TemplateResponse("home.html", context)
