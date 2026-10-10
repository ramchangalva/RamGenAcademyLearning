"""
Configuration Management for Production
Enhanced configuration with validation and type safety
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = {
        "extra": "ignore"  # Ignore extra fields from environment
    }
    """Application settings with validation"""
    
    # App Info
    APP_NAME: str = "TradePulse AI"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Intelligent Multi-Asset Trading Analysis Platform"
    
    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: os.urandom(32).hex(),
        description="Secret key for JWT tokens and encryption"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,
        ge=1,
        le=10080,
        description="JWT token expiration in minutes"
    )
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "http://localhost:8888,http://localhost:3000").split(","),
        description="Allowed CORS origins"
    )
    
    # API Keys (AI Providers)
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google API key")
    COHERE_API_KEY: str = Field(default="", description="Cohere API key")
    HUGGINGFACE_API_KEY: str = Field(default="", description="HuggingFace API key")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Max requests per window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Rate limit window in seconds"
    )
    
    # Database (for future use)
    DATABASE_URL: str = Field(
        default="sqlite:///./data/tradepulse.db",
        description="Database connection URL"
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: (
            os.getenv("CORS_ORIGINS", "http://localhost:8888").split(",") 
            if os.getenv("CORS_ORIGINS") 
            else ["http://localhost:8888"]
        ),
        description="CORS allowed origins (default: localhost only for security)"
    )
    
    # Security Settings
    ENABLE_CSRF: bool = Field(
        default=True,
        description="Enable CSRF protection"
    )
    SESSION_COOKIE_SECURE: bool = Field(
        default=True,
        description="Secure session cookies (HTTPS only)"
    )
    SESSION_COOKIE_HTTPONLY: bool = Field(
        default=True,
        description="HTTP-only session cookies"
    )
    ENCRYPT_USER_DATA: bool = Field(
        default=True,
        description="Encrypt user data (API keys, portfolios)"
    )
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()


settings = Settings()
