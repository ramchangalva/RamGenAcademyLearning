"""
Asset Analysis Routes (Stocks, Crypto, Commodities, ETFs)
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pandas as pd
import traceback
import logging

from app.core.config import settings
from app.utils.rate_limiting import get_client_identifier
from app.services.multi_asset_fetcher import MultiAssetFetcher
from app.utils.template_context import get_common_context
from app.utils.input_validation import (
    validate_symbol, validate_period, validate_interval, 
    validate_asset_type, sanitize_user_id, sanitize_error_message
)

# Import analysis services
from app.services.technical_analyzer import TechnicalAnalyzer
from app.services.enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from app.services.enhanced_fundamental_analyzer import EnhancedFundamentalAnalyzer
from app.services.prediction_engine import PredictionEngine
from app.services.chart_generator import ChartGenerator
from app.services.ai_buy_sell_engine import AIBuySellEngine
from app.services.smart_entry_exit import SmartEntryExitSystem
from app.services.ai_stop_loss_manager import AIStopLossManager
from app.services.risk_management import RiskManagementDashboard
from app.services.swing_trading_analyzer import SwingTradingAnalyzer
from app.services.multi_timeframe_predictor import MultiTimeframePredictor
from app.services.news_analyzer import NewsAnalyzer
import plotly

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

# Initialize services
asset_fetcher = MultiAssetFetcher()
enhanced_technical = EnhancedTechnicalAnalyzer
enhanced_fundamental = EnhancedFundamentalAnalyzer()
prediction_engine = PredictionEngine()
ai_buy_sell_engine = AIBuySellEngine()
smart_entry_exit = SmartEntryExitSystem()
ai_stop_loss_manager = AIStopLossManager()
risk_manager = RiskManagementDashboard()
multi_timeframe_predictor = MultiTimeframePredictor()
news_analyzer = NewsAnalyzer()

def plotly_fig_to_html(fig) -> str:
    """Convert Plotly figure to HTML string"""
    try:
        return plotly.offline.plot(
            fig,
            output_type='div',
            include_plotlyjs='cdn',
            config={'displayModeBar': True, 'responsive': True}
        )
    except Exception as e:
        logger.error(f"Error converting plotly figure to HTML: {e}")
        return "<div>Error generating chart</div>"


def _get_prior_day_row(data: pd.DataFrame) -> Optional[pd.Series]:
    """
    Get the prior day's OHLC row from daily historical data.
    If the latest row is today, use the previous row; otherwise use the latest row.
    """
    if data.empty:
        return None
    if len(data) == 1:
        return data.iloc[-1]

    try:
        latest_idx = data.index[-1]
        # If index is datetime-like, compare dates
        if hasattr(latest_idx, "date"):
            today = datetime.now().date()
            if latest_idx.date() == today and len(data) >= 2:
                return data.iloc[-2]
        return data.iloc[-1]
    except Exception:
        # Fallback to second last row when available
        return data.iloc[-2] if len(data) >= 2 else data.iloc[-1]


def _build_watchlist_levels(
    watchlist: List[str],
    asset_type: str,
    user_symbol: str,
) -> List[Dict]:
    """
    Build watchlist overview with prior day high/low and best intraday/swing entry prices.
    Uses existing analysis services to stay consistent with main analysis view.
    """
    results: List[Dict] = []
    if not watchlist:
        return results

    for symbol in watchlist[:10]:  # Limit to first 10 symbols for performance
        try:
            sym = symbol.upper().strip()
            # Skip current analysis symbol (already shown in detail)
            if sym == (user_symbol or "").upper().strip():
                continue

            historical = asset_fetcher.get_historical_data(sym, asset_type, period="6mo", interval="1d")
            if historical.empty or "Close" not in historical.columns:
                continue

            prior_row = _get_prior_day_row(historical)
            if prior_row is None:
                continue

            prior_high = float(prior_row["High"])
            prior_low = float(prior_row["Low"])
            current_price = float(historical["Close"].iloc[-1])

            # Technical signals
            enhanced_ta = enhanced_technical(historical)
            tech_signals = enhanced_ta.get_technical_signals()

            # Fundamentals (for stocks/ETFs)
            fundamental_data: Dict = {}
            if asset_type in ["stock", "etf"]:
                try:
                    fundamental_data = enhanced_fundamental.analyze_with_summary(sym)
                except Exception:
                    fundamental_data = {}

            # Support/Resistance
            sr_levels = prediction_engine.predict_support_resistance(historical)

            # AI recommendation
            ai_rec = ai_buy_sell_engine.generate_recommendation(
                sym,
                historical,
                tech_signals,
                fundamental_data if fundamental_data else {},
            )

            # Entry/Exit levels (reusing SmartEntryExitSystem)
            entry_exit_levels = smart_entry_exit.calculate_entry_exit(
                historical,
                ai_rec.get("action", "HOLD"),
                sr_levels,
                current_price,
                risk_profile="medium",
            )

            best_intraday_entry = entry_exit_levels.get("entry", {}).get("aggressive")
            best_swing_entry = entry_exit_levels.get("entry", {}).get("safe")

            results.append(
                {
                    "symbol": sym,
                    "prior_high": round(prior_high, 2),
                    "prior_low": round(prior_low, 2),
                    "current_price": round(current_price, 2),
                    "best_intraday_entry": round(best_intraday_entry, 2) if best_intraday_entry else None,
                    "best_swing_entry": round(best_swing_entry, 2) if best_swing_entry else None,
                    "action": ai_rec.get("action", "HOLD"),
                    "risk_reward": entry_exit_levels.get("risk_reward"),
                }
            )
        except Exception as e:
            logger.warning(f"Error building watchlist levels for {symbol}: {e}")
            continue

    return results

@router.get("/analysis", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def analysis_page(request: Request, symbol: Optional[str] = None, 
                       asset_type: Optional[str] = "stock",
                       period: Optional[str] = "1y", 
                       interval: Optional[str] = "1d"):
    """Asset analysis page"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = sanitize_user_id(request.cookies.get("user_id") or get_client_identifier(request))
    
    context = get_common_context(
        request,
        user_id,
        "analysis",
        symbol=symbol,
        asset_type=asset_type,
        period=period,
        interval=interval,
        has_analysis=False
    )
    
    if symbol:
        try:
            # Validate inputs
            is_valid, error_msg = validate_symbol(symbol, asset_type)
            if not is_valid:
                context["error"] = error_msg or "Invalid symbol"
                return templates.TemplateResponse("analysis.html", context)
            
            is_valid, error_msg = validate_period(period)
            if not is_valid:
                context["error"] = error_msg or "Invalid period"
                return templates.TemplateResponse("analysis.html", context)
            
            is_valid, error_msg = validate_interval(interval)
            if not is_valid:
                context["error"] = error_msg or "Invalid interval"
                return templates.TemplateResponse("analysis.html", context)
            
            is_valid, error_msg = validate_asset_type(asset_type)
            if not is_valid:
                context["error"] = error_msg or "Invalid asset type"
                return templates.TemplateResponse("analysis.html", context)
            
            symbol = symbol.upper().strip()
            
            # Fetch asset data
            asset_info = asset_fetcher.get_asset_info(symbol, asset_type)
            historical_data = asset_fetcher.get_historical_data(symbol, asset_type, period, interval)
            
            if historical_data.empty:
                context["error"] = f"Could not fetch data for {symbol}. Please check the symbol and asset type."
                return templates.TemplateResponse("analysis.html", context)
            
            # Enhanced Technical Analysis
            enhanced_ta = enhanced_technical(historical_data)
            technical_signals = enhanced_ta.get_technical_signals()
            summary_stats = enhanced_ta.get_summary_statistics()
            technical_with_explanations = enhanced_ta.get_indicators_with_explanations()
            
            # Enhanced Fundamental Analysis (for stocks/ETFs)
            fundamental_data = {}
            if asset_type in ['stock', 'etf']:
                fundamental_data = enhanced_fundamental.analyze_with_summary(symbol)
            
            # Get current price early (needed for predictions)
            current_price = summary_stats.get('current_price', historical_data['Close'].iloc[-1])
            
            # Short-term predictions (5 days) - for backward compatibility
            price_predictions = prediction_engine.predict_price(historical_data, days_ahead=5)
            support_resistance = prediction_engine.predict_support_resistance(historical_data)
            
            # Multi-timeframe predictions (1M, 3M, 6M, 12M, 24M)
            # Fetch news and analyze sentiment
            news_analysis = news_analyzer.get_news_analysis(symbol, days_back=30)
            
            # Generate multi-timeframe predictions
            multi_predictions = multi_timeframe_predictor.predict_multi_timeframe(
                historical_data=historical_data,
                fundamental_data=fundamental_data if fundamental_data else {},
                technical_signals=technical_signals,
                news_sentiment=news_analysis,
                current_price=current_price
            )
            
            # AI Buy/Sell Engine
            ai_recommendation = ai_buy_sell_engine.generate_recommendation(
                symbol,
                historical_data,
                technical_signals,
                fundamental_data if fundamental_data else {}
            )
            
            # Smart Entry & Exit System
            entry_exit = smart_entry_exit.calculate_entry_exit(
                historical_data,
                ai_recommendation.get('action', 'HOLD'),
                support_resistance,
                current_price,
                risk_profile='medium'
            )
            
            # AI Stop Loss Manager
            stop_loss_data = ai_stop_loss_manager.calculate_stop_loss(
                historical_data,
                entry_exit['entry']['aggressive'],
                ai_recommendation.get('action', 'HOLD'),
                support_resistance,
                risk_profile='medium',
                use_trailing=False,
                current_price=current_price
            )
            
            # Risk Management
            risk_calculation = risk_manager.calculate_risk(
                entry_exit['entry']['aggressive'],
                stop_loss_data['stop_loss'],
                account_size=10000,
                risk_percent=2.0
            )
            
            # Swing Trading Analysis - Price-based entry/exit levels
            swing_analyzer = SwingTradingAnalyzer(historical_data)
            swing_trading_plan = swing_analyzer.get_swing_trading_plan(
                current_price=current_price,
                technical_signals=technical_signals,
                support_resistance=support_resistance,
                recommendation=ai_recommendation.get('action', 'HOLD')
            )
            
            # Intraday levels (for same-day traders)
            intraday_levels = swing_analyzer.get_intraday_levels(
                current_price=current_price,
                support=support_resistance.get('support', current_price * 0.95),
                resistance=support_resistance.get('resistance', current_price * 1.05),
                atr=float(historical_data['ATR'].iloc[-1]) if 'ATR' in historical_data.columns and not historical_data['ATR'].isna().iloc[-1] else current_price * 0.02
            )
            
            # Watchlist overview: prior day levels & suggested entries for each watchlist symbol
            watchlist = context.get("watchlist", [])
            watchlist_levels = _build_watchlist_levels(
                watchlist=watchlist,
                asset_type=asset_type,
                user_symbol=symbol,
            )
            
            # Generate Chart with EMA alerts
            chart_gen = ChartGenerator(historical_data, symbol)
            chart_fig = chart_gen.create_main_chart(show_indicators=True, interval=interval)
            chart_html = plotly_fig_to_html(chart_fig)
            ema_alerts = chart_gen.get_ema_alerts()
            
            # Comparison chart (1h vs 1d)
            comparison_chart_html = None
            try:
                data_1h = asset_fetcher.get_historical_data(symbol, asset_type, period="5d", interval="1h")
                data_1d = asset_fetcher.get_historical_data(symbol, asset_type, period="1mo", interval="1d")
                if not data_1h.empty and not data_1d.empty:
                    comparison_chart_gen = ChartGenerator(data_1h, symbol)
                    comparison_fig = comparison_chart_gen.create_comparison_chart(data_1h, data_1d)
                    comparison_chart_html = plotly_fig_to_html(comparison_fig)
            except Exception as e:
                logger.warning(f"Could not create comparison chart: {e}")
            
            # Update context with analysis data
            context.update({
                "has_analysis": True,
                "asset_info": asset_info,
                "technical_signals": technical_signals,
                "technical_explanations": technical_with_explanations,
                "summary_stats": summary_stats,
                "fundamental_data": fundamental_data,
                "price_predictions": price_predictions,
                "support_resistance": support_resistance,
                "recommendation": ai_recommendation,
                "entry_exit": entry_exit,
                "stop_loss_data": stop_loss_data,
                "risk_calculation": risk_calculation,
                "chart_html": chart_html,
                "comparison_chart_html": comparison_chart_html,
                "ema_alerts": ema_alerts,
                "swing_trading_plan": swing_trading_plan,
                "intraday_levels": intraday_levels,
                "multi_predictions": multi_predictions,
                "news_analysis": news_analysis,
                "watchlist_levels": watchlist_levels,
                "has_chart": True
            })
            
        except Exception as e:
            error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
            logger.error(f"Error analyzing {asset_type} {symbol}: {error_msg}")
            if settings.DEBUG:
                logger.error(traceback.format_exc())
            context["error"] = f"Error analyzing {symbol}: {error_msg}"
            context["has_analysis"] = False
    
    # Ensure has_analysis is always defined
    if "has_analysis" not in context:
        context["has_analysis"] = False
    
    try:
        return templates.TemplateResponse("analysis.html", context)
    except Exception as e:
        logger.error(f"Error rendering analysis template: {e}")
        if settings.DEBUG:
            logger.error(traceback.format_exc())
        # Return a simple error page (sanitized)
        from fastapi.responses import HTMLResponse
        error_msg = sanitize_error_message(e, include_details=settings.DEBUG)
        return HTMLResponse(
            content=f"<h1>Error</h1><p>An error occurred. Please try again later.</p>",
            status_code=500
        )

@router.post("/analysis", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def analyze_asset(request: Request, symbol: Optional[str] = Form(None), 
                       asset_type: str = Form("stock"),
                       period: str = Form("1y"), 
                       interval: str = Form("1d")):
    """Analyze asset via POST request"""
    return await analysis_page(request, symbol=symbol, asset_type=asset_type, 
                              period=period, interval=interval)

@router.get("/api/asset/{symbol}/info")
@limiter.limit("60/minute")
async def get_asset_info(request: Request, symbol: str, asset_type: str = "stock"):
    """Get asset information"""
    try:
        symbol = symbol.upper().strip()
        asset_info = asset_fetcher.get_asset_info(symbol, asset_type)
        
        if 'error' in asset_info:
            return JSONResponse(
                status_code=404,
                content={"error": asset_info.get('error', 'Asset not found')}
            )
        
        return JSONResponse(content=asset_info)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
