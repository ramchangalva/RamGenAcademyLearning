"""
Portfolio, Asset, Liability, and Insurance models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class Currency(str, enum.Enum):
    """Supported currencies"""
    USD = "USD"
    INR = "INR"


class AssetType(str, enum.Enum):
    """Asset types"""
    MUTUAL_FUNDS = "mutual_funds"
    STOCKS = "stocks"
    FIXED_INCOME = "fixed_income"
    REAL_ESTATE = "real_estate"
    RETIREMENT_ACCOUNT = "retirement_account"
    SMALL_SAVINGS = "small_savings"
    CASH = "cash"
    OTHER = "other"


class LiabilityType(str, enum.Enum):
    """Liability types"""
    HOME_LOAN = "home_loan"
    PERSONAL_LOAN = "personal_loan"
    CREDIT_CARD = "credit_card"
    CAR_LOAN = "car_loan"
    OTHER = "other"


class Portfolio(Base):
    """Portfolio model"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False, default="Main Portfolio")
    cash_balance = Column(Float, nullable=True)
    cash_currency = Column(SQLEnum(Currency), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="portfolios")
    assets = relationship("Asset", back_populates="portfolio", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="portfolio", cascade="all, delete-orphan")
    insurance = relationship("Insurance", back_populates="portfolio", cascade="all, delete-orphan")


class Asset(Base):
    """Asset model"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    name = Column(String, nullable=False)
    ticker_symbol = Column(String(32), nullable=True)
    description = Column(String, nullable=True)
    value = Column(Float, nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False, default=Currency.USD)
    quantity = Column(Float, nullable=True)  # For stocks, mutual funds
    purchase_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="assets")


class Liability(Base):
    """Liability model"""
    __tablename__ = "liabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    liability_type = Column(SQLEnum(LiabilityType), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    outstanding_amount = Column(Float, nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False, default=Currency.USD)
    interest_rate = Column(Float, nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="liabilities")


class Insurance(Base):
    """Insurance model"""
    __tablename__ = "insurance"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    insurance_type = Column(String, nullable=False)  # life, health, term, etc.
    name = Column(String, nullable=False)
    coverage_amount = Column(Float, nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False, default=Currency.USD)
    premium_amount = Column(Float, nullable=True)
    premium_frequency = Column(String, nullable=True)  # monthly, yearly
    policy_number = Column(String, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="insurance")
