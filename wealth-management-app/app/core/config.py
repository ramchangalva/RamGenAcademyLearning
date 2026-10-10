"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "Wealth Management Planner"
    APP_VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BCRYPT_ROUNDS: int = 12
    SESSION_TIMEOUT_MINUTES: int = 60
    CSRF_ENABLED: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./wealth_management.db"
    
    # Redis (Optional)
    REDIS_URL: Optional[str] = None
    
    # Exchange Rate API
    EXCHANGE_RATE_API_KEY: Optional[str] = None
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate-api.com/v4/latest/USD"

    # AI wealth advisor (OpenAI). Leave key empty to disable assistant UI.
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # n8n / TradePulse agent sync: HMAC for outbound webhook body (shared with n8n Verify node)
    TRADING_SYNC_HMAC_SECRET: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
