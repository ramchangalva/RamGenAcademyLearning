"""
Security Middleware
CSRF protection, security headers, input validation
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import secrets
import logging

from app.core.config import settings
from app.utils.security import SecurityManager

logger = logging.getLogger(__name__)

security_manager = SecurityManager(settings.SECRET_KEY)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # CSRF protection for state-changing methods
        # Skip CSRF in development mode for easier testing
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if settings.ENABLE_CSRF and settings.ENVIRONMENT != "development":
                csrf_token = request.headers.get("X-CSRF-Token")
                session_token = request.cookies.get("csrf_token")
                
                if not csrf_token or not security_manager.validate_csrf_token(csrf_token, session_token or ""):
                    return JSONResponse(
                        status_code=403,
                        content={"error": "CSRF token validation failed"}
                    )
        
        # Process request
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://cdn.plot.ly https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "frame-src 'self' https://cdn.plot.ly; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Set CSRF token cookie if not exists
        if not request.cookies.get("csrf_token"):
            csrf_token = security_manager.generate_csrf_token()
            response.set_cookie(
                "csrf_token",
                csrf_token,
                httponly=True,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite="strict",
                max_age=86400  # 24 hours
            )
        
        return response
