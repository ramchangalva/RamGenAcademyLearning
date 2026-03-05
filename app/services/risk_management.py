"""
Risk Management Dashboard
Risk per trade calculator, position sizing, win/loss expectancy
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskManagementDashboard:
    """Comprehensive risk management system"""
    
    def calculate_risk(self, entry_price: float, stop_loss: float,
                      account_size: float, risk_percent: float = 2.0) -> Dict:
        """
        Calculate risk per trade
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            account_size: Total account size
            risk_percent: Risk percentage per trade (default 2%)
        
        Returns:
            {
                'risk_per_trade': float,
                'risk_amount': float,
                'position_size': float,
                'shares': int,
                'max_loss': float,
                'risk_reward_ratio': float
            }
        """
        try:
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share <= 0:
                return self._default_risk(entry_price, account_size)
            
            risk_amount = account_size * (risk_percent / 100)
            position_size = risk_amount / risk_per_share
            shares = int(position_size)
            max_loss = shares * risk_per_share
            
            return {
                'risk_per_trade': risk_percent,
                'risk_amount': round(risk_amount, 2),
                'position_size': round(position_size * entry_price, 2),
                'shares': shares,
                'max_loss': round(max_loss, 2),
                'risk_per_share': round(risk_per_share, 2),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk: {e}")
            return self._default_risk(entry_price, account_size)
    
    def calculate_position_sizing(self, account_size: float, risk_percent: float,
                                 entry_price: float, stop_loss: float,
                                 target_price: Optional[float] = None) -> Dict:
        """Calculate optimal position sizing"""
        try:
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share <= 0:
                risk_per_share = entry_price * 0.02  # Default 2%
            
            risk_amount = account_size * (risk_percent / 100)
            shares = int(risk_amount / risk_per_share)
            position_value = shares * entry_price
            
            # Risk/Reward
            risk_reward = None
            if target_price:
                reward_per_share = abs(target_price - entry_price)
                risk_reward = reward_per_share / risk_per_share if risk_per_share > 0 else 0
            
            return {
                'account_size': round(account_size, 2),
                'risk_percent': risk_percent,
                'risk_amount': round(risk_amount, 2),
                'shares': shares,
                'position_value': round(position_value, 2),
                'position_percent': round((position_value / account_size) * 100, 2),
                'risk_per_share': round(risk_per_share, 2),
                'risk_reward_ratio': round(risk_reward, 2) if risk_reward else None,
                'max_loss': round(shares * risk_per_share, 2),
                'max_loss_percent': round((shares * risk_per_share / account_size) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating position sizing: {e}")
            return {}
    
    def calculate_win_loss_expectancy(self, win_rate: float, avg_win: float,
                                     avg_loss: float, num_trades: int = 100) -> Dict:
        """
        Calculate win/loss expectancy
        
        Args:
            win_rate: Win rate percentage (0-100)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount
            num_trades: Number of trades to simulate
        """
        try:
            wins = int(num_trades * (win_rate / 100))
            losses = num_trades - wins
            
            total_profit = wins * avg_win
            total_loss = losses * avg_loss
            net_expectancy = total_profit - total_loss
            expectancy_per_trade = net_expectancy / num_trades
            
            return {
                'win_rate': win_rate,
                'num_trades': num_trades,
                'wins': wins,
                'losses': losses,
                'total_profit': round(total_profit, 2),
                'total_loss': round(total_loss, 2),
                'net_expectancy': round(net_expectancy, 2),
                'expectancy_per_trade': round(expectancy_per_trade, 2),
                'profit_factor': round(total_profit / total_loss, 2) if total_loss > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating expectancy: {e}")
            return {}
    
    def capital_protection_mode(self, account_size: float, current_drawdown: float,
                               max_drawdown_percent: float = 20.0) -> Dict:
        """
        Capital protection mode - reduces risk when drawdown is high
        
        Args:
            account_size: Current account size
            current_drawdown: Current drawdown amount
            max_drawdown_percent: Maximum allowed drawdown percentage
        """
        try:
            drawdown_percent = (current_drawdown / account_size) * 100 if account_size > 0 else 0
            max_drawdown = account_size * (max_drawdown_percent / 100)
            
            # Calculate risk reduction
            if drawdown_percent >= max_drawdown_percent * 0.8:
                risk_reduction = 0.5  # Reduce risk by 50%
                mode = 'HIGH_PROTECTION'
                message = 'High drawdown detected - Risk reduced to 1% per trade'
            elif drawdown_percent >= max_drawdown_percent * 0.5:
                risk_reduction = 0.75  # Reduce risk by 25%
                mode = 'MODERATE_PROTECTION'
                message = 'Moderate drawdown - Risk reduced to 1.5% per trade'
            else:
                risk_reduction = 1.0  # Normal risk
                mode = 'NORMAL'
                message = 'Normal risk parameters active'
            
            adjusted_risk = 2.0 * risk_reduction  # Base risk is 2%
            
            return {
                'mode': mode,
                'drawdown_percent': round(drawdown_percent, 2),
                'max_drawdown': round(max_drawdown, 2),
                'risk_reduction': round(risk_reduction * 100, 1),
                'adjusted_risk_percent': round(adjusted_risk, 2),
                'message': message,
                'recommendation': 'Reduce position sizes' if mode != 'NORMAL' else 'Normal trading'
            }
            
        except Exception as e:
            logger.error(f"Error in capital protection mode: {e}")
            return {'mode': 'NORMAL', 'adjusted_risk_percent': 2.0}
    
    def _default_risk(self, entry_price: float, account_size: float) -> Dict:
        """Default risk calculation"""
        risk_percent = 2.0
        risk_amount = account_size * (risk_percent / 100)
        default_stop = entry_price * 0.98
        risk_per_share = entry_price - default_stop
        shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        
        return {
            'risk_per_trade': risk_percent,
            'risk_amount': round(risk_amount, 2),
            'position_size': round(shares * entry_price, 2),
            'shares': shares,
            'max_loss': round(shares * risk_per_share, 2),
            'risk_per_share': round(risk_per_share, 2)
        }
