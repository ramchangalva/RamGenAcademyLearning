"""
AI wealth advisor: OpenAI tool-calling with read-only and draft (confirmable) portfolio tools.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.portfolio import Asset, Currency, Insurance, Liability, Portfolio
from app.services.ai_credentials import advisor_openai_config
from app.models.retirement import RetirementPlan
from app.models.user import User
from app.services.advisor_apply import (
    CreateAssetPayload,
    CreateLiabilityPayload,
    DeleteAssetPayload,
    DeleteLiabilityPayload,
    UpdateAssetPayload,
    UpdateLiabilityPayload,
)
from app.services.portfolio_calculator import PortfolioCalculator

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """You are a personal wealth-planning assistant embedded in a portfolio web app. You help users understand their finances and think through goals using only data from your tools.

Rules:
- Call tools whenever the user asks about balances, net worth, allocation, debts, insurance, or retirement plans—or when you need numbers to give a useful answer.
- Never invent holdings, amounts, or account details. If tools return empty data, say so and suggest adding entries in the app.
- Be concise, clear, and supportive. Use bullet lists when comparing several items.
- Give general education (diversification, emergency funds, debt paydown order, saving rate) rather than specific buy/sell instructions for individual securities.
- You are not a licensed financial, tax, or legal advisor. When users ask for personalized investment picks, tax strategy, or legal steps, remind them to consult a qualified professional in their jurisdiction.
- The app supports USD and INR; respect the base_currency the user prefers when discussing totals.

