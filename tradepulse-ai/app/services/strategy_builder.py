"""
Strategy Builder with Backtesting
Visual rule builder for trading strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StrategyBuilder:
    """Strategy builder and backtesting system"""
    
    def __init__(self):
        from app.services.technical_analyzer import TechnicalAnalyzer
        
        self.technical_analyzer = TechnicalAnalyzer
    
    def build_strategy(self, rules: List[Dict]) -> Dict:
        """
        Build a trading strategy from rules
        
        Args:
            rules: [
                {
                    'condition': 'IF',
                    'indicator': 'RSI',
                    'operator': '<',
                    'value': 30,
                    'logic': 'AND' or 'OR'
                },
                ...
            ]
        
        Returns:
            {
                'strategy_id': str,
                'rules': List[Dict],
                'entry_conditions': List[Dict],
                'exit_conditions': List[Dict]
            }
        """
        try:
            strategy_id = f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Separate entry and exit conditions
            entry_conditions = []
            exit_conditions = []
            
            for rule in rules:
                if rule.get('type') == 'entry':
                    entry_conditions.append(rule)
                elif rule.get('type') == 'exit':
                    exit_conditions.append(rule)
                else:
                    entry_conditions.append(rule)  # Default to entry
            
            return {
                'strategy_id': strategy_id,
                'rules': rules,
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error building strategy: {e}")
            return {}
    
    def backtest_strategy(self, strategy: Dict, data: pd.DataFrame,
                         initial_capital: float = 10000) -> Dict:
        """
        Backtest a strategy on historical data
        
        Returns:
            {
                'total_return': float,
                'win_rate': float,
                'total_trades': int,
                'sharpe_ratio': float,
                'max_drawdown': float,
                'trades': List[Dict]
            }
        """
        try:
            if data.empty or len(data) < 50:
                return {'error': 'Insufficient data for backtesting'}
            
            # Analyze data
            ta = self.technical_analyzer(data)
            signals = ta.get_technical_signals()
            
            # Simulate trades
            capital = initial_capital
            trades = []
            positions = []
            equity_curve = [capital]
            
            entry_conditions = strategy.get('entry_conditions', [])
            exit_conditions = strategy.get('exit_conditions', [])
            
            for i in range(20, len(data)):
                current_data = data.iloc[:i+1]
                current_price = data['Close'].iloc[i]
                
                # Check entry conditions
                if self._check_conditions(entry_conditions, current_data, i):
                    # Enter position
                    position_size = capital * 0.1  # 10% of capital per trade
                    shares = int(position_size / current_price)
                    
                    if shares > 0:
                        positions.append({
                            'entry_price': current_price,
                            'shares': shares,
                            'entry_index': i,
                            'entry_date': data.index[i] if hasattr(data.index[i], 'isoformat') else str(data.index[i])
                        })
                        capital -= shares * current_price
                
                # Check exit conditions for open positions
                for pos in positions[:]:
                    if self._check_conditions(exit_conditions, current_data, i, pos):
                        # Exit position
                        profit_loss = (current_price - pos['entry_price']) * pos['shares']
                        capital += pos['shares'] * current_price
                        
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': current_price,
                            'shares': pos['shares'],
                            'profit_loss': profit_loss,
                            'return_pct': (profit_loss / (pos['entry_price'] * pos['shares'])) * 100
                        })
                        
                        positions.remove(pos)
                
                equity_curve.append(capital)
            
            # Close remaining positions
            if positions and len(data) > 0:
                final_price = data['Close'].iloc[-1]
                for pos in positions:
                    profit_loss = (final_price - pos['entry_price']) * pos['shares']
                    capital += pos['shares'] * final_price
                    trades.append({
                        'entry_price': pos['entry_price'],
                        'exit_price': final_price,
                        'shares': pos['shares'],
                        'profit_loss': profit_loss,
                        'return_pct': (profit_loss / (pos['entry_price'] * pos['shares'])) * 100
                    })
            
            # Calculate metrics
            total_return = ((capital - initial_capital) / initial_capital) * 100
            wins = [t for t in trades if t['profit_loss'] > 0]
            win_rate = (len(wins) / len(trades) * 100) if trades else 0
            
            # Sharpe ratio
            returns = [t['return_pct'] for t in trades]
            sharpe = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
            
            # Max drawdown
            equity_array = np.array(equity_curve)
            running_max = np.maximum.accumulate(equity_array)
            drawdown = (equity_array - running_max) / running_max * 100
            max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
            
            return {
                'total_return': round(total_return, 2),
                'win_rate': round(win_rate, 1),
                'total_trades': len(trades),
                'wins': len(wins),
                'losses': len(trades) - len(wins),
                'sharpe_ratio': round(sharpe, 2),
                'max_drawdown': round(max_drawdown, 2),
                'final_capital': round(capital, 2),
                'initial_capital': initial_capital,
                'trades': trades[-10:] if len(trades) > 10 else trades  # Last 10 trades
            }
            
        except Exception as e:
            logger.error(f"Error backtesting strategy: {e}")
            return {'error': str(e)}
    
    def _check_conditions(self, conditions: List[Dict], data: pd.DataFrame,
                          index: int, position: Optional[Dict] = None) -> bool:
        """Check if conditions are met"""
        try:
            if not conditions:
                return False
            
            ta = self.technical_analyzer(data)
            signals = ta.get_technical_signals()
            indicators = signals.get('indicators', {})
            
            results = []
            logic_operator = 'AND'  # Default
            
            for condition in conditions:
                indicator = condition.get('indicator')
                operator = condition.get('operator')
                value = condition.get('value')
                logic = condition.get('logic', 'AND')
                
                if indicator == 'RSI':
                    current_value = indicators.get('RSI', 50)
                elif indicator == 'MACD':
                    current_value = indicators.get('MACD', 0)
                elif indicator == 'Price':
                    current_value = data['Close'].iloc[-1]
                else:
                    current_value = 0
                
                # Evaluate condition
                if operator == '<':
                    result = current_value < value
                elif operator == '>':
                    result = current_value > value
                elif operator == '==':
                    result = abs(current_value - value) < 0.01
                else:
                    result = False
                
                results.append(result)
                if logic in ['OR', 'AND']:
                    logic_operator = logic
            
            # Combine results
            if logic_operator == 'AND':
                return all(results)
            else:
                return any(results)
                
        except Exception as e:
            logger.error(f"Error checking conditions: {e}")
            return False
    
    def optimize_parameters(self, strategy: Dict, data: pd.DataFrame,
                           parameter_ranges: Dict) -> Dict:
        """
        Optimize strategy parameters using backtesting
        
        Args:
            parameter_ranges: {
                'RSI': {'min': 20, 'max': 40, 'step': 5},
                'MACD': {'min': -1, 'max': 1, 'step': 0.1}
            }
        """
        try:
            best_strategy = strategy.copy()
            best_return = -float('inf')
            best_params = {}
            
            # Simple grid search (can be optimized)
            for rsi_val in range(parameter_ranges.get('RSI', {}).get('min', 20),
                               parameter_ranges.get('RSI', {}).get('max', 40) + 1,
                               parameter_ranges.get('RSI', {}).get('step', 5)):
                
                # Update strategy with new parameter
                updated_strategy = strategy.copy()
                for rule in updated_strategy.get('entry_conditions', []):
                    if rule.get('indicator') == 'RSI':
                        rule['value'] = rsi_val
                
                # Backtest
                result = self.backtest_strategy(updated_strategy, data)
                
                if result.get('total_return', -100) > best_return:
                    best_return = result['total_return']
                    best_params = {'RSI': rsi_val}
                    best_strategy = updated_strategy
            
            return {
                'best_parameters': best_params,
                'best_return': round(best_return, 2),
                'optimized_strategy': best_strategy
            }
            
        except Exception as e:
            logger.error(f"Error optimizing parameters: {e}")
            return {'error': str(e)}
