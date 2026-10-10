"""Trade Journal Routes"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Form
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from datetime import datetime

from app.utils.rate_limiting import get_client_identifier
from app.utils.template_context import get_common_context
from app.services.trade_journal import TradeJournal

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize trade journal (per-user)
def get_trade_journal(user_id: str) -> TradeJournal:
    """Get trade journal instance for user"""
    journal_file = f"data/trade_journal_{user_id}.json"
    return TradeJournal(journal_file=journal_file)

@router.get("/trade-journal", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def trade_journal_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user_id = request.cookies.get("user_id") or get_client_identifier(request)
    context = get_common_context(request, user_id, "trade-journal")
    
    # Load trades and statistics
    journal = get_trade_journal(user_id)
    trades = journal.get_trades()
    statistics = journal.get_statistics()
    ai_feedback = journal.get_ai_feedback()
    
    context.update({
        "trades": trades,
        "statistics": statistics,
        "ai_feedback": ai_feedback
    })
    
    return templates.TemplateResponse("trade_journal.html", context)

@router.post("/api/trade-journal/add")
@limiter.limit("30/minute")
async def add_trade(request: Request,
                   symbol: str = Form(...),
                   entry_price: float = Form(...),
                   exit_price: Optional[float] = Form(None),
                   quantity: float = Form(...),
                   action: str = Form("BUY"),
                   entry_date: Optional[str] = Form(None),
                   exit_date: Optional[str] = Form(None),
                   stop_loss: Optional[float] = Form(None),
                   target_price: Optional[float] = Form(None),
                   reason: Optional[str] = Form("")):
    """Add a trade to the journal"""
    try:
        user_id = request.cookies.get("user_id") or get_client_identifier(request)
        journal = get_trade_journal(user_id)
        
        # Calculate profit/loss if exit price provided
        profit_loss = None
        result = None
        if exit_price:
            if action == "BUY":
                profit_loss = (exit_price - entry_price) * quantity
            else:  # SELL
                profit_loss = (entry_price - exit_price) * quantity
            
            result = "WIN" if profit_loss > 0 else "LOSS" if profit_loss < 0 else "BREAKEVEN"
        
        trade_data = {
            'symbol': symbol.upper(),
            'action': action,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'stop_loss': stop_loss or entry_price * 0.95 if action == "BUY" else entry_price * 1.05,
            'target_price': target_price or entry_price * 1.05 if action == "BUY" else entry_price * 0.95,
            'shares': int(quantity),
            'entry_date': entry_date or datetime.now().isoformat(),
            'exit_date': exit_date,
            'reason': reason or f"{action} {symbol} at ${entry_price:.2f}",
            'result': result,
            'profit_loss': profit_loss
        }
        
        success = journal.log_trade(trade_data)
        
        if success:
            # Return updated trades and statistics
            trades = journal.get_trades(limit=10)
            statistics = journal.get_statistics()
            
            return JSONResponse(content={
                'success': True,
                'message': 'Trade logged successfully',
                'trades': trades,
                'statistics': statistics
            })
        else:
            return JSONResponse(
                status_code=500,
                content={'success': False, 'error': 'Failed to save trade'}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )

@router.get("/api/trade-journal/trades")
@limiter.limit("60/minute")
async def get_trades(request: Request):
    """Get all trades for the user"""
    try:
        user_id = request.cookies.get("user_id") or get_client_identifier(request)
        journal = get_trade_journal(user_id)
        trades = journal.get_trades()
        statistics = journal.get_statistics()
        ai_feedback = journal.get_ai_feedback()
        
        return JSONResponse(content={
            'trades': trades,
            'statistics': statistics,
            'ai_feedback': ai_feedback
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )
