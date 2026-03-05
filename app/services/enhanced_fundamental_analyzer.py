"""
Enhanced Fundamental Analysis Engine with AI Summaries
Provides plain English summaries of company fundamentals
"""
from app.services.fundamental_analyzer import FundamentalAnalyzer
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class EnhancedFundamentalAnalyzer(FundamentalAnalyzer):
    """Enhanced fundamental analyzer with AI summaries"""
    
    def analyze_with_summary(self, symbol: str) -> Dict:
        """Perform fundamental analysis with AI-generated summary"""
        try:
            # Get base analysis
            analysis = self.analyze(symbol)
            
            if 'error' in analysis:
                return analysis
            
            # Generate AI summary
            ai_summary = self._generate_ai_summary(analysis)
            analysis['ai_summary'] = ai_summary
            
            # Valuation assessment
            valuation_assessment = self._assess_valuation(analysis)
            analysis['valuation_assessment'] = valuation_assessment
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in enhanced fundamental analysis: {e}")
            return {'symbol': symbol.upper(), 'error': str(e)}
    
    def _generate_ai_summary(self, analysis: Dict) -> str:
        """Generate plain English AI summary"""
        try:
            summary_parts = []
            
            # Company info
            company_name = analysis.get('company_name', 'Company')
            sector = analysis.get('sector', 'N/A')
            summary_parts.append(f"{company_name} operates in the {sector} sector.")
            
            # Valuation
            pe = analysis['valuation'].get('pe_ratio')
            if isinstance(pe, (int, float)) and pe > 0:
                if pe < 15:
                    summary_parts.append("The stock appears undervalued based on P/E ratio.")
                elif pe > 30:
                    summary_parts.append("The stock appears overvalued with a high P/E ratio.")
                else:
                    summary_parts.append("Valuation metrics suggest fair pricing.")
            
            # Profitability
            profit_margin = analysis['profitability'].get('profit_margin', 0)
            roe = analysis['profitability'].get('roe', 0)
            
            if profit_margin > 20 and roe > 20:
                summary_parts.append("Strong profitability with high profit margins and return on equity.")
            elif profit_margin < 5 or roe < 10:
                summary_parts.append("Profitability metrics are concerning - low margins or returns.")
            else:
                summary_parts.append("Moderate profitability metrics.")
            
            # Financial health
            debt_to_equity = analysis['financial_health'].get('debt_to_equity')
            if isinstance(debt_to_equity, (int, float)):
                if debt_to_equity < 0.5:
                    summary_parts.append("Strong financial health with low debt levels.")
                elif debt_to_equity > 2.0:
                    summary_parts.append("High debt levels raise concerns about financial stability.")
                else:
                    summary_parts.append("Moderate debt levels.")
            
            # Growth
            revenue_growth = analysis['growth'].get('revenue_growth', 0)
            if revenue_growth > 20:
                summary_parts.append(f"Strong revenue growth ({revenue_growth:.1f}%) indicates expanding business.")
            elif revenue_growth < -10:
                summary_parts.append(f"Declining revenue ({revenue_growth:.1f}%) is a red flag.")
            else:
                summary_parts.append("Moderate revenue growth.")
            
            # Overall assessment
            score = analysis.get('fundamental_score', 50)
            rating = analysis.get('fundamental_rating', 'HOLD')
            
            if rating in ['STRONG_BUY', 'BUY']:
                summary_parts.append(f"Overall: Strong fundamentals (Score: {score}/100) suggest good investment potential.")
            elif rating in ['STRONG_SELL', 'SELL']:
                summary_parts.append(f"Overall: Weak fundamentals (Score: {score}/100) suggest caution.")
            else:
                summary_parts.append(f"Overall: Mixed fundamentals (Score: {score}/100) - neutral outlook.")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return "Unable to generate summary at this time."
    
    def _assess_valuation(self, analysis: Dict) -> Dict:
        """Assess if stock is undervalued, fair, or overvalued"""
        try:
            pe = analysis['valuation'].get('pe_ratio')
            pb = analysis['valuation'].get('price_to_book')
            peg = analysis['valuation'].get('peg_ratio')
            
            signals = []
            score = 0
            
            # P/E assessment
            if isinstance(pe, (int, float)) and pe > 0:
                if pe < 15:
                    signals.append('UNDERVALUED_PE')
                    score += 1
                elif pe > 30:
                    signals.append('OVERVALUED_PE')
                    score -= 1
            
            # P/B assessment
            if isinstance(pb, (int, float)) and pb > 0:
                if pb < 1.5:
                    signals.append('UNDERVALUED_PB')
                    score += 1
                elif pb > 3.0:
                    signals.append('OVERVALUED_PB')
                    score -= 1
            
            # PEG assessment
            if isinstance(peg, (int, float)) and peg > 0:
                if peg < 1.0:
                    signals.append('UNDERVALUED_PEG')
                    score += 1
                elif peg > 2.0:
                    signals.append('OVERVALUED_PEG')
                    score -= 1
            
            # Determine overall valuation
            if score >= 2:
                valuation = 'UNDERVALUED'
                message = 'Stock appears undervalued based on multiple metrics'
            elif score <= -2:
                valuation = 'OVERVALUED'
                message = 'Stock appears overvalued based on multiple metrics'
            else:
                valuation = 'FAIR'
                message = 'Stock appears fairly valued'
            
            return {
                'valuation': valuation,
                'message': message,
                'signals': signals,
                'score': score
            }
            
        except Exception as e:
            logger.error(f"Error assessing valuation: {e}")
            return {'valuation': 'UNKNOWN', 'message': 'Unable to assess valuation'}
