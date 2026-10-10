"""
TradePulse AI - Production-Ready Application
Main application entry point with proper structure
"""
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.middleware.security import SecurityMiddleware
from app.utils.rate_limiting import get_client_identifier
from fastapi import Request, status
from fastapi.responses import RedirectResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None
)

# Rate limiting
limiter = Limiter(key_func=get_client_identifier)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware
app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import and include routers
from app.routes import home, analysis, portfolio, market_scanner, risk_management, trade_journal, alerts, strategy, chatbot, help, watchlist, ai_assistant, dashboard

app.include_router(home.router, tags=["Home"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(portfolio.router, tags=["Portfolio"])
app.include_router(market_scanner.router, tags=["Market Scanner"])
app.include_router(risk_management.router, tags=["Risk Management"])
app.include_router(trade_journal.router, tags=["Trade Journal"])
app.include_router(alerts.router, tags=["Alerts"])
app.include_router(strategy.router, tags=["Strategy"])
app.include_router(chatbot.router, tags=["Chatbot"])
app.include_router(ai_assistant.router, tags=["AI Assistant"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(help.router, tags=["Help"])
app.include_router(watchlist.router, tags=["Watchlist"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler - redirect to home"""
    # Only redirect if it's a page route, not API routes
    if request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"error": "Endpoint not found"}
        )
    # Redirect page routes to home
    return RedirectResponse(url="/home", status_code=302)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8888,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
