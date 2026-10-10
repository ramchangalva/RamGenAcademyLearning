"""
Retirement planning models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class RetirementPlan(Base):
    """Retirement planning model"""
    __tablename__ = "retirement_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_name = Column(String, nullable=False)
    
    # Primary scenario (amounts in USD; column names kept for DB compatibility)
    usa_target_age = Column(Integer, nullable=True)
    usa_current_age = Column(Integer, nullable=True)
    usa_retirement_corpus_usd = Column(Float, nullable=True)
    usa_monthly_expense_usd = Column(Float, nullable=True)
    usa_current_savings_usd = Column(Float, nullable=True)
    usa_monthly_contribution_usd = Column(Float, nullable=True)
    usa_expected_return_pct = Column(Float, nullable=True, default=7.0)
    usa_inflation_pct = Column(Float, nullable=True, default=3.0)
    
    # Secondary scenario (amounts in INR; column names kept for DB compatibility)
    india_target_age = Column(Integer, nullable=True)
    india_current_age = Column(Integer, nullable=True)
    india_retirement_corpus_inr = Column(Float, nullable=True)
    india_monthly_expense_inr = Column(Float, nullable=True)
    india_current_savings_inr = Column(Float, nullable=True)
    india_monthly_contribution_inr = Column(Float, nullable=True)
    india_expected_return_pct = Column(Float, nullable=True, default=8.0)
    india_inflation_pct = Column(Float, nullable=True, default=6.0)
    
    # Common
    is_active = Column(Boolean, default=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
