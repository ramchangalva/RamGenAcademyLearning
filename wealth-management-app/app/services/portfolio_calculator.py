"""
Portfolio calculation service
"""
from typing import List, Dict, Optional
from app.models.portfolio import Asset, Liability, Insurance, Currency
from app.services.exchange_rate import exchange_rate_service


class PortfolioCalculator:
    """Service for calculating portfolio metrics"""
    
    def __init__(self):
        self.exchange_service = exchange_rate_service
    
    async def calculate_portfolio_summary(
        self,
        assets: List[Asset],
        liabilities: List[Liability],
        insurance: List[Insurance],
        base_currency: Currency = Currency.USD
    ) -> Dict:
        """
        Calculate portfolio summary with currency conversion
        """
        # Calculate total assets
        total_assets_usd = 0.0
        total_assets_inr = 0.0
        assets_by_type = {}
        
        for asset in assets:
            asset_value_usd = asset.value if asset.currency == Currency.USD else await self.exchange_service.convert_amount(
                asset.value, Currency.INR.value, Currency.USD.value
            )
            asset_value_inr = asset.value if asset.currency == Currency.INR else await self.exchange_service.convert_amount(
                asset.value, Currency.USD.value, Currency.INR.value
            )
            
            total_assets_usd += asset_value_usd
            total_assets_inr += asset_value_inr
            
            # Group by type
            asset_type = asset.asset_type.value
            if asset_type not in assets_by_type:
                assets_by_type[asset_type] = {"usd": 0.0, "inr": 0.0}
            assets_by_type[asset_type]["usd"] += asset_value_usd
            assets_by_type[asset_type]["inr"] += asset_value_inr
        
        # Calculate total liabilities
        total_liabilities_usd = 0.0
        total_liabilities_inr = 0.0
        
        for liability in liabilities:
            liability_value_usd = liability.outstanding_amount if liability.currency == Currency.USD else await self.exchange_service.convert_amount(
                liability.outstanding_amount, Currency.INR.value, Currency.USD.value
            )
            liability_value_inr = liability.outstanding_amount if liability.currency == Currency.INR else await self.exchange_service.convert_amount(
                liability.outstanding_amount, Currency.USD.value, Currency.INR.value
            )
            
            total_liabilities_usd += liability_value_usd
            total_liabilities_inr += liability_value_inr
        
        # Calculate total insurance
        total_insurance_usd = 0.0
        total_insurance_inr = 0.0
        
        for ins in insurance:
            insurance_value_usd = ins.coverage_amount if ins.currency == Currency.USD else await self.exchange_service.convert_amount(
                ins.coverage_amount, Currency.INR.value, Currency.USD.value
            )
            insurance_value_inr = ins.coverage_amount if ins.currency == Currency.INR else await self.exchange_service.convert_amount(
                ins.coverage_amount, Currency.USD.value, Currency.INR.value
            )
            
            total_insurance_usd += insurance_value_usd
            total_insurance_inr += insurance_value_inr
        
        # Calculate net worth
        net_worth_usd = total_assets_usd - total_liabilities_usd
        net_worth_inr = total_assets_inr - total_liabilities_inr
        
        # Calculate asset allocation percentages
        asset_allocation = {}
        if total_assets_usd > 0:
            for asset_type, values in assets_by_type.items():
                asset_allocation[asset_type] = {
                    "usd": values["usd"],
                    "inr": values["inr"],
                    "percentage": (values["usd"] / total_assets_usd) * 100
                }
        
        return {
            "net_worth": {
                "usd": net_worth_usd,
                "inr": net_worth_inr
            },
            "assets": {
                "total_usd": total_assets_usd,
                "total_inr": total_assets_inr,
                "by_type": assets_by_type,
                "allocation": asset_allocation
            },
            "liabilities": {
                "total_usd": total_liabilities_usd,
                "total_inr": total_liabilities_inr
            },
            "insurance": {
                "total_usd": total_insurance_usd,
                "total_inr": total_insurance_inr
            },
            "base_currency": base_currency.value
        }
