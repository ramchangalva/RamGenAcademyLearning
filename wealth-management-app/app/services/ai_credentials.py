"""
Resolve OpenAI-compatible credentials for the wealth advisor (user settings + env fallback).
"""
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.secrets_crypto import decrypt_secret
from app.models.user import User
from app.models.user_ai_settings import UserAISettings

# Advisor chat is implemented with the OpenAI SDK (works with OpenAI and many compatible gateways).
SUPPORTED_ADVISOR_PROVIDERS = frozenset({"openai"})


def get_or_create_ai_settings(db: Session, user_id: int) -> UserAISettings:
    row = db.query(UserAISettings).filter(UserAISettings.user_id == user_id).first()
    if not row:
        row = UserAISettings(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def advisor_openai_config(db: Session, user: User) -> Optional[Tuple[str, Optional[str], str]]:
    """
    Returns (api_key, base_url_or_none, model) for AsyncOpenAI, or None if the advisor cannot run.
    """
    row = db.query(UserAISettings).filter(UserAISettings.user_id == user.id).first()
    provider = (row.active_provider if row else None) or "openai"
    model = settings.OPENAI_MODEL
    if row and row.active_model and row.active_model.strip():
        model = row.active_model.strip()

    if provider not in SUPPORTED_ADVISOR_PROVIDERS:
        return None

    if row and row.openai_api_key_encrypted:
        key = decrypt_secret(row.openai_api_key_encrypted)
        if key and key.strip():
            base = (row.openai_base_url or "").strip() or None
            return key.strip(), base, model

    env_key = (settings.OPENAI_API_KEY or "").strip()
    if env_key:
        return env_key, None, model

    return None


def is_advisor_available(db: Session, user: User) -> bool:
    return advisor_openai_config(db, user) is not None
