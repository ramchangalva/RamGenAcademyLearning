"""
AI Stock Assistant Service
Provides AI assistance with stock analysis context
"""
import logging
from typing import Dict, List, Optional
import json

from app.services.chatbot_providers import ChatbotManager
from app.services.multi_asset_fetcher import MultiAssetFetcher
from app.services.enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from app.services.enhanced_fundamental_analyzer import EnhancedFundamentalAnalyzer
from app.services.ai_buy_sell_engine import AIBuySellEngine
from app.services.prediction_engine import PredictionEngine
from app.services.news_analyzer import NewsAnalyzer

logger = logging.getLogger(__name__)


class AIStockAssistant:
    """AI Assistant with stock analysis context"""
    
    def __init__(self):
        self.chatbot_manager = ChatbotManager()
        self.asset_fetcher = MultiAssetFetcher()
        self.enhanced_technical = EnhancedTechnicalAnalyzer
        self.enhanced_fundamental = EnhancedFundamentalAnalyzer()
        self.ai_buy_sell_engine = AIBuySellEngine()
        self.prediction_engine = PredictionEngine()
        self.news_analyzer = NewsAnalyzer()
    
    def get_stock_analysis_context(self, symbol: str, asset_type: str = "stock") -> Dict:
        """Get comprehensive stock analysis context for AI"""
        try:
            # Fetch data
            asset_info = self.asset_fetcher.get_asset_info(symbol, asset_type)
            historical_data = self.asset_fetcher.get_historical_data(symbol, asset_type, period="1y", interval="1d")
            
            if historical_data.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Technical Analysis
            enhanced_ta = self.enhanced_technical(historical_data)
            technical_signals = enhanced_ta.get_technical_signals()
            summary_stats = enhanced_ta.get_summary_statistics()
            
            current_price = summary_stats.get('current_price', historical_data['Close'].iloc[-1])
            
            # Fundamental Analysis
            fundamental_data = {}
            if asset_type in ['stock', 'etf']:
                try:
                    fundamental_data = self.enhanced_fundamental.analyze_with_summary(symbol)
                except:
                    pass
            
            # AI Recommendation
            ai_recommendation = self.ai_buy_sell_engine.generate_recommendation(
                symbol,
                historical_data,
                technical_signals,
                fundamental_data
            )
            
            # Support/Resistance
            support_resistance = self.prediction_engine.predict_support_resistance(historical_data)
            
            # News Analysis
            news_analysis = self.news_analyzer.get_news_analysis(symbol, days_back=7)
            
            # Price predictions
            price_predictions = self.prediction_engine.predict_price(historical_data, days_ahead=5)
            
            # Build context summary
            context = {
                'symbol': symbol,
                'name': asset_info.get('longName', symbol),
                'current_price': round(current_price, 2),
                'technical_indicators': {
                    'rsi': technical_signals.get('rsi', {}).get('value', 50),
                    'macd_signal': technical_signals.get('macd', {}).get('signal', 'NEUTRAL'),
                    'ema_trend': technical_signals.get('ema', {}).get('trend', 'NEUTRAL'),
                    'volume_trend': technical_signals.get('volume', {}).get('trend', 'NEUTRAL')
                },
                'support_resistance': {
                    'support': round(support_resistance.get('support', current_price * 0.95), 2),
                    'resistance': round(support_resistance.get('resistance', current_price * 1.05), 2)
                },
                'ai_recommendation': {
                    'action': ai_recommendation.get('action', 'HOLD'),
                    'confidence': ai_recommendation.get('confidence', 0),
                    'reasoning': ai_recommendation.get('reasoning', '')
                },
                'fundamental_metrics': {
                    'pe_ratio': fundamental_data.get('valuation_metrics', {}).get('pe_ratio', 0) if fundamental_data else 0,
                    'market_cap': asset_info.get('marketCap', 0),
                    'revenue_growth': fundamental_data.get('growth_metrics', {}).get('revenue_growth', 0) if fundamental_data else 0
                },
                'news_sentiment': {
                    'sentiment': news_analysis.get('sentiment_analysis', {}).get('sentiment', 'NEUTRAL'),
                    'score': news_analysis.get('sentiment_analysis', {}).get('sentiment_score', 0),
                    'recent_headlines': [item.get('title', '') for item in news_analysis.get('news_items', [])[:3]]
                },
                'price_predictions': {
                    'next_5_days': round(price_predictions.get('predicted_price', current_price), 2),
                    'direction': price_predictions.get('direction', 'NEUTRAL')
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting stock analysis context for {symbol}: {e}")
            return {'error': str(e)}
    
    def format_context_for_ai(self, context: Dict) -> str:
        """Format stock analysis context as a readable string for AI"""
        if 'error' in context:
            return f"Error: {context['error']}"
        
        lines = [
            f"Stock Analysis for {context.get('symbol', 'N/A')} ({context.get('name', 'N/A')}):",
            f"",
            f"Current Price: ${context.get('current_price', 0)}",
            f"",
            f"Technical Indicators:",
            f"  - RSI: {context.get('technical_indicators', {}).get('rsi', 50)}",
            f"  - MACD Signal: {context.get('technical_indicators', {}).get('macd_signal', 'NEUTRAL')}",
            f"  - EMA Trend: {context.get('technical_indicators', {}).get('ema_trend', 'NEUTRAL')}",
            f"  - Volume Trend: {context.get('technical_indicators', {}).get('volume_trend', 'NEUTRAL')}",
            f"",
            f"Support/Resistance:",
            f"  - Support: ${context.get('support_resistance', {}).get('support', 0)}",
            f"  - Resistance: ${context.get('support_resistance', {}).get('resistance', 0)}",
            f"",
            f"AI Recommendation:",
            f"  - Action: {context.get('ai_recommendation', {}).get('action', 'HOLD')}",
            f"  - Confidence: {context.get('ai_recommendation', {}).get('confidence', 0)}%",
            f"  - Reasoning: {context.get('ai_recommendation', {}).get('reasoning', 'N/A')}",
            f"",
            f"Fundamental Metrics:",
            f"  - P/E Ratio: {context.get('fundamental_metrics', {}).get('pe_ratio', 0)}",
            f"  - Market Cap: ${context.get('fundamental_metrics', {}).get('market_cap', 0):,}",
            f"  - Revenue Growth: {context.get('fundamental_metrics', {}).get('revenue_growth', 0)}%",
            f"",
            f"News Sentiment:",
            f"  - Sentiment: {context.get('news_sentiment', {}).get('sentiment', 'NEUTRAL')}",
            f"  - Score: {context.get('news_sentiment', {}).get('score', 0)}",
            f"  - Recent Headlines:",
        ]
        
        for headline in context.get('news_sentiment', {}).get('recent_headlines', []):
            lines.append(f"    - {headline}")
        
        lines.extend([
            f"",
            f"Price Predictions:",
            f"  - Next 5 Days: ${context.get('price_predictions', {}).get('next_5_days', 0)}",
            f"  - Direction: {context.get('price_predictions', {}).get('direction', 'NEUTRAL')}",
        ])
        
        return "\n".join(lines)
    
    def chat_with_context(self, messages: List[Dict], symbol: Optional[str] = None, 
                         asset_type: str = "stock", provider_name: str = "openai",
                         model: Optional[str] = None, user_api_keys: Optional[Dict] = None) -> Dict:
        """Chat with AI using stock analysis context"""
        try:
            # If symbol is provided, add context to messages
            if symbol:
                context = self.get_stock_analysis_context(symbol, asset_type)
                context_text = self.format_context_for_ai(context)
                
                # Create system message with context
                system_message = {
                    'role': 'system',
                    'content': f"""You are an expert stock analyst AI assistant. You have access to comprehensive analysis data for {symbol}.

{context_text}

Use this information to answer questions about the stock. Be specific, cite the data, and provide actionable insights. If asked about entry/exit points, use the support/resistance levels and AI recommendations provided."""
                }
                
                # Prepend system message to messages
                messages_with_context = [system_message] + messages
            else:
                messages_with_context = messages
            
            # Get available models if not specified
            if not model:
                models = self.chatbot_manager.get_provider_models(provider_name)
                if models:
                    model = models[0]
                else:
                    return {
                        'success': False,
                        'error': f'No models available for provider {provider_name}'
                    }
            
            # Call chatbot
            result = self.chatbot_manager.chat(
                provider_name=provider_name,
                messages=messages_with_context,
                model=model,
                user_api_keys=user_api_keys,
                temperature=0.7,
                max_tokens=1500
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI stock assistant chat: {e}")
            return {
                'success': False,
                'error': str(e)
            }
