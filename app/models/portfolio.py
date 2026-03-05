"""
Portfolio Management Models
"""
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class Holding(BaseModel):
    """Individual holding in portfolio"""
    symbol: str = Field(..., description="Asset symbol")
    asset_type: str = Field(..., description="Type: stock, crypto, commodity, etf")
    quantity: float = Field(..., gt=0, description="Number of shares/units")
    purchase_price: float = Field(..., gt=0, description="Average purchase price")
    current_price: float = Field(default=0.0, description="Current market price")
    purchase_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    notes: Optional[str] = Field(default=None, description="Additional notes")
    
    @validator('asset_type')
    def validate_asset_type(cls, v):
        allowed = ['stock', 'crypto', 'commodity', 'etf']
        if v.lower() not in allowed:
            raise ValueError(f"Asset type must be one of {allowed}")
        return v.lower()


class Portfolio(BaseModel):
    """User portfolio"""
    user_id: str = Field(..., description="User identifier")
    holdings: List[Holding] = Field(default_factory=list)
    total_value: float = Field(default=0.0, description="Total portfolio value")
    total_cost: float = Field(default=0.0, description="Total cost basis")
    total_pnl: float = Field(default=0.0, description="Total profit/loss")
    total_pnl_percent: float = Field(default=0.0, description="Total P&L percentage")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def calculate_metrics(self):
        """Calculate portfolio metrics"""
        self.total_cost = sum(h.quantity * h.purchase_price for h in self.holdings)
        self.total_value = sum(h.quantity * h.current_price for h in self.holdings)
        self.total_pnl = self.total_value - self.total_cost
        self.total_pnl_percent = (self.total_pnl / self.total_cost * 100) if self.total_cost > 0 else 0.0
        self.last_updated = datetime.now().isoformat()


class PortfolioPerformance(BaseModel):
    """Portfolio performance metrics"""
    daily_pnl: float = 0.0
    daily_pnl_percent: float = 0.0
    weekly_pnl: float = 0.0
    weekly_pnl_percent: float = 0.0
    monthly_pnl: float = 0.0
    monthly_pnl_percent: float = 0.0
    best_performer: Optional[Dict] = None
    worst_performer: Optional[Dict] = None
    asset_allocation: Dict[str, float] = Field(default_factory=dict)
