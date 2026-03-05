"""
AI Buy/Sell Engine - Advanced Recommendation System
Combines technical indicators, market structure, trend strength, and volume behavior
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AIBuySellEngine:
    """Advanced AI-powered buy/sell recommendation engine"""
    
    def __init__(self):
        from app.services.technical_analyzer import TechnicalAnalyzer
        from app.services.fundamental_analyzer import FundamentalAnalyzer
        from app.services.prediction_engine import PredictionEngine
        
        self.technical_analyzer = TechnicalAnalyzer
        self.fundamental_analyzer = FundamentalAnalyzer
        self.prediction_engine = PredictionEngine()
    
    def generate_recommendation(self, symbol: str, historical_data: pd.DataFrame, 
                                technical_signals: Dict, fundamental_data: Dict,
                                market_structure: Dict = None) -> Dict:
        """
        Generate comprehensive AI buy/sell recommendation
        
        Returns:
            {
                'action': 'BUY' | 'SELL' | 'HOLD',
                'confidence': 0-100,
                'reasoning': str,
                'factors': {
                    'technical': float,
                    'fundamental': float,
                    'market_structure': float,
                    'volume': float,
                    'trend_strength': float
                }
            }
        """
        try:
            # Analyze market structure if not provided
            if market_structure is None:
                market_structure = self._analyze_market_structure(historical_data)
            
            # Analyze trend strength
            trend_strength = self._analyze_trend_strength(historical_data, technical_signals)
            
            # Analyze volume behavior
            volume_analysis = self._analyze_volume_behavior(historical_data)
            
            # Calculate weighted scores
            technical_score = self._score_technical(technical_signals)
            fundamental_score = self._score_fundamental(fundamental_data)
            structure_score = self._score_market_structure(market_structure)
            trend_score = trend_strength['score']
            volume_score = volume_analysis['score']
            
            # Weighted combination (can be adjusted)
            weights = {
                'technical': 0.30,
                'fundamental': 0.20,
                'market_structure': 0.20,
                'trend_strength': 0.15,
                'volume': 0.15
            }
            
            overall_score = (
                technical_score * weights['technical'] +
                fundamental_score * weights['fundamental'] +
                structure_score * weights['market_structure'] +
                trend_score * weights['trend_strength'] +
                volume_score * weights['volume']
            )
            
            # Determine action
            if overall_score >= 70:
                action = 'BUY'
                confidence = min(95, overall_score + 5)
            elif overall_score >= 55:
                action = 'BUY'
                confidence = overall_score
            elif overall_score >= 45:
                action = 'HOLD'
                confidence = 50
            elif overall_score >= 30:
                action = 'SELL'
                confidence = 100 - overall_score
            else:
                action = 'SELL'
                confidence = min(95, 100 - overall_score + 5)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                action, confidence, technical_score, fundamental_score,
                structure_score, trend_strength, volume_analysis, market_structure
            )
            
            return {
                'action': action,
                'confidence': round(confidence, 1),
                'overall_score': round(overall_score, 1),
                'reasoning': reasoning,
                'factors': {
                    'technical': round(technical_score, 1),
                    'fundamental': round(fundamental_score, 1),
                    'market_structure': round(structure_score, 1),
                    'trend_strength': round(trend_score, 1),
                    'volume': round(volume_score, 1)
                },
                'trend_strength': trend_strength,
                'volume_analysis': volume_analysis,
                'market_structure': market_structure
            }
            
        except Exception as e:
            logger.error(f"Error in AI Buy/Sell Engine: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': f'Error generating recommendation: {str(e)}',
                'factors': {}
            }
    
    def _analyze_market_structure(self, data: pd.DataFrame) -> Dict:
        """Analyze market structure (higher highs, higher lows, etc.)"""
        if data.empty or len(data) < 20:
            return {'structure': 'UNKNOWN', 'score': 50}
        
        try:
            # Identify swing highs and lows
            highs = data['High'].rolling(window=5, center=True).max()
            lows = data['Low'].rolling(window=5, center=True).min()
            
            recent_highs = highs.tail(20).values
            recent_lows = lows.tail(20).values
            
            # Check for higher highs and higher lows (bullish)
            higher_highs = sum(1 for i in range(1, len(recent_highs)) 
                              if recent_highs[i] > recent_highs[i-1])
            higher_lows = sum(1 for i in range(1, len(recent_lows)) 
                             if recent_lows[i] > recent_lows[i-1])
            
            # Check for lower highs and lower lows (bearish)
            lower_highs = sum(1 for i in range(1, len(recent_highs)) 
                             if recent_highs[i] < recent_highs[i-1])
            lower_lows = sum(1 for i in range(1, len(recent_lows)) 
                            if recent_lows[i] < recent_lows[i-1])
            
            bullish_signals = higher_highs + higher_lows
            bearish_signals = lower_highs + lower_lows
            
            if bullish_signals > bearish_signals * 1.5:
                structure = 'BULLISH'
                score = 60 + min(20, bullish_signals * 2)
            elif bearish_signals > bullish_signals * 1.5:
                structure = 'BEARISH'
                score = 40 - min(20, bearish_signals * 2)
            else:
                structure = 'NEUTRAL'
                score = 50
            
            return {
                'structure': structure,
                'score': max(0, min(100, score)),
                'higher_highs': higher_highs,
                'higher_lows': higher_lows,
                'lower_highs': lower_highs,
                'lower_lows': lower_lows
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market structure: {e}")
            return {'structure': 'UNKNOWN', 'score': 50}
    
    def _analyze_trend_strength(self, data: pd.DataFrame, technical_signals: Dict) -> Dict:
        """Analyze trend strength using multiple indicators"""
        try:
            score = 50
            strength = 'NEUTRAL'
            
            # ADX from technical signals
            if 'indicators' in technical_signals:
                adx = technical_signals['indicators'].get('ADX', 0)
                if adx > 25:
                    score += 20
                    strength = 'STRONG'
                elif adx > 20:
                    score += 10
                    strength = 'MODERATE'
                else:
                    strength = 'WEAK'
            
            # Moving average alignment
            if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
                latest = data.iloc[-1]
                if not pd.isna(latest['SMA_20']) and not pd.isna(latest['SMA_50']):
                    if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
                        score += 15
                    elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
                        score -= 15
            
            # Price momentum
            returns = data['Close'].pct_change().tail(10)
            positive_days = (returns > 0).sum()
            if positive_days >= 7:
                score += 10
            elif positive_days <= 3:
                score -= 10
            
            return {
                'strength': strength,
                'score': max(0, min(100, score)),
                'adx': technical_signals.get('indicators', {}).get('ADX', 0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend strength: {e}")
            return {'strength': 'UNKNOWN', 'score': 50}
    
    def _analyze_volume_behavior(self, data: pd.DataFrame) -> Dict:
        """Analyze volume patterns and behavior"""
        try:
            if 'Volume' not in data.columns:
                return {'pattern': 'UNKNOWN', 'score': 50}
            
            score = 50
            
            # Volume trend
            volume_ma = data['Volume'].rolling(window=20).mean()
            recent_volume = data['Volume'].tail(5).mean()
            avg_volume = volume_ma.iloc[-1]
            
            if recent_volume > avg_volume * 1.2:
                score += 15  # Above average volume
            elif recent_volume < avg_volume * 0.8:
                score -= 10  # Below average volume
            
            # Volume-price relationship
            price_change = data['Close'].pct_change().tail(5)
            volume_change = data['Volume'].pct_change().tail(5)
            
            # Positive correlation (price up + volume up = bullish)
            positive_correlation = ((price_change > 0) & (volume_change > 0)).sum()
            negative_correlation = ((price_change < 0) & (volume_change > 0)).sum()
            
            if positive_correlation > negative_correlation:
                score += 10
            elif negative_correlation > positive_correlation:
                score -= 10
            
            # Volume pattern
            if recent_volume > avg_volume * 1.5:
                pattern = 'HIGH_VOLUME'
            elif recent_volume < avg_volume * 0.7:
                pattern = 'LOW_VOLUME'
            else:
                pattern = 'NORMAL'
            
            return {
                'pattern': pattern,
                'score': max(0, min(100, score)),
                'recent_volume': recent_volume,
                'avg_volume': avg_volume,
                'volume_ratio': recent_volume / avg_volume if avg_volume > 0 else 1
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume behavior: {e}")
            return {'pattern': 'UNKNOWN', 'score': 50}
    
    def _score_technical(self, technical_signals: Dict) -> float:
        """Score technical analysis"""
        if not technical_signals:
            return 50.0
        
        score = 50.0
        overall = technical_signals.get('overall', 'NEUTRAL')
        buy_signals = technical_signals.get('buy_signals', 0)
        sell_signals = technical_signals.get('sell_signals', 0)
        
        if overall == 'BULLISH':
            score = 60.0 + (buy_signals * 5.0)
        elif overall == 'BEARISH':
            score = 40.0 - (sell_signals * 5.0)
        
        return max(0.0, min(100.0, score))
    
    def _score_fundamental(self, fundamental_data: Dict) -> float:
        """Score fundamental analysis"""
        if not fundamental_data or 'fundamental_score' not in fundamental_data:
            return 50.0
        
        return float(fundamental_data.get('fundamental_score', 50))
    
    def _score_market_structure(self, market_structure: Dict) -> float:
        """Score market structure"""
        return float(market_structure.get('score', 50))
    
    def _generate_reasoning(self, action: str, confidence: float, 
                           tech_score: float, fund_score: float,
                           structure_score: float, trend_strength: Dict,
                           volume_analysis: Dict, market_structure: Dict) -> str:
        """Generate plain English reasoning"""
        reasons = []
        
        # Action summary
        if action == 'BUY':
            reasons.append(f"✅ BUY Recommendation with {confidence:.0f}% confidence")
        elif action == 'SELL':
            reasons.append(f"❌ SELL Recommendation with {confidence:.0f}% confidence")
        else:
            reasons.append(f"⏸ HOLD Recommendation - Waiting for clearer signals")
        
        # Technical
        if tech_score >= 65:
            reasons.append(f"📈 Strong Technical Signals ({tech_score:.0f}/100) - Multiple bullish indicators")
        elif tech_score <= 35:
            reasons.append(f"📉 Weak Technical Signals ({tech_score:.0f}/100) - Bearish indicators dominate")
        
        # Fundamental
        if fund_score >= 70:
            reasons.append(f"💼 Strong Fundamentals ({fund_score:.0f}/100) - Healthy financial metrics")
        elif fund_score <= 30:
            reasons.append(f"⚠️ Weak Fundamentals ({fund_score:.0f}/100) - Concerning financial metrics")
        
        # Market Structure
        structure = market_structure.get('structure', 'NEUTRAL')
        if structure == 'BULLISH':
            reasons.append(f"📊 Bullish Market Structure - Higher highs and higher lows detected")
        elif structure == 'BEARISH':
            reasons.append(f"📊 Bearish Market Structure - Lower highs and lower lows detected")
        
        # Trend Strength
        trend = trend_strength.get('strength', 'NEUTRAL')
        if trend == 'STRONG':
            reasons.append(f"💪 Strong Trend - ADX indicates strong directional movement")
        elif trend == 'WEAK':
            reasons.append(f"🔻 Weak Trend - Lack of clear directional movement")
        
        # Volume
        volume_pattern = volume_analysis.get('pattern', 'NORMAL')
        volume_ratio = volume_analysis.get('volume_ratio', 1)
        if volume_pattern == 'HIGH_VOLUME' and volume_ratio > 1.5:
            reasons.append(f"📊 High Volume Activity - {volume_ratio:.1f}x average volume suggests strong interest")
        elif volume_pattern == 'LOW_VOLUME':
            reasons.append(f"📊 Low Volume - Reduced participation may indicate lack of conviction")
        
        return "\n\n".join(reasons)
