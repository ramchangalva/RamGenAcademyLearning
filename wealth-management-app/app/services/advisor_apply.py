"""
Execute advisor-proposed portfolio changes after explicit user confirmation.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.portfolio import Asset, AssetType, Currency, Liability, LiabilityType, Portfolio
from app.models.user import User


def _ensure_portfolio(db: Session, user_id: int) -> Portfolio:
    p = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if not p:
        p = Portfolio(user_id=user_id, name="Main Portfolio")
        db.add(p)
        db.commit()
        db.refresh(p)
    return p


class CreateAssetPayload(BaseModel):
    asset_type: AssetType
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    value: float = Field(..., gt=0)
    currency: Currency = Currency.USD
    quantity: Optional[float] = None
    purchase_date: Optional[datetime] = None


class UpdateAssetPayload(BaseModel):
    asset_id: int
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    value: Optional[float] = Field(None, gt=0)
    currency: Optional[Currency] = None
    quantity: Optional[float] = None
    asset_type: Optional[AssetType] = None


class DeleteAssetPayload(BaseModel):
    asset_id: int


class CreateLiabilityPayload(BaseModel):
    liability_type: LiabilityType
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    outstanding_amount: float = Field(..., gt=0)
    currency: Currency = Currency.USD
    interest_rate: Optional[float] = None
    due_date: Optional[datetime] = None


class UpdateLiabilityPayload(BaseModel):
    liability_id: int
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    outstanding_amount: Optional[float] = Field(None, gt=0)
    currency: Optional[Currency] = None
    interest_rate: Optional[float] = None
    due_date: Optional[datetime] = None
    liability_type: Optional[LiabilityType] = None


class DeleteLiabilityPayload(BaseModel):
    liability_id: int


def apply_advisor_action(
    *,
    db: Session,
    user: User,
    action: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    portfolio = _ensure_portfolio(db, user.id)

    if action == "create_asset":
        data = CreateAssetPayload.model_validate(payload)
        asset = Asset(
            portfolio_id=portfolio.id,
            asset_type=data.asset_type,
            name=data.name,
            description=data.description,
            value=data.value,
            currency=data.currency,
            quantity=data.quantity,
            purchase_date=data.purchase_date,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return {"ok": True, "id": asset.id, "kind": "asset"}

    if action == "update_asset":
        data = UpdateAssetPayload.model_validate(payload)
        asset = db.query(Asset).filter(
            Asset.id == data.asset_id,
            Asset.portfolio_id == portfolio.id,
        ).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        if data.name is not None:
            asset.name = data.name
        if data.description is not None:
            asset.description = data.description
        if data.value is not None:
            asset.value = data.value
        if data.currency is not None:
            asset.currency = data.currency
        if data.quantity is not None:
            asset.quantity = data.quantity
        if data.asset_type is not None:
            asset.asset_type = data.asset_type
        db.commit()
        db.refresh(asset)
        return {"ok": True, "id": asset.id, "kind": "asset"}

    if action == "delete_asset":
        data = DeleteAssetPayload.model_validate(payload)
        asset = db.query(Asset).filter(
            Asset.id == data.asset_id,
            Asset.portfolio_id == portfolio.id,
        ).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        db.delete(asset)
        db.commit()
        return {"ok": True, "id": data.asset_id, "kind": "asset"}

    if action == "create_liability":
        data = CreateLiabilityPayload.model_validate(payload)
        liability = Liability(
            portfolio_id=portfolio.id,
            liability_type=data.liability_type,
            name=data.name,
            description=data.description,
            outstanding_amount=data.outstanding_amount,
            currency=data.currency,
            interest_rate=data.interest_rate,
            due_date=data.due_date,
        )
        db.add(liability)
        db.commit()
        db.refresh(liability)
        return {"ok": True, "id": liability.id, "kind": "liability"}

    if action == "update_liability":
        data = UpdateLiabilityPayload.model_validate(payload)
        liability = db.query(Liability).filter(
            Liability.id == data.liability_id,
            Liability.portfolio_id == portfolio.id,
        ).first()
        if not liability:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liability not found")
        if data.name is not None:
            liability.name = data.name
        if data.description is not None:
            liability.description = data.description
        if data.outstanding_amount is not None:
            liability.outstanding_amount = data.outstanding_amount
        if data.currency is not None:
            liability.currency = data.currency
        if data.interest_rate is not None:
            liability.interest_rate = data.interest_rate
        if data.due_date is not None:
            liability.due_date = data.due_date
        if data.liability_type is not None:
            liability.liability_type = data.liability_type
        db.commit()
        db.refresh(liability)
        return {"ok": True, "id": liability.id, "kind": "liability"}

    if action == "delete_liability":
        data = DeleteLiabilityPayload.model_validate(payload)
        liability = db.query(Liability).filter(
            Liability.id == data.liability_id,
            Liability.portfolio_id == portfolio.id,
        ).first()
        if not liability:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liability not found")
        db.delete(liability)
        db.commit()
        return {"ok": True, "id": data.liability_id, "kind": "liability"}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown action: {action}",
    )
