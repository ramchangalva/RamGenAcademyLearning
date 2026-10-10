"""
Public market benchmarks (major global equity indices).

Quotes are fetched from Yahoo Finance chart metadata (unofficial but commonly used).
Google Finance does not provide a documented public HTTP API suitable for backend use.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/market", tags=["market"])

# Globally recognized benchmarks (symbols are Yahoo Finance tickers)
BENCHMARKS: List[Dict[str, str]] = [
    {"symbol": "^GSPC", "name": "S&P 500"},
    {"symbol": "^IXIC", "name": "Nasdaq Composite"},
    {"symbol": "^STOXX50E", "name": "EURO STOXX 50"},
]

CHART_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


async def _fetch_benchmark(
    client: httpx.AsyncClient, symbol: str, display_name: str
) -> Optional[Dict[str, Any]]:
    enc = quote(symbol, safe="")
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{enc}"
    try:
        r = await client.get(
            url,
            params={"range": "5d", "interval": "1d"},
            headers=CHART_HEADERS,
            timeout=20.0,
        )
        r.raise_for_status()
        payload = r.json()
        chart = (payload.get("chart") or {}).get("result") or []
        if not chart:
            return None
        meta = chart[0].get("meta") or {}
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        if price is None:
            return None
        try:
            price_f = float(price)
        except (TypeError, ValueError):
            return None
        pct = 0.0
        if prev is not None:
            try:
                prev_f = float(prev)
                if prev_f:
                    pct = (price_f - prev_f) / prev_f * 100.0
            except (TypeError, ValueError):
                pass
        as_of = ""
        rmt = meta.get("regularMarketTime")
        if rmt is not None:
            try:
                as_of = datetime.fromtimestamp(int(rmt), tz=timezone.utc).strftime("%Y-%m-%d")
            except (TypeError, ValueError, OSError):
                as_of = ""
        return {
            "id": symbol,
            "name": display_name,
            "last": price_f,
            "percent_change": round(pct, 2),
            "as_of": as_of,
        }
    except Exception:
        return None


@router.get("/benchmarks")
async def market_benchmarks() -> Dict[str, Any]:
    """
    Latest levels for major global equity indices. No authentication.
    """
    indices: List[Dict[str, Any]] = []
    as_of: Optional[str] = None
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for b in BENCHMARKS:
                row = await _fetch_benchmark(client, b["symbol"], b["name"])
                if row:
                    indices.append(row)
                    if not as_of and row.get("as_of"):
                        as_of = row["as_of"]
    except Exception:
        return {
            "live": False,
            "indices": [],
            "source": None,
            "error": "provider_unavailable",
        }

    if not indices:
        return {
            "live": False,
            "indices": [],
            "source": None,
            "error": "provider_unavailable",
        }

    return {
        "live": True,
        "indices": indices,
        "source": "Yahoo Finance",
        "as_of": as_of,
    }
