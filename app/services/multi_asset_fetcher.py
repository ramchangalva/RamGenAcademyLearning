"""
Multi-Asset Data Fetcher
Supports stocks, crypto, commodities, and ETFs
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class MultiAssetFetcher:
    """Fetches data for stocks, crypto, commodities, and ETFs"""
    
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
    
    def _normalize_symbol(self, symbol: str, asset_type: str) -> str:
        """Normalize symbol based on asset type"""
        symbol = symbol.upper().strip()
        
        if asset_type == 'crypto':
            # yfinance uses format like BTC-USD, ETH-USD
            if '-' not in symbol:
                # Assume USD pair if not specified
                return f"{symbol}-USD"
        elif asset_type == 'commodity':
            # Commodities: GC=F (Gold), CL=F (Crude Oil), etc.
            if '=F' not in symbol:
                # Map common commodity symbols
                commodity_map = {
                    'GOLD': 'GC=F',
                    'SILVER': 'SI=F',
                    'OIL': 'CL=F',
                    'CRUDE': 'CL=F',
                    'NATURALGAS': 'NG=F',
                    'COPPER': 'HG=F'
                }
                if symbol in commodity_map:
                    return commodity_map[symbol]
                return f"{symbol}=F"
        elif asset_type == 'etf':
            # ETFs use standard ticker format
            pass
        
        return symbol
    
    def get_asset_info(self, symbol: str, asset_type: str = 'stock') -> Dict:
        """Get asset information for any asset type"""
        cache_key = f"info_{asset_type}_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            normalized_symbol = self._normalize_symbol(symbol, asset_type)
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info
            
            if not info:
                raise ValueError(f"No data available for {asset_type}: {symbol}")
            
            # Common fields for all asset types
            result = {
                'symbol': symbol.upper(),
                'normalized_symbol': normalized_symbol,
                'asset_type': asset_type,
                'name': info.get('longName') or info.get('shortName') or symbol,
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice') or 0,
                'volume': info.get('volume') or info.get('regularMarketVolume', 0),
                'previous_close': info.get('previousClose', 0),
                'day_change': 0.0,
                'day_change_percent': 0.0,
            }
            
            # Calculate day change
            if result['current_price'] and result['previous_close']:
                result['day_change'] = result['current_price'] - result['previous_close']
                result['day_change_percent'] = (result['day_change'] / result['previous_close'] * 100) if result['previous_close'] > 0 else 0
            
            # Asset-specific fields
            if asset_type == 'stock':
                result.update({
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 'N/A'),
                    'dividend_yield': (info.get('dividendYield', 0) * 100) if info.get('dividendYield') else 0,
                    '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                    '52_week_low': info.get('fiftyTwoWeekLow', 0),
                })
            elif asset_type == 'crypto':
                result.update({
                    'market_cap': info.get('marketCap', 0),
                    'circulating_supply': info.get('circulatingSupply', 0),
                    'total_supply': info.get('totalSupply', 0),
                    '24h_high': info.get('dayHigh', 0),
                    '24h_low': info.get('dayLow', 0),
                })
            elif asset_type == 'commodity':
                result.update({
                    'unit': info.get('currency', 'USD'),
                    'contract_size': info.get('contractSize', 'N/A'),
                })
            elif asset_type == 'etf':
                result.update({
                    'sector': info.get('sector', 'N/A'),
                    'expense_ratio': info.get('annualReportExpenseRatio', 'N/A'),
                    'total_assets': info.get('totalAssets', 0),
                    'dividend_yield': (info.get('dividendYield', 0) * 100) if info.get('dividendYield') else 0,
                })
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching {asset_type} info for {symbol}: {e}")
            return {
                'symbol': symbol.upper(),
                'asset_type': asset_type,
                'name': symbol,
                'error': str(e)
            }
    
    def get_historical_data(self, symbol: str, asset_type: str = 'stock', 
                           period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        """Get historical data for any asset type"""
        cache_key = f"historical_{asset_type}_{symbol}_{period}_{interval}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            normalized_symbol = self._normalize_symbol(symbol, asset_type)
            ticker = yf.Ticker(normalized_symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No historical data for {asset_type} {symbol}")
                return pd.DataFrame()
            
            # Ensure proper column names
            data.columns = [col.capitalize() for col in data.columns]
            
            # Validate required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {asset_type} {symbol}: {e}")
            return pd.DataFrame()
    
    def search_assets(self, query: str, asset_type: str = 'stock', limit: int = 10) -> List[Dict]:
        """Search for assets by name or symbol"""
        # This is a simplified search - in production, use a proper search API
        results = []
        query = query.upper().strip()
        
        # Common asset mappings
        if asset_type == 'crypto':
            common_crypto = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD', 
                           'XRP-USD', 'DOT-USD', 'DOGE-USD', 'AVAX-USD', 'MATIC-USD']
            results = [{'symbol': s.split('-')[0], 'name': s} for s in common_crypto if query in s]
        elif asset_type == 'commodity':
            commodities = {
                'GOLD': 'GC=F',
                'SILVER': 'SI=F',
                'OIL': 'CL=F',
                'NATURALGAS': 'NG=F',
                'COPPER': 'HG=F',
                'PLATINUM': 'PL=F'
            }
            results = [{'symbol': k, 'name': k, 'normalized': v} 
                      for k, v in commodities.items() if query in k]
        elif asset_type == 'etf':
            common_etfs = ['SPY', 'QQQ', 'VTI', 'VOO', 'IWM', 'EFA', 'EEM', 'GLD', 'SLV', 'USO']
            results = [{'symbol': s, 'name': s} for s in common_etfs if query in s]
        
        return results[:limit]
