"""
Per-user AI provider API keys and model preferences (encrypted keys).
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class UserAISettings(Base):
    __tablename__ = "user_ai_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    openai_api_key_encrypted = Column(Text, nullable=True)
    openai_base_url = Column(String(512), nullable=True)

    anthropic_api_key_encrypted = Column(Text, nullable=True)
    google_api_key_encrypted = Column(Text, nullable=True)
    cohere_api_key_encrypted = Column(Text, nullable=True)
    huggingface_api_key_encrypted = Column(Text, nullable=True)

    active_provider = Column(String(32), nullable=False, default="openai")
    active_model = Column(String(128), nullable=False, default="gpt-4o-mini")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="ai_settings")
