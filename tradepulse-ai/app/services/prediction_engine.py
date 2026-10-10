"""
Prediction Engine Module
Provides price predictions using statistical and ML methods with robust error handling
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
import warnings

warnings.filterwarnings('ignore')

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
except ImportError as e:
    logging.error(f"Failed to import sklearn: {e}")
    raise

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Generates price predictions for stocks"""
    
    def predict_price(self, data: pd.DataFrame, days_ahead: int = 5) -> Dict:
        """Predict future prices using linear regression"""
        if data.empty or len(data) < 30:
            return {'error': 'Insufficient data for prediction (need at least 30 days)'}
        
        if days_ahead < 1 or days_ahead > 30:
            return {'error': 'days_ahead must be between 1 and 30'}
        
        try:
            # Prepare data
            df = data.copy()
            
            # Ensure we have Close column
            if 'Close' not in df.columns:
                return {'error': 'Missing Close price data'}
            
            df = df[['Close']].copy()
            df['Date'] = df.index
            
            # Create features
            df['Days'] = (df['Date'] - df['Date'].min()).dt.days
            df = df.sort_values('Days')
            
            # Use last 60 days for training (or all if less than 60)
            train_size = min(60, len(df))
            train_data = df.tail(train_size).copy()
            
            if len(train_data) < 10:
                return {'error': 'Insufficient historical data for training (need at least 10 days)'}
            
            X = train_data[['Days']].values
            y = train_data['Close'].values
            
            # Validate data
            if np.any(np.isnan(X)) or np.any(np.isnan(y)):
                return {'error': 'Invalid data: contains NaN values'}
            
            if np.any(np.isinf(X)) or np.any(np.isinf(y)):
                return {'error': 'Invalid data: contains infinite values'}
            
            # Train model
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict future days
            last_day = train_data['Days'].max()
            future_days = np.array([[last_day + i] for i in range(1, days_ahead + 1)])
            predictions = model.predict(future_days)
            
            # Ensure predictions are positive
            predictions = np.maximum(predictions, 0.01)
            
            # Calculate confidence based on R-squared
            score = model.score(X, y)
            confidence = max(50, min(95, score * 100))
            
            # Get current price
            current_price = float(df['Close'].iloc[-1])
            
            if current_price <= 0:
                return {'error': 'Invalid current price'}
            
            # Calculate price change predictions
            price_changes = []
            for i, pred in enumerate(predictions):
                change = pred - current_price
                change_pct = (change / current_price * 100) if current_price > 0 else 0
                price_changes.append({
                    'day': i + 1,
                    'predicted_price': round(float(pred), 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2)
                })
            
            # Overall prediction
            avg_prediction = float(np.mean(predictions))
            overall_change = avg_prediction - current_price
            overall_change_pct = (overall_change / current_price * 100) if current_price > 0 else 0
            
            return {
                'current_price': round(current_price, 2),
                'predictions': price_changes,
                'average_prediction': round(avg_prediction, 2),
                'overall_change': round(overall_change, 2),
                'overall_change_pct': round(overall_change_pct, 2),
                'confidence': round(confidence, 1),
                'days_ahead': days_ahead,
                'trend': 'BULLISH' if overall_change > 0 else 'BEARISH' if overall_change < 0 else 'NEUTRAL'
            }
            
        except Exception as e:
            logger.error(f"Error in price prediction: {e}")
            return {'error': f'Prediction error: {str(e)}'}
    
    def predict_support_resistance(self, data: pd.DataFrame) -> Dict:
        """Predict support and resistance levels"""
        if data.empty:
            return {'error': 'No data available'}
        
        try:
            # Validate required columns
            if 'High' not in data.columns or 'Low' not in data.columns or 'Close' not in data.columns:
                return {'error': 'Missing required price columns (High, Low, Close)'}
            
            # Use recent data (last 60 days or all if less)
            recent_data = data.tail(60)
            
            if len(recent_data) < 10:
                return {'error': 'Insufficient data for support/resistance calculation'}
            
            # Calculate support (recent lows)
            support_levels = []
            window_size = min(5, len(recent_data) // 4)
            
            for i in range(window_size, len(recent_data) - window_size):
                window = recent_data.iloc[i-window_size:i+window_size]
                if recent_data.iloc[i]['Low'] == window['Low'].min():
                    support_levels.append(float(recent_data.iloc[i]['Low']))
            
            # Calculate resistance (recent highs)
            resistance_levels = []
            for i in range(window_size, len(recent_data) - window_size):
                window = recent_data.iloc[i-window_size:i+window_size]
                if recent_data.iloc[i]['High'] == window['High'].max():
                    resistance_levels.append(float(recent_data.iloc[i]['High']))
            
            current_price = float(data['Close'].iloc[-1])
            
            if current_price <= 0:
                return {'error': 'Invalid current price'}
            
            # Find nearest support and resistance
            valid_support = [s for s in support_levels if 0 < s < current_price]
            valid_resistance = [r for r in resistance_levels if r > current_price]
            
            support = max(valid_support, default=current_price * 0.95) if valid_support else current_price * 0.95
            resistance = min(valid_resistance, default=current_price * 1.05) if valid_resistance else current_price * 1.05
            
            # Ensure support < current < resistance
            if support >= current_price:
                support = current_price * 0.95
            if resistance <= current_price:
                resistance = current_price * 1.05
            
            return {
                'current_price': round(current_price, 2),
                'support': round(support, 2),
                'resistance': round(resistance, 2),
                'support_distance': round(((current_price - support) / current_price * 100), 2),
                'resistance_distance': round(((resistance - current_price) / current_price * 100), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {'error': f'Support/Resistance calculation error: {str(e)}'}
