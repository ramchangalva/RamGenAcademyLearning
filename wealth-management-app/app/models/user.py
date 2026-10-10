"""
User model for authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="owner", cascade="all, delete-orphan")
    ai_settings = relationship("UserAISettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    watchlist_symbols = relationship(
        "WatchlistSymbol", back_populates="user", cascade="all, delete-orphan"
    )
    trading_integration = relationship(
        "UserTradingIntegration",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
