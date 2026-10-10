"""
AI Stop Loss Manager
Automatic stop loss based on ATR, support/resistance, and risk profile
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AIStopLossManager:
    """Intelligent stop loss management system"""
    
    def calculate_stop_loss(self, data: pd.DataFrame, entry_price: float,
                           recommendation: str, support_resistance: Dict,
                           risk_profile: str = 'medium', use_trailing: bool = False,
                           current_price: Optional[float] = None) -> Dict:
        """
        Calculate optimal stop loss
        
        Args:
            data: Historical price data
            entry_price: Entry price for the position
            recommendation: BUY or SELL
            support_resistance: Support and resistance levels
            risk_profile: 'low', 'medium', or 'high'
            use_trailing: Whether to use trailing stop loss
            current_price: Current price (for trailing stop)
        
        Returns:
            {
                'stop_loss': float,
                'stop_loss_type': str,
                'distance': float,
                'distance_pct': float,
                'risk_amount': float,
                'trailing_stop': Optional[float],
                'alert_threshold': float,
                'reasoning': str
            }
        """
        try:
            if data.empty:
                return self._default_stop_loss(entry_price, risk_profile)
            
            # Calculate ATR-based stop loss
            atr = self._calculate_atr(data)
            atr_stop = self._atr_based_stop(entry_price, atr, recommendation, risk_profile)
            
            # Support/Resistance based stop loss
            sr_stop = self._support_resistance_stop(
                entry_price, support_resistance, recommendation
            )
            
            # Risk profile based stop loss
            risk_stop = self._risk_profile_stop(entry_price, risk_profile, recommendation)
            
            # Choose best stop loss (most conservative for buys, most aggressive for sells)
            if recommendation in ['BUY', 'STRONG_BUY']:
                # For buys, use the highest stop loss (closest to entry = less risk)
                stop_loss = max(atr_stop, sr_stop, risk_stop)
            else:
                # For sells, use the lowest stop loss
                stop_loss = min(atr_stop, sr_stop, risk_stop)
            
            # Calculate trailing stop if enabled
            trailing_stop = None
            if use_trailing and current_price:
                trailing_stop = self._calculate_trailing_stop(
                    entry_price, current_price, stop_loss, atr, recommendation
                )
                if trailing_stop:
                    stop_loss = trailing_stop
            
            # Calculate distances
            distance = abs(entry_price - stop_loss)
            distance_pct = (distance / entry_price) * 100 if entry_price > 0 else 0
            
            # Alert threshold (warn when price gets within 2% of stop loss)
            alert_threshold = stop_loss * (1.02 if recommendation in ['BUY', 'STRONG_BUY'] else 0.98)
            
            # Generate reasoning
            reasoning = self._generate_stop_reasoning(
                stop_loss, atr_stop, sr_stop, risk_stop, atr, risk_profile
            )
            
            return {
                'stop_loss': round(stop_loss, 2),
                'stop_loss_type': 'trailing' if trailing_stop else 'static',
                'distance': round(distance, 2),
                'distance_pct': round(distance_pct, 2),
                'risk_amount': round(distance, 2),
                'trailing_stop': round(trailing_stop, 2) if trailing_stop else None,
                'alert_threshold': round(alert_threshold, 2),
                'reasoning': reasoning,
                'atr_value': round(atr, 2),
                'components': {
                    'atr_based': round(atr_stop, 2),
                    'support_resistance': round(sr_stop, 2),
                    'risk_profile': round(risk_stop, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return self._default_stop_loss(entry_price, risk_profile)
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(data) < period:
                return data['Close'].std() * 0.02
            
            high = data['High']
            low = data['Low']
            close = data['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean().iloc[-1]
            
            return float(atr) if not pd.isna(atr) else data['Close'].iloc[-1] * 0.02
            
        except Exception:
            return 1.0
    
    def _atr_based_stop(self, entry_price: float, atr: float, 
                        recommendation: str, risk_profile: str) -> float:
        """Calculate ATR-based stop loss"""
        # Multipliers based on risk profile
        if risk_profile == 'low':
            multiplier = 1.5  # Tighter stop
        elif risk_profile == 'high':
            multiplier = 2.5  # Wider stop
        else:
            multiplier = 2.0  # Medium stop
        
        if recommendation in ['BUY', 'STRONG_BUY']:
            return entry_price - (atr * multiplier)
        else:
            return entry_price + (atr * multiplier)
    
    def _support_resistance_stop(self, entry_price: float, 
                                 support_resistance: Dict, recommendation: str) -> float:
        """Calculate stop loss based on support/resistance"""
        support = support_resistance.get('support', entry_price * 0.95)
        resistance = support_resistance.get('resistance', entry_price * 1.05)
        
        if recommendation in ['BUY', 'STRONG_BUY']:
            # Stop loss just below support
            return support * 0.97
        else:
            # Stop loss just above resistance
            return resistance * 1.03
    
    def _risk_profile_stop(self, entry_price: float, risk_profile: str,
                          recommendation: str) -> float:
        """Calculate stop loss based on risk profile percentage"""
        if risk_profile == 'low':
            risk_pct = 0.015  # 1.5% risk
        elif risk_profile == 'high':
            risk_pct = 0.03   # 3% risk
        else:
            risk_pct = 0.02   # 2% risk
        
        if recommendation in ['BUY', 'STRONG_BUY']:
            return entry_price * (1 - risk_pct)
        else:
            return entry_price * (1 + risk_pct)
    
    def _calculate_trailing_stop(self, entry_price: float, current_price: float,
                                initial_stop: float, atr: float,
                                recommendation: str) -> Optional[float]:
        """Calculate trailing stop loss"""
        try:
            if recommendation in ['BUY', 'STRONG_BUY']:
                # For long positions, trailing stop moves up
                if current_price > entry_price:
                    # Trail by 2 ATR below current price
                    trailing = current_price - (atr * 2)
                    # Only move stop up, never down
                    return max(initial_stop, trailing)
            else:
                # For short positions, trailing stop moves down
                if current_price < entry_price:
                    # Trail by 2 ATR above current price
                    trailing = current_price + (atr * 2)
                    # Only move stop down, never up
                    return min(initial_stop, trailing)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating trailing stop: {e}")
            return None
    
    def check_stop_loss_alert(self, current_price: float, stop_loss_data: Dict) -> Dict:
        """Check if stop loss alert should be triggered"""
        stop_loss = stop_loss_data['stop_loss']
        alert_threshold = stop_loss_data['alert_threshold']
        
        distance_to_stop = abs(current_price - stop_loss)
        distance_pct = (distance_to_stop / current_price) * 100 if current_price > 0 else 0
        
        # Alert levels
        if distance_pct <= 1.0:
            alert_level = 'CRITICAL'
            message = '⚠️ CRITICAL: Price very close to stop loss!'
        elif distance_pct <= 2.0:
            alert_level = 'WARNING'
            message = '⚠️ WARNING: Price approaching stop loss'
        elif distance_pct <= 3.0:
            alert_level = 'CAUTION'
            message = 'ℹ️ CAUTION: Monitor stop loss distance'
        else:
            alert_level = 'SAFE'
            message = '✅ Stop loss distance is safe'
        
        return {
            'alert_level': alert_level,
            'message': message,
            'distance_to_stop': round(distance_to_stop, 2),
            'distance_pct': round(distance_pct, 2),
            'should_alert': alert_level in ['CRITICAL', 'WARNING']
        }
    
    def _generate_stop_reasoning(self, final_stop: float, atr_stop: float,
                                sr_stop: float, risk_stop: float,
                                atr: float, risk_profile: str) -> str:
        """Generate reasoning for stop loss placement"""
        reasons = []
        
        # Determine which method was primary
        if abs(final_stop - atr_stop) < abs(final_stop - sr_stop):
            reasons.append(f"Stop loss based on ATR volatility ({atr:.2f})")
        else:
            reasons.append("Stop loss placed below/above key support/resistance level")
        
        reasons.append(f"Risk profile: {risk_profile.upper()}")
        reasons.append(f"Stop loss distance: {abs(final_stop - (final_stop + atr)):.2f} ({abs(final_stop - (final_stop + atr)) / final_stop * 100:.1f}%)")
        
        return " | ".join(reasons)
    
    def _default_stop_loss(self, entry_price: float, risk_profile: str) -> Dict:
        """Default stop loss if calculation fails"""
        risk_pct = 0.02 if risk_profile == 'medium' else (0.015 if risk_profile == 'low' else 0.03)
        stop_loss = entry_price * (1 - risk_pct)
        
        return {
            'stop_loss': round(stop_loss, 2),
            'stop_loss_type': 'static',
            'distance': round(entry_price * risk_pct, 2),
            'distance_pct': round(risk_pct * 100, 2),
            'risk_amount': round(entry_price * risk_pct, 2),
            'trailing_stop': None,
            'alert_threshold': round(stop_loss * 1.02, 2),
            'reasoning': f'Default {risk_pct*100:.1f}% stop loss',
            'atr_value': 0,
            'components': {}
        }
