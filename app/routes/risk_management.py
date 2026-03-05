"""Risk Management Routes"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.utils.rate_limiting import get_client_identifier
from app.utils.template_context import get_common_context

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/risk-management", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def risk_management_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = request.cookies.get("user_id") or get_client_identifier(request)
    context = get_common_context(request, user_id, "risk-management")
    
    return templates.TemplateResponse("risk_management.html", context)
