"""
User AI API key configuration (encrypted at rest).
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.secrets_crypto import encrypt_secret
from app.models.user import User
from app.models.user_ai_settings import UserAISettings
from app.services.ai_credentials import get_or_create_ai_settings

router = APIRouter(prefix="/api/settings/ai", tags=["settings-ai"])

PROVIDER_FIELDS = {
    "openai": "openai_api_key_encrypted",
    "anthropic": "anthropic_api_key_encrypted",
    "google": "google_api_key_encrypted",
    "cohere": "cohere_api_key_encrypted",
    "huggingface": "huggingface_api_key_encrypted",
}


class SaveKeyBody(BaseModel):
    provider: Literal["openai", "anthropic", "google", "cohere", "huggingface"]
    api_key: Optional[str] = Field(None, max_length=4096)
    """Empty string clears the key; omit to leave unchanged."""
    base_url: Optional[str] = Field(None, max_length=512)
    """OpenAI-compatible base URL (openai only). Empty clears."""


class PreferencesBody(BaseModel):
    active_provider: Literal["openai", "anthropic", "google", "cohere", "huggingface"]
    active_model: str = Field(..., min_length=1, max_length=128)
    openai_base_url: Optional[str] = Field(None, max_length=512)


def _status_payload(row: UserAISettings) -> dict:
    return {
        "providers": {
            "openai": {"configured": bool(row.openai_api_key_encrypted)},
            "anthropic": {"configured": bool(row.anthropic_api_key_encrypted)},
            "google": {"configured": bool(row.google_api_key_encrypted)},
            "cohere": {"configured": bool(row.cohere_api_key_encrypted)},
            "huggingface": {"configured": bool(row.huggingface_api_key_encrypted)},
        },
        "openai_base_url": row.openai_base_url or "",
        "active_provider": row.active_provider,
        "active_model": row.active_model,
    }


@router.get("")
async def get_ai_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_or_create_ai_settings(db, user.id)
    return _status_payload(row)


@router.post("/key")
async def save_provider_key(
    body: SaveKeyBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attr = PROVIDER_FIELDS.get(body.provider)
    if not attr:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown provider")

    row = get_or_create_ai_settings(db, user.id)

    if body.api_key is not None:
        stripped = body.api_key.strip()
        if not stripped:
            setattr(row, attr, None)
        else:
            setattr(row, attr, encrypt_secret(stripped))

    if body.provider == "openai" and body.base_url is not None:
        bu = body.base_url.strip()
        row.openai_base_url = bu if bu else None

    db.commit()
    db.refresh(row)
    return _status_payload(row)


@router.post("/clear")
async def clear_all_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_or_create_ai_settings(db, user.id)
    for attr in PROVIDER_FIELDS.values():
        setattr(row, attr, None)
    row.openai_base_url = None
    db.commit()
    db.refresh(row)
    return _status_payload(row)


@router.put("/preferences")
async def update_preferences(
    body: PreferencesBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_or_create_ai_settings(db, user.id)
    row.active_provider = body.active_provider
    row.active_model = body.active_model.strip()
    if body.openai_base_url is not None:
        bu = body.openai_base_url.strip()
        row.openai_base_url = bu if bu else None
    db.commit()
    db.refresh(row)
    return _status_payload(row)
