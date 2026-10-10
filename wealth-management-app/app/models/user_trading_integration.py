"""n8n / TradePulse agent-to-agent integration settings per user."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class UserTradingIntegration(Base):
    __tablename__ = "user_trading_integration"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    n8n_webhook_url = Column(Text, nullable=True)
    tradpulse_base_url = Column(String(512), nullable=False, default="http://127.0.0.1:8888")
    n8n_pull_token = Column(String(128), nullable=True, index=True)
    enabled = Column(Boolean, nullable=False, default=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="trading_integration")
