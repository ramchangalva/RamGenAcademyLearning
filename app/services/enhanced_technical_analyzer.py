"""
Enhanced Technical Analysis Module
Provides indicators with plain English explanations
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from app.services.technical_analyzer import TechnicalAnalyzer
import logging

logger = logging.getLogger(__name__)


class EnhancedTechnicalAnalyzer(TechnicalAnalyzer):
    """Enhanced technical analyzer with plain English explanations"""
    
    def get_indicators_with_explanations(self) -> Dict:
        """Get all indicators with plain English explanations"""
        if self.data.empty:
            return {'indicators': [], 'explanations': []}
        
        try:
            latest = self.data.iloc[-1]
            indicators = []
            explanations = []
            
            # RSI Analysis
            if 'RSI' in self.data.columns and not pd.isna(latest['RSI']):
                rsi = latest['RSI']
                indicators.append({'name': 'RSI', 'value': round(rsi, 2)})
                
                if rsi > 70:
                    explanations.append({
                        'indicator': 'RSI',
                        'status': 'OVERSOLD',
                        'explanation': f'RSI at {rsi:.1f} indicates overbought conditions. Momentum is weakening and price may pull back soon.',
                        'action': 'Consider taking profits or waiting for a pullback'
                    })
                elif rsi < 30:
                    explanations.append({
                        'indicator': 'RSI',
                        'status': 'OVERSOLD',
                        'explanation': f'RSI at {rsi:.1f} shows oversold conditions. Selling pressure may be exhausted, potential bounce ahead.',
                        'action': 'Watch for bullish reversal signals'
                    })
                elif 30 <= rsi <= 70:
                    explanations.append({
                        'indicator': 'RSI',
                        'status': 'NEUTRAL',
                        'explanation': f'RSI at {rsi:.1f} is in neutral territory. Momentum is balanced with no extreme conditions.',
                        'action': 'Monitor for trend continuation or reversal'
                    })
            
            # MACD Analysis
            if all(col in self.data.columns for col in ['MACD', 'MACD_signal', 'MACD_diff']):
                if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_signal']):
                    macd = latest['MACD']
                    signal = latest['MACD_signal']
                    diff = latest['MACD_diff']
                    
                    indicators.append({
                        'name': 'MACD',
                        'value': round(macd, 2),
                        'signal': round(signal, 2),
                        'histogram': round(diff, 2)
                    })
                    
                    if macd > signal and diff > 0:
                        explanations.append({
                            'indicator': 'MACD',
                            'status': 'BULLISH',
                            'explanation': f'MACD ({macd:.2f}) is above signal line ({signal:.2f}) with positive histogram. Bullish momentum is strengthening.',
                            'action': 'Bullish trend confirmed - consider long positions'
                        })
                    elif macd < signal and diff < 0:
                        explanations.append({
                            'indicator': 'MACD',
                            'status': 'BEARISH',
                            'explanation': f'MACD ({macd:.2f}) is below signal line ({signal:.2f}) with negative histogram. Bearish momentum is building.',
                            'action': 'Bearish trend confirmed - consider short positions or exits'
                        })
                    else:
                        explanations.append({
                            'indicator': 'MACD',
                            'status': 'NEUTRAL',
                            'explanation': 'MACD and signal line are converging. Trend strength is weakening, potential reversal ahead.',
                            'action': 'Wait for clearer directional signal'
                        })
            
            # Moving Averages Analysis
            if all(col in self.data.columns for col in ['SMA_20', 'SMA_50', 'SMA_200']):
                sma20 = latest['SMA_20']
                sma50 = latest['SMA_50']
                sma200 = latest['SMA_200']
                price = latest['Close']
                
                if not pd.isna(sma20) and not pd.isna(sma50):
                    indicators.append({
                        'name': 'Moving Averages',
                        'SMA_20': round(sma20, 2),
                        'SMA_50': round(sma50, 2),
                        'SMA_200': round(sma200, 2) if not pd.isna(sma200) else None
                    })
                    
                    if price > sma20 > sma50:
                        explanations.append({
                            'indicator': 'Moving Averages',
                            'status': 'BULLISH',
                            'explanation': f'Price ({price:.2f}) is above all key moving averages (20, 50, 200). Strong uptrend with all timeframes aligned.',
                            'action': 'Bullish trend - consider long positions on pullbacks'
                        })
                    elif price < sma20 < sma50:
                        explanations.append({
                            'indicator': 'Moving Averages',
                            'status': 'BEARISH',
                            'explanation': f'Price ({price:.2f}) is below all key moving averages. Downtrend confirmed across multiple timeframes.',
                            'action': 'Bearish trend - avoid long positions or consider shorts'
                        })
                    else:
                        explanations.append({
                            'indicator': 'Moving Averages',
                            'status': 'MIXED',
                            'explanation': 'Moving averages are mixed. No clear trend direction - market is in consolidation.',
                            'action': 'Wait for breakout above or below key levels'
                        })
            
            # Bollinger Bands Analysis
            if all(col in self.data.columns for col in ['BB_high', 'BB_low', 'BB_mid']):
                if not pd.isna(latest['BB_high']) and not pd.isna(latest['BB_low']):
                    price = latest['Close']
                    bb_high = latest['BB_high']
                    bb_low = latest['BB_low']
                    bb_mid = latest['BB_mid']
                    
                    bb_width = ((bb_high - bb_low) / bb_mid) * 100 if bb_mid > 0 else 0
                    
                    indicators.append({
                        'name': 'Bollinger Bands',
                        'upper': round(bb_high, 2),
                        'middle': round(bb_mid, 2),
                        'lower': round(bb_low, 2),
                        'width': round(bb_width, 2)
                    })
                    
                    if price > bb_high:
                        explanations.append({
                            'indicator': 'Bollinger Bands',
                            'status': 'OVERBOUGHT',
                            'explanation': f'Price ({price:.2f}) is above upper Bollinger Band ({bb_high:.2f}). Volatility expansion suggests potential reversal or continuation.',
                            'action': 'High volatility - watch for reversal or strong breakout'
                        })
                    elif price < bb_low:
                        explanations.append({
                            'indicator': 'Bollinger Bands',
                            'status': 'OVERSOLD',
                            'explanation': f'Price ({price:.2f}) is below lower Bollinger Band ({bb_low:.2f}). Oversold conditions may lead to bounce.',
                            'action': 'Potential buying opportunity if other indicators confirm'
                        })
                    else:
                        explanations.append({
                            'indicator': 'Bollinger Bands',
                            'status': 'NORMAL',
                            'explanation': f'Price is within Bollinger Bands. Band width ({bb_width:.1f}%) indicates {"high" if bb_width > 5 else "low"} volatility.',
                            'action': 'Normal volatility - trend likely to continue'
                        })
            
            # VWAP Analysis
            if 'VWAP' in self.data.columns and not pd.isna(latest['VWAP']):
                vwap = latest['VWAP']
                price = latest['Close']
                
                indicators.append({'name': 'VWAP', 'value': round(vwap, 2)})
                
                if price > vwap:
                    explanations.append({
                        'indicator': 'VWAP',
                        'status': 'BULLISH',
                        'explanation': f'Price ({price:.2f}) is above VWAP ({vwap:.2f}). Institutional buying pressure is positive.',
                        'action': 'Bullish institutional sentiment'
                    })
                else:
                    explanations.append({
                        'indicator': 'VWAP',
                        'status': 'BEARISH',
                        'explanation': f'Price ({price:.2f}) is below VWAP ({vwap:.2f}). Institutional selling pressure is negative.',
                        'action': 'Bearish institutional sentiment'
                    })
            
            # Fibonacci Retracement (if we have recent swing)
            fib_levels = self._calculate_fibonacci_levels()
            if fib_levels:
                indicators.append({'name': 'Fibonacci', 'levels': fib_levels})
                explanations.append({
                    'indicator': 'Fibonacci',
                    'status': 'INFO',
                    'explanation': f'Key Fibonacci levels identified. Price is near {fib_levels.get("current_level", "unknown")} retracement level.',
                    'action': 'Watch for support/resistance at Fibonacci levels'
                })
            
            return {
                'indicators': indicators,
                'explanations': explanations,
                'summary': self._generate_summary(explanations)
            }
            
        except Exception as e:
            logger.error(f"Error getting indicators with explanations: {e}")
            return {'indicators': [], 'explanations': [], 'summary': 'Unable to generate analysis'}
    
    def _calculate_fibonacci_levels(self) -> Dict:
        """Calculate Fibonacci retracement levels"""
        try:
            if len(self.data) < 20:
                return {}
            
            recent_data = self.data.tail(60)
            swing_high = recent_data['High'].max()
            swing_low = recent_data['Low'].min()
            current_price = self.data['Close'].iloc[-1]
            
            diff = swing_high - swing_low
            if diff <= 0:
                return {}
            
            # Fibonacci levels
            fib_levels = {
                '0.0': swing_high,
                '0.236': swing_high - (diff * 0.236),
                '0.382': swing_high - (diff * 0.382),
                '0.5': swing_high - (diff * 0.5),
                '0.618': swing_high - (diff * 0.618),
                '0.786': swing_high - (diff * 0.786),
                '1.0': swing_low
            }
            
            # Find current level
            current_level = None
            for level, price in fib_levels.items():
                if abs(current_price - price) / current_price < 0.02:  # Within 2%
                    current_level = level
                    break
            
            return {
                'swing_high': round(swing_high, 2),
                'swing_low': round(swing_low, 2),
                'levels': {k: round(v, 2) for k, v in fib_levels.items()},
                'current_level': current_level,
                'current_price': round(current_price, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci levels: {e}")
            return {}
    
    def _generate_summary(self, explanations: List[Dict]) -> str:
        """Generate overall summary from explanations"""
        if not explanations:
            return "No technical analysis available"
        
        bullish_count = sum(1 for exp in explanations if exp.get('status') == 'BULLISH')
        bearish_count = sum(1 for exp in explanations if exp.get('status') == 'BEARISH')
        neutral_count = sum(1 for exp in explanations if exp.get('status') in ['NEUTRAL', 'MIXED'])
        
        if bullish_count > bearish_count:
            return f"Overall technical picture is BULLISH ({bullish_count} bullish signals vs {bearish_count} bearish). Multiple indicators suggest upward momentum."
        elif bearish_count > bullish_count:
            return f"Overall technical picture is BEARISH ({bearish_count} bearish signals vs {bullish_count} bullish). Multiple indicators suggest downward pressure."
        else:
            return f"Technical signals are MIXED ({bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral). Wait for clearer directional confirmation."
