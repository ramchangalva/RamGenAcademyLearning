"""
AI Market Scanner
Scans multiple assets for breakouts, reversals, volume spikes, and trend changes
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from app.services.data_fetcher import StockDataFetcher
from app.services.technical_analyzer import TechnicalAnalyzer
from app.services.ai_buy_sell_engine import AIBuySellEngine

logger = logging.getLogger(__name__)


class AIMarketScanner:
    """AI-powered market scanner for multiple assets"""
    
    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        self.ai_engine = AIBuySellEngine()
        
        # Popular symbols to scan (can be expanded)
        self.scan_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM',
            'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'DIS', 'BAC', 'ADBE',
            'NFLX', 'CRM', 'PYPL', 'INTC', 'CMCSA', 'PEP', 'COST', 'TMO',
            'AVGO', 'CSCO', 'ABT', 'NKE', 'MRK', 'ACN', 'TXN', 'QCOM', 'DHR'
        ]
    
    def scan_market(self, scan_type: str = 'all', filters: Optional[Dict] = None) -> Dict:
        """
        Scan market for opportunities
        
        Args:
            scan_type: 'breakouts', 'reversals', 'volume_spikes', 'trend_changes', 'all'
            filters: {
                'timeframe': 'intraday', 'swing', 'long_term',
                'min_volume': float,
                'min_confidence': float
            }
        
        Returns:
            {
                'breakouts': List[Dict],
                'reversals': List[Dict],
                'volume_spikes': List[Dict],
                'trend_changes': List[Dict],
                'timestamp': str
            }
        """
        try:
            if filters is None:
                filters = {}
            
            results = {
                'breakouts': [],
                'reversals': [],
                'volume_spikes': [],
                'trend_changes': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Determine period based on timeframe
            timeframe = filters.get('timeframe', 'swing')
            period_map = {
                'intraday': '5d',
                'swing': '3mo',
                'long_term': '1y'
            }
            period = period_map.get(timeframe, '3mo')
            
            # Scan symbols (with rate limiting)
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self._scan_symbol, symbol, scan_type, period, filters): symbol
                    for symbol in self.scan_symbols[:20]  # Limit to 20 for performance
                }
                
                for future in as_completed(futures):
                    symbol = futures[future]
                    try:
                        scan_result = future.result(timeout=10)
                        if scan_result:
                            for key in results.keys():
                                if key in scan_result and scan_result[key]:
                                    results[key].extend(scan_result[key])
                    except Exception as e:
                        logger.warning(f"Error scanning {symbol}: {e}")
                    time.sleep(0.1)  # Rate limiting
            
            # Sort and filter results
            for key in ['breakouts', 'reversals', 'volume_spikes', 'trend_changes']:
                results[key] = sorted(
                    results[key],
                    key=lambda x: x.get('score', 0) or x.get('confidence', 0),
                    reverse=True
                )[:10]  # Top 10
            
            return results
            
        except Exception as e:
            logger.error(f"Error in market scan: {e}")
            return {
                'breakouts': [],
                'reversals': [],
                'volume_spikes': [],
                'trend_changes': [],
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _scan_symbol(self, symbol: str, scan_type: str, period: str,
                    filters: Dict) -> Optional[Dict]:
        """Scan a single symbol"""
        try:
            # Get interval based on period
            interval = '1d' if period in ['3mo', '1y'] else '1h'
            data = self.data_fetcher.get_historical_data(symbol, period=period, interval=interval)
            if data.empty or len(data) < 20:
                return None
            
            # Set symbol name in index for reference
            if data.index.name is None:
                data.index.name = symbol
            
            results = {
                'breakouts': [],
                'reversals': [],
                'volume_spikes': [],
                'trend_changes': []
            }
            
            # Technical analysis
            ta = TechnicalAnalyzer(data)
            signals = ta.get_technical_signals()
            
            # Check for breakouts
            if scan_type in ['breakouts', 'all']:
                breakout = self._detect_breakout(symbol, data, signals)
                if breakout:
                    results['breakouts'].append(breakout)
            
            # Check for reversals
            if scan_type in ['reversals', 'all']:
                reversal = self._detect_reversal(symbol, data, signals)
                if reversal:
                    results['reversals'].append(reversal)
            
            # Check for volume spikes
            if scan_type in ['volume_spikes', 'all']:
                volume_spike = self._detect_volume_spike(symbol, data, filters)
                if volume_spike:
                    results['volume_spikes'].append(volume_spike)
            
            # Check for trend changes
            if scan_type in ['trend_changes', 'all']:
                trend_change = self._detect_trend_change(symbol, data, signals)
                if trend_change:
                    results['trend_changes'].append(trend_change)
            
            return results if any(results.values()) else None
            
        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            return None
    
    def _detect_breakout(self, symbol: str, data: pd.DataFrame, signals: Dict) -> Optional[Dict]:
        """Detect price breakouts"""
        try:
            if len(data) < 20:
                return None
            
            latest = data.iloc[-1]
            recent_high = data['High'].tail(20).max()
            recent_low = data['Low'].tail(20).min()
            current_price = latest['Close']
            
            # Check for breakout above resistance
            if 'BB_high' in data.columns and not pd.isna(latest['BB_high']):
                if current_price > latest['BB_high']:
                    # Volume confirmation
                    volume_ratio = latest['Volume'] / data['Volume'].tail(20).mean()
                    
                    if volume_ratio > 1.2:  # Above average volume
                        symbol_name = data.index.name if data.index.name else symbol
                        return {
                            'symbol': symbol_name,
                            'type': 'BREAKOUT_UP',
                            'price': round(current_price, 2),
                            'resistance': round(latest['BB_high'], 2),
                            'volume_ratio': round(volume_ratio, 2),
                            'confidence': min(90, 60 + (volume_ratio - 1) * 20),
                            'timestamp': datetime.now().isoformat()
                        }
            
            # Check for breakdown below support
            if 'BB_low' in data.columns and not pd.isna(latest['BB_low']):
                if current_price < latest['BB_low']:
                    volume_ratio = latest['Volume'] / data['Volume'].tail(20).mean()
                    
                    if volume_ratio > 1.2:
                        symbol_name = data.index.name if data.index.name else symbol
                        return {
                            'symbol': symbol_name,
                            'type': 'BREAKDOWN_DOWN',
                            'price': round(current_price, 2),
                            'support': round(latest['BB_low'], 2),
                            'volume_ratio': round(volume_ratio, 2),
                            'confidence': min(90, 60 + (volume_ratio - 1) * 20),
                            'timestamp': datetime.now().isoformat()
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error detecting breakout: {e}")
            return None
    
    def _detect_reversal(self, symbol: str, data: pd.DataFrame, signals: Dict) -> Optional[Dict]:
        """Detect potential reversals"""
        try:
            if len(data) < 20:
                return None
            
            # Check RSI for reversal signals
            if 'RSI' in data.columns:
                latest_rsi = data['RSI'].iloc[-1]
                prev_rsi = data['RSI'].iloc[-2] if len(data) > 1 else latest_rsi
                
                # Oversold reversal
                if latest_rsi < 30 and prev_rsi < latest_rsi:
                    symbol_name = data.index.name if data.index.name else symbol
                    return {
                        'symbol': symbol_name,
                        'type': 'BULLISH_REVERSAL',
                        'indicator': 'RSI',
                        'value': round(latest_rsi, 2),
                        'confidence': 70,
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Overbought reversal
                if latest_rsi > 70 and prev_rsi > latest_rsi:
                    symbol_name = data.index.name if data.index.name else symbol
                    return {
                        'symbol': symbol_name,
                        'type': 'BEARISH_REVERSAL',
                        'indicator': 'RSI',
                        'value': round(latest_rsi, 2),
                        'confidence': 70,
                        'timestamp': datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error detecting reversal: {e}")
            return None
    
    def _detect_volume_spike(self, symbol: str, data: pd.DataFrame, filters: Dict) -> Optional[Dict]:
        """Detect volume spikes"""
        try:
            if 'Volume' not in data.columns:
                return None
            
            latest = data.iloc[-1]
            avg_volume = data['Volume'].tail(20).mean()
            current_volume = latest['Volume']
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            min_volume = filters.get('min_volume', 1.5)
            
            if volume_ratio >= min_volume:
                price_change = (latest['Close'] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100 if len(data) > 1 else 0
                symbol_name = data.index.name if data.index.name else symbol
                
                return {
                    'symbol': symbol_name,
                    'type': 'VOLUME_SPIKE',
                    'volume_ratio': round(volume_ratio, 2),
                    'price_change': round(price_change, 2),
                    'direction': 'UP' if price_change > 0 else 'DOWN',
                    'confidence': min(95, 50 + (volume_ratio - 1) * 15),
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error detecting volume spike: {e}")
            return None
    
    def _detect_trend_change(self, symbol: str, data: pd.DataFrame, signals: Dict) -> Optional[Dict]:
        """Detect trend changes"""
        try:
            if len(data) < 50:
                return None
            
            # Compare recent trend vs longer term
            short_ma = data['Close'].tail(10).mean()
            long_ma = data['Close'].tail(50).mean()
            prev_short_ma = data['Close'].iloc[-20:-10].mean() if len(data) > 20 else short_ma
            
            # Bullish trend change
            if short_ma > long_ma and prev_short_ma <= long_ma:
                symbol_name = data.index.name if data.index.name else symbol
                return {
                    'symbol': symbol_name,
                    'type': 'BULLISH_TREND_CHANGE',
                    'short_ma': round(short_ma, 2),
                    'long_ma': round(long_ma, 2),
                    'confidence': 75,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Bearish trend change
            if short_ma < long_ma and prev_short_ma >= long_ma:
                symbol_name = data.index.name if data.index.name else symbol
                return {
                    'symbol': symbol_name,
                    'type': 'BEARISH_TREND_CHANGE',
                    'short_ma': round(short_ma, 2),
                    'long_ma': round(long_ma, 2),
                    'confidence': 75,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error detecting trend change: {e}")
            return None
