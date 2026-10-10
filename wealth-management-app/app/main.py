"""
Main FastAPI application
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.core.security import decode_access_token
from app.core.middleware import SecurityHeadersMiddleware
from app.api import advisor, auth, market, portfolio, retirement, settings_ai, trading
from app.models.user import User
from app.models.user_ai_settings import UserAISettings  # noqa: F401 — register model for create_all
from app.models.watchlist_symbol import WatchlistSymbol  # noqa: F401
from app.models.user_trading_integration import UserTradingIntegration  # noqa: F401

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Wealth Management Planning Application"
)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(auth.router)
app.include_router(advisor.router)
app.include_router(settings_ai.router)
app.include_router(trading.router)
app.include_router(market.router)
app.include_router(portfolio.router)
app.include_router(retirement.router)


async def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from cookie"""
    try:
        token = request.cookies.get("access_token")
        if not token:
            if settings.DEBUG:
                print("[!] No access_token cookie found in request")
            return None
        
        if settings.DEBUG:
            print(f"[+] Cookie found: {token[:30]}...")
        
        payload = decode_access_token(token)
        if not payload:
            if settings.DEBUG:
                print("[-] Failed to decode token")
            return None
        
        if settings.DEBUG:
            print(f"[+] Token decoded. Payload keys: {list(payload.keys())}")
        
        user_id = payload.get("sub")
        if not user_id:
            if settings.DEBUG:
                print("[-] No 'sub' in token payload")
            return None
        
        # Ensure user_id is an integer
        try:
            user_id_int = int(user_id)
            if settings.DEBUG:
                print(f"[+] User ID from token: {user_id_int} (converted from {type(user_id).__name__})")
        except (ValueError, TypeError) as e:
            if settings.DEBUG:
                print(f"[-] Invalid user_id type: {type(user_id)}, value: {user_id}, error: {e}")
            return None
        
        user = db.query(User).filter(User.id == user_id_int).first()
        if user and user.is_active:
            if settings.DEBUG:
                print(f"[+] User authenticated: {user.username} (ID: {user.id})")
            return user
        
        if settings.DEBUG:
            if not user:
                print(f"[-] User with ID {user_id_int} not found in database")
            elif not user.is_active:
                print(f"[-] User {user.username} is inactive")
        
        return None
    except Exception as e:
        if settings.DEBUG:
            print(f"[-] ERROR in get_current_user_from_cookie: {e}")
            import traceback
            traceback.print_exc()
        return None


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Home page"""
    user = await get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/portfolio/summary")
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page"""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    """Login page"""
    error = request.query_params.get("error")
    user = await get_current_user_from_cookie(request, db)
    
    if user:
        return RedirectResponse(url="/portfolio/summary")
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error}
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """Registration page"""
    error = request.query_params.get("error")
    user = await get_current_user_from_cookie(request, db)
    
    if user:
        return RedirectResponse(url="/portfolio/summary")
    
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": error}
    )


@app.get("/portfolio/summary", response_class=HTMLResponse)
async def portfolio_summary(request: Request, db: Session = Depends(get_db)):
    """Portfolio summary page"""
    user = await get_current_user_from_cookie(request, db)
    
    if not user:
        # Debug: Check if cookie exists
        token = request.cookies.get("access_token")
        if settings.DEBUG:
            if token:
                print(f"[!] Token exists but user not found. Token: {token[:30]}...")
                # Try to decode it
                from app.core.security import decode_access_token
                decoded = decode_access_token(token)
                print(f"   Decoded payload: {decoded}")
            else:
                print("[!] No access_token cookie found in request")
        return RedirectResponse(url="/login?error=session_expired")
    
    return templates.TemplateResponse(
        "portfolio_summary.html",
        {
            "request": request,
            "user": user,
            "current_date": datetime.now().strftime("%d/%m/%Y")
        }
    )


@app.get("/portfolio/assets", response_class=HTMLResponse)
async def portfolio_assets(request: Request, db: Session = Depends(get_db)):
    """Assets page"""
    user = await get_current_user_from_cookie(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "assets.html",
        {"request": request, "user": user}
    )


@app.get("/portfolio/liabilities", response_class=HTMLResponse)
async def portfolio_liabilities(request: Request, db: Session = Depends(get_db)):
    """Liabilities page"""
    user = await get_current_user_from_cookie(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "liabilities.html",
        {"request": request, "user": user}
    )


@app.get("/settings/trading-n8n", response_class=HTMLResponse)
async def trading_n8n_settings(request: Request, db: Session = Depends(get_db)):
    """n8n + TradePulse trading integration (watchlist, export, webhook push)."""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?error=session_expired")
    return templates.TemplateResponse(
        "trading_n8n.html",
        {"request": request, "user": user},
    )


@app.get("/settings/api-keys", response_class=HTMLResponse)
async def api_keys_settings(request: Request, db: Session = Depends(get_db)):
    """Per-user AI provider API keys and model preferences."""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?error=session_expired")
    return templates.TemplateResponse(
        "api_keys.html",
        {"request": request, "user": user},
    )


@app.get("/plan", response_class=HTMLResponse)
async def retirement_plan(request: Request, db: Session = Depends(get_db)):
    """Retirement planning page"""
    user = await get_current_user_from_cookie(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "retirement_plan.html",
        {"request": request, "user": user}
    )


@app.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Browsers request /favicon.ico by default; redirect to SVG favicon."""
    return RedirectResponse(url="/static/favicon.svg")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/api/test-auth")
async def test_auth(request: Request, db: Session = Depends(get_db)):
    """Test authentication endpoint - comprehensive debugging"""
    from fastapi.responses import JSONResponse
    
    result = {
        "authenticated": False,
        "has_cookie": False,
        "cookie_value": None,
        "token_decode_success": False,
        "token_payload": None,
        "user_found": False,
        "user_id": None,
        "username": None,
        "errors": []
    }
    
    # Check for cookie
    token = request.cookies.get("access_token")
    result["has_cookie"] = bool(token)
    if token:
        result["cookie_value"] = token[:50] + "..." if len(token) > 50 else token
        
        # Try to decode
        payload = decode_access_token(token)
        if payload:
            result["token_decode_success"] = True
            result["token_payload"] = {
                "sub": payload.get("sub"),
                "sub_type": str(type(payload.get("sub"))),
                "exp": payload.get("exp")
            }
            
            # Try to get user
            user_id = payload.get("sub")
            if user_id:
                try:
                    user_id_int = int(user_id)
                    user = db.query(User).filter(User.id == user_id_int).first()
                    if user:
                        result["user_found"] = True
                        result["user_id"] = user.id
                        result["username"] = user.username
                        result["authenticated"] = user.is_active
                    else:
                        result["errors"].append(f"User with ID {user_id_int} not found in database")
                except (ValueError, TypeError) as e:
                    result["errors"].append(f"Invalid user_id: {user_id} (error: {e})")
            else:
                result["errors"].append("No 'sub' in token payload")
        else:
            result["errors"].append("Failed to decode token")
    else:
        result["errors"].append("No access_token cookie found")
    
    return JSONResponse(result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.DEBUG
    )
