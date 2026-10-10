"""
n8n / TradePulse agent-to-agent integration: watchlist, portfolio meta, signed export, webhook push.
"""
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.portfolio import Currency, Portfolio
from app.models.user import User
from app.models.user_trading_integration import UserTradingIntegration
from app.models.watchlist_symbol import WatchlistSymbol
from app.services.trading_sync_payload import attach_signature, build_trading_sync_bundle

router = APIRouter(prefix="/api/trading", tags=["trading-integration"])


def _get_or_create_integration(db: Session, user_id: int) -> UserTradingIntegration:
    import secrets

    row = db.query(UserTradingIntegration).filter(UserTradingIntegration.user_id == user_id).first()
    if not row:
        row = UserTradingIntegration(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    if not row.n8n_pull_token:
        row.n8n_pull_token = secrets.token_urlsafe(32)
        db.commit()
        db.refresh(row)
    return row


class IntegrationUpdate(BaseModel):
    n8n_webhook_url: Optional[str] = None
    tradpulse_base_url: Optional[str] = Field(None, max_length=512)
    enabled: Optional[bool] = None


class WatchlistAdd(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32)
    notes: Optional[str] = Field(None, max_length=2000)


class PortfolioCashUpdate(BaseModel):
    cash_balance: Optional[float] = None
    cash_currency: Optional[Currency] = None


def _user_from_n8n_token(db: Session, token: Optional[str]) -> Optional[User]:
    if not token or not str(token).strip():
        return None
    integ = (
        db.query(UserTradingIntegration)
        .filter(UserTradingIntegration.n8n_pull_token == token.strip())
        .first()
    )
    if not integ or not integ.enabled:
        return None
    return db.query(User).filter(User.id == integ.user_id).first()


@router.get("/integration")
async def get_integration(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = _get_or_create_integration(db, user.id)
    return {
        "n8n_webhook_url": row.n8n_webhook_url,
        "tradpulse_base_url": row.tradpulse_base_url,
        "enabled": row.enabled,
        "n8n_pull_token": row.n8n_pull_token,
    }


@router.put("/integration")
async def put_integration(
    body: IntegrationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _get_or_create_integration(db, user.id)
    if body.n8n_webhook_url is not None:
        row.n8n_webhook_url = body.n8n_webhook_url.strip() or None
    if body.tradpulse_base_url is not None:
        row.tradpulse_base_url = body.tradpulse_base_url.strip() or "http://127.0.0.1:8888"
    if body.enabled is not None:
        row.enabled = body.enabled
    db.commit()
    db.refresh(row)
    return {
        "n8n_webhook_url": row.n8n_webhook_url,
        "tradpulse_base_url": row.tradpulse_base_url,
        "enabled": row.enabled,
        "n8n_pull_token": row.n8n_pull_token,
    }


@router.post("/integration/rotate-token")
async def rotate_pull_token(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import secrets

    row = _get_or_create_integration(db, user.id)
    row.n8n_pull_token = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(row)
    return {"n8n_pull_token": row.n8n_pull_token}


@router.get("/watchlist")
async def list_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(WatchlistSymbol).filter(WatchlistSymbol.user_id == user.id).order_by(WatchlistSymbol.symbol).all()
    )
    return [{"id": r.id, "symbol": r.symbol, "notes": r.notes} for r in rows]


@router.post("/watchlist")
async def add_watchlist(
    body: WatchlistAdd,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sym = body.symbol.strip().upper()
    if not sym:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    existing = (
        db.query(WatchlistSymbol)
        .filter(WatchlistSymbol.user_id == user.id, WatchlistSymbol.symbol == sym)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Symbol already on watchlist")
    row = WatchlistSymbol(user_id=user.id, symbol=sym, notes=body.notes)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "symbol": row.symbol, "notes": row.notes}


@router.delete("/watchlist/{symbol}")
async def remove_watchlist(
    symbol: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sym = symbol.strip().upper()
    row = (
        db.query(WatchlistSymbol)
        .filter(WatchlistSymbol.user_id == user.id, WatchlistSymbol.symbol == sym)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.put("/portfolio-cash")
async def update_portfolio_cash(
    body: PortfolioCashUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=user.id, name="Main Portfolio")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    portfolio.cash_balance = body.cash_balance
    portfolio.cash_currency = body.cash_currency
    db.commit()
    db.refresh(portfolio)
    return {
        "cash_balance": portfolio.cash_balance,
        "cash_currency": portfolio.cash_currency.value if portfolio.cash_currency else None,
    }


@router.get("/export")
async def export_signed_bundle(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    integ = _get_or_create_integration(db, user.id)
    bundle = await build_trading_sync_bundle(db, user)
    bundle["tradpulse_base_url_hint"] = integ.tradpulse_base_url
    return attach_signature(bundle)


@router.get("/export/n8n")
async def export_signed_bundle_n8n(
    x_n8n_token: str = Header(..., alias="X-N8N-Token"),
    db: Session = Depends(get_db),
):
    """Machine-to-machine: use pull token from Settings → Trading / n8n (header only, no browser cookie)."""
    user = _user_from_n8n_token(db, x_n8n_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-N8N-Token")
    integ = _get_or_create_integration(db, user.id)
    bundle = await build_trading_sync_bundle(db, user)
    bundle["tradpulse_base_url_hint"] = integ.tradpulse_base_url
    return attach_signature(bundle)


@router.post("/push-n8n")
async def push_to_n8n_webhook(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = _get_or_create_integration(db, user.id)
    if not row.n8n_webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set n8n_webhook_url in trading integration settings first.",
        )
    if not row.enabled:
        raise HTTPException(status_code=400, detail="Integration disabled")

    bundle = await build_trading_sync_bundle(db, user)
    bundle["tradpulse_base_url_hint"] = row.tradpulse_base_url
    signed = attach_signature(bundle)
    import json

    raw = json.dumps(signed, separators=(",", ":")).encode("utf-8")
    resp = None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                row.n8n_webhook_url,
                content=raw,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"n8n webhook request failed: {e!s}"[:500],
        ) from e
    return {"ok": True, "status_code": resp.status_code if resp else 200}
