"""
Input Validation Utilities
Centralized input validation and sanitization
"""
import re
from typing import Optional, List
from app.utils.security import SecurityManager
from app.core.config import settings

security_manager = SecurityManager(settings.SECRET_KEY)


def validate_symbol(symbol: str, asset_type: str = 'stock') -> tuple[bool, Optional[str]]:
    """
    Validate asset symbol
    
    Returns:
        (is_valid, error_message)
    """
    if not symbol:
        return False, "Symbol is required"
    
    symbol = str(symbol).strip().upper()
    
    # Length check
    if len(symbol) > 20:
        return False, "Symbol too long (max 20 characters)"
    
    # Type-specific validation
    if asset_type == 'crypto':
        if not re.match(r'^[A-Z0-9-]+$', symbol):
            return False, "Invalid crypto symbol format"
    elif asset_type == 'commodity':
        if not re.match(r'^[A-Z0-9=]+$', symbol):
            return False, "Invalid commodity symbol format"
    else:  # stock, etf
        if not re.match(r'^[A-Z0-9]+$', symbol):
            return False, "Invalid stock/ETF symbol format"
    
    return True, None


def sanitize_string(input_str: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """Sanitize string input"""
    if not isinstance(input_str, str):
        return ""
    
    sanitized = input_str.strip()[:max_length]
    
    if not allow_html:
        # Remove HTML tags
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        # Remove script content
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized


def validate_float(value: any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> tuple[bool, Optional[float], Optional[str]]:
    """Validate float value"""
    try:
        float_val = float(value)
        
        if min_val is not None and float_val < min_val:
            return False, None, f"Value must be at least {min_val}"
        
        if max_val is not None and float_val > max_val:
            return False, None, f"Value must be at most {max_val}"
        
        return True, float_val, None
    except (ValueError, TypeError):
        return False, None, "Invalid number format"


def validate_integer(value: any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> tuple[bool, Optional[int], Optional[str]]:
    """Validate integer value"""
    try:
        int_val = int(value)
        
        if min_val is not None and int_val < min_val:
            return False, None, f"Value must be at least {min_val}"
        
        if max_val is not None and int_val > max_val:
            return False, None, f"Value must be at most {max_val}"
        
        return True, int_val, None
    except (ValueError, TypeError):
        return False, None, "Invalid integer format"


def validate_period(period: str) -> tuple[bool, Optional[str]]:
    """Validate time period parameter"""
    valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    if period not in valid_periods:
        return False, f"Invalid period. Must be one of: {', '.join(valid_periods)}"
    return True, None


def validate_interval(interval: str) -> tuple[bool, Optional[str]]:
    """Validate interval parameter"""
    valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
    if interval not in valid_intervals:
        return False, f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
    return True, None


def validate_asset_type(asset_type: str) -> tuple[bool, Optional[str]]:
    """Validate asset type"""
    valid_types = ['stock', 'crypto', 'commodity', 'etf']
    if asset_type not in valid_types:
        return False, f"Invalid asset type. Must be one of: {', '.join(valid_types)}"
    return True, None


def sanitize_user_id(user_id: str) -> str:
    """Sanitize user ID to prevent injection"""
    if not user_id:
        return ""
    
    # Remove dangerous characters, limit length
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', str(user_id))[:100]
    return sanitized


def validate_provider_name(provider: str) -> tuple[bool, Optional[str]]:
    """Validate AI provider name"""
    valid_providers = ['openai', 'anthropic', 'google', 'cohere', 'huggingface']
    if provider not in valid_providers:
        return False, f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
    return True, None


def sanitize_error_message(error: Exception, include_details: bool = False) -> str:
    """Sanitize error messages to prevent information leakage"""
    error_msg = str(error)
    
    # In production, don't expose internal details
    if not include_details and settings.ENVIRONMENT == "production":
        # Generic error messages
        if "traceback" in error_msg.lower() or "file" in error_msg.lower():
            return "An internal error occurred. Please try again later."
        
        # Remove file paths
        error_msg = re.sub(r'[A-Z]:\\[^\s]+', '[PATH]', error_msg)
        error_msg = re.sub(r'/[^\s]+', '[PATH]', error_msg)
    
    # Limit error message length
    return error_msg[:500]
