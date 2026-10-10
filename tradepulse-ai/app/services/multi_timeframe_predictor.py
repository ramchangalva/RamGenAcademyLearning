"""
Multi-Timeframe Prediction Engine
Predicts stock prices for 1M, 3M, 6M, 12M, 24M using fundamentals, technical analysis, and news
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

try:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
except ImportError as e:
    logging.error(f"Failed to import sklearn: {e}")
    raise

logger = logging.getLogger(__name__)


class MultiTimeframePredictor:
    """Predicts stock prices for multiple timeframes using ML and fundamental analysis"""
    
    def __init__(self):
        self.timeframes = {
            '1M': 30,      # 1 month = ~30 trading days
            '3M': 90,      # 3 months = ~90 trading days
            '6M': 180,     # 6 months = ~180 trading days
            '12M': 365,    # 12 months = ~365 trading days
            '24M': 730     # 24 months = ~730 trading days
        }
    
    def predict_multi_timeframe(self, 
                                historical_data: pd.DataFrame,
                                fundamental_data: Dict,
                                technical_signals: Dict,
                                news_sentiment: Dict,
                                current_price: float) -> Dict:
        """
        Predict prices for multiple timeframes
        
        Args:
            historical_data: Historical price data with indicators
            fundamental_data: Fundamental analysis data
            technical_signals: Technical analysis signals
            news_sentiment: News sentiment analysis
            current_price: Current stock price
        
        Returns:
            Dictionary with predictions for each timeframe
        """
        try:
            if historical_data.empty or len(historical_data) < 60:
                return {'error': 'Insufficient historical data (need at least 60 days)'}
            
            if current_price <= 0:
                return {'error': 'Invalid current price'}
            
            predictions = {}
            
            # Predict for each timeframe
            for timeframe, days in self.timeframes.items():
                pred = self._predict_timeframe(
                    historical_data,
                    fundamental_data,
                    technical_signals,
                    news_sentiment,
                    current_price,
                    days,
                    timeframe
                )
                predictions[timeframe] = pred
            
            # Calculate overall trend
            overall_trend = self._calculate_overall_trend(predictions, current_price)
            
            return {
                'current_price': round(current_price, 2),
                'predictions': predictions,
                'overall_trend': overall_trend,
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe prediction: {e}")
            return {'error': f'Prediction error: {str(e)}'}
    
    def _predict_timeframe(self,
                          historical_data: pd.DataFrame,
                          fundamental_data: Dict,
                          technical_signals: Dict,
                          news_sentiment: Dict,
                          current_price: float,
                          days_ahead: int,
                          timeframe: str) -> Dict:
        """Predict price for a specific timeframe"""
        try:
            # Method 1: Technical-based prediction (ML on historical patterns)
            technical_pred = self._technical_prediction(historical_data, days_ahead)
            
            # Method 2: Fundamental-based prediction
            fundamental_pred = self._fundamental_prediction(
                fundamental_data, current_price, days_ahead
            )
            
            # Method 3: News sentiment adjustment
            news_adjustment = self._news_adjustment(
                news_sentiment, current_price, days_ahead
            )
            
            # Combine predictions with weights
            weights = self._get_weights_for_timeframe(timeframe)
            
            # Calculate weighted prediction
            tech_weight = weights['technical']
            fund_weight = weights['fundamental']
            news_weight = weights['news']
            
            # Base prediction from technical analysis
            base_pred = technical_pred.get('predicted_price', current_price)
            
            # Adjust with fundamentals
            if fundamental_pred and 'predicted_price' in fundamental_pred:
                fund_price = fundamental_pred['predicted_price']
                # Blend technical and fundamental
                blended = (base_pred * tech_weight) + (fund_price * fund_weight)
            else:
                blended = base_pred
            
            # Apply news sentiment adjustment
            if news_adjustment:
                sentiment_multiplier = news_adjustment.get('multiplier', 1.0)
                final_pred = blended * sentiment_multiplier
            else:
                final_pred = blended
            
            # Ensure reasonable bounds (not more than 3x or less than 0.1x current price)
            final_pred = max(current_price * 0.1, min(current_price * 3.0, final_pred))
            
            # Calculate change
            change = final_pred - current_price
            change_pct = (change / current_price * 100) if current_price > 0 else 0
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                technical_pred, fundamental_pred, news_sentiment, timeframe
            )
            
            return {
                'timeframe': timeframe,
                'days_ahead': days_ahead,
                'predicted_price': round(final_pred, 2),
                'current_price': round(current_price, 2),
                'change': round(change, 2),
                'change_pct': round(change_pct, 2),
                'confidence': round(confidence, 1),
                'trend': 'BULLISH' if change > 0 else 'BEARISH' if change < 0 else 'NEUTRAL',
                'breakdown': {
                    'technical_pred': round(technical_pred.get('predicted_price', current_price), 2),
                    'fundamental_pred': round(fundamental_pred.get('predicted_price', current_price), 2) if fundamental_pred else None,
                    'news_adjustment_pct': round((news_adjustment.get('multiplier', 1.0) - 1.0) * 100, 2) if news_adjustment else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting {timeframe}: {e}")
            return {
                'timeframe': timeframe,
                'error': str(e),
                'predicted_price': current_price,
                'confidence': 50
            }
    
    def _technical_prediction(self, data: pd.DataFrame, days_ahead: int) -> Dict:
        """Predict using technical analysis and ML"""
        try:
            if len(data) < 30:
                return {'predicted_price': float(data['Close'].iloc[-1]), 'confidence': 50}
            
            # Prepare features
            df = data.copy()
            df = df[['Close', 'Volume']].copy()
            
            # Add technical indicators as features if available
            if 'RSI' in data.columns:
                df['RSI'] = data['RSI']
            if 'MACD' in data.columns:
                df['MACD'] = data['MACD']
            if 'EMA_20' in data.columns:
                df['EMA_20'] = data['EMA_20']
            if 'EMA_50' in data.columns:
                df['EMA_50'] = data['EMA_50']
            
            # Create time-based features
            df['Date'] = df.index
            df['Days'] = (df['Date'] - df['Date'].min()).dt.days
            
            # Calculate price momentum
            df['Price_Change'] = df['Close'].pct_change()
            df['Volume_Change'] = df['Volume'].pct_change()
            
            # Use last 252 days (1 year) for training
            train_data = df.tail(252).copy()
            train_data = train_data.dropna()
            
            if len(train_data) < 30:
                # Fallback to simple linear regression
                return self._simple_linear_prediction(data, days_ahead)
            
            # Prepare features and target
            feature_cols = ['Days', 'Close', 'Volume']
            if 'RSI' in train_data.columns:
                feature_cols.append('RSI')
            if 'MACD' in train_data.columns:
                feature_cols.append('MACD')
            if 'Price_Change' in train_data.columns:
                feature_cols.append('Price_Change')
            
            available_features = [col for col in feature_cols if col in train_data.columns]
            
            if len(available_features) < 2:
                return self._simple_linear_prediction(data, days_ahead)
            
            X = train_data[available_features].values
            y = train_data['Close'].values
            
            # Remove any NaN or Inf values
            mask = ~(np.isnan(X).any(axis=1) | np.isinf(X).any(axis=1) | np.isnan(y) | np.isinf(y))
            X = X[mask]
            y = y[mask]
            
            if len(X) < 20:
                return self._simple_linear_prediction(data, days_ahead)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model (using Ridge for regularization)
            model = Ridge(alpha=1.0)
            model.fit(X_scaled, y)
            
            # Predict
            last_features = train_data[available_features].iloc[-1:].values
            last_features_scaled = scaler.transform(last_features)
            
            # Extrapolate for future days
            last_day = train_data['Days'].iloc[-1]
            future_day = last_day + days_ahead
            
            # Create future feature vector
            future_features = last_features.copy()
            future_features[0, available_features.index('Days')] = future_day
            
            # Adjust other features based on trends
            if 'Price_Change' in available_features:
                avg_change = train_data['Price_Change'].tail(30).mean()
                future_features[0, available_features.index('Price_Change')] = avg_change
            
            future_features_scaled = scaler.transform(future_features)
            predicted_price = model.predict(future_features_scaled)[0]
            
            # Calculate confidence based on R-squared
            score = model.score(X_scaled, y)
            confidence = max(40, min(90, score * 100))
            
            return {
                'predicted_price': max(0.01, float(predicted_price)),
                'confidence': confidence,
                'method': 'ML_Ridge'
            }
            
        except Exception as e:
            logger.warning(f"ML prediction failed, using simple method: {e}")
            return self._simple_linear_prediction(data, days_ahead)
    
    def _simple_linear_prediction(self, data: pd.DataFrame, days_ahead: int) -> Dict:
        """Simple linear regression fallback"""
        try:
            df = data[['Close']].copy()
            df['Date'] = df.index
            df['Days'] = (df['Date'] - df['Date'].min()).dt.days
            
            train_data = df.tail(60).copy()
            X = train_data[['Days']].values
            y = train_data['Close'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            last_day = train_data['Days'].max()
            future_day = last_day + days_ahead
            predicted_price = model.predict([[future_day]])[0]
            
            score = model.score(X, y)
            confidence = max(30, min(70, score * 100))
            
            return {
                'predicted_price': max(0.01, float(predicted_price)),
                'confidence': confidence,
                'method': 'Linear'
            }
        except Exception as e:
            logger.error(f"Simple prediction failed: {e}")
            current_price = float(data['Close'].iloc[-1])
            return {
                'predicted_price': current_price,
                'confidence': 30,
                'method': 'Fallback'
            }
    
    def _fundamental_prediction(self, fundamental_data: Dict, current_price: float, days_ahead: int) -> Optional[Dict]:
        """Predict based on fundamental analysis"""
        try:
            if not fundamental_data or 'error' in fundamental_data:
                return None
            
            # Extract from nested structure
            valuation = fundamental_data.get('valuation', {})
            growth = fundamental_data.get('growth', {})
            profitability = fundamental_data.get('profitability', {})
            financial_health = fundamental_data.get('financial_health', {})
            
            # Get key fundamental metrics
            pe_ratio = valuation.get('pe_ratio')
            if pe_ratio == 'N/A' or not isinstance(pe_ratio, (int, float)):
                pe_ratio = None
            
            growth_rate = growth.get('revenue_growth', 0)
            if not isinstance(growth_rate, (int, float)):
                growth_rate = 0
            
            profit_margin = profitability.get('profit_margin', 0)
            if not isinstance(profit_margin, (int, float)):
                profit_margin = 0
            
            debt_equity = financial_health.get('debt_to_equity', 0)
            if debt_equity == 'N/A' or not isinstance(debt_equity, (int, float)):
                debt_equity = 0
            
            # Calculate fundamental score
            fundamental_score = 50  # Base score
            
            # Adjust based on P/E ratio (lower is better, but not too low)
            if pe_ratio:
                if 10 <= pe_ratio <= 25:
                    fundamental_score += 10
                elif pe_ratio > 30:
                    fundamental_score -= 10
            
            # Adjust based on growth
            if growth_rate > 0:
                fundamental_score += min(20, growth_rate / 5)
            elif growth_rate < -10:
                fundamental_score -= 10
            
            # Adjust based on profit margin
            if profit_margin > 0:
                fundamental_score += min(15, profit_margin / 2)
            
            # Adjust based on debt
            if debt_equity > 1.0:
                fundamental_score -= 10
            
            # Convert score to price prediction
            # Higher fundamental score = higher price prediction
            score_multiplier = 1 + ((fundamental_score - 50) / 100) * (days_ahead / 365)
            
            # For longer timeframes, fundamentals matter more
            if days_ahead > 180:
                score_multiplier = 1 + ((fundamental_score - 50) / 50) * (days_ahead / 365)
            
            predicted_price = current_price * score_multiplier
            
            return {
                'predicted_price': max(0.01, float(predicted_price)),
                'fundamental_score': fundamental_score,
                'method': 'Fundamental'
            }
            
        except Exception as e:
            logger.warning(f"Fundamental prediction failed: {e}")
            return None
    
    def _news_adjustment(self, news_sentiment: Dict, current_price: float, days_ahead: int) -> Optional[Dict]:
        """Adjust prediction based on news sentiment"""
        try:
            if not news_sentiment or 'sentiment_analysis' not in news_sentiment:
                return None
            
            sentiment_data = news_sentiment['sentiment_analysis']
            sentiment_score = sentiment_data.get('sentiment_score', 0)
            sentiment = sentiment_data.get('sentiment', 'NEUTRAL')
            
            # News impact decays over time (more impact on short-term)
            time_decay = max(0.1, 1.0 - (days_ahead / 365))
            
            # Convert sentiment score (-100 to +100) to multiplier
            # For 1M: full impact, for 24M: minimal impact
            sentiment_multiplier = 1.0 + (sentiment_score / 100) * 0.1 * time_decay
            
            # Clamp multiplier to reasonable range
            sentiment_multiplier = max(0.9, min(1.1, sentiment_multiplier))
            
            return {
                'multiplier': sentiment_multiplier,
                'sentiment_score': sentiment_score,
                'sentiment': sentiment,
                'time_decay': time_decay
            }
            
        except Exception as e:
            logger.warning(f"News adjustment failed: {e}")
            return None
    
    def _get_weights_for_timeframe(self, timeframe: str) -> Dict:
        """Get prediction weights based on timeframe"""
        # For shorter timeframes, technical analysis matters more
        # For longer timeframes, fundamentals matter more
        weights = {
            '1M': {'technical': 0.6, 'fundamental': 0.3, 'news': 0.1},
            '3M': {'technical': 0.5, 'fundamental': 0.4, 'news': 0.1},
            '6M': {'technical': 0.4, 'fundamental': 0.5, 'news': 0.1},
            '12M': {'technical': 0.3, 'fundamental': 0.6, 'news': 0.1},
            '24M': {'technical': 0.2, 'fundamental': 0.7, 'news': 0.1}
        }
        return weights.get(timeframe, {'technical': 0.4, 'fundamental': 0.5, 'news': 0.1})
    
    def _calculate_confidence(self, technical_pred: Dict, fundamental_pred: Optional[Dict],
                             news_sentiment: Dict, timeframe: str) -> float:
        """Calculate overall confidence for prediction"""
        try:
            confidences = []
            
            # Technical confidence
            if technical_pred and 'confidence' in technical_pred:
                tech_conf = technical_pred['confidence']
                # Weight decreases for longer timeframes
                weight = 0.6 if timeframe in ['1M', '3M'] else 0.4
                confidences.append(tech_conf * weight)
            
            # Fundamental confidence
            if fundamental_pred:
                # Fundamentals are more reliable for longer timeframes
                fund_conf = 70 if timeframe in ['12M', '24M'] else 60
                weight = 0.3 if timeframe in ['1M', '3M'] else 0.5
                confidences.append(fund_conf * weight)
            else:
                # Penalize if no fundamental data
                confidences.append(30 * 0.2)
            
            # News confidence (lower weight, less reliable)
            if news_sentiment and 'sentiment_analysis' in news_sentiment:
                news_count = news_sentiment['sentiment_analysis'].get('news_count', 0)
                news_conf = min(80, 50 + (news_count * 2))
                confidences.append(news_conf * 0.1)
            
            if confidences:
                total_confidence = sum(confidences)
                return max(30, min(95, total_confidence))
            else:
                return 50
                
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 50
    
    def _calculate_overall_trend(self, predictions: Dict, current_price: float) -> Dict:
        """Calculate overall trend across all timeframes"""
        try:
            bullish_count = 0
            bearish_count = 0
            total_change_pct = 0
            avg_confidence = 0
            
            for timeframe, pred in predictions.items():
                if 'error' not in pred:
                    if pred.get('trend') == 'BULLISH':
                        bullish_count += 1
                    elif pred.get('trend') == 'BEARISH':
                        bearish_count += 1
                    
                    total_change_pct += pred.get('change_pct', 0)
                    avg_confidence += pred.get('confidence', 50)
            
            if len(predictions) > 0:
                avg_confidence = avg_confidence / len(predictions)
                avg_change_pct = total_change_pct / len(predictions)
            else:
                avg_confidence = 50
                avg_change_pct = 0
            
            if bullish_count > bearish_count:
                overall_trend = 'BULLISH'
            elif bearish_count > bullish_count:
                overall_trend = 'BEARISH'
            else:
                overall_trend = 'NEUTRAL'
            
            return {
                'trend': overall_trend,
                'bullish_timeframes': bullish_count,
                'bearish_timeframes': bearish_count,
                'average_change_pct': round(avg_change_pct, 2),
                'average_confidence': round(avg_confidence, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall trend: {e}")
            return {
                'trend': 'NEUTRAL',
                'bullish_timeframes': 0,
                'bearish_timeframes': 0,
                'average_change_pct': 0,
                'average_confidence': 50
            }
