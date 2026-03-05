"""
Dashboard Service - Center of Intelligence for Stock Analysts
Aggregates KPIs, real-time data, and analysis for watchlist stocks
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from app.services.multi_asset_fetcher import MultiAssetFetcher
from app.services.enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from app.services.enhanced_fundamental_analyzer import EnhancedFundamentalAnalyzer
from app.services.news_analyzer import NewsAnalyzer
from app.services.ai_buy_sell_engine import AIBuySellEngine
from app.services.prediction_engine import PredictionEngine
from app.services.swing_trading_analyzer import SwingTradingAnalyzer

logger = logging.getLogger(__name__)


class DashboardService:
    """Service to aggregate dashboard KPIs and data"""
    
    def __init__(self):
        self.asset_fetcher = MultiAssetFetcher()
        self.enhanced_technical = EnhancedTechnicalAnalyzer
        self.enhanced_fundamental = EnhancedFundamentalAnalyzer()
        self.news_analyzer = NewsAnalyzer()
        self.ai_buy_sell_engine = AIBuySellEngine()
        self.prediction_engine = PredictionEngine()
    
    def get_watchlist_kpis(self, symbols: List[str], asset_type: str = "stock") -> Dict:
        """Get aggregated KPIs for all watchlist stocks"""
        try:
            if not symbols:
                return {
                    'total_stocks': 0,
                    'kpis': [],
                    'summary': {
                        'avg_price_change': 0,
                        'bullish_count': 0,
                        'bearish_count': 0,
                        'neutral_count': 0,
                        'total_volume': 0
                    }
                }
            
            kpis = []
            total_volume = 0
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
            price_changes = []
            
            for symbol in symbols[:20]:  # Limit to 20 stocks for performance
                try:
                    # Fetch basic data
                    asset_info = self.asset_fetcher.get_asset_info(symbol, asset_type)
                    historical_data = self.asset_fetcher.get_historical_data(
                        symbol, asset_type, period="1mo", interval="1d"
                    )
                    
                    if historical_data.empty:
                        continue
                    
                    # Technical Analysis
                    enhanced_ta = self.enhanced_technical(historical_data)
                    technical_signals = enhanced_ta.get_technical_signals()
                    summary_stats = enhanced_ta.get_summary_statistics()
                    
                    current_price = summary_stats.get('current_price', historical_data['Close'].iloc[-1])
                    
                    # Calculate price change
                    if len(historical_data) > 1:
                        prev_price = historical_data['Close'].iloc[-2]
                        price_change = current_price - prev_price
                        price_change_pct = (price_change / prev_price * 100) if prev_price > 0 else 0
                        price_changes.append(price_change_pct)
                    else:
                        price_change = 0
                        price_change_pct = 0
                    
                    # AI Recommendation
                    fundamental_data = {}
                    if asset_type in ['stock', 'etf']:
                        try:
                            fundamental_data = self.enhanced_fundamental.analyze_with_summary(symbol)
                        except:
                            pass
                    
                    ai_recommendation = self.ai_buy_sell_engine.generate_recommendation(
                        symbol,
                        historical_data,
                        technical_signals,
                        fundamental_data
                    )
                    
                    action = ai_recommendation.get('action', 'HOLD')
                    if action == 'BUY':
                        bullish_count += 1
                    elif action == 'SELL':
                        bearish_count += 1
                    else:
                        neutral_count += 1
                    
                    # Support/Resistance
                    support_resistance = self.prediction_engine.predict_support_resistance(historical_data)
                    
                    # Volume
                    volume = int(historical_data['Volume'].iloc[-1]) if 'Volume' in historical_data.columns else 0
                    total_volume += volume
                    
                    # RSI
                    rsi = technical_signals.get('rsi', {}).get('value', 50)
                    
                    # MACD Signal
                    macd_signal = technical_signals.get('macd', {}).get('signal', 'NEUTRAL')
                    
                    # Prior day high/low
                    if len(historical_data) >= 2:
                        prior_day = historical_data.iloc[-2]
                        prior_high = float(prior_day['High'])
                        prior_low = float(prior_day['Low'])
                    else:
                        prior_high = current_price * 1.02
                        prior_low = current_price * 0.98
                    
                    kpi = {
                        'symbol': symbol,
                        'name': asset_info.get('longName', symbol),
                        'current_price': float(round(current_price, 2)),
                        'price_change': float(round(price_change, 2)),
                        'price_change_pct': float(round(price_change_pct, 2)),
                        'volume': int(volume),
                        'rsi': float(round(rsi, 2)),
                        'macd_signal': str(macd_signal),
                        'ai_recommendation': str(action),
                        'confidence': float(ai_recommendation.get('confidence', 0)),
                        'support': float(round(support_resistance.get('support', current_price * 0.95), 2)),
                        'resistance': float(round(support_resistance.get('resistance', current_price * 1.05), 2)),
                        'prior_day_high': float(round(prior_high, 2)),
                        'prior_day_low': float(round(prior_low, 2)),
                        'market_cap': float(asset_info.get('marketCap', 0)),
                        'pe_ratio': float(fundamental_data.get('valuation_metrics', {}).get('pe_ratio', 0)) if fundamental_data else 0.0,
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    kpis.append(kpi)
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol} for dashboard: {e}")
                    continue
            
            # Calculate summary
            avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
            
            return {
                'total_stocks': int(len(kpis)),
                'kpis': kpis,
                'summary': {
                    'avg_price_change': float(round(avg_price_change, 2)),
                    'bullish_count': int(bullish_count),
                    'bearish_count': int(bearish_count),
                    'neutral_count': int(neutral_count),
                    'total_volume': int(total_volume),
                    'last_updated': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting watchlist KPIs: {e}")
            return {
                'total_stocks': 0,
                'kpis': [],
                'summary': {},
                'error': str(e)
            }
    
    def get_market_overview(self) -> Dict:
        """Get overall market overview"""
        try:
            # Fetch major indices
            major_indices = ['^GSPC', '^DJI', '^IXIC', '^VIX']  # S&P 500, Dow, Nasdaq, VIX
            
            overview = []
            for index in major_indices:
                try:
                    historical_data = self.asset_fetcher.get_historical_data(
                        index, 'stock', period="5d", interval="1d"
                    )
                    if not historical_data.empty and len(historical_data) > 0:
                        current = float(historical_data['Close'].iloc[-1])
                        prev = float(historical_data['Close'].iloc[-2]) if len(historical_data) > 1 else current
                        change = current - prev
                        change_pct = (change / prev * 100) if prev > 0 else 0.0
                        
                        overview.append({
                            'symbol': index,
                            'name': {
                                '^GSPC': 'S&P 500',
                                '^DJI': 'Dow Jones',
                                '^IXIC': 'NASDAQ',
                                '^VIX': 'VIX'
                            }.get(index, index),
                            'value': float(round(current, 2)),
                            'change': float(round(change, 2)),
                            'change_pct': float(round(change_pct, 2))
                        })
                except Exception as e:
                    logger.debug(f"Error fetching {index}: {e}")
                    continue
            
            return {
                'indices': overview,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {'indices': [], 'error': str(e)}
    
    def get_top_movers(self, symbols: List[str], asset_type: str = "stock", limit: int = 5) -> Dict:
        """Get top gainers and losers from watchlist"""
        try:
            kpis_data = self.get_watchlist_kpis(symbols, asset_type)
            kpis = kpis_data.get('kpis', [])
            
            # Sort by price change percentage
            gainers = sorted(
                [k for k in kpis if k.get('price_change_pct', 0) > 0],
                key=lambda x: x.get('price_change_pct', 0),
                reverse=True
            )[:limit]
            
            losers = sorted(
                [k for k in kpis if k.get('price_change_pct', 0) < 0],
                key=lambda x: x.get('price_change_pct', 0)
            )[:limit]
            
            return {
                'gainers': gainers,
                'losers': losers,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting top movers: {e}")
            return {'gainers': [], 'losers': [], 'error': str(e)}
