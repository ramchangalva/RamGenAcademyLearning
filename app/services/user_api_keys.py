"""
User API Key Manager
Stores and retrieves user-specific API keys for AI providers
"""
import json
import os
from typing import Dict, Optional
import logging

from app.core.config import settings
from app.utils.security import SecurityManager

logger = logging.getLogger(__name__)


class UserAPIKeyManager:
    """Manages user-specific API keys for AI providers"""
    
    def __init__(self, data_dir: str = "data"):
        # Prevent path traversal
        if not data_dir or ".." in data_dir or "/" in data_dir.replace(os.sep, ""):
            data_dir = "data"
        
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        self.keys_file = os.path.join(self.data_dir, "user_api_keys.json")
        
        # Initialize security manager for encryption
        self.security_manager = SecurityManager(settings.SECRET_KEY)
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from file"""
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    self.keys = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding {self.keys_file}. Initializing empty keys.")
                self.keys = {}
        else:
            self.keys = {}
    
    def _save_keys(self):
        """Save API keys to file"""
        try:
            with open(self.keys_file, 'w') as f:
                json.dump(self.keys, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving API keys: {e}")
    
    def set_api_key(self, user_id: str, provider: str, api_key: str, base_url: Optional[str] = None):
        """Set API key for a user and provider"""
        # Validate inputs
        if not user_id or not provider or not api_key:
            raise ValueError("user_id, provider, and api_key are required")
        
        # Sanitize inputs
        user_id = str(user_id).strip()[:100]  # Limit length
        provider = str(provider).strip()[:50]
        api_key = str(api_key).strip()[:500]  # Reasonable API key length limit
        
        # Validate provider name (alphanumeric and hyphens only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', provider):
            raise ValueError("Invalid provider name")
        
        if user_id not in self.keys:
            self.keys[user_id] = {}
        
        # Encrypt API key if encryption is enabled
        if settings.ENCRYPT_USER_DATA:
            encrypted_key = self.security_manager.encrypt_data(api_key)
            if encrypted_key:
                api_key = encrypted_key
            else:
                logger.warning("Encryption failed, storing API key in plaintext")
        
        # Sanitize base_url if provided
        sanitized_base_url = None
        if base_url:
            sanitized_base_url = str(base_url).strip()[:500]
            # Basic URL validation
            if not (sanitized_base_url.startswith('http://') or sanitized_base_url.startswith('https://')):
                logger.warning(f"Invalid base_url format: {sanitized_base_url}")
                sanitized_base_url = None
        
        self.keys[user_id][provider] = {
            'api_key': api_key,
            'base_url': sanitized_base_url,
            'encrypted': settings.ENCRYPT_USER_DATA
        }
        self._save_keys()
        return True
    
    def get_api_key(self, user_id: str, provider: str) -> Optional[Dict]:
        """Get API key for a user and provider"""
        if not user_id or not provider:
            return None
        
        if user_id in self.keys and provider in self.keys[user_id]:
            key_data = self.keys[user_id][provider].copy()
            
            # Decrypt if encrypted
            if key_data.get('encrypted', False) and settings.ENCRYPT_USER_DATA:
                decrypted_key = self.security_manager.decrypt_data(key_data['api_key'])
                if decrypted_key:
                    key_data['api_key'] = decrypted_key
                    key_data['encrypted'] = False
            
            return key_data
        return None
    
    def get_all_keys(self, user_id: str) -> Dict:
        """Get all API keys for a user (decrypted)"""
        if not user_id:
            return {}
        
        user_keys = self.keys.get(user_id, {}).copy()
        
        # Decrypt all keys
        if settings.ENCRYPT_USER_DATA:
            for provider, key_data in user_keys.items():
                if key_data.get('encrypted', False):
                    decrypted_key = self.security_manager.decrypt_data(key_data['api_key'])
                    if decrypted_key:
                        key_data['api_key'] = decrypted_key
                        key_data['encrypted'] = False
        
        return user_keys
    
    def delete_api_key(self, user_id: str, provider: str) -> bool:
        """Delete API key for a user and provider"""
        if user_id in self.keys and provider in self.keys[user_id]:
            del self.keys[user_id][provider]
            self._save_keys()
            return True
        return False
    
    def has_api_key(self, user_id: str, provider: str) -> bool:
        """Check if user has API key for provider"""
        return user_id in self.keys and provider in self.keys[user_id] and bool(self.keys[user_id][provider].get('api_key'))
