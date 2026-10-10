"""
Technical Analysis Module
Performs comprehensive technical analysis on stock data with robust error handling
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

try:
    from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
    from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
    from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel
    from ta.volume import VolumeWeightedAveragePrice, OnBalanceVolumeIndicator
except ImportError as e:
    logging.error(f"Failed to import ta library: {e}")
    raise

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Performs technical analysis on stock data"""
    
    def __init__(self, data: pd.DataFrame):
        if data.empty:
            logger.warning("Empty dataframe provided to TechnicalAnalyzer")
            self.data = pd.DataFrame()
            return
        
        self.data = data.copy()
        if len(data) > 1:
            self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate all technical indicators with error handling"""
        if self.data.empty or len(self.data) < 20:
            logger.warning("Insufficient data for technical indicators (need at least 20 rows)")
            return
        
        try:
            # Ensure proper column names
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in self.data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            close = self.data['Close']
            high = self.data['High']
            low = self.data['Low']
            open_price = self.data['Open']
            volume = self.data['Volume']
            
            # Moving Averages
            if len(self.data) >= 20:
                self.data['SMA_20'] = SMAIndicator(close=close, window=20).sma_indicator()
            if len(self.data) >= 50:
                self.data['SMA_50'] = SMAIndicator(close=close, window=50).sma_indicator()
            if len(self.data) >= 200:
                self.data['SMA_200'] = SMAIndicator(close=close, window=200).sma_indicator()
            
            # Exponential Moving Averages
            if len(self.data) >= 20:
                self.data['EMA_20'] = EMAIndicator(close=close, window=20).ema_indicator()
            if len(self.data) >= 12:
                self.data['EMA_12'] = EMAIndicator(close=close, window=12).ema_indicator()
            if len(self.data) >= 26:
                self.data['EMA_26'] = EMAIndicator(close=close, window=26).ema_indicator()
            if len(self.data) >= 50:
                self.data['EMA_50'] = EMAIndicator(close=close, window=50).ema_indicator()
            if len(self.data) >= 200:
                self.data['EMA_200'] = EMAIndicator(close=close, window=200).ema_indicator()
            
            # MACD
            if len(self.data) >= 26:
                macd = MACD(close=close)
                self.data['MACD'] = macd.macd()
                self.data['MACD_signal'] = macd.macd_signal()
                self.data['MACD_diff'] = macd.macd_diff()
            
            # RSI
            if len(self.data) >= 14:
                self.data['RSI'] = RSIIndicator(close=close, window=14).rsi()
            
            # Stochastic Oscillator
            if len(self.data) >= 14:
                stoch = StochasticOscillator(high=high, low=low, close=close, window=14)
                self.data['Stoch_K'] = stoch.stoch()
                self.data['Stoch_D'] = stoch.stoch_signal()
            
            # Williams %R
            if len(self.data) >= 14:
                self.data['Williams_R'] = WilliamsRIndicator(high=high, low=low, close=close).williams_r()
            
            # Bollinger Bands
            if len(self.data) >= 20:
                bb = BollingerBands(close=close, window=20, window_dev=2)
                self.data['BB_high'] = bb.bollinger_hband()
                self.data['BB_low'] = bb.bollinger_lband()
                self.data['BB_mid'] = bb.bollinger_mavg()
            
            # Average True Range
            if len(self.data) >= 14:
                self.data['ATR'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
            
            # ADX (Trend Strength)
            if len(self.data) >= 14:
                adx = ADXIndicator(high=high, low=low, close=close, window=14)
                self.data['ADX'] = adx.adx()
                self.data['ADX_pos'] = adx.adx_pos()
                self.data['ADX_neg'] = adx.adx_neg()
            
            # Volume Indicators
            if len(self.data) >= 1:
                self.data['VWAP'] = VolumeWeightedAveragePrice(
                    high=high, low=low, close=close, volume=volume
                ).volume_weighted_average_price()
                
                obv = OnBalanceVolumeIndicator(close=close, volume=volume)
                self.data['OBV'] = obv.on_balance_volume()
            
            # Keltner Channel
            if len(self.data) >= 20:
                kc = KeltnerChannel(high=high, low=low, close=close, window=20)
                self.data['KC_high'] = kc.keltner_channel_hband()
                self.data['KC_low'] = kc.keltner_channel_lband()
                self.data['KC_mid'] = kc.keltner_channel_mband()
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            # Continue with partial indicators
    
    def get_technical_signals(self) -> Dict:
        """Get technical trading signals"""
        if self.data.empty:
            return {'overall': 'NEUTRAL', 'signals': [], 'buy_signals': 0, 'sell_signals': 0}
        
        try:
            latest = self.data.iloc[-1]
            signals = []
            buy_signals = 0
            sell_signals = 0
            
            # RSI Signals
            if 'RSI' in self.data.columns and not pd.isna(latest['RSI']):
                rsi = latest['RSI']
                if rsi < 30:
                    signals.append({
                        'indicator': 'RSI',
                        'signal': 'BUY',
                        'value': round(rsi, 2),
                        'reason': 'Oversold condition'
                    })
                    buy_signals += 1
                elif rsi > 70:
                    signals.append({
                        'indicator': 'RSI',
                        'signal': 'SELL',
                        'value': round(rsi, 2),
                        'reason': 'Overbought condition'
                    })
                    sell_signals += 1
            
            # MACD Signals
            if all(col in self.data.columns for col in ['MACD', 'MACD_signal', 'MACD_diff']):
                if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_signal']):
                    if latest['MACD'] > latest['MACD_signal'] and latest['MACD_diff'] > 0:
                        signals.append({
                            'indicator': 'MACD',
                            'signal': 'BUY',
                            'value': round(latest['MACD'], 2),
                            'reason': 'Bullish crossover'
                        })
                        buy_signals += 1
                    elif latest['MACD'] < latest['MACD_signal'] and latest['MACD_diff'] < 0:
                        signals.append({
                            'indicator': 'MACD',
                            'signal': 'SELL',
                            'value': round(latest['MACD'], 2),
                            'reason': 'Bearish crossover'
                        })
                        sell_signals += 1
            
            # Moving Average Signals
            if all(col in self.data.columns for col in ['SMA_20', 'SMA_50']):
                if not pd.isna(latest['SMA_20']) and not pd.isna(latest['SMA_50']):
                    price = latest['Close']
                    if price > latest['SMA_20'] > latest['SMA_50']:
                        signals.append({
                            'indicator': 'MA',
                            'signal': 'BUY',
                            'value': round(price, 2),
                            'reason': 'Price above both SMAs (bullish trend)'
                        })
                        buy_signals += 1
                    elif price < latest['SMA_20'] < latest['SMA_50']:
                        signals.append({
                            'indicator': 'MA',
                            'signal': 'SELL',
                            'value': round(price, 2),
                            'reason': 'Price below both SMAs (bearish trend)'
                        })
                        sell_signals += 1
            
            # Bollinger Bands
            if all(col in self.data.columns for col in ['BB_high', 'BB_low']):
                if not pd.isna(latest['BB_high']) and not pd.isna(latest['BB_low']):
                    price = latest['Close']
                    if price < latest['BB_low']:
                        signals.append({
                            'indicator': 'BB',
                            'signal': 'BUY',
                            'value': round(price, 2),
                            'reason': 'Price below lower Bollinger Band'
                        })
                        buy_signals += 1
                    elif price > latest['BB_high']:
                        signals.append({
                            'indicator': 'BB',
                            'signal': 'SELL',
                            'value': round(price, 2),
                            'reason': 'Price above upper Bollinger Band'
                        })
                        sell_signals += 1
            
            # Stochastic Oscillator
            if all(col in self.data.columns for col in ['Stoch_K', 'Stoch_D']):
                if not pd.isna(latest['Stoch_K']) and not pd.isna(latest['Stoch_D']):
                    if latest['Stoch_K'] < 20 and latest['Stoch_K'] > latest['Stoch_D']:
                        signals.append({
                            'indicator': 'Stochastic',
                            'signal': 'BUY',
                            'value': round(latest['Stoch_K'], 2),
                            'reason': 'Oversold with bullish crossover'
                        })
                        buy_signals += 1
                    elif latest['Stoch_K'] > 80 and latest['Stoch_K'] < latest['Stoch_D']:
                        signals.append({
                            'indicator': 'Stochastic',
                            'signal': 'SELL',
                            'value': round(latest['Stoch_K'], 2),
                            'reason': 'Overbought with bearish crossover'
                        })
                        sell_signals += 1
            
            # ADX (Trend Strength)
            if 'ADX' in self.data.columns and not pd.isna(latest['ADX']):
                adx_value = latest['ADX']
                if adx_value > 25:
                    trend_strength = 'STRONG'
                elif adx_value > 20:
                    trend_strength = 'MODERATE'
                else:
                    trend_strength = 'WEAK'
                signals.append({
                    'indicator': 'ADX',
                    'signal': 'INFO',
                    'value': round(adx_value, 2),
                    'reason': f'Trend strength: {trend_strength}'
                })
            
            # Determine overall signal
            if buy_signals > sell_signals:
                overall = 'BULLISH'
            elif sell_signals > buy_signals:
                overall = 'BEARISH'
            else:
                overall = 'NEUTRAL'
            
            return {
                'overall': overall,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'signals': signals,
                'indicators': self._get_indicator_values(latest)
            }
            
        except Exception as e:
            logger.error(f"Error getting technical signals: {e}")
            return {'overall': 'NEUTRAL', 'signals': [], 'buy_signals': 0, 'sell_signals': 0}
    
    def _get_indicator_values(self, latest: pd.Series) -> Dict:
        """Get current indicator values"""
        indicators = {}
        
        indicator_map = {
            'RSI': 'RSI',
            'MACD': 'MACD',
            'MACD_signal': 'MACD Signal',
            'SMA_20': 'SMA 20',
            'SMA_50': 'SMA 50',
            'SMA_200': 'SMA 200',
            'EMA_50': 'EMA 50',
            'EMA_200': 'EMA 200',
            'BB_high': 'BB Upper',
            'BB_low': 'BB Lower',
            'ATR': 'ATR',
            'ADX': 'ADX',
            'Stoch_K': 'Stochastic %K',
            'Stoch_D': 'Stochastic %D'
        }
        
        for col, name in indicator_map.items():
            if col in self.data.columns and not pd.isna(latest[col]):
                try:
                    indicators[name] = round(float(latest[col]), 2)
                except (ValueError, TypeError):
                    continue
        
        return indicators
    
    def get_summary_statistics(self) -> Dict:
        """Get summary statistics"""
        if self.data.empty:
            return {}
        
        try:
            latest = self.data.iloc[-1]
            prev = self.data.iloc[-2] if len(self.data) > 1 else latest
            
            price_change = latest['Close'] - prev['Close']
            price_change_pct = (price_change / prev['Close']) * 100 if prev['Close'] != 0 else 0
            
            return {
                'current_price': round(float(latest['Close']), 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'volume': int(latest.get('Volume', 0)),
                'high_52w': round(float(self.data['High'].max()), 2),
                'low_52w': round(float(self.data['Low'].min()), 2),
                'avg_volume': int(self.data['Volume'].mean()) if 'Volume' in self.data.columns else 0,
                'volatility': round(float(self.data['Close'].pct_change().std() * 100), 2),
            }
            
        except Exception as e:
            logger.error(f"Error getting summary statistics: {e}")
            return {}
