"""
Recommendation Engine Module
Provides Buy/Sell recommendations with detailed reasoning and robust error handling
"""
from typing import Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates trading recommendations with reasoning"""
    
    def __init__(self):
        from app.services.prediction_engine import PredictionEngine
        self.prediction_engine = PredictionEngine()
    
    def generate_recommendation(self, symbol: str, technical_data: pd.DataFrame, 
                                technical_signals: Dict, fundamental_data: Dict) -> Dict:
        """Generate comprehensive buy/sell recommendation"""
        
        try:
            # Validate inputs
            if technical_data.empty:
                return self._error_response(symbol, "No technical data available")
            
            if not technical_signals:
                return self._error_response(symbol, "No technical signals available")
            
            if not fundamental_data or 'error' in fundamental_data:
                logger.warning(f"Fundamental data error for {symbol}, using defaults")
                fundamental_data = self._default_fundamental_data()
            
            # Get predictions
            predictions = self.prediction_engine.predict_price(technical_data, days_ahead=5)
            support_resistance = self.prediction_engine.predict_support_resistance(technical_data)
            
            # Analyze technical signals
            technical_score = self._analyze_technical(technical_signals)
            
            # Analyze fundamentals
            fundamental_score = fundamental_data.get('fundamental_score', 50)
            fundamental_rating = fundamental_data.get('fundamental_rating', 'HOLD')
            
            # Analyze predictions
            prediction_score = self._analyze_predictions(predictions)
            
            # Calculate overall score (weighted)
            overall_score = (
                technical_score * 0.40 +  # 40% weight on technical
                fundamental_score * 0.35 +  # 35% weight on fundamentals
                prediction_score * 0.25     # 25% weight on predictions
            )
            
            # Determine recommendation
            recommendation, confidence = self._determine_recommendation(overall_score)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                recommendation, technical_signals, fundamental_data, 
                predictions, support_resistance, technical_score, 
                fundamental_score, prediction_score
            )
            
            # Risk assessment
            risk_level = self._assess_risk(technical_data, technical_signals, fundamental_data)
            
            # Entry/Exit levels
            entry_exit = self._calculate_entry_exit(
                technical_data, support_resistance, recommendation
            )
            
            return {
                'symbol': symbol.upper(),
                'recommendation': recommendation,
                'confidence': round(confidence, 1),
                'overall_score': round(overall_score, 1),
                'reasoning': reasoning,
                'risk_level': risk_level,
                'entry_exit': entry_exit,
                'breakdown': {
                    'technical_score': round(technical_score, 1),
                    'fundamental_score': round(fundamental_score, 1),
                    'prediction_score': round(prediction_score, 1)
                },
                'key_factors': self._extract_key_factors(
                    technical_signals, fundamental_data, predictions
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation for {symbol}: {e}")
            return self._error_response(symbol, str(e))
    
    def _error_response(self, symbol: str, error: str) -> Dict:
        """Generate error response"""
        return {
            'symbol': symbol.upper(),
            'recommendation': 'HOLD',
            'confidence': 0,
            'overall_score': 50,
            'reasoning': f'Error generating recommendation: {error}',
            'risk_level': {'level': 'UNKNOWN', 'score': 50, 'factors': []},
            'entry_exit': {},
            'breakdown': {'technical_score': 50, 'fundamental_score': 50, 'prediction_score': 50},
            'key_factors': [],
            'error': error
        }
    
    def _default_fundamental_data(self) -> Dict:
        """Return default fundamental data when actual data is unavailable"""
        return {
            'fundamental_score': 50,
            'fundamental_rating': 'HOLD'
        }
    
    def _analyze_technical(self, technical_signals: Dict) -> float:
        """Analyze technical signals and return score"""
        if not technical_signals or 'overall' not in technical_signals:
            return 50.0
        
        score = 50.0
        overall = technical_signals.get('overall', 'NEUTRAL')
        buy_signals = technical_signals.get('buy_signals', 0)
        sell_signals = technical_signals.get('sell_signals', 0)
        
        if overall == 'BULLISH':
            score = 60.0 + (buy_signals * 5.0)
        elif overall == 'BEARISH':
            score = 40.0 - (sell_signals * 5.0)
        
        # Adjust based on signal strength
        total_signals = buy_signals + sell_signals
        if total_signals > 0:
            signal_ratio = buy_signals / total_signals
            score = 50.0 + ((signal_ratio - 0.5) * 40.0)
        
        return max(0.0, min(100.0, score))
    
    def _analyze_predictions(self, predictions: Dict) -> float:
        """Analyze predictions and return score"""
        if 'error' in predictions:
            return 50.0
        
        score = 50.0
        trend = predictions.get('trend', 'NEUTRAL')
        overall_change_pct = predictions.get('overall_change_pct', 0)
        confidence = predictions.get('confidence', 50)
        
        if trend == 'BULLISH':
            score = 60.0 + min(20.0, overall_change_pct * 2.0)
        elif trend == 'BEARISH':
            score = 40.0 + max(-20.0, overall_change_pct * 2.0)
        
        # Adjust for confidence
        score = score * (confidence / 100.0) + 50.0 * (1 - confidence / 100.0)
        
        return max(0.0, min(100.0, score))
    
    def _determine_recommendation(self, overall_score: float) -> tuple:
        """Determine recommendation and confidence from overall score"""
        if overall_score >= 75:
            return ('STRONG_BUY', min(95, overall_score + 5))
        elif overall_score >= 60:
            return ('BUY', overall_score)
        elif overall_score >= 45:
            return ('HOLD', 50)
        elif overall_score >= 30:
            return ('SELL', 100 - overall_score)
        else:
            return ('STRONG_SELL', min(95, 100 - overall_score + 5))
    
    def _generate_reasoning(self, recommendation: str, technical_signals: Dict,
                           fundamental_data: Dict, predictions: Dict,
                           support_resistance: Dict, tech_score: float,
                           fund_score: float, pred_score: float) -> str:
        """Generate detailed reasoning for recommendation"""
        reasons = []
        
        # Technical Analysis Reasoning
        if tech_score >= 65:
            reasons.append(f"✅ Strong Technical Signals: Multiple bullish indicators suggest upward momentum. Technical score: {tech_score:.1f}/100")
        elif tech_score <= 35:
            reasons.append(f"⚠️ Weak Technical Signals: Bearish indicators dominate. Technical score: {tech_score:.1f}/100")
        else:
            reasons.append(f"➡️ Mixed Technical Signals: Neutral to slightly positive. Technical score: {tech_score:.1f}/100")
        
        # Fundamental Analysis Reasoning
        if fund_score >= 70:
            reasons.append(f"✅ Strong Fundamentals: Company shows healthy financial metrics. Fundamental score: {fund_score:.1f}/100")
        elif fund_score <= 30:
            reasons.append(f"⚠️ Weak Fundamentals: Financial metrics are concerning. Fundamental score: {fund_score:.1f}/100")
        else:
            reasons.append(f"➡️ Moderate Fundamentals: Mixed financial indicators. Fundamental score: {fund_score:.1f}/100")
        
        # Prediction Reasoning
        if 'error' not in predictions:
            trend = predictions.get('trend', 'NEUTRAL')
            change_pct = predictions.get('overall_change_pct', 0)
            if trend == 'BULLISH' and change_pct > 2:
                reasons.append(f"📈 Positive Price Prediction: Model predicts {change_pct:.1f}% increase over next 5 days")
            elif trend == 'BEARISH' and change_pct < -2:
                reasons.append(f"📉 Negative Price Prediction: Model predicts {change_pct:.1f}% decrease over next 5 days")
            else:
                reasons.append(f"➡️ Neutral Price Prediction: Model suggests minimal price movement")
        
        # Support/Resistance
        if 'error' not in support_resistance:
            current = support_resistance.get('current_price', 0)
            support = support_resistance.get('support', 0)
            resistance = support_resistance.get('resistance', 0)
            if current > 0:
                support_dist = ((current - support) / current * 100) if support > 0 else 0
                resistance_dist = ((resistance - current) / current * 100) if resistance > 0 else 0
                reasons.append(f"📊 Support: ${support:.2f} ({support_dist:.1f}% below), Resistance: ${resistance:.2f} ({resistance_dist:.1f}% above)")
        
        # Key Technical Indicators
        if technical_signals and 'signals' in technical_signals:
            buy_count = technical_signals.get('buy_signals', 0)
            sell_count = technical_signals.get('sell_signals', 0)
            if buy_count > sell_count:
                reasons.append(f"🔺 {buy_count} Buy signals vs {sell_count} Sell signals from technical indicators")
            elif sell_count > buy_count:
                reasons.append(f"🔻 {sell_count} Sell signals vs {buy_count} Buy signals from technical indicators")
        
        # Combine all reasons
        reasoning_text = "\n\n".join(reasons)
        
        # Add final recommendation summary
        recommendation_summaries = {
            'STRONG_BUY': "🎯 STRONG BUY RECOMMENDATION: All factors align positively. High confidence entry opportunity.",
            'BUY': "🎯 BUY RECOMMENDATION: Positive factors outweigh negatives. Good entry opportunity.",
            'HOLD': "🎯 HOLD RECOMMENDATION: Mixed signals suggest waiting for clearer direction.",
            'SELL': "🎯 SELL RECOMMENDATION: Negative factors suggest reducing position or exiting.",
            'STRONG_SELL': "🎯 STRONG SELL RECOMMENDATION: Multiple red flags. Consider exiting position."
        }
        
        reasoning_text += f"\n\n{recommendation_summaries.get(recommendation, '')}"
        
        return reasoning_text
    
    def _assess_risk(self, data: pd.DataFrame, technical_signals: Dict, 
                    fundamental_data: Dict) -> Dict:
        """Assess risk level"""
        risk_factors = []
        risk_score = 50  # Base risk
        
        try:
            # Volatility risk
            if not data.empty and 'Close' in data.columns:
                volatility = data['Close'].pct_change().std() * 100
                if volatility > 3:
                    risk_factors.append('High volatility')
                    risk_score += 15
                elif volatility < 1:
                    risk_factors.append('Low volatility')
                    risk_score -= 5
            
            # Technical risk
            if technical_signals and technical_signals.get('overall') == 'BEARISH':
                risk_factors.append('Bearish technical signals')
                risk_score += 10
            
            # Fundamental risk
            fund_score = fundamental_data.get('fundamental_score', 50)
            if fund_score < 40:
                risk_factors.append('Weak fundamentals')
                risk_score += 15
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'HIGH'
        elif risk_score >= 50:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'level': risk_level,
            'score': min(100, risk_score),
            'factors': risk_factors
        }
    
    def _calculate_entry_exit(self, data: pd.DataFrame, support_resistance: Dict,
                            recommendation: str) -> Dict:
        """Calculate entry and exit levels"""
        if data.empty or 'Close' not in data.columns:
            return {}
        
        try:
            current_price = float(data['Close'].iloc[-1])
            support = support_resistance.get('support', current_price * 0.95)
            resistance = support_resistance.get('resistance', current_price * 1.05)
            
            if recommendation in ['STRONG_BUY', 'BUY']:
                entry = max(support, current_price * 0.98)  # Slightly below current or at support
                stop_loss = support * 0.97  # Just below support
                take_profit_1 = current_price * 1.05  # 5% target
                take_profit_2 = resistance  # At resistance
            elif recommendation in ['STRONG_SELL', 'SELL']:
                entry = min(resistance, current_price * 1.02)  # Slightly above current or at resistance
                stop_loss = resistance * 1.03  # Just above resistance
                take_profit_1 = current_price * 0.95  # 5% target
                take_profit_2 = support  # At support
            else:  # HOLD
                entry = current_price
                stop_loss = support * 0.97
                take_profit_1 = resistance
                take_profit_2 = None
            
            risk_reward = 'N/A'
            if entry > stop_loss and take_profit_1:
                risk_reward = round((take_profit_1 - entry) / (entry - stop_loss), 2)
            
            return {
                'entry': round(entry, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit_1': round(take_profit_1, 2),
                'take_profit_2': round(take_profit_2, 2) if take_profit_2 else None,
                'risk_reward_ratio': risk_reward
            }
            
        except Exception as e:
            logger.error(f"Error calculating entry/exit: {e}")
            return {}
    
    def _extract_key_factors(self, technical_signals: Dict, 
                           fundamental_data: Dict, predictions: Dict) -> list:
        """Extract key factors influencing recommendation"""
        factors = []
        
        # Technical factors
        if technical_signals:
            overall = technical_signals.get('overall', 'NEUTRAL')
            if overall == 'BULLISH':
                factors.append('Strong bullish technical trend')
            elif overall == 'BEARISH':
                factors.append('Bearish technical trend')
        
        # Fundamental factors
        fund_rating = fundamental_data.get('fundamental_rating', 'HOLD')
        if fund_rating in ['STRONG_BUY', 'BUY']:
            factors.append('Strong fundamental metrics')
        elif fund_rating in ['STRONG_SELL', 'SELL']:
            factors.append('Weak fundamental metrics')
        
        # Prediction factors
        if 'error' not in predictions:
            trend = predictions.get('trend', 'NEUTRAL')
            if trend == 'BULLISH':
                factors.append('Positive price prediction')
            elif trend == 'BEARISH':
                factors.append('Negative price prediction')
        
        return factors