Portfolio changes:
- To add, change, or remove assets or liabilities, use the draft_* tools. Each draft is shown to the user with a Confirm button—nothing is saved until they confirm.
- After calling draft tools, briefly explain what will happen if they confirm.
- Use exact enum values for asset_type and liability_type (e.g. stocks, mutual_funds, cash, home_loan, credit_card)."""

READ_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_snapshot",
            "description": (
                "Aggregated portfolio: net worth, asset/liability/insurance totals, "
                "and asset allocation percentages by category."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {
                        "type": "string",
                        "enum": ["USD", "INR"],
                        "description": "Primary currency for interpreting totals in your reply.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_assets",
            "description": "List all assets with type, name, value, currency, and optional quantity.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_liabilities",
            "description": "List all liabilities with type, name, outstanding balance, currency, interest rate if any.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_retirement_plans",
            "description": (
                "Summarize saved retirement plans: name, ages, and whether primary (USD) "
                "and secondary (INR) sections are filled."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

DRAFT_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "draft_create_asset",
            "description": "Propose creating a new asset. User must confirm in the UI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {
                        "type": "string",
                        "enum": [
                            "mutual_funds",
                            "stocks",
                            "fixed_income",
                            "real_estate",
                            "retirement_account",
                            "small_savings",
                            "cash",
                            "other",
                        ],
                    },
                    "name": {"type": "string"},
                    "value": {"type": "number"},
                    "currency": {"type": "string", "enum": ["USD", "INR"]},
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "purchase_date": {
                        "type": "string",
                        "description": "Optional ISO date YYYY-MM-DD",
                    },
                },
                "required": ["asset_type", "name", "value", "currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_update_asset",
            "description": "Propose updating an existing asset. Use list_assets for ids.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "value": {"type": "number"},
                    "currency": {"type": "string", "enum": ["USD", "INR"]},
                    "quantity": {"type": "number"},
                    "asset_type": {
                        "type": "string",
                        "enum": [
                            "mutual_funds",
                            "stocks",
                            "fixed_income",
                            "real_estate",
                            "retirement_account",
                            "small_savings",
                            "cash",
                            "other",
                        ],
                    },
                },
                "required": ["asset_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_delete_asset",
            "description": "Propose deleting an asset by id.",
            "parameters": {
                "type": "object",
                "properties": {"asset_id": {"type": "integer"}},
                "required": ["asset_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_create_liability",
            "description": "Propose creating a liability. User must confirm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "liability_type": {
                        "type": "string",
                        "enum": [
                            "home_loan",
                            "personal_loan",
                            "credit_card",
                            "car_loan",
                            "other",
                        ],
                    },
                    "name": {"type": "string"},
                    "outstanding_amount": {"type": "number"},
                    "currency": {"type": "string", "enum": ["USD", "INR"]},
                    "description": {"type": "string"},
                    "interest_rate": {"type": "number", "description": "Annual % if known"},
                    "due_date": {"type": "string", "description": "Optional ISO date"},
                },
                "required": ["liability_type", "name", "outstanding_amount", "currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_update_liability",
            "description": "Propose updating a liability. Use list_liabilities for ids.",
            "parameters": {
                "type": "object",
                "properties": {
                    "liability_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "outstanding_amount": {"type": "number"},
                    "currency": {"type": "string", "enum": ["USD", "INR"]},
                    "interest_rate": {"type": "number"},
                    "due_date": {"type": "string"},
                    "liability_type": {
                        "type": "string",
                        "enum": [
                            "home_loan",
                            "personal_loan",
                            "credit_card",
                            "car_loan",
                            "other",
                        ],
                    },
                },
                "required": ["liability_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_delete_liability",
            "description": "Propose deleting a liability by id.",
            "parameters": {
                "type": "object",
                "properties": {"liability_id": {"type": "integer"}},
                "required": ["liability_id"],
            },
        },
    },
]

TOOL_DEFINITIONS: List[Dict[str, Any]] = READ_TOOLS + DRAFT_TOOLS


def _parse_currency(s: Optional[str], fallback: Currency) -> Currency:
    if not s:
        return fallback
    try:
        return Currency(s.upper())
    except ValueError:
        return fallback


def _parse_iso_date(s: Optional[str]) -> Optional[datetime]:
    if not s or not str(s).strip():
        return None
    try:
        return datetime.fromisoformat(str(s).strip()[:10])
    except ValueError:
        return None


async def _load_portfolio_context(
    db: Session, user_id: int
) -> Tuple[Optional[Portfolio], List[Asset], List[Liability], List[Insurance]]:
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if not portfolio:
        return None, [], [], []
    assets = db.query(Asset).filter(Asset.portfolio_id == portfolio.id).all()
    liabilities = db.query(Liability).filter(Liability.portfolio_id == portfolio.id).all()
    insurance = db.query(Insurance).filter(Insurance.portfolio_id == portfolio.id).all()
    return portfolio, assets, liabilities, insurance


class AdvisorService:
    def __init__(self) -> None:
        self._calculator = PortfolioCalculator()

    async def run_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        user: User,
        db: Session,
        default_base: Currency,
        draft_sink: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        portfolio, assets, liabilities, insurance = await _load_portfolio_context(db, user.id)

        if name == "draft_create_asset":
            if draft_sink is None:
                return json.dumps({"error": "draft_sink_missing"})
            raw = dict(arguments)
            raw["purchase_date"] = _parse_iso_date(raw.get("purchase_date"))
            try:
                payload = CreateAssetPayload.model_validate(raw)
            except Exception as e:
                return json.dumps({"error": "validation_failed", "detail": str(e)})
            did = str(uuid.uuid4())
            draft_sink.append(
                {
                    "draft_id": did,
                    "action": "create_asset",
                    "payload": json.loads(payload.model_dump_json()),
                }
            )
            return json.dumps(
                {
                    "recorded": True,
                    "draft_id": did,
                    "summary": f"Create {payload.asset_type.value}: {payload.name}",
                }
            )

        if name == "draft_update_asset":
            if draft_sink is None:
                return json.dumps({"error": "draft_sink_missing"})
            raw = {k: v for k, v in arguments.items() if v is not None}
            if "asset_id" in raw and raw["asset_id"] is not None:
                raw["asset_id"] = int(float(raw["asset_id"]))
            if "purchase_date" in raw:
                raw["purchase_date"] = _parse_iso_date(raw.get("purchase_date"))
            try:
                payload = UpdateAssetPayload.model_validate(raw)
            except Exception as e:
                return json.dumps({"error": "validation_failed", "detail": str(e)})
            did = str(uuid.uuid4())
            draft_sink.append(
                {
                    "draft_id": did,
                    "action": "update_asset",
                    "payload": json.loads(payload.model_dump_json()),
                }
            )
            return json.dumps({"recorded": True, "draft_id": did, "summary": f"Update asset #{payload.asset_id}"})

        if name == "draft_delete_asset":
            if draft_sink is None:
                return json.dumps({"error": "draft_sink_missing"})
            args = dict(arguments)
            if "asset_id" in args and args["asset_id"] is not None:
                args["asset_id"] = int(float(args["asset_id"]))
            try:
                payload = DeleteAssetPayload.model_validate(args)
            except Exception as e:
                return json.dumps({"error": "validation_failed", "detail": str(e)})
            did = str(uuid.uuid4())
            draft_sink.append(
                {
                    "draft_id": did,
                    "action": "delete_asset",
                    "payload": json.loads(payload.model_dump_json()),
                }
            )
            return json.dumps({"recorded": True, "draft_id": did, "summary": f"Delete asset #{payload.asset_id}"})

        if name == "draft_create_liability":
            if draft_sink is None:
                return json.dumps({"error": "draft_sink_missing"})
            raw = dict(arguments)
            raw["due_date"] = _parse_iso_date(raw.get("due_date"))
            try:
                payload = CreateLiabilityPayload.model_validate(raw)
            except Exception as e:
                return json.dumps({"error": "validation_failed", "detail": str(e)})
            did = str(uuid.uuid4())
            draft_sink.append(
                {
                    "draft_id": did,
                    "action": "create_liability",
                    "payload": json.loads(payload.model_dump_json()),
                }
            )
            return json.dumps(
                {
                    "recorded": True,
                    "draft_id": did,
                    "summary": f"Create {payload.liability_type.value}: {payload.name}",
                }
            )

        if name == "draft_update_liability":
            if draft_sink is None:
                return json.dumps({"error": "draft_sink_missing"})
            raw = {k: v for k, v in arguments.items() if v is not None}
            if "liability_id" in raw and raw["liability_id"] is not None:
                raw["liability_id"] = int(float(raw["liability_id"]))
            if "due_date" in raw:
                raw["due_date"] = _parse_iso_date(raw.get("due_date"))
            try:
                payload = UpdateLiabilityPayload.model_validate(raw)
            except Exception as e:
                return json.dumps({"error": "validation_failed", "detail": str(e)})
            did = str(uuid.uuid4())
            draft_sink.append(
                {
                    "draft_id": did,
                    "action": "update_liability",
                    "payload": json.loads(payload.model_dump_json()),
                }
            )
            return json.dumps(
                {"recorded": True, "draft_id": did, "summary": f"Update liability #{payload.liability_id}"}
            )

        if name == "draft_delete_liability":
            if draft_sink is None:
                return json.dumps({"error": "draft_sink_missing"})
            args = dict(arguments)
            if "liability_id" in args and args["liability_id"] is not None:
                args["liability_id"] = int(float(args["liability_id"]))
            try:
                payload = DeleteLiabilityPayload.model_validate(args)
            except Exception as e:
                return json.dumps({"error": "validation_failed", "detail": str(e)})
            did = str(uuid.uuid4())
            draft_sink.append(
                {
                    "draft_id": did,
                    "action": "delete_liability",
                    "payload": json.loads(payload.model_dump_json()),
                }
            )
            return json.dumps(
                {"recorded": True, "draft_id": did, "summary": f"Delete liability #{payload.liability_id}"}
            )

        if name == "get_portfolio_snapshot":
            base = _parse_currency(arguments.get("base_currency"), default_base)
            if not portfolio:
                return json.dumps(
                    {
                        "message": "No portfolio yet; user has not created holdings in the app.",
                        "net_worth_usd": 0,
                        "net_worth_inr": 0,
                    }
                )
            summary = await self._calculator.calculate_portfolio_summary(
                assets, liabilities, insurance, base
            )
            return json.dumps(summary, default=str)

        if name == "list_assets":
            if not portfolio:
                return json.dumps({"assets": []})
            rows = [
                {
                    "id": a.id,
                    "type": a.asset_type.value if a.asset_type else None,
                    "name": a.name,
                    "value": a.value,
                    "currency": a.currency.value if a.currency else None,
                    "quantity": a.quantity,
                }
                for a in assets
            ]
            return json.dumps({"assets": rows, "count": len(rows)})

        if name == "list_liabilities":
            if not portfolio:
                return json.dumps({"liabilities": []})
            rows = [
                {
                    "id": L.id,
                    "type": L.liability_type.value if L.liability_type else None,
                    "name": L.name,
                    "outstanding_amount": L.outstanding_amount,
                    "currency": L.currency.value if L.currency else None,
                    "interest_rate_pct": L.interest_rate,
                }
                for L in liabilities
            ]
            return json.dumps({"liabilities": rows, "count": len(rows)})

        if name == "list_retirement_plans":
            plans = (
                db.query(RetirementPlan)
                .filter(RetirementPlan.user_id == user.id, RetirementPlan.is_active == True)
                .all()
            )
            rows = []
            for p in plans:
                rows.append(
                    {
                        "id": p.id,
                        "plan_name": p.plan_name,
                        "primary_target_age": p.usa_target_age,
                        "primary_current_age": p.usa_current_age,
                        "secondary_target_age": p.india_target_age,
                        "secondary_current_age": p.india_current_age,
                        "notes_preview": (p.notes or "")[:200],
                    }
                )
            return json.dumps({"plans": rows, "count": len(rows)})

        return json.dumps({"error": f"unknown_tool:{name}"})

    async def chat(
        self,
        *,
        user: User,
        db: Session,
        messages: List[Dict[str, str]],
        base_currency: Currency,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        cfg = advisor_openai_config(db, user)
        if not cfg:
            raise RuntimeError("advisor_disabled")

        api_key, base_url, model = cfg
        drafts: List[Dict[str, Any]] = []
        client = (
            AsyncOpenAI(api_key=api_key, base_url=base_url)
            if base_url
            else AsyncOpenAI(api_key=api_key)
        )

        openai_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    f"The signed-in user's display name is {user.username!r}. "
                    f"Preferred reporting currency for this session: {base_currency.value}."
                ),
            },
        ]
        openai_messages.extend(messages)

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.chat.completions.create(
                model=model,
                messages=openai_messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.5,
                max_tokens=1600,
            )
            choice = response.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                text = (msg.content or "").strip() or "I could not generate a reply. Please try again."
                return text, drafts

            assistant_payload: Dict[str, Any] = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
            if msg.content:
                assistant_payload["content"] = msg.content
            openai_messages.append(assistant_payload)

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                try:
                    result = await self.run_tool(
                        tc.function.name, args, user, db, base_currency, draft_sink=drafts
                    )
                except Exception as e:
                    logger.exception("Advisor tool error")
                    result = json.dumps({"error": str(e)})
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

        return (
            "I reached the tool-call limit for this turn. Please ask a simpler question "
            "or split it into parts.",
            drafts,
        )


advisor_service = AdvisorService()
