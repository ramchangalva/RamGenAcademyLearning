"""
Smart Entry & Exit System
Provides best buy zones, partial profit targets, and dynamic updates
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SmartEntryExitSystem:
    """Intelligent entry and exit level calculation"""
    
    def calculate_entry_exit(self, data: pd.DataFrame, recommendation: str,
                            support_resistance: Dict, current_price: float,
                            risk_profile: str = 'medium') -> Dict:
        """
        Calculate smart entry and exit levels
        
        Args:
            data: Historical price data
            recommendation: BUY, SELL, or HOLD
            support_resistance: Support and resistance levels
            current_price: Current stock price
            risk_profile: 'low', 'medium', or 'high'
        
        Returns:
            {
                'entry': {
                    'aggressive': float,
                    'safe': float,
                    'current': float
                },
                'exit': {
                    'partial_1': float,  # 25% profit target
                    'partial_2': float,  # 50% profit target
                    'final': float       # 100% profit target
                },
                'stop_loss': float,
                'risk_reward': float,
                'position_sizing': {
                    'conservative': float,
                    'moderate': float,
                    'aggressive': float
                }
            }
        """
        try:
            support = support_resistance.get('support', current_price * 0.95)
            resistance = support_resistance.get('resistance', current_price * 1.05)
            
            # Calculate ATR for volatility-based levels
            atr = self._calculate_atr(data)
            
            if recommendation in ['BUY', 'STRONG_BUY']:
                return self._calculate_buy_levels(
                    current_price, support, resistance, atr, risk_profile
                )
            elif recommendation in ['SELL', 'STRONG_SELL']:
                return self._calculate_sell_levels(
                    current_price, support, resistance, atr, risk_profile
                )
            else:  # HOLD
                return self._calculate_hold_levels(
                    current_price, support, resistance, atr
                )
                
        except Exception as e:
            logger.error(f"Error calculating entry/exit: {e}")
            return self._default_levels(current_price)
    
    def _calculate_buy_levels(self, current_price: float, support: float,
                              resistance: float, atr: float, risk_profile: str) -> Dict:
        """Calculate buy entry and exit levels"""
        
        # Entry levels
        aggressive_entry = max(support, current_price * 0.98)  # Slightly below current
        safe_entry = support * 0.99  # Near support
        
        # Stop loss (below support with ATR buffer)
        stop_loss = support - (atr * 0.5)
        if stop_loss > support * 0.97:
            stop_loss = support * 0.97
        
        # Profit targets
        risk = aggressive_entry - stop_loss
        if risk <= 0:
            risk = current_price * 0.02
        
        # Adjust targets based on risk profile
        if risk_profile == 'low':
            multiplier_1, multiplier_2, multiplier_3 = 1.5, 2.5, 4.0
        elif risk_profile == 'high':
            multiplier_1, multiplier_2, multiplier_3 = 2.0, 3.5, 5.0
        else:  # medium
            multiplier_1, multiplier_2, multiplier_3 = 1.5, 2.5, 4.0
        
        partial_1 = aggressive_entry + (risk * multiplier_1)  # 25% position
        partial_2 = aggressive_entry + (risk * multiplier_2)  # 50% position
        final_exit = min(resistance, aggressive_entry + (risk * multiplier_3))  # 25% position
        
        # Position sizing recommendations
        position_sizing = self._calculate_position_sizing(
            risk, current_price, risk_profile
        )
        
        return {
            'entry': {
                'aggressive': round(aggressive_entry, 2),
                'safe': round(safe_entry, 2),
                'current': round(current_price, 2),
                'recommended': 'aggressive' if current_price <= aggressive_entry * 1.01 else 'safe'
            },
            'exit': {
                'partial_1': round(partial_1, 2),  # Take 25% profit
                'partial_2': round(partial_2, 2),  # Take another 25% (50% total)
                'final': round(final_exit, 2)      # Exit remaining 50%
            },
            'stop_loss': round(stop_loss, 2),
            'risk_reward': round((partial_1 - aggressive_entry) / risk, 2) if risk > 0 else 0,
            'position_sizing': position_sizing,
            'risk_amount': round(risk, 2),
            'risk_percent': round((risk / aggressive_entry) * 100, 2) if aggressive_entry > 0 else 0
        }
    
    def _calculate_sell_levels(self, current_price: float, support: float,
                               resistance: float, atr: float, risk_profile: str) -> Dict:
        """Calculate sell entry and exit levels"""
        
        # Entry levels (for short positions)
        aggressive_entry = min(resistance, current_price * 1.02)
        safe_entry = resistance * 1.01
        
        # Stop loss (above resistance)
        stop_loss = resistance + (atr * 0.5)
        if stop_loss < resistance * 1.03:
            stop_loss = resistance * 1.03
        
        # Profit targets
        risk = stop_loss - aggressive_entry
        if risk <= 0:
            risk = current_price * 0.02
        
        if risk_profile == 'low':
            multiplier_1, multiplier_2, multiplier_3 = 1.5, 2.5, 4.0
        elif risk_profile == 'high':
            multiplier_1, multiplier_2, multiplier_3 = 2.0, 3.5, 5.0
        else:
            multiplier_1, multiplier_2, multiplier_3 = 1.5, 2.5, 4.0
        
        partial_1 = aggressive_entry - (risk * multiplier_1)
        partial_2 = aggressive_entry - (risk * multiplier_2)
        final_exit = max(support, aggressive_entry - (risk * multiplier_3))
        
        position_sizing = self._calculate_position_sizing(
            risk, current_price, risk_profile
        )
        
        return {
            'entry': {
                'aggressive': round(aggressive_entry, 2),
                'safe': round(safe_entry, 2),
                'current': round(current_price, 2),
                'recommended': 'aggressive' if current_price >= aggressive_entry * 0.99 else 'safe'
            },
            'exit': {
                'partial_1': round(partial_1, 2),
                'partial_2': round(partial_2, 2),
                'final': round(final_exit, 2)
            },
            'stop_loss': round(stop_loss, 2),
            'risk_reward': round((aggressive_entry - partial_1) / risk, 2) if risk > 0 else 0,
            'position_sizing': position_sizing,
            'risk_amount': round(risk, 2),
            'risk_percent': round((risk / aggressive_entry) * 100, 2) if aggressive_entry > 0 else 0
        }
    
    def _calculate_hold_levels(self, current_price: float, support: float,
                               resistance: float, atr: float) -> Dict:
        """Calculate levels for HOLD recommendation"""
        return {
            'entry': {
                'aggressive': round(current_price, 2),
                'safe': round(current_price, 2),
                'current': round(current_price, 2),
                'recommended': 'wait'
            },
            'exit': {
                'partial_1': round(resistance * 0.98, 2),
                'partial_2': round(resistance, 2),
                'final': round(resistance * 1.02, 2)
            },
            'stop_loss': round(support * 0.97, 2),
            'risk_reward': 0,
            'position_sizing': {'conservative': 0, 'moderate': 0, 'aggressive': 0},
            'risk_amount': 0,
            'risk_percent': 0
        }
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(data) < period:
                return data['Close'].std() * 0.02  # Fallback
            
            high = data['High']
            low = data['Low']
            close = data['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean().iloc[-1]
            
            return float(atr) if not pd.isna(atr) else data['Close'].iloc[-1] * 0.02
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return data['Close'].iloc[-1] * 0.02 if not data.empty else 1.0
    
    def _calculate_position_sizing(self, risk_amount: float, current_price: float,
                                   risk_profile: str) -> Dict:
        """Calculate recommended position sizes based on risk"""
        if risk_amount <= 0 or current_price <= 0:
            return {'conservative': 0, 'moderate': 0, 'aggressive': 0}
        
        # Risk percentages based on profile
        if risk_profile == 'low':
            risk_pct = 0.01  # 1% of capital
        elif risk_profile == 'high':
            risk_pct = 0.03  # 3% of capital
        else:
            risk_pct = 0.02  # 2% of capital
        
        # Assuming $10,000 account for calculation (user can scale)
        account_size = 10000
        risk_dollar = account_size * risk_pct
        
        # Position size = risk_dollar / risk_per_share
        position_size = risk_dollar / risk_amount
        
        # Conservative: 50% of calculated size
        # Moderate: 100% of calculated size
        # Aggressive: 150% of calculated size
        
        return {
            'conservative': round(position_size * 0.5, 2),
            'moderate': round(position_size, 2),
            'aggressive': round(position_size * 1.5, 2),
            'risk_percent': risk_pct * 100,
            'risk_dollar': round(risk_dollar, 2)
        }
    
    def _default_levels(self, current_price: float) -> Dict:
        """Return default levels if calculation fails"""
        return {
            'entry': {
                'aggressive': round(current_price, 2),
                'safe': round(current_price, 2),
                'current': round(current_price, 2),
                'recommended': 'wait'
            },
            'exit': {
                'partial_1': round(current_price * 1.05, 2),
                'partial_2': round(current_price * 1.10, 2),
                'final': round(current_price * 1.15, 2)
            },
            'stop_loss': round(current_price * 0.95, 2),
            'risk_reward': 0,
            'position_sizing': {'conservative': 0, 'moderate': 0, 'aggressive': 0},
            'risk_amount': 0,
            'risk_percent': 0
        }
    
    def get_dynamic_updates(self, current_price: float, entry_exit: Dict) -> Dict:
        """Get dynamic updates as price moves"""
        entry = entry_exit['entry']['aggressive']
        stop_loss = entry_exit['stop_loss']
        partial_1 = entry_exit['exit']['partial_1']
        
        # Calculate distance to each level
        distance_to_entry = abs(current_price - entry) / entry * 100
        distance_to_stop = abs(current_price - stop_loss) / entry * 100
        distance_to_target = abs(current_price - partial_1) / entry * 100
        
        # Status
        if current_price <= entry * 1.01:
            status = 'AT_ENTRY'
            message = 'Price is near entry zone - Consider entering'
        elif current_price >= partial_1 * 0.98:
            status = 'NEAR_TARGET'
            message = 'Price approaching first profit target - Consider partial exit'
        elif current_price <= stop_loss * 1.02:
            status = 'NEAR_STOP'
            message = '⚠️ Price approaching stop loss - Monitor closely'
        else:
            status = 'IN_TRADE'
            message = 'Position is active - Monitor for exit signals'
        
        return {
            'status': status,
            'message': message,
            'current_price': round(current_price, 2),
            'distances': {
                'to_entry': round(distance_to_entry, 2),
                'to_stop': round(distance_to_stop, 2),
                'to_target': round(distance_to_target, 2)
            },
            'profit_loss': round(current_price - entry, 2),
            'profit_loss_pct': round((current_price - entry) / entry * 100, 2)
        }
