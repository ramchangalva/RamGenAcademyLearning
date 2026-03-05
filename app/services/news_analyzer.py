"""
News Analyzer Module
Fetches and analyzes market news for sentiment analysis
"""
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Analyzes market news and sentiment for predictions"""
    
    def __init__(self):
        self.api_key = None  # Can be set via environment variable
        # Using free news sources that don't require API keys
        self.news_sources = []
    
    def fetch_news(self, symbol: str, days_back: int = 30) -> List[Dict]:
        """Fetch recent news for a symbol"""
        try:
            news_items = []
            
            # Try to fetch from yfinance news (free, no API key needed)
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                news_data = ticker.news
                
                if news_data:
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    for item in news_data:
                        try:
                            pub_date = datetime.fromtimestamp(item.get('providerPublishTime', 0))
                            if pub_date >= cutoff_date:
                                news_items.append({
                                    'title': item.get('title', ''),
                                    'publisher': item.get('publisher', 'Unknown'),
                                    'date': pub_date.strftime('%Y-%m-%d'),
                                    'link': item.get('link', ''),
                                    'type': item.get('type', 'STORY')
                                })
                        except Exception as e:
                            logger.debug(f"Error parsing news item: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Could not fetch news from yfinance: {e}")
            
            return news_items[:20]  # Limit to 20 most recent
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []
    
    def analyze_sentiment(self, news_items: List[Dict], symbol: str) -> Dict:
        """Analyze sentiment from news headlines"""
        try:
            if not news_items:
                return {
                    'sentiment_score': 0,
                    'sentiment': 'NEUTRAL',
                    'news_count': 0,
                    'positive_keywords': [],
                    'negative_keywords': [],
                    'recent_news': []
                }
            
            # Keywords for sentiment analysis
            positive_keywords = [
                'beat', 'surge', 'rally', 'gain', 'growth', 'profit', 'revenue', 'upgrade',
                'bullish', 'outperform', 'buy', 'strong', 'positive', 'increase', 'rise',
                'expansion', 'acquisition', 'partnership', 'breakthrough', 'record'
            ]
            
            negative_keywords = [
                'miss', 'drop', 'fall', 'decline', 'loss', 'downgrade', 'bearish',
                'underperform', 'sell', 'weak', 'negative', 'decrease', 'cut', 'layoff',
                'lawsuit', 'investigation', 'warning', 'concern', 'risk', 'volatility'
            ]
            
            positive_count = 0
            negative_count = 0
            positive_keywords_found = []
            negative_keywords_found = []
            
            for item in news_items:
                title_lower = item.get('title', '').lower()
                
                # Count positive keywords
                for keyword in positive_keywords:
                    if keyword in title_lower:
                        positive_count += 1
                        if keyword not in positive_keywords_found:
                            positive_keywords_found.append(keyword)
                
                # Count negative keywords
                for keyword in negative_keywords:
                    if keyword in title_lower:
                        negative_count += 1
                        if keyword not in negative_keywords_found:
                            negative_keywords_found.append(keyword)
            
            # Calculate sentiment score (-100 to +100)
            total_keywords = positive_count + negative_count
            if total_keywords > 0:
                sentiment_score = ((positive_count - negative_count) / total_keywords) * 100
            else:
                sentiment_score = 0
            
            # Determine sentiment
            if sentiment_score > 20:
                sentiment = 'BULLISH'
            elif sentiment_score < -20:
                sentiment = 'BEARISH'
            else:
                sentiment = 'NEUTRAL'
            
            return {
                'sentiment_score': round(sentiment_score, 2),
                'sentiment': sentiment,
                'news_count': len(news_items),
                'positive_keywords': positive_keywords_found[:5],
                'negative_keywords': negative_keywords_found[:5],
                'recent_news': news_items[:5]  # Top 5 most recent
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment_score': 0,
                'sentiment': 'NEUTRAL',
                'news_count': 0,
                'positive_keywords': [],
                'negative_keywords': [],
                'recent_news': []
            }
    
    def get_news_analysis(self, symbol: str, days_back: int = 30) -> Dict:
        """Get comprehensive news analysis"""
        try:
            news_items = self.fetch_news(symbol, days_back)
            sentiment = self.analyze_sentiment(news_items, symbol)
            
            return {
                'symbol': symbol,
                'news_items': news_items,
                'sentiment_analysis': sentiment,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting news analysis for {symbol}: {e}")
            return {
                'symbol': symbol,
                'news_items': [],
                'sentiment_analysis': {
                    'sentiment_score': 0,
                    'sentiment': 'NEUTRAL',
                    'news_count': 0
                },
                'error': str(e)
            }
    
    def get_realtime_news_feed(self, symbols: List[str], hours_back: int = 24, limit_per_symbol: int = 5) -> List[Dict]:
        """Get real-time news feed for multiple symbols"""
        try:
            all_news = []
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for symbol in symbols[:20]:  # Limit to 20 symbols
                try:
                    news_items = self.fetch_news(symbol, days_back=1)
                    
                    for item in news_items[:limit_per_symbol]:
                        try:
                            # Parse date
                            pub_date = datetime.strptime(item.get('date', ''), '%Y-%m-%d')
                            if pub_date >= cutoff_time:
                                item['symbol'] = symbol
                                item['timestamp'] = pub_date.isoformat()
                                all_news.append(item)
                        except:
                            # If date parsing fails, include it anyway (might be recent)
                            item['symbol'] = symbol
                            item['timestamp'] = datetime.now().isoformat()
                            all_news.append(item)
                except Exception as e:
                    logger.debug(f"Error fetching news for {symbol}: {e}")
                    continue
            
            # Sort by date (most recent first)
            all_news.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return all_news[:50]  # Return top 50 most recent
            
        except Exception as e:
            logger.error(f"Error getting realtime news feed: {e}")
            return []
