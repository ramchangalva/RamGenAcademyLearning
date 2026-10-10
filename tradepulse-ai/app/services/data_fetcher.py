"""
Stock Data Fetcher Module
Fetches live stock data using yfinance with caching and error handling
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetches stock data from yfinance with caching and error handling"""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache:
            return False
        cache_time, _ = self._cache[cache_key]
        return (datetime.now() - cache_time).seconds < self._cache_ttl
    
    def _get_cached(self, cache_key: str):
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key][1]
        return None
    
    def _set_cache(self, cache_key: str, data):
        """Store data in cache"""
        self._cache[cache_key] = (datetime.now(), data)
    
    def get_stock_info(self, symbol: str) -> Dict:
        """Get basic stock information"""
        cache_key = f"info_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                raise ValueError(f"No data available for symbol: {symbol}")
            
            result = {
                'symbol': symbol.upper(),
                'name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice') or 0,
                'volume': info.get('volume') or info.get('regularMarketVolume', 0),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'forward_pe': info.get('forwardPE', 'N/A'),
                'dividend_yield': (info.get('dividendYield', 0) * 100) if info.get('dividendYield') else 0,
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
                'beta': info.get('beta', 'N/A'),
                'eps': info.get('trailingEps', 'N/A'),
                'revenue': info.get('totalRevenue', 0),
                'profit_margin': (info.get('profitMargins', 0) * 100) if info.get('profitMargins') else 0,
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'roe': (info.get('returnOnEquity', 0) * 100) if info.get('returnOnEquity') else 0,
                'roa': (info.get('returnOnAssets', 0) * 100) if info.get('returnOnAssets') else 0,
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return {
                'symbol': symbol.upper(),
                'name': symbol,
                'error': str(e)
            }
    
    def get_historical_data(self, symbol: str, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        """Get historical stock data with optional interval"""
        cache_key = f"historical_{symbol}_{period}_{interval}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No historical data for {symbol} with period {period} and interval {interval}")
                return pd.DataFrame()
            
            # Ensure proper column names (capitalize first letter)
            data.columns = [col.capitalize() for col in data.columns]
            
            # Validate required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_intraday_data(self, symbol: str, interval: str = '1h', period: str = '5d') -> pd.DataFrame:
        """Get intraday data (1h, 15m, 5m, etc.)"""
        return self.get_historical_data(symbol, period=period, interval=interval)
    
    def get_realtime_data(self, symbol: str) -> Dict:
        """Get real-time stock data"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get intraday data first
            data = ticker.history(period='1d', interval='1m')
            
            if data.empty:
                # Fallback to daily data
                data = ticker.history(period='5d')
            
            if data.empty:
                return {'error': 'No data available', 'symbol': symbol.upper()}
            
            latest = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else latest
            
            current_price = float(latest['Close'])
            prev_price = float(prev['Close'])
            change = current_price - prev_price
            change_pct = (change / prev_price * 100) if prev_price > 0 else 0
            
            return {
                'symbol': symbol.upper(),
                'current_price': round(current_price, 2),
                'price_change': round(change, 2),
                'price_change_pct': round(change_pct, 2),
                'volume': int(latest.get('Volume', 0)),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching realtime data for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol.upper()}
    
    def get_popular_stocks(self) -> List[str]:
        """Get list of popular stocks (deprecated - returns empty list)"""
        return []
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
