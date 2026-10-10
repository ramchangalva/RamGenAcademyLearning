"""
Swing Trading Analyzer
Provides price-based entry and exit levels for swing and intraday traders
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SwingTradingAnalyzer:
    """Analyzes price patterns and provides actionable entry/exit price levels"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        if not self.data.empty:
            self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate technical indicators needed for swing trading"""
        try:
            if 'ATR' not in self.data.columns and len(self.data) >= 14:
                high = self.data['High']
                low = self.data['Low']
                close = self.data['Close']
                
                # Calculate ATR
                tr1 = high - low
                tr2 = abs(high - close.shift())
                tr3 = abs(low - close.shift())
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                self.data['ATR'] = tr.rolling(window=14).mean()
            
            # Calculate recent support/resistance
            if len(self.data) >= 20:
                recent_data = self.data.tail(20)
                self.recent_high = float(recent_data['High'].max())
                self.recent_low = float(recent_data['Low'].min())
            else:
                self.recent_high = float(self.data['High'].max()) if not self.data.empty else 0
                self.recent_low = float(self.data['Low'].min()) if not self.data.empty else 0
                
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            self.recent_high = 0
            self.recent_low = 0
    
    def get_swing_trading_plan(self, 
                               current_price: float,
                               technical_signals: Dict,
                               support_resistance: Dict,
                               recommendation: str) -> Dict:
        """
        Get comprehensive swing trading plan with price levels
        
        Returns actionable entry/exit prices for swing traders (1-5 days) and intraday traders
        """
        try:
            if current_price <= 0:
                return {'error': 'Invalid current price'}
            
            # Get ATR for volatility-based calculations
            atr = float(self.data['ATR'].iloc[-1]) if 'ATR' in self.data.columns and not self.data['ATR'].isna().iloc[-1] else current_price * 0.02
            
            support = support_resistance.get('support', self.recent_low)
            resistance = support_resistance.get('resistance', self.recent_high)
            
            # Determine trading direction
            is_bullish = recommendation in ['BUY', 'STRONG_BUY'] or technical_signals.get('overall') == 'BULLISH'
            is_bearish = recommendation in ['SELL', 'STRONG_SELL'] or technical_signals.get('overall') == 'BEARISH'
            
            if is_bullish:
                return self._generate_bullish_plan(current_price, support, resistance, atr, technical_signals)
            elif is_bearish:
                return self._generate_bearish_plan(current_price, support, resistance, atr, technical_signals)
            else:
                return self._generate_neutral_plan(current_price, support, resistance, atr)
                
        except Exception as e:
            logger.error(f"Error generating swing trading plan: {e}")
            return {'error': str(e)}
    
    def _generate_bullish_plan(self, current_price: float, support: float, 
                               resistance: float, atr: float, technical_signals: Dict) -> Dict:
        """Generate bullish swing trading plan"""
        try:
            # Entry levels
            # Aggressive: Enter now or on small pullback
            aggressive_entry = current_price * 0.998  # Slightly below current for limit order
            
            # Safe: Wait for pullback to support or EMA
            safe_entry = max(support * 0.995, current_price * 0.97)
            
            # Ideal: Best entry point (between safe and aggressive)
            ideal_entry = (aggressive_entry + safe_entry) / 2
            
            # Stop loss (below support with ATR buffer)
            stop_loss = support - (atr * 0.5)
            if stop_loss >= support * 0.98:
                stop_loss = support * 0.97
            
            # Calculate risk per share
            risk_per_share = ideal_entry - stop_loss
            if risk_per_share <= 0:
                risk_per_share = current_price * 0.02
            
            # Profit targets (multiple exits for swing traders)
            # Target 1: Quick scalp (1-2 days) - 1.5x risk
            target_1 = ideal_entry + (risk_per_share * 1.5)
            target_1_pct = ((target_1 - ideal_entry) / ideal_entry) * 100
            
            # Target 2: Swing target (3-5 days) - 2.5x risk
            target_2 = min(resistance, ideal_entry + (risk_per_share * 2.5))
            target_2_pct = ((target_2 - ideal_entry) / ideal_entry) * 100
            
            # Target 3: Extended target (breakout) - 4x risk
            target_3 = min(resistance * 1.02, ideal_entry + (risk_per_share * 4.0))
            target_3_pct = ((target_3 - ideal_entry) / ideal_entry) * 100
            
            # Risk/Reward ratios
            rr_target_1 = (target_1 - ideal_entry) / risk_per_share if risk_per_share > 0 else 0
            rr_target_2 = (target_2 - ideal_entry) / risk_per_share if risk_per_share > 0 else 0
            rr_target_3 = (target_3 - ideal_entry) / risk_per_share if risk_per_share > 0 else 0
            
            # Position sizing (for $10,000 account, risking 2%)
            account_risk = 200  # 2% of $10,000
            shares_aggressive = int(account_risk / risk_per_share) if risk_per_share > 0 else 0
            shares_safe = int(account_risk / (aggressive_entry - stop_loss)) if (aggressive_entry - stop_loss) > 0 else 0
            
            return {
                'direction': 'BULLISH',
                'recommendation': 'LONG',
                'current_price': round(current_price, 2),
                'entry_levels': {
                    'aggressive': {
                        'price': round(aggressive_entry, 2),
                        'description': 'Enter now or on small pullback',
                        'shares': shares_safe,
                        'risk': round((aggressive_entry - stop_loss) * shares_safe, 2) if shares_safe > 0 else 0
                    },
                    'ideal': {
                        'price': round(ideal_entry, 2),
                        'description': 'Best entry point (recommended)',
                        'shares': shares_aggressive,
                        'risk': round(risk_per_share * shares_aggressive, 2) if shares_aggressive > 0 else 0
                    },
                    'safe': {
                        'price': round(safe_entry, 2),
                        'description': 'Wait for pullback to support',
                        'shares': int(account_risk / (safe_entry - stop_loss)) if (safe_entry - stop_loss) > 0 else 0,
                        'risk': account_risk
                    }
                },
                'stop_loss': {
                    'price': round(stop_loss, 2),
                    'distance_pct': round(((ideal_entry - stop_loss) / ideal_entry) * 100, 2),
                    'description': 'Stop loss below support'
                },
                'profit_targets': {
                    'target_1': {
                        'price': round(target_1, 2),
                        'profit_pct': round(target_1_pct, 2),
                        'profit_per_share': round(target_1 - ideal_entry, 2),
                        'risk_reward': round(rr_target_1, 2),
                        'timeframe': '1-2 days (Quick Scalp)',
                        'position_exit': '25%'
                    },
                    'target_2': {
                        'price': round(target_2, 2),
                        'profit_pct': round(target_2_pct, 2),
                        'profit_per_share': round(target_2 - ideal_entry, 2),
                        'risk_reward': round(rr_target_2, 2),
                        'timeframe': '3-5 days (Swing)',
                        'position_exit': '50%'
                    },
                    'target_3': {
                        'price': round(target_3, 2),
                        'profit_pct': round(target_3_pct, 2),
                        'profit_per_share': round(target_3 - ideal_entry, 2),
                        'risk_reward': round(rr_target_3, 2),
                        'timeframe': '5+ days (Extended)',
                        'position_exit': '25%'
                    }
                },
                'risk_analysis': {
                    'risk_per_share': round(risk_per_share, 2),
                    'max_risk_pct': round((risk_per_share / ideal_entry) * 100, 2),
                    'recommended_position_size': shares_aggressive,
                    'total_risk_amount': round(risk_per_share * shares_aggressive, 2) if shares_aggressive > 0 else 0
                },
                'trading_strategy': {
                    'holding_period': '1-5 days',
                    'style': 'Swing Trading',
                    'entry_strategy': 'Scale in: 50% at ideal, 30% at safe, 20% at aggressive',
                    'exit_strategy': 'Scale out: 25% at Target 1, 50% at Target 2, 25% at Target 3'
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating bullish plan: {e}")
            return {'error': str(e)}
    
    def _generate_bearish_plan(self, current_price: float, support: float,
                              resistance: float, atr: float, technical_signals: Dict) -> Dict:
        """Generate bearish swing trading plan (for short positions)"""
        try:
            # Entry levels for short
            aggressive_entry = current_price * 1.002  # Slightly above current
            safe_entry = min(resistance * 1.005, current_price * 1.03)
            ideal_entry = (aggressive_entry + safe_entry) / 2
            
            # Stop loss (above resistance)
            stop_loss = resistance + (atr * 0.5)
            if stop_loss <= resistance * 1.02:
                stop_loss = resistance * 1.03
            
            # Risk per share
            risk_per_share = stop_loss - ideal_entry
            if risk_per_share <= 0:
                risk_per_share = current_price * 0.02
            
            # Profit targets (downward)
            target_1 = ideal_entry - (risk_per_share * 1.5)
            target_2 = max(support, ideal_entry - (risk_per_share * 2.5))
            target_3 = max(support * 0.98, ideal_entry - (risk_per_share * 4.0))
            
            account_risk = 200
            shares = int(account_risk / risk_per_share) if risk_per_share > 0 else 0
            
            # Calculate profit percentages and R:R
            target_1_pct = ((ideal_entry - target_1) / ideal_entry) * 100
            target_2_pct = ((ideal_entry - target_2) / ideal_entry) * 100
            target_3_pct = ((ideal_entry - target_3) / ideal_entry) * 100
            
            rr_target_1 = (ideal_entry - target_1) / risk_per_share if risk_per_share > 0 else 0
            rr_target_2 = (ideal_entry - target_2) / risk_per_share if risk_per_share > 0 else 0
            rr_target_3 = (ideal_entry - target_3) / risk_per_share if risk_per_share > 0 else 0
            
            return {
                'direction': 'BEARISH',
                'recommendation': 'SHORT',
                'current_price': round(current_price, 2),
                'entry_levels': {
                    'aggressive': {
                        'price': round(aggressive_entry, 2),
                        'description': 'Enter now or on small bounce',
                        'shares': shares,
                        'risk': round(risk_per_share * shares, 2) if shares > 0 else 0
                    },
                    'ideal': {
                        'price': round(ideal_entry, 2),
                        'description': 'Best entry point (recommended)',
                        'shares': shares,
                        'risk': round(risk_per_share * shares, 2) if shares > 0 else 0
                    },
                    'safe': {
                        'price': round(safe_entry, 2),
                        'description': 'Wait for bounce to resistance',
                        'shares': int(account_risk / (stop_loss - safe_entry)) if (stop_loss - safe_entry) > 0 else 0,
                        'risk': account_risk
                    }
                },
                'stop_loss': {
                    'price': round(stop_loss, 2),
                    'distance_pct': round(((stop_loss - ideal_entry) / ideal_entry) * 100, 2),
                    'description': 'Stop loss above resistance'
                },
                'profit_targets': {
                    'target_1': {
                        'price': round(target_1, 2),
                        'profit_pct': round(target_1_pct, 2),
                        'profit_per_share': round(ideal_entry - target_1, 2),
                        'risk_reward': round(rr_target_1, 2),
                        'timeframe': '1-2 days (Quick Scalp)',
                        'position_exit': '25%'
                    },
                    'target_2': {
                        'price': round(target_2, 2),
                        'profit_pct': round(target_2_pct, 2),
                        'profit_per_share': round(ideal_entry - target_2, 2),
                        'risk_reward': round(rr_target_2, 2),
                        'timeframe': '3-5 days (Swing)',
                        'position_exit': '50%'
                    },
                    'target_3': {
                        'price': round(target_3, 2),
                        'profit_pct': round(target_3_pct, 2),
                        'profit_per_share': round(ideal_entry - target_3, 2),
                        'risk_reward': round(rr_target_3, 2),
                        'timeframe': '5+ days (Extended)',
                        'position_exit': '25%'
                    }
                },
                'risk_analysis': {
                    'risk_per_share': round(risk_per_share, 2),
                    'max_risk_pct': round((risk_per_share / ideal_entry) * 100, 2),
                    'recommended_position_size': shares,
                    'total_risk_amount': round(risk_per_share * shares, 2) if shares > 0 else 0
                },
                'trading_strategy': {
                    'holding_period': '1-5 days',
                    'style': 'Swing Trading (Short)',
                    'entry_strategy': 'Scale in: 50% at ideal, 30% at safe, 20% at aggressive',
                    'exit_strategy': 'Scale out: 25% at Target 1, 50% at Target 2, 25% at Target 3'
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating bearish plan: {e}")
            return {'error': str(e)}
    
    def _generate_neutral_plan(self, current_price: float, support: float,
                              resistance: float, atr: float) -> Dict:
        """Generate neutral/range trading plan"""
        return {
            'direction': 'NEUTRAL',
            'recommendation': 'HOLD / RANGE TRADE',
            'current_price': round(current_price, 2),
            'range': {
                'support': round(support, 2),
                'resistance': round(resistance, 2),
                'range_pct': round(((resistance - support) / current_price) * 100, 2)
            },
            'strategy': 'Trade the range: Buy near support, sell near resistance',
            'entry_levels': {
                'buy_zone': {
                    'price': round(support * 1.01, 2),
                    'description': 'Buy near support level'
                },
                'sell_zone': {
                    'price': round(resistance * 0.99, 2),
                    'description': 'Sell near resistance level'
                }
            },
            'stop_loss': {
                'price': round(support * 0.98, 2),
                'distance_pct': round(((support * 1.01 - support * 0.98) / (support * 1.01)) * 100, 2),
                'description': 'Stop loss below support'
            },
            'profit_targets': {
                'target_1': {
                    'price': round(resistance * 0.99, 2),
                    'profit_pct': round(((resistance * 0.99 - support * 1.01) / (support * 1.01)) * 100, 2),
                    'timeframe': 'Range trade',
                    'position_exit': '100%'
                }
            },
            'risk_analysis': {
                'risk_per_share': round((support * 1.01 - support * 0.98), 2),
                'max_risk_pct': round(((support * 1.01 - support * 0.98) / (support * 1.01)) * 100, 2),
                'recommended_position_size': 0,
                'total_risk_amount': 0
            },
            'trading_strategy': {
                'holding_period': '1-3 days',
                'style': 'Range Trading',
                'entry_strategy': 'Buy near support, sell near resistance',
                'exit_strategy': 'Take profit at resistance, stop loss below support'
            }
        }
    
    def get_intraday_levels(self, current_price: float, support: float, 
                           resistance: float, atr: float) -> Dict:
        """Get intraday trading levels (for same-day traders)"""
        try:
            # Intraday entry (tighter levels)
            entry_long = current_price * 0.9995  # Very tight
            entry_short = current_price * 1.0005
            
            # Intraday stop loss (tighter)
            stop_long = current_price - (atr * 0.3)
            stop_short = current_price + (atr * 0.3)
            
            # Quick targets
            target_long_1 = current_price + (atr * 0.5)
            target_long_2 = current_price + (atr * 1.0)
            
            target_short_1 = current_price - (atr * 0.5)
            target_short_2 = current_price - (atr * 1.0)
            
            return {
                'intraday_long': {
                    'entry': round(entry_long, 2),
                    'stop_loss': round(stop_long, 2),
                    'target_1': round(target_long_1, 2),
                    'target_2': round(target_long_2, 2)
                },
                'intraday_short': {
                    'entry': round(entry_short, 2),
                    'stop_loss': round(stop_short, 2),
                    'target_1': round(target_short_1, 2),
                    'target_2': round(target_short_2, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error getting intraday levels: {e}")
            return {}
