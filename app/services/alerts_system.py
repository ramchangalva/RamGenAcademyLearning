"""
Custom Alerts System
Alerts for buy/sell signals, stop loss, targets, and indicator crossovers
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AlertsSystem:
    """Custom alerts management system"""
    
    def __init__(self, alerts_file: str = "alerts.json"):
        self.alerts_file = alerts_file
        self.alerts_path = Path(alerts_file)
        self._ensure_alerts_exists()
    
    def _ensure_alerts_exists(self):
        """Ensure alerts file exists"""
        if not self.alerts_path.exists():
            with open(self.alerts_path, 'w') as f:
                json.dump({'alerts': [], 'settings': {}}, f)
    
    def create_alert(self, alert_data: Dict) -> bool:
        """
        Create a new alert
        
        Args:
            alert_data: {
                'symbol': str,
                'alert_type': 'buy_signal', 'sell_signal', 'stop_loss', 'target_reached', 'indicator_crossover', 'news_price',
                'condition': Dict,  # Condition details
                'delivery_methods': List[str],  # 'app', 'email', 'telegram', 'whatsapp'
                'active': bool
            }
        """
        try:
            with open(self.alerts_path, 'r') as f:
                data = json.load(f)
            
            alert_data['id'] = len(data['alerts']) + 1
            alert_data['created_at'] = datetime.now().isoformat()
            alert_data['triggered'] = False
            alert_data['triggered_at'] = None
            
            data['alerts'].append(alert_data)
            
            with open(self.alerts_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return False
    
    def check_alerts(self, symbol: str, current_data: Dict) -> List[Dict]:
        """
        Check if any alerts should be triggered
        
        Args:
            symbol: Stock symbol
            current_data: {
                'price': float,
                'signals': Dict,
                'indicators': Dict
            }
        
        Returns:
            List of triggered alerts
        """
        try:
            with open(self.alerts_path, 'r') as f:
                data = json.load(f)
            
            triggered = []
            
            for alert in data['alerts']:
                if not alert.get('active', True) or alert.get('triggered', False):
                    continue
                
                if alert['symbol'] != symbol:
                    continue
                
                # Check alert condition
                if self._check_condition(alert, current_data):
                    alert['triggered'] = True
                    alert['triggered_at'] = datetime.now().isoformat()
                    triggered.append(alert)
            
            # Save updated alerts
            if triggered:
                with open(self.alerts_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            return triggered
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []
    
    def _check_condition(self, alert: Dict, current_data: Dict) -> bool:
        """Check if alert condition is met"""
        alert_type = alert.get('alert_type')
        condition = alert.get('condition', {})
        
        try:
            if alert_type == 'buy_signal':
                signals = current_data.get('signals', {})
                return signals.get('overall') == 'BULLISH' and signals.get('buy_signals', 0) > 0
            
            elif alert_type == 'sell_signal':
                signals = current_data.get('signals', {})
                return signals.get('overall') == 'BEARISH' and signals.get('sell_signals', 0) > 0
            
            elif alert_type == 'stop_loss':
                price = current_data.get('price', 0)
                stop_loss = condition.get('stop_loss', 0)
                threshold = condition.get('threshold', 0.02)  # 2% default
                return abs(price - stop_loss) / price <= threshold
            
            elif alert_type == 'target_reached':
                price = current_data.get('price', 0)
                target = condition.get('target_price', 0)
                return price >= target * 0.99  # Within 1%
            
            elif alert_type == 'indicator_crossover':
                indicators = current_data.get('indicators', {})
                indicator = condition.get('indicator')
                value = condition.get('value')
                
                if indicator == 'RSI':
                    current_rsi = indicators.get('RSI', 0)
                    if condition.get('direction') == 'above':
                        return current_rsi > value
                    else:
                        return current_rsi < value
                
                elif indicator == 'MACD':
                    macd = indicators.get('MACD', 0)
                    signal = indicators.get('MACD_signal', 0)
                    if condition.get('direction') == 'above':
                        return macd > signal
                    else:
                        return macd < signal
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking condition: {e}")
            return False
    
    def get_alerts(self, symbol: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """Get all alerts, optionally filtered by symbol"""
        try:
            with open(self.alerts_path, 'r') as f:
                data = json.load(f)
            
            alerts = data.get('alerts', [])
            
            if symbol:
                alerts = [a for a in alerts if a.get('symbol') == symbol]
            
            if active_only:
                alerts = [a for a in alerts if a.get('active', True) and not a.get('triggered', False)]
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert"""
        try:
            with open(self.alerts_path, 'r') as f:
                data = json.load(f)
            
            data['alerts'] = [a for a in data['alerts'] if a.get('id') != alert_id]
            
            with open(self.alerts_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            return False
