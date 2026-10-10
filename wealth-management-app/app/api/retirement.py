"""
Retirement planning API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.retirement import RetirementPlan
from app.services.retirement_calculator import RetirementCalculator
from pydantic import BaseModel

router = APIRouter(prefix="/api/retirement", tags=["retirement"])

retirement_calculator = RetirementCalculator()


class RetirementPlanCreate(BaseModel):
    plan_name: str
    # Primary plan (USD fields; API keys unchanged for compatibility)
    usa_target_age: Optional[int] = None
    usa_current_age: Optional[int] = None
    usa_retirement_corpus_usd: Optional[float] = None
    usa_monthly_expense_usd: Optional[float] = None
    usa_current_savings_usd: Optional[float] = None
    usa_monthly_contribution_usd: Optional[float] = None
    usa_expected_return_pct: Optional[float] = 7.0
    usa_inflation_pct: Optional[float] = 3.0
    # Secondary plan (INR fields; API keys unchanged for compatibility)
    india_target_age: Optional[int] = None
    india_current_age: Optional[int] = None
    india_retirement_corpus_inr: Optional[float] = None
    india_monthly_expense_inr: Optional[float] = None
    india_current_savings_inr: Optional[float] = None
    india_monthly_contribution_inr: Optional[float] = None
    india_expected_return_pct: Optional[float] = 8.0
    india_inflation_pct: Optional[float] = 6.0
    notes: Optional[str] = None


@router.post("/plans")
async def create_retirement_plan(
    plan_data: RetirementPlanCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new retirement plan"""
    plan = RetirementPlan(
        user_id=user.id,
        **plan_data.dict()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return plan


@router.get("/plans")
async def get_retirement_plans(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all retirement plans for user"""
    plans = db.query(RetirementPlan).filter(
        RetirementPlan.user_id == user.id,
        RetirementPlan.is_active == True
    ).all()
    
    return plans


@router.get("/plans/{plan_id}/calculate")
async def calculate_retirement_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate retirement plan projections"""
    plan = db.query(RetirementPlan).filter(
        RetirementPlan.id == plan_id,
        RetirementPlan.user_id == user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement plan not found"
        )
    
    results = {}
    
    # Primary (USD) plan
    if plan.usa_current_age and plan.usa_target_age:
        usa_result = retirement_calculator.calculate_usa_retirement(
            current_age=plan.usa_current_age,
            target_age=plan.usa_target_age,
            current_savings=plan.usa_current_savings_usd or 0,
            monthly_contribution=plan.usa_monthly_contribution_usd or 0,
            monthly_expense=plan.usa_monthly_expense_usd or 0,
            expected_return=plan.usa_expected_return_pct or 7.0,
            inflation=plan.usa_inflation_pct or 3.0
        )
        results["usa"] = usa_result
    
    # Secondary (INR) plan
    if plan.india_current_age and plan.india_target_age:
        india_result = retirement_calculator.calculate_india_retirement(
            current_age=plan.india_current_age,
            target_age=plan.india_target_age,
            current_savings=plan.india_current_savings_inr or 0,
            monthly_contribution=plan.india_monthly_contribution_inr or 0,
            monthly_expense=plan.india_monthly_expense_inr or 0,
            expected_return=plan.india_expected_return_pct or 8.0,
            inflation=plan.india_inflation_pct or 6.0
        )
        # Convert keys to INR
        india_result_renamed = {}
        for key, value in india_result.items():
            new_key = key.replace("_usd", "_inr")
            india_result_renamed[new_key] = value
        results["india"] = india_result_renamed
    
    # Calculate combined if both exist
    if "usa" in results and "india" in results:
        combined = await retirement_calculator.calculate_combined_retirement(
            results["usa"], results["india"]
        )
        results["combined"] = combined
    
    return results
