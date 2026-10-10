# Wealth app ↔ n8n ↔ TradePulse AI ↔ Slack

This describes **agent-to-agent** style orchestration: the **Wealth Management** app exports portfolio + watchlist; **n8n** calls **TradePulse AI** HTTP APIs; **Slack** receives consolidated trade ideas.

## Wealth app endpoints (default `http://127.0.0.1:9000`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/api/trading/export` | Session cookie / Bearer | Signed JSON bundle (browser) |
| `GET` | `/api/trading/export/n8n` | Header `X-N8N-Token: <pull_token>` | Same bundle for n8n **HTTP Request** node |
| `POST` | `/api/trading/push-n8n` | Session | POSTs signed JSON to your **n8n Webhook** URL |
| `PUT` | `/api/trading/integration` | Session | Save `n8n_webhook_url`, `tradpulse_base_url` |
| `GET`/`POST`/`DELETE` | `/api/trading/watchlist` | Session | Watchlist CRUD |

**Pull token:** Settings UI **Trade SYNC** page, or `GET /api/trading/integration` (after login).

**HMAC:** Field `signature_sha256` signs the JSON object **without** that field, using HMAC-SHA256 and secret `TRADING_SYNC_HMAC_SECRET` (or falls back to app `SECRET_KEY`). In n8n, use a **Code** node to strip `signature_sha256`, stringify with sorted keys, and verify with a **Crypto** node if you need integrity checks.

## Payload shape (`wealth.trading_sync.v1`)

- `symbols_for_tradpulse`: deduped list from **watchlist** + inferred tickers from **stock/mutual_fund** holdings (`ticker_symbol` or `name` if it looks like a ticker).
- `portfolio.holdings`: rows with `value`, `currency`, `quantity`, `ticker`.
- `portfolio.cash_balance` / `cash_currency`: optional uninvested cash (set in Trade SYNC UI).
- `tradpulse_base_url_hint`: copy saved in integration (e.g. `http://127.0.0.1:8888`).

## TradePulse AI HTTP APIs (default `http://127.0.0.1:8888`)

Use in n8n **HTTP Request** nodes (loop over `symbols_for_tradpulse` or `watchlist`):

- **Batch (recommended):** `POST {{tradpulse_base_url}}/api/integration/symbols/snapshot-batch`  
  Body: `{ "symbols": ["AAPL","MSFT"], "asset_type": "stock" }` — returns `results[]` with `symbol` + `info` per ticker (TradePulse repo).

- **Single:** `GET {{tradpulse_base_url}}/api/asset/{{symbol}}/info?asset_type=stock`  
  Same underlying fetcher as the batch route.

Optional chat-style analysis (requires user API keys in TradePulse cookie context — harder from n8n):

- `POST /api/chatbot/chat` with JSON body `messages`, `provider`, `model` — usually better to use an **OpenAI** (or other) node in n8n with a prompt built from the wealth bundle + TradePulse `/api/asset/.../info` responses.

## Example n8n workflow (outline)

1. **Webhook** (POST) *or* **Schedule Trigger** + **HTTP Request** `GET …/api/trading/export/n8n` with header `X-N8N-Token`.
2. **Code**: parse JSON; optionally verify `signature_sha256`.
3. **Split Out** / **Loop** over `symbols_for_tradpulse`.
4. **HTTP Request**: `GET {{$vars.tradpulseBase}}/api/asset/{{$json.symbol}}/info`.
5. **OpenAI** (or **HTTP Request** to your LLM): prompt to output a **table**: intraday (entry, stop, target) and longer-term stance per symbol, respecting `cash_balance` and current `holdings`.
6. **Slack**: post message (channel of your choice) with the table and disclaimers (*not financial advice*).

**Push mode:** In the Wealth UI, **Push to n8n now** sends the same signed body to your **Webhook** URL so step 1 receives the bundle without polling.

## SQLite migrations (existing installs)

New tables/columns require a DB update. For a quick local fix:

```sql
-- portfolios
ALTER TABLE portfolios ADD COLUMN cash_balance FLOAT;
ALTER TABLE portfolios ADD COLUMN cash_currency VARCHAR(3);

-- assets
ALTER TABLE assets ADD COLUMN ticker_symbol VARCHAR(32);
```

New tables `watchlist_symbols` and `user_trading_integration` are created on next app start if you use `create_all` on a fresh DB; for an existing DB, recreate tables or use Alembic.

## Environment

```env
# Optional: dedicated secret for webhook HMAC (else SECRET_KEY is used)
TRADING_SYNC_HMAC_SECRET=
```

## Compliance

Automated buy/sell/stop suggestions are **educational only**. Log retention, broker execution, and regulatory obligations are your responsibility; do not treat Slack output as an order management system without proper controls.
