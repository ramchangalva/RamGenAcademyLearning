"""
Portfolio API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.portfolio import Portfolio, Asset, Liability, Insurance, Currency, AssetType, LiabilityType
from app.services.portfolio_calculator import PortfolioCalculator
from app.services.exchange_rate import exchange_rate_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

portfolio_calculator = PortfolioCalculator()


class AssetCreate(BaseModel):
    asset_type: AssetType
    name: str
    ticker_symbol: Optional[str] = None
    description: Optional[str] = None
    value: float
    currency: Currency = Currency.USD
    quantity: Optional[float] = None
    purchase_date: Optional[datetime] = None


class LiabilityCreate(BaseModel):
    liability_type: LiabilityType
    name: str
    description: Optional[str] = None
    outstanding_amount: float
    currency: Currency = Currency.USD
    interest_rate: Optional[float] = None
    due_date: Optional[datetime] = None


class InsuranceCreate(BaseModel):
    insurance_type: str
    name: str
    coverage_amount: float
    currency: Currency = Currency.USD
    premium_amount: Optional[float] = None
    premium_frequency: Optional[str] = None
    policy_number: Optional[str] = None
    expiry_date: Optional[datetime] = None


@router.get("/summary")
async def get_portfolio_summary(
    base_currency: Currency = Currency.USD,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio summary"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    
    if not portfolio:
        # Create default portfolio
        portfolio = Portfolio(user_id=user.id, name="Main Portfolio")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    assets = db.query(Asset).filter(Asset.portfolio_id == portfolio.id).all()
    liabilities = db.query(Liability).filter(Liability.portfolio_id == portfolio.id).all()
    insurance_list = db.query(Insurance).filter(Insurance.portfolio_id == portfolio.id).all()
    
    summary = await portfolio_calculator.calculate_portfolio_summary(
        assets, liabilities, insurance_list, base_currency
    )
    
    return summary


@router.post("/assets")
async def create_asset(
    asset_data: AssetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new asset"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=user.id, name="Main Portfolio")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    asset = Asset(
        portfolio_id=portfolio.id,
        **asset_data.dict()
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return asset


@router.get("/assets")
async def get_assets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assets"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    
    if not portfolio:
        return []
    
    assets = db.query(Asset).filter(Asset.portfolio_id == portfolio.id).all()
    return assets


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an asset owned by the current user."""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.portfolio_id == portfolio.id
    ).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    db.delete(asset)
    db.commit()
    return {"ok": True}


@router.post("/liabilities")
async def create_liability(
    liability_data: LiabilityCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new liability"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=user.id, name="Main Portfolio")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    liability = Liability(
        portfolio_id=portfolio.id,
        **liability_data.dict()
    )
    db.add(liability)
    db.commit()
    db.refresh(liability)
    
    return liability


@router.get("/liabilities")
async def get_liabilities(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all liabilities"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    
    if not portfolio:
        return []
    
    liabilities = db.query(Liability).filter(Liability.portfolio_id == portfolio.id).all()
    return liabilities


@router.delete("/liabilities/{liability_id}")
async def delete_liability(
    liability_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a liability owned by the current user."""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liability not found")

    liability = db.query(Liability).filter(
        Liability.id == liability_id,
        Liability.portfolio_id == portfolio.id
    ).first()
    if not liability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liability not found")

    db.delete(liability)
    db.commit()
    return {"ok": True}


@router.post("/insurance")
async def create_insurance(
    insurance_data: InsuranceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new insurance entry"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=user.id, name="Main Portfolio")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    insurance = Insurance(
        portfolio_id=portfolio.id,
        **insurance_data.dict()
    )
    db.add(insurance)
    db.commit()
    db.refresh(insurance)
    
    return insurance


@router.get("/exchange-rate")
async def get_exchange_rate(
    from_currency: str = "USD",
    to_currency: str = "USD"
):
    """Get current exchange rate"""
    rate = await exchange_rate_service.get_exchange_rate(from_currency, to_currency)
    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": rate
    }
