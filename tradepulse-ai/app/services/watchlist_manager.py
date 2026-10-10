"""
Watchlist Manager - Per-user stock watchlist management
Uses session-based storage for per-user watchlists
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# File-based storage for watchlists (in production, use database)
WATCHLIST_DIR = "data"
WATCHLIST_FILE = os.path.join(WATCHLIST_DIR, "watchlists.json")


class WatchlistManager:
    """Manages per-user stock watchlists"""
    
    def __init__(self):
        """Initialize watchlist manager"""
        self._ensure_data_dir()
        self._watchlists = self._load_watchlists()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(WATCHLIST_DIR):
            os.makedirs(WATCHLIST_DIR, exist_ok=True)
    
    def _load_watchlists(self) -> Dict:
        """Load watchlists from file"""
        try:
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading watchlists: {e}")
            return {}
    
    def _save_watchlists(self):
        """Save watchlists to file"""
        try:
            with open(WATCHLIST_FILE, 'w') as f:
                json.dump(self._watchlists, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving watchlists: {e}")
    
    def _get_user_id(self, session_id: str) -> str:
        """Get or create user ID from session"""
        if not session_id:
            # Generate a temporary session ID (in production, use proper session management)
            import uuid
            return str(uuid.uuid4())
        
        # Sanitize user ID to prevent path traversal
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', str(session_id))[:100]
        return sanitized if sanitized else str(uuid.uuid4())
    
    def get_watchlist(self, user_id: str) -> List[str]:
        """Get user's watchlist"""
        user_id = self._get_user_id(user_id)
        if user_id not in self._watchlists:
            self._watchlists[user_id] = {
                'stocks': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        return self._watchlists[user_id].get('stocks', [])
    
    def add_stock(self, user_id: str, symbol: str) -> bool:
        """Add stock to user's watchlist"""
        try:
            user_id = self._get_user_id(user_id)
            symbol = symbol.upper().strip()
            
            # Validate symbol length and format
            if not symbol or len(symbol) > 20:
                logger.warning(f"Invalid symbol: {symbol}")
                return False
            
            # Validate symbol format (alphanumeric only)
            import re
            if not re.match(r'^[A-Z0-9]+$', symbol):
                logger.warning(f"Invalid symbol format: {symbol}")
                return False
            
            if user_id not in self._watchlists:
                self._watchlists[user_id] = {
                    'stocks': [],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            
            # Limit watchlist size
            if len(self._watchlists[user_id]['stocks']) >= 50:
                logger.warning(f"Watchlist full for user {user_id}")
                return False
            
            if symbol not in self._watchlists[user_id]['stocks']:
                self._watchlists[user_id]['stocks'].append(symbol)
                self._watchlists[user_id]['updated_at'] = datetime.now().isoformat()
                self._save_watchlists()
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding stock to watchlist: {e}")
            return False
    
    def remove_stock(self, user_id: str, symbol: str) -> bool:
        """Remove stock from user's watchlist"""
        try:
            user_id = self._get_user_id(user_id)
            symbol = symbol.upper().strip()
            
            if user_id in self._watchlists:
                if symbol in self._watchlists[user_id]['stocks']:
                    self._watchlists[user_id]['stocks'].remove(symbol)
                    self._watchlists[user_id]['updated_at'] = datetime.now().isoformat()
                    self._save_watchlists()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error removing stock from watchlist: {e}")
            return False
    
    def clear_watchlist(self, user_id: str) -> bool:
        """Clear user's watchlist"""
        try:
            user_id = self._get_user_id(user_id)
            if user_id in self._watchlists:
                self._watchlists[user_id]['stocks'] = []
                self._watchlists[user_id]['updated_at'] = datetime.now().isoformat()
                self._save_watchlists()
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing watchlist: {e}")
            return False
    
    def get_watchlist_info(self, user_id: str) -> Dict:
        """Get watchlist information"""
        user_id = self._get_user_id(user_id)
        stocks = self.get_watchlist(user_id)
        return {
            'stocks': stocks,
            'count': len(stocks),
            'user_id': user_id
        }
