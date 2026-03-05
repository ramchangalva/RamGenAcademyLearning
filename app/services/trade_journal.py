"""
Trade Journal with AI Feedback
Auto-logs trades and provides AI analysis of trading performance
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)


class TradeJournal:
    """Trade journaling system with AI feedback"""
    
    def __init__(self, journal_file: str = "trade_journal.json"):
        self.journal_file = journal_file
        self.journal_path = Path(journal_file)
        self._ensure_journal_exists()
    
    def _ensure_journal_exists(self):
        """Ensure journal file exists"""
        # Create data directory if it doesn't exist
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.journal_path.exists():
            with open(self.journal_path, 'w') as f:
                json.dump({'trades': [], 'statistics': {}}, f)
    
    def log_trade(self, trade_data: Dict) -> bool:
        """
        Log a trade
        
        Args:
            trade_data: {
                'symbol': str,
                'action': 'BUY' or 'SELL',
                'entry_price': float,
                'exit_price': Optional[float],
                'stop_loss': float,
                'target_price': Optional[float],
                'shares': int,
                'entry_date': str,
                'exit_date': Optional[str],
                'reason': str,
                'result': Optional['WIN' or 'LOSS'],
                'profit_loss': Optional[float]
            }
        """
        try:
            # Load existing journal
            with open(self.journal_path, 'r') as f:
                journal = json.load(f)
            
            # Add trade
            trade_data['id'] = len(journal['trades']) + 1
            trade_data['logged_at'] = datetime.now().isoformat()
            journal['trades'].append(trade_data)
            
            # Update statistics
            journal['statistics'] = self._calculate_statistics(journal['trades'])
            
            # Save
            with open(self.journal_path, 'w') as f:
                json.dump(journal, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
            return False
    
    def get_trades(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all trades"""
        try:
            with open(self.journal_path, 'r') as f:
                journal = json.load(f)
            
            trades = journal.get('trades', [])
            if limit:
                trades = trades[-limit:]
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get trading statistics"""
        try:
            with open(self.journal_path, 'r') as f:
                journal = json.load(f)
            
            return journal.get('statistics', {})
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_ai_feedback(self) -> Dict:
        """
        Get AI-generated feedback on trading performance
        
        Returns:
            {
                'weekly_report': str,
                'mistakes': List[str],
                'strengths': List[str],
                'recommendations': List[str],
                'improvement_areas': List[str]
            }
        """
        try:
            trades = self.get_trades()
            if not trades:
                return {
                    'weekly_report': 'No trades logged yet. Start trading to get AI feedback!',
                    'mistakes': [],
                    'strengths': [],
                    'recommendations': [],
                    'improvement_areas': []
                }
            
            # Analyze recent trades (last 30 days)
            recent_trades = [t for t in trades 
                           if self._is_recent(t.get('entry_date', ''), days=30)]
            
            if not recent_trades:
                return {
                    'weekly_report': 'No recent trades to analyze.',
                    'mistakes': [],
                    'strengths': [],
                    'recommendations': [],
                    'improvement_areas': []
                }
            
            # Calculate metrics
            completed_trades = [t for t in recent_trades if t.get('result')]
            wins = [t for t in completed_trades if t.get('result') == 'WIN']
            losses = [t for t in completed_trades if t.get('result') == 'LOSS']
            
            win_rate = (len(wins) / len(completed_trades) * 100) if completed_trades else 0
            avg_win = np.mean([t.get('profit_loss', 0) for t in wins]) if wins else 0
            avg_loss = np.mean([abs(t.get('profit_loss', 0)) for t in losses]) if losses else 0
            
            # Generate feedback
            mistakes = []
            strengths = []
            recommendations = []
            improvement_areas = []
            
            # Analyze exit patterns
            early_exits = sum(1 for t in wins 
                            if t.get('exit_price') and t.get('target_price') 
                            and t.get('exit_price') < t.get('target_price') * 0.8)
            
            if early_exits > len(wins) * 0.5:
                mistakes.append("Exiting winners too early - Consider partial profits")
                recommendations.append("Use partial profit targets: Take 25% at first target, 50% at second")
            
            # Analyze stop loss hits
            stop_loss_hits = sum(1 for t in losses if t.get('exit_price') == t.get('stop_loss'))
            if stop_loss_hits > 0:
                strengths.append(f"Good risk management - {stop_loss_hits} stop losses respected")
            
            # Win rate analysis
            if win_rate >= 60:
                strengths.append(f"Excellent win rate: {win_rate:.1f}%")
            elif win_rate < 40:
                mistakes.append(f"Low win rate: {win_rate:.1f}% - Review entry criteria")
                improvement_areas.append("Improve entry timing and signal quality")
            
            # Risk/Reward analysis
            if avg_win > 0 and avg_loss > 0:
                risk_reward = avg_win / avg_loss
                if risk_reward >= 2.0:
                    strengths.append(f"Good risk/reward ratio: {risk_reward:.2f}")
                elif risk_reward < 1.0:
                    mistakes.append(f"Poor risk/reward: {risk_reward:.2f} - Risking more than potential reward")
                    recommendations.append("Aim for minimum 2:1 risk/reward ratio")
            
            # Generate weekly report
            weekly_report = self._generate_weekly_report(
                recent_trades, win_rate, avg_win, avg_loss, wins, losses
            )
            
            return {
                'weekly_report': weekly_report,
                'mistakes': mistakes,
                'strengths': strengths,
                'recommendations': recommendations,
                'improvement_areas': improvement_areas,
                'metrics': {
                    'total_trades': len(recent_trades),
                    'completed_trades': len(completed_trades),
                    'win_rate': round(win_rate, 1),
                    'avg_win': round(avg_win, 2),
                    'avg_loss': round(avg_loss, 2),
                    'profit_factor': round(avg_win / avg_loss, 2) if avg_loss > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating AI feedback: {e}")
            return {
                'weekly_report': f'Error generating feedback: {str(e)}',
                'mistakes': [],
                'strengths': [],
                'recommendations': [],
                'improvement_areas': []
            }
    
    def _calculate_statistics(self, trades: List[Dict]) -> Dict:
        """Calculate trading statistics"""
        try:
            completed = [t for t in trades if t.get('result')]
            if not completed:
                return {}
            
            wins = [t for t in completed if t.get('result') == 'WIN']
            losses = [t for t in completed if t.get('result') == 'LOSS']
            
            total_profit = sum(t.get('profit_loss', 0) for t in wins)
            total_loss = sum(abs(t.get('profit_loss', 0)) for t in losses)
            
            return {
                'total_trades': len(trades),
                'completed_trades': len(completed),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': round(len(wins) / len(completed) * 100, 1) if completed else 0,
                'total_profit': round(total_profit, 2),
                'total_loss': round(total_loss, 2),
                'net_pnl': round(total_profit - total_loss, 2),
                'avg_win': round(np.mean([t.get('profit_loss', 0) for t in wins]), 2) if wins else 0,
                'avg_loss': round(np.mean([abs(t.get('profit_loss', 0)) for t in losses]), 2) if losses else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def _is_recent(self, date_str: str, days: int = 30) -> bool:
        """Check if date is within recent days"""
        try:
            if not date_str:
                return False
            trade_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            days_ago = datetime.now() - timedelta(days=days)
            return trade_date >= days_ago
        except:
            return False
    
    def _generate_weekly_report(self, trades: List[Dict], win_rate: float,
                               avg_win: float, avg_loss: float,
                               wins: List[Dict], losses: List[Dict]) -> str:
        """Generate weekly performance report"""
        report = []
        report.append(f"Weekly Trading Report - {len(trades)} trades analyzed\n")
        report.append(f"Win Rate: {win_rate:.1f}% ({len(wins)} wins, {len(losses)} losses)")
        
        if avg_win > 0 and avg_loss > 0:
            report.append(f"Average Win: ${avg_win:.2f} | Average Loss: ${avg_loss:.2f}")
            risk_reward = avg_win / avg_loss
            report.append(f"Risk/Reward Ratio: {risk_reward:.2f}")
        
        total_pnl = sum(t.get('profit_loss', 0) for t in trades if t.get('profit_loss'))
        report.append(f"Total P&L: ${total_pnl:.2f}")
        
        return "\n".join(report)
