"""
Retirement planning calculator service
"""
from typing import Dict, Optional
from app.models.retirement import RetirementPlan
from app.services.exchange_rate import exchange_rate_service


class RetirementCalculator:
    """Service for retirement planning calculations"""
    
    def __init__(self):
        self.exchange_service = exchange_rate_service
    
    def calculate_usa_retirement(
        self,
        current_age: int,
        target_age: int,
        current_savings: float,
        monthly_contribution: float,
        monthly_expense: float,
        expected_return: float = 7.0,
        inflation: float = 3.0
    ) -> Dict:
        """
        Primary retirement projection (amounts in USD).
        Returns: corpus needed, projected corpus, shortfall/surplus
        """
        years_to_retirement = target_age - current_age
        
        if years_to_retirement <= 0:
            return {
                "error": "Target age must be greater than current age"
            }
        
        # Calculate corpus needed at retirement (considering inflation)
        years_in_retirement = 30  # Assume 30 years in retirement
        monthly_expense_at_retirement = monthly_expense * ((1 + inflation / 100) ** years_to_retirement)
        
        # Calculate corpus needed using present value of annuity
        # Simplified calculation
        real_return = (expected_return - inflation) / 100
        if real_return > 0:
            corpus_needed = monthly_expense_at_retirement * 12 * (
                (1 - (1 / ((1 + real_return) ** years_in_retirement))) / real_return
            )
        else:
            corpus_needed = monthly_expense_at_retirement * 12 * years_in_retirement
        
        # Calculate projected corpus
        monthly_return = expected_return / 100 / 12
        months_to_retirement = years_to_retirement * 12
        
        # Future value of current savings
        fv_current = current_savings * ((1 + monthly_return) ** months_to_retirement)
        
        # Future value of monthly contributions (annuity)
        if monthly_return > 0:
            fv_contributions = monthly_contribution * (
                (((1 + monthly_return) ** months_to_retirement) - 1) / monthly_return
            )
        else:
            fv_contributions = monthly_contribution * months_to_retirement
        
        projected_corpus = fv_current + fv_contributions
        
        # Calculate shortfall/surplus
        shortfall = max(0, corpus_needed - projected_corpus)
        surplus = max(0, projected_corpus - corpus_needed)
        
        # Calculate required monthly contribution to meet goal
        if monthly_return > 0 and shortfall > 0:
            required_contribution = shortfall / (
                (((1 + monthly_return) ** months_to_retirement) - 1) / monthly_return
            )
        else:
            required_contribution = monthly_contribution
        
        return {
            "years_to_retirement": years_to_retirement,
            "corpus_needed_usd": corpus_needed,
            "projected_corpus_usd": projected_corpus,
            "shortfall_usd": shortfall,
            "surplus_usd": surplus,
            "current_savings_usd": current_savings,
            "monthly_contribution_usd": monthly_contribution,
            "required_monthly_contribution_usd": required_contribution,
            "monthly_expense_at_retirement_usd": monthly_expense_at_retirement,
            "on_track": shortfall == 0
        }
    
    def calculate_india_retirement(
        self,
        current_age: int,
        target_age: int,
        current_savings: float,
        monthly_contribution: float,
        monthly_expense: float,
        expected_return: float = 8.0,
        inflation: float = 6.0
    ) -> Dict:
        """
        Secondary retirement projection (amounts in INR; same math as primary).
        """
        result = self.calculate_usa_retirement(
            current_age, target_age, current_savings,
            monthly_contribution, monthly_expense,
            expected_return, inflation
        )
        
        # Rename keys from USD to INR
        renamed_result = {}
        for key, value in result.items():
            new_key = key.replace("_usd", "_inr")
            renamed_result[new_key] = value
        
        return renamed_result
    
    async def calculate_combined_retirement(
        self,
        usa_plan: Dict,
        india_plan: Dict
    ) -> Dict:
        """
        Calculate combined retirement plan with currency conversion
        """
        # Get exchange rate
        usd_to_inr = await self.exchange_service.get_exchange_rate("USD", "INR")
        
        # Convert USA plan to INR for comparison
        usa_corpus_inr = usa_plan.get("corpus_needed_usd", 0) * usd_to_inr
        usa_projected_inr = usa_plan.get("projected_corpus_usd", 0) * usd_to_inr
        
        # Total corpus needed
        total_corpus_needed_inr = usa_corpus_inr + india_plan.get("corpus_needed_inr", 0)
        total_projected_inr = usa_projected_inr + india_plan.get("projected_corpus_inr", 0)
        
        return {
            "total_corpus_needed_inr": total_corpus_needed_inr,
            "total_projected_inr": total_projected_inr,
            "usa_plan": usa_plan,
            "india_plan": india_plan,
            "exchange_rate_usd_inr": usd_to_inr
        }
