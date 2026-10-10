"""
Automatic Strategy Generator
Generates trading strategies based on current market analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AutoStrategyGenerator:
    """Automatically generates trading strategies based on analysis"""
    
    def __init__(self):
        pass
    
    def generate_strategy_from_analysis(self,
                                       symbol: str,
                                       technical_signals: Dict,
                                       fundamental_data: Dict,
                                       historical_data: pd.DataFrame,
                                       support_resistance: Dict,
                                       current_price: float,
                                       recommendation: str) -> Dict:
        """
        Generate automatic trading strategy based on analysis
        
        Returns:
            {
                'strategy_name': str,
                'strategy_type': str,  # 'Momentum', 'Mean Reversion', 'Breakout', 'Trend Following'
                'entry_conditions': List[Dict],
                'exit_conditions': List[Dict],
                'stop_loss': float,
                'take_profit': float,
                'risk_reward': float,
                'confidence': float,
                'description': str,
                'backtest_ready': bool
            }
        """
        try:
            # Analyze market conditions
            market_condition = self._analyze_market_condition(
                technical_signals, fundamental_data, historical_data
            )
            
            # Generate strategy based on condition
            if market_condition == 'MOMENTUM':
                return self._generate_momentum_strategy(
                    symbol, technical_signals, support_resistance, current_price, recommendation
                )
            elif market_condition == 'MEAN_REVERSION':
                return self._generate_mean_reversion_strategy(
                    symbol, technical_signals, support_resistance, current_price, recommendation
                )
            elif market_condition == 'BREAKOUT':
                return self._generate_breakout_strategy(
                    symbol, technical_signals, support_resistance, current_price, recommendation
                )
            else:  # TREND_FOLLOWING
                return self._generate_trend_following_strategy(
                    symbol, technical_signals, support_resistance, current_price, recommendation
                )
                
        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return {'error': str(e)}
    
    def _analyze_market_condition(self, technical_signals: Dict,
                                  fundamental_data: Dict,
                                  historical_data: pd.DataFrame) -> str:
        """Analyze current market condition"""
        try:
            # Check RSI
            rsi = None
            if 'indicators' in technical_signals:
                rsi = technical_signals['indicators'].get('RSI')
            
            # Check trend
            overall_signal = technical_signals.get('overall', 'NEUTRAL')
            
            # Check volatility
            if len(historical_data) >= 20:
                volatility = historical_data['Close'].pct_change().std() * 100
            else:
                volatility = 0
            
            # Determine market condition
            if rsi:
                if rsi < 30:
                    return 'MEAN_REVERSION'  # Oversold - mean reversion opportunity
                elif rsi > 70:
                    return 'MEAN_REVERSION'  # Overbought - mean reversion opportunity
                elif 40 <= rsi <= 60 and overall_signal == 'BULLISH':
                    return 'MOMENTUM'  # Neutral RSI with bullish trend
                elif volatility > 3:
                    return 'BREAKOUT'  # High volatility - breakout potential
                else:
                    return 'TREND_FOLLOWING'
            else:
                return 'TREND_FOLLOWING'
                
        except Exception as e:
            logger.error(f"Error analyzing market condition: {e}")
            return 'TREND_FOLLOWING'
    
    def _generate_momentum_strategy(self, symbol: str, technical_signals: Dict,
                                   support_resistance: Dict, current_price: float,
                                   recommendation: str) -> Dict:
        """Generate momentum trading strategy"""
        try:
            entry_conditions = []
            exit_conditions = []
            
            # Entry conditions
            if recommendation in ['BUY', 'STRONG_BUY']:
                entry_conditions = [
                    {
                        'indicator': 'RSI',
                        'operator': '>',
                        'value': 50,
                        'description': 'RSI above 50 (bullish momentum)'
                    },
                    {
                        'indicator': 'MACD',
                        'operator': '>',
                        'value': 0,
                        'description': 'MACD positive (bullish crossover)'
                    },
                    {
                        'indicator': 'Price',
                        'operator': '>',
                        'value': support_resistance.get('support', current_price * 0.95),
                        'description': 'Price above support level'
                    }
                ]
                
                stop_loss = support_resistance.get('support', current_price * 0.95)
                take_profit = support_resistance.get('resistance', current_price * 1.10)
            else:
                entry_conditions = [
                    {
                        'indicator': 'RSI',
                        'operator': '<',
                        'value': 50,
                        'description': 'RSI below 50 (bearish momentum)'
                    },
                    {
                        'indicator': 'MACD',
                        'operator': '<',
                        'value': 0,
                        'description': 'MACD negative (bearish crossover)'
                    }
                ]
                stop_loss = support_resistance.get('resistance', current_price * 1.05)
                take_profit = support_resistance.get('support', current_price * 0.90)
            
            # Exit conditions
            exit_conditions = [
                {
                    'indicator': 'Price',
                    'operator': '>=',
                    'value': take_profit,
                    'description': 'Take profit target reached'
                },
                {
                    'indicator': 'RSI',
                    'operator': '>',
                    'value': 70 if recommendation in ['BUY', 'STRONG_BUY'] else 30,
                    'description': 'RSI extreme (overbought/oversold)'
                }
            ]
            
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            return {
                'strategy_name': f'{symbol} Momentum Strategy',
                'strategy_type': 'Momentum',
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'risk_reward': round(risk_reward, 2),
                'confidence': 75.0,
                'description': 'Momentum strategy: Enter when price shows strong directional movement with RSI and MACD confirmation. Exit at profit target or RSI extreme.',
                'backtest_ready': True,
                'holding_period': '1-3 days',
                'risk_level': 'Medium'
            }
            
        except Exception as e:
            logger.error(f"Error generating momentum strategy: {e}")
            return {'error': str(e)}
    
    def _generate_mean_reversion_strategy(self, symbol: str, technical_signals: Dict,
                                         support_resistance: Dict, current_price: float,
                                         recommendation: str) -> Dict:
        """Generate mean reversion strategy"""
        try:
            rsi = technical_signals.get('indicators', {}).get('RSI', 50)
            
            if rsi < 30:
                # Oversold - buy opportunity
                entry_conditions = [
                    {
                        'indicator': 'RSI',
                        'operator': '<',
                        'value': 30,
                        'description': 'RSI oversold (< 30)'
                    },
                    {
                        'indicator': 'Price',
                        'operator': '<=',
                        'value': support_resistance.get('support', current_price * 0.95),
                        'description': 'Price at or near support'
                    }
                ]
                stop_loss = support_resistance.get('support', current_price * 0.95) * 0.98
                take_profit = current_price * 1.05
            else:
                # Overbought - sell opportunity
                entry_conditions = [
                    {
                        'indicator': 'RSI',
                        'operator': '>',
                        'value': 70,
                        'description': 'RSI overbought (> 70)'
                    },
                    {
                        'indicator': 'Price',
                        'operator': '>=',
                        'value': support_resistance.get('resistance', current_price * 1.05),
                        'description': 'Price at or near resistance'
                    }
                ]
                stop_loss = support_resistance.get('resistance', current_price * 1.05) * 1.02
                take_profit = current_price * 0.95
            
            exit_conditions = [
                {
                    'indicator': 'RSI',
                    'operator': '==',
                    'value': 50,
                    'description': 'RSI returns to neutral (50)'
                },
                {
                    'indicator': 'Price',
                    'operator': '>=',
                    'value': take_profit if rsi < 30 else take_profit,
                    'description': 'Mean reversion target reached'
                }
            ]
            
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            return {
                'strategy_name': f'{symbol} Mean Reversion Strategy',
                'strategy_type': 'Mean Reversion',
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'risk_reward': round(risk_reward, 2),
                'confidence': 70.0,
                'description': 'Mean reversion strategy: Enter when RSI reaches extreme levels (oversold/overbought) and price is at support/resistance. Exit when price returns to mean.',
                'backtest_ready': True,
                'holding_period': '1-5 days',
                'risk_level': 'Medium-High'
            }
            
        except Exception as e:
            logger.error(f"Error generating mean reversion strategy: {e}")
            return {'error': str(e)}
    
    def _generate_breakout_strategy(self, symbol: str, technical_signals: Dict,
                                   support_resistance: Dict, current_price: float,
                                   recommendation: str) -> Dict:
        """Generate breakout strategy"""
        try:
            resistance = support_resistance.get('resistance', current_price * 1.05)
            
            entry_conditions = [
                {
                    'indicator': 'Price',
                    'operator': '>',
                    'value': resistance,
                    'description': f'Price breaks above resistance (${resistance:.2f})'
                },
                {
                    'indicator': 'Volume',
                    'operator': '>',
                    'value': 'average',
                    'description': 'Volume above average (confirmation)'
                }
            ]
            
            stop_loss = resistance * 0.98  # Just below breakout level
            take_profit = resistance * 1.10  # 10% above breakout
            
            exit_conditions = [
                {
                    'indicator': 'Price',
                    'operator': '>=',
                    'value': take_profit,
                    'description': 'Breakout target reached'
                },
                {
                    'indicator': 'Price',
                    'operator': '<',
                    'value': stop_loss,
                    'description': 'Breakout fails - stop loss'
                }
            ]
            
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            return {
                'strategy_name': f'{symbol} Breakout Strategy',
                'strategy_type': 'Breakout',
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'risk_reward': round(risk_reward, 2),
                'confidence': 65.0,
                'description': 'Breakout strategy: Enter when price breaks above resistance with volume confirmation. Exit at target or if breakout fails.',
                'backtest_ready': True,
                'holding_period': '3-7 days',
                'risk_level': 'High'
            }
            
        except Exception as e:
            logger.error(f"Error generating breakout strategy: {e}")
            return {'error': str(e)}
    
    def _generate_trend_following_strategy(self, symbol: str, technical_signals: Dict,
                                          support_resistance: Dict, current_price: float,
                                          recommendation: str) -> Dict:
        """Generate trend following strategy"""
        try:
            if recommendation in ['BUY', 'STRONG_BUY']:
                entry_conditions = [
                    {
                        'indicator': 'EMA_20',
                        'operator': '>',
                        'value': 'EMA_50',
                        'description': 'EMA 20 > EMA 50 (uptrend)'
                    },
                    {
                        'indicator': 'Price',
                        'operator': '>',
                        'value': 'EMA_20',
                        'description': 'Price above EMA 20'
                    },
                    {
                        'indicator': 'ADX',
                        'operator': '>',
                        'value': 25,
                        'description': 'ADX > 25 (strong trend)'
                    }
                ]
                stop_loss = support_resistance.get('support', current_price * 0.95)
                take_profit = support_resistance.get('resistance', current_price * 1.15)
            else:
                entry_conditions = [
                    {
                        'indicator': 'EMA_20',
                        'operator': '<',
                        'value': 'EMA_50',
                        'description': 'EMA 20 < EMA 50 (downtrend)'
                    },
                    {
                        'indicator': 'Price',
                        'operator': '<',
                        'value': 'EMA_20',
                        'description': 'Price below EMA 20'
                    }
                ]
                stop_loss = support_resistance.get('resistance', current_price * 1.05)
                take_profit = support_resistance.get('support', current_price * 0.85)
            
            exit_conditions = [
                {
                    'indicator': 'EMA_20',
                    'operator': 'cross',
                    'value': 'EMA_50',
                    'description': 'EMA crossover (trend reversal)'
                },
                {
                    'indicator': 'Price',
                    'operator': '>=',
                    'value': take_profit,
                    'description': 'Trend target reached'
                }
            ]
            
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            return {
                'strategy_name': f'{symbol} Trend Following Strategy',
                'strategy_type': 'Trend Following',
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'risk_reward': round(risk_reward, 2),
                'confidence': 80.0,
                'description': 'Trend following strategy: Enter when price and EMAs align in trend direction. Exit on trend reversal or target reached.',
                'backtest_ready': True,
                'holding_period': '5-20 days',
                'risk_level': 'Low-Medium'
            }
            
        except Exception as e:
            logger.error(f"Error generating trend following strategy: {e}")
            return {'error': str(e)}
    
    def generate_multiple_strategies(self, symbol: str, technical_signals: Dict,
                                    fundamental_data: Dict, historical_data: pd.DataFrame,
                                    support_resistance: Dict, current_price: float,
                                    recommendation: str) -> List[Dict]:
        """Generate multiple strategy options"""
        try:
            strategies = []
            
            # Generate all strategy types
            strategies.append(self._generate_momentum_strategy(
                symbol, technical_signals, support_resistance, current_price, recommendation
            ))
            strategies.append(self._generate_mean_reversion_strategy(
                symbol, technical_signals, support_resistance, current_price, recommendation
            ))
            strategies.append(self._generate_breakout_strategy(
                symbol, technical_signals, support_resistance, current_price, recommendation
            ))
            strategies.append(self._generate_trend_following_strategy(
                symbol, technical_signals, support_resistance, current_price, recommendation
            ))
            
            # Filter out errors and sort by confidence
            valid_strategies = [s for s in strategies if 'error' not in s]
            valid_strategies.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            return valid_strategies
            
        except Exception as e:
            logger.error(f"Error generating multiple strategies: {e}")
            return []
