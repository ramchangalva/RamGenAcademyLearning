"""
Fundamental Analysis Module
Analyzes stock fundamentals with comprehensive error handling
"""
import yfinance as yf
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Performs fundamental analysis on stocks"""
    
    def analyze(self, symbol: str) -> Dict:
        """Perform comprehensive fundamental analysis"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                raise ValueError(f"No fundamental data available for {symbol}")
            
            # Get financials (may fail for some stocks)
            financials = None
            balance_sheet = None
            cashflow = None
            
            try:
                financials = ticker.financials
            except Exception as e:
                logger.warning(f"Could not fetch financials for {symbol}: {e}")
            
            try:
                balance_sheet = ticker.balance_sheet
            except Exception as e:
                logger.warning(f"Could not fetch balance sheet for {symbol}: {e}")
            
            try:
                cashflow = ticker.cashflow
            except Exception as e:
                logger.warning(f"Could not fetch cashflow for {symbol}: {e}")
            
            # Calculate key metrics
            analysis = {
                'symbol': symbol.upper(),
                'company_name': info.get('longName') or info.get('shortName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                
                # Valuation Metrics
                'valuation': {
                    'market_cap': info.get('marketCap', 0),
                    'enterprise_value': info.get('enterpriseValue', 0),
                    'pe_ratio': self._safe_get(info, 'trailingPE', 'N/A'),
                    'forward_pe': self._safe_get(info, 'forwardPE', 'N/A'),
                    'peg_ratio': self._safe_get(info, 'pegRatio', 'N/A'),
                    'price_to_book': self._safe_get(info, 'priceToBook', 'N/A'),
                    'price_to_sales': self._safe_get(info, 'priceToSalesTrailing12Months', 'N/A'),
                    'ev_to_revenue': self._safe_get(info, 'enterpriseToRevenue', 'N/A'),
                    'ev_to_ebitda': self._safe_get(info, 'enterpriseToEbitda', 'N/A'),
                },
                
                # Profitability
                'profitability': {
                    'profit_margin': self._percent_convert(info.get('profitMargins', 0)),
                    'operating_margin': self._percent_convert(info.get('operatingMargins', 0)),
                    'gross_margin': self._percent_convert(info.get('grossMargins', 0)),
                    'roe': self._percent_convert(info.get('returnOnEquity', 0)),
                    'roa': self._percent_convert(info.get('returnOnAssets', 0)),
                    'roic': self._percent_convert(info.get('returnOnInvestedCapital', 0)),
                },
                
                # Financial Health
                'financial_health': {
                    'debt_to_equity': self._safe_get(info, 'debtToEquity', 'N/A'),
                    'current_ratio': self._safe_get(info, 'currentRatio', 'N/A'),
                    'quick_ratio': self._safe_get(info, 'quickRatio', 'N/A'),
                    'cash_per_share': self._safe_get(info, 'totalCashPerShare', 'N/A'),
                    'debt_to_assets': self._safe_get(info, 'debtToAssets', 'N/A'),
                },
                
                # Growth
                'growth': {
                    'revenue_growth': self._percent_convert(info.get('revenueGrowth', 0)),
                    'earnings_growth': self._percent_convert(info.get('earningsGrowth', 0)),
                    'earnings_quarterly_growth': self._percent_convert(info.get('earningsQuarterlyGrowth', 0)),
                },
                
                # Dividends
                'dividends': {
                    'dividend_yield': self._percent_convert(info.get('dividendYield', 0)),
                    'dividend_rate': info.get('dividendRate', 0),
                    'payout_ratio': self._percent_convert(info.get('payoutRatio', 0)),
                },
                
                # Other Metrics
                'other': {
                    'beta': self._safe_get(info, 'beta', 'N/A'),
                    '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                    '52_week_low': info.get('fiftyTwoWeekLow', 0),
                    'avg_volume': info.get('averageVolume', 0),
                    'shares_outstanding': info.get('sharesOutstanding', 0),
                    'float_shares': info.get('floatShares', 0),
                }
            }
            
            # Calculate fundamental score
            analysis['fundamental_score'] = self._calculate_fundamental_score(analysis)
            analysis['fundamental_rating'] = self._get_rating(analysis['fundamental_score'])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing fundamentals for {symbol}: {e}")
            return {
                'symbol': symbol.upper(),
                'error': str(e)
            }
    
    def _safe_get(self, data: dict, key: str, default):
        """Safely get value from dict, handling None and invalid values"""
        value = data.get(key, default)
        if value is None:
            return default
        if isinstance(value, (int, float)) and (value == float('inf') or value == float('-inf')):
            return default
        return value
    
    def _percent_convert(self, value: Optional[float]) -> float:
        """Convert decimal to percentage"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value * 100)
        return 0.0
    
    def _calculate_fundamental_score(self, analysis: Dict) -> float:
        """Calculate overall fundamental score (0-100)"""
        score = 50  # Base score
        
        try:
            # Valuation (lower PE is better, but not too low)
            pe = analysis['valuation'].get('pe_ratio')
            if isinstance(pe, (int, float)) and pe > 0:
                if 10 <= pe <= 25:
                    score += 10
                elif pe < 10:
                    score += 5
                elif pe > 50:
                    score -= 10
            
            # Profitability
            profit_margin = analysis['profitability'].get('profit_margin', 0)
            if profit_margin > 20:
                score += 15
            elif profit_margin > 10:
                score += 10
            elif profit_margin > 5:
                score += 5
            elif profit_margin < 0:
                score -= 15
            
            roe = analysis['profitability'].get('roe', 0)
            if roe > 20:
                score += 10
            elif roe > 15:
                score += 5
            elif roe < 0:
                score -= 10
            
            # Financial Health
            debt_to_equity = analysis['financial_health'].get('debt_to_equity')
            if isinstance(debt_to_equity, (int, float)):
                if debt_to_equity < 0.5:
                    score += 10
                elif debt_to_equity < 1.0:
                    score += 5
                elif debt_to_equity > 2.0:
                    score -= 10
            
            current_ratio = analysis['financial_health'].get('current_ratio')
            if isinstance(current_ratio, (int, float)) and current_ratio > 1.5:
                score += 5
            
            # Growth
            revenue_growth = analysis['growth'].get('revenue_growth', 0)
            if revenue_growth > 20:
                score += 10
            elif revenue_growth > 10:
                score += 5
            elif revenue_growth < -10:
                score -= 10
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score: {e}")
        
        return max(0, min(100, score))
    
    def _get_rating(self, score: float) -> str:
        """Get rating based on score"""
        if score >= 80:
            return 'STRONG_BUY'
        elif score >= 65:
            return 'BUY'
        elif score >= 50:
            return 'HOLD'
        elif score >= 35:
            return 'SELL'
        else:
            return 'STRONG_SELL'
