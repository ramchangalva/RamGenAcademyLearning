"""
Portfolio Management Service
Manages user portfolios with holdings tracking and performance analysis
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.models.portfolio import Portfolio, Holding, PortfolioPerformance

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manages user portfolios"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
        self._portfolios = self._load_portfolios()
    
    def _load_portfolios(self) -> Dict:
        """Load portfolios from file"""
        if os.path.exists(self.portfolios_file):
            try:
                with open(self.portfolios_file, 'r') as f:
                    data = json.load(f)
                    # Convert to Portfolio objects
                    portfolios = {}
                    for user_id, portfolio_data in data.items():
                        holdings = [Holding(**h) for h in portfolio_data.get('holdings', [])]
                        portfolio = Portfolio(
                            user_id=user_id,
                            holdings=holdings,
                            total_value=portfolio_data.get('total_value', 0.0),
                            total_cost=portfolio_data.get('total_cost', 0.0),
                            total_pnl=portfolio_data.get('total_pnl', 0.0),
                            total_pnl_percent=portfolio_data.get('total_pnl_percent', 0.0),
                            last_updated=portfolio_data.get('last_updated', datetime.now().isoformat())
                        )
                        portfolios[user_id] = portfolio
                    return portfolios
            except Exception as e:
                logger.error(f"Error loading portfolios: {e}")
                return {}
        return {}
    
    def _save_portfolios(self):
        """Save portfolios to file"""
        try:
            data = {}
            for user_id, portfolio in self._portfolios.items():
                data[user_id] = {
                    'holdings': [h.dict() for h in portfolio.holdings],
                    'total_value': portfolio.total_value,
                    'total_cost': portfolio.total_cost,
                    'total_pnl': portfolio.total_pnl,
                    'total_pnl_percent': portfolio.total_pnl_percent,
                    'last_updated': portfolio.last_updated
                }
            with open(self.portfolios_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving portfolios: {e}")
    
    def get_portfolio(self, user_id: str) -> Portfolio:
        """Get user's portfolio"""
        if user_id not in self._portfolios:
            self._portfolios[user_id] = Portfolio(user_id=user_id)
        portfolio = self._portfolios[user_id]
        portfolio.calculate_metrics()
        return portfolio
    
    def add_holding(self, user_id: str, holding: Holding) -> bool:
        """Add or update holding in portfolio"""
        try:
            portfolio = self.get_portfolio(user_id)
            
            # Check if holding already exists
            existing_idx = None
            for idx, h in enumerate(portfolio.holdings):
                if h.symbol.upper() == holding.symbol.upper() and h.asset_type == holding.asset_type:
                    existing_idx = idx
                    break
            
            if existing_idx is not None:
                # Update existing holding (average the purchase price)
                existing = portfolio.holdings[existing_idx]
                total_quantity = existing.quantity + holding.quantity
                total_cost = (existing.quantity * existing.purchase_price) + (holding.quantity * holding.purchase_price)
                existing.quantity = total_quantity
                existing.purchase_price = total_cost / total_quantity if total_quantity > 0 else existing.purchase_price
                existing.current_price = holding.current_price
                if holding.notes:
                    existing.notes = holding.notes
            else:
                # Add new holding
                portfolio.holdings.append(holding)
            
            portfolio.calculate_metrics()
            self._save_portfolios()
            return True
        except Exception as e:
            logger.error(f"Error adding holding: {e}")
            return False
    
    def remove_holding(self, user_id: str, symbol: str, asset_type: str) -> bool:
        """Remove holding from portfolio"""
        try:
            portfolio = self.get_portfolio(user_id)
            portfolio.holdings = [
                h for h in portfolio.holdings 
                if not (h.symbol.upper() == symbol.upper() and h.asset_type == asset_type)
            ]
            portfolio.calculate_metrics()
            self._save_portfolios()
            return True
        except Exception as e:
            logger.error(f"Error removing holding: {e}")
            return False
    
    def update_holding_prices(self, user_id: str, prices: Dict[str, float]):
        """Update current prices for holdings"""
        try:
            portfolio = self.get_portfolio(user_id)
            for holding in portfolio.holdings:
                key = f"{holding.symbol}_{holding.asset_type}"
                if key in prices:
                    holding.current_price = prices[key]
            portfolio.calculate_metrics()
            self._save_portfolios()
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
    
    def get_performance(self, user_id: str) -> PortfolioPerformance:
        """Get portfolio performance metrics"""
        portfolio = self.get_portfolio(user_id)
        performance = PortfolioPerformance()
        
        # Calculate asset allocation
        if portfolio.total_value > 0:
            for holding in portfolio.holdings:
                holding_value = holding.quantity * holding.current_price
                if holding.asset_type not in performance.asset_allocation:
                    performance.asset_allocation[holding.asset_type] = 0.0
                performance.asset_allocation[holding.asset_type] += (holding_value / portfolio.total_value * 100)
        
        # Find best and worst performers
        if portfolio.holdings:
            holdings_with_pnl = []
            for holding in portfolio.holdings:
                pnl = (holding.current_price - holding.purchase_price) * holding.quantity
                pnl_percent = ((holding.current_price - holding.purchase_price) / holding.purchase_price * 100) if holding.purchase_price > 0 else 0
                holdings_with_pnl.append({
                    'symbol': holding.symbol,
                    'asset_type': holding.asset_type,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                })
            
            if holdings_with_pnl:
                best = max(holdings_with_pnl, key=lambda x: x['pnl_percent'])
                worst = min(holdings_with_pnl, key=lambda x: x['pnl_percent'])
                performance.best_performer = best
                performance.worst_performer = worst
        
        return performance
