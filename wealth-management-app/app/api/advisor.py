"""
AI wealth advisor API (OpenAI + portfolio tools + confirmable drafts + streaming).
"""
import asyncio
import json
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.portfolio import Currency
from app.models.user import User
from app.services.advisor_apply import apply_advisor_action
from app.services.advisor_service import advisor_service
from app.services.ai_credentials import advisor_openai_config, is_advisor_available

router = APIRouter(prefix="/api/advisor", tags=["advisor"])

ALLOWED_ACTIONS = frozenset(
    {
        "create_asset",
        "update_asset",
        "delete_asset",
        "create_liability",
        "update_liability",
        "delete_liability",
    }
)


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=12000)


class ChatRequest(BaseModel):
    messages: List[ChatMessageIn] = Field(..., min_length=1, max_length=24)
    base_currency: Optional[str] = "USD"


class ApplyDraftRequest(BaseModel):
    action: str
    payload: dict


def _sanitize_messages(messages: List[ChatMessageIn]) -> List[dict]:
    out: List[dict] = []
    for m in messages[-20:]:
        c = (m.content or "").strip()
        if not c:
            continue
        out.append({"role": m.role, "content": c[:8000]})
    return out


@router.get("/status")
async def advisor_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Whether the assistant is configured (user key, compatible gateway, or server env)."""
    if not is_advisor_available(db, user):
        return {"available": False, "model": None}
    cfg = advisor_openai_config(db, user)
    return {"available": True, "model": cfg[2] if cfg else None}


@router.post("/chat")
async def advisor_chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not is_advisor_available(db, user):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI advisor is not configured. Add an OpenAI API key in Settings → API keys, "
                "or set OPENAI_API_KEY on the server."
            ),
        )

    msgs = _sanitize_messages(body.messages)
    if not msgs or msgs[-1]["role"] != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Send a non-empty user message as the last item in messages.",
        )

    try:
        base = Currency(body.base_currency.upper()) if body.base_currency else Currency.USD
    except ValueError:
        base = Currency.USD

    try:
        reply, drafts = await advisor_service.chat(user=user, db=db, messages=msgs, base_currency=base)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI advisor is not configured.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service failed to respond. Try again shortly.",
        )

    return {"role": "assistant", "content": reply, "drafts": drafts}


@router.post("/chat/stream")
async def advisor_chat_stream(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not is_advisor_available(db, user):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI advisor is not configured. Add an OpenAI API key in Settings → API keys, "
                "or set OPENAI_API_KEY on the server."
            ),
        )

    msgs = _sanitize_messages(body.messages)
    if not msgs or msgs[-1]["role"] != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Send a non-empty user message as the last item in messages.",
        )

    try:
        base = Currency(body.base_currency.upper()) if body.base_currency else Currency.USD
    except ValueError:
        base = Currency.USD

    async def event_gen():
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        try:
            reply, drafts = await advisor_service.chat(
                user=user, db=db, messages=msgs, base_currency=base
            )
        except RuntimeError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Advisor not configured'})}\n\n"
            return
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'message': 'AI request failed'})}\n\n"
            return

        chunk = 32
        for i in range(0, len(reply), chunk):
            part = reply[i : i + chunk]
            yield f"data: {json.dumps({'type': 'token', 'text': part})}\n\n"
            await asyncio.sleep(0.015)

        yield f"data: {json.dumps({'type': 'drafts', 'items': drafts})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/apply")
async def advisor_apply_draft(
    body: ApplyDraftRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")
    try:
        result = apply_advisor_action(db=db, user=user, action=body.action, payload=body.payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)[:500],
        ) from e
    return result
