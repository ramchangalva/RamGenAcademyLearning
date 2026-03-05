"""
Rate Limiting Utilities
"""
from datetime import datetime, timedelta
from typing import Dict
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
_rate_limit_store: Dict[str, list] = {}


def check_rate_limit(identifier: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """Check if request is within rate limit"""
    try:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        if identifier not in _rate_limit_store:
            _rate_limit_store[identifier] = []
        
        # Clean old requests
        _rate_limit_store[identifier] = [
            req_time for req_time in _rate_limit_store[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(_rate_limit_store[identifier]) >= max_requests:
            return False
        
        # Add current request
        _rate_limit_store[identifier].append(now)
        return True
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return True


def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting"""
    try:
        # Try to get user ID from cookie
        user_id = request.cookies.get("user_id")
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check X-Forwarded-For for proxied requests
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
        
    except Exception as e:
        logger.error(f"Error getting client identifier: {e}")
        return "unknown"
