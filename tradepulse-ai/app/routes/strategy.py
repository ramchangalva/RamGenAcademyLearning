"""Strategy Builder Routes"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from app.utils.rate_limiting import get_client_identifier
from app.utils.template_context import get_common_context
from app.services.auto_strategy_generator import AutoStrategyGenerator
from app.services.multi_asset_fetcher import MultiAssetFetcher
from app.services.enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from app.services.enhanced_fundamental_analyzer import EnhancedFundamentalAnalyzer
from app.services.ai_buy_sell_engine import AIBuySellEngine
from app.services.prediction_engine import PredictionEngine

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize services
auto_strategy_gen = AutoStrategyGenerator()
asset_fetcher = MultiAssetFetcher()
enhanced_technical = EnhancedTechnicalAnalyzer
enhanced_fundamental = EnhancedFundamentalAnalyzer()
ai_buy_sell_engine = AIBuySellEngine()
prediction_engine = PredictionEngine()

@router.get("/strategy", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def strategy_page(request: Request, symbol: Optional[str] = None, asset_type: Optional[str] = "stock"):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = request.cookies.get("user_id") or get_client_identifier(request)
    context = get_common_context(request, user_id, "strategy")
    
    context['symbol'] = symbol
    context['asset_type'] = asset_type
    context['strategies'] = []
    context['has_analysis'] = False
    
    # If symbol provided, generate automatic strategies
    if symbol:
        try:
            symbol = symbol.upper().strip()
            
            # Fetch data
            historical_data = asset_fetcher.get_historical_data(symbol, asset_type, period="1y", interval="1d")
            
            if not historical_data.empty:
                # Perform analysis
                enhanced_ta = enhanced_technical(historical_data)
                technical_signals = enhanced_ta.get_technical_signals()
                
                fundamental_data = {}
                if asset_type in ['stock', 'etf']:
                    fundamental_data = enhanced_fundamental.analyze_with_summary(symbol)
                
                ai_recommendation = ai_buy_sell_engine.generate_recommendation(
                    symbol,
                    historical_data,
                    technical_signals,
                    fundamental_data if fundamental_data else {}
                )
                
                support_resistance = prediction_engine.predict_support_resistance(historical_data)
                current_price = historical_data['Close'].iloc[-1]
                
                # Generate automatic strategies
                strategies = auto_strategy_gen.generate_multiple_strategies(
                    symbol=symbol,
                    technical_signals=technical_signals,
                    fundamental_data=fundamental_data if fundamental_data else {},
                    historical_data=historical_data,
                    support_resistance=support_resistance,
                    current_price=current_price,
                    recommendation=ai_recommendation.get('action', 'HOLD')
                )
                
                context.update({
                    'strategies': strategies,
                    'has_analysis': True,
                    'technical_signals': technical_signals,
                    'recommendation': ai_recommendation,
                    'current_price': current_price,
                    'support_resistance': support_resistance
                })
                
        except Exception as e:
            context['error'] = f"Error generating strategies: {str(e)}"
    
    return templates.TemplateResponse("strategy.html", context)

@router.get("/api/strategy/generate")
@limiter.limit("30/minute")
async def generate_strategy(request: Request, symbol: str, asset_type: str = "stock"):
    """Generate strategies for a symbol"""
    try:
        symbol = symbol.upper().strip()
        
        # Fetch data
        historical_data = asset_fetcher.get_historical_data(symbol, asset_type, period="1y", interval="1d")
        
        if historical_data.empty:
            return JSONResponse(
                status_code=404,
                content={'error': 'No data available for symbol'}
            )
        
        # Perform analysis
        enhanced_ta = enhanced_technical(historical_data)
        technical_signals = enhanced_ta.get_technical_signals()
        
        fundamental_data = {}
        if asset_type in ['stock', 'etf']:
            fundamental_data = enhanced_fundamental.analyze_with_summary(symbol)
        
        ai_recommendation = ai_buy_sell_engine.generate_recommendation(
            symbol,
            historical_data,
            technical_signals,
            fundamental_data if fundamental_data else {}
        )
        
        support_resistance = prediction_engine.predict_support_resistance(historical_data)
        current_price = historical_data['Close'].iloc[-1]
        
        # Generate strategies
        strategies = auto_strategy_gen.generate_multiple_strategies(
            symbol=symbol,
            technical_signals=technical_signals,
            fundamental_data=fundamental_data if fundamental_data else {},
            historical_data=historical_data,
            support_resistance=support_resistance,
            current_price=current_price,
            recommendation=ai_recommendation.get('action', 'HOLD')
        )
        
        return JSONResponse(content={
            'symbol': symbol,
            'strategies': strategies,
            'recommendation': ai_recommendation,
            'current_price': current_price
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )
