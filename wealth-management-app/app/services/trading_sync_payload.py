"""
Build a single JSON bundle for n8n → TradePulse agent workflows (stocks watchlist + holdings + cash).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.portfolio import Asset, AssetType, Portfolio
from app.models.user import User
from app.models.watchlist_symbol import WatchlistSymbol


def _hmac_secret() -> str:
    return (settings.TRADING_SYNC_HMAC_SECRET or settings.SECRET_KEY or "").encode("utf-8")


def sign_payload_body(raw_json_bytes: bytes) -> str:
    return hmac.new(_hmac_secret(), raw_json_bytes, hashlib.sha256).hexdigest()


def _infer_ticker_from_name(name: str) -> Optional[str]:
    if not name or not str(name).strip():
        return None
    token = str(name).strip().upper()
    if re.match(r"^[A-Z0-9.\-]{1,12}$", token):
        return token
    return None


def collect_tickers_from_assets(assets: List[Asset]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for a in assets:
        sym = (a.ticker_symbol or "").strip().upper() if getattr(a, "ticker_symbol", None) else None
        if not sym and a.asset_type in (AssetType.STOCKS, AssetType.MUTUAL_FUNDS):
            sym = _infer_ticker_from_name(a.name)
        rows.append(
            {
                "asset_id": a.id,
                "name": a.name,
                "ticker": sym,
                "asset_type": a.asset_type.value if a.asset_type else None,
                "value": a.value,
                "currency": a.currency.value if a.currency else None,
                "quantity": a.quantity,
            }
        )
    return rows


def all_unique_symbols(holdings: List[Dict[str, Any]], watchlist: List[WatchlistSymbol]) -> List[str]:
    found: Set[str] = set()
    out: List[str] = []
    for w in watchlist:
        s = (w.symbol or "").strip().upper()
        if s and s not in found:
            found.add(s)
            out.append(s)
    for h in holdings:
        t = h.get("ticker")
        if t and t not in found:
            found.add(t)
            out.append(t)
    return out


async def build_trading_sync_bundle(db: Session, user: User) -> Dict[str, Any]:
    from app.services.portfolio_calculator import PortfolioCalculator
    from app.models.portfolio import Currency

    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    assets: List[Asset] = []
    if portfolio:
        assets = db.query(Asset).filter(Asset.portfolio_id == portfolio.id).all()

    watchlist = (
        db.query(WatchlistSymbol).filter(WatchlistSymbol.user_id == user.id).order_by(WatchlistSymbol.symbol).all()
    )

    holdings = collect_tickers_from_assets(assets)
    symbols_union = all_unique_symbols(holdings, watchlist)

    calc = PortfolioCalculator()
    summary_usd = await calc.calculate_portfolio_summary(assets, [], [], Currency.USD)

    cash_balance = getattr(portfolio, "cash_balance", None) if portfolio else None
    cash_currency = None
    if portfolio and getattr(portfolio, "cash_currency", None) is not None:
        cash_currency = portfolio.cash_currency.value

    bundle: Dict[str, Any] = {
        "schema": "wealth.trading_sync.v1",
        "event": "wealth.portfolio.sync",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": {"id": user.id, "username": user.username},
        "tradpulse_base_url_hint": None,
        "portfolio": {
            "portfolio_id": portfolio.id if portfolio else None,
            "net_worth_usd": summary_usd["net_worth"]["usd"],
            "net_worth_inr": summary_usd["net_worth"]["inr"],
            "total_assets_usd": summary_usd["assets"]["total_usd"],
            "total_assets_inr": summary_usd["assets"]["total_inr"],
            "cash_balance": cash_balance,
            "cash_currency": cash_currency,
            "holdings": holdings,
        },
        "watchlist": [{"symbol": w.symbol.upper(), "notes": w.notes} for w in watchlist],
        "symbols_for_tradpulse": symbols_union,
        "analysis_hints": {
            "intraday": "Request intraday entry/exit/stop from TradePulse AI or your LLM node using symbols_for_tradpulse.",
            "long_term": "Request swing/long-term stance per holding + watchlist.",
            "slack": "Post consolidated buy/sell/stop-loss table to your Slack channel from n8n.",
        },
    }
    return bundle


def attach_signature(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Mutates bundle with signature over JSON (stable key order)."""
    body = json.dumps(bundle, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = sign_payload_body(body)
    out = dict(bundle)
    out["signature_sha256"] = sig
    return out
