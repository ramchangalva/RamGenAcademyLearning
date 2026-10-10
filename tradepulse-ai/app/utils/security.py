"""
Enhanced Security Utilities
Includes encryption, CSRF protection, input validation
"""
import hashlib
import hmac
import secrets
import base64
from typing import Optional, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    """Enhanced security manager with encryption and CSRF protection"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self._fernet = self._init_fernet()
    
    def _init_fernet(self) -> Optional[Fernet]:
        """Initialize Fernet encryption"""
        try:
            # Derive key from secret
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'tradepulse_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
            return Fernet(key)
        except Exception as e:
            logger.error(f"Error initializing encryption: {e}")
            return None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self._fernet:
            return data  # Fallback to plain text if encryption fails
        try:
            return self._fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self._fernet:
            return encrypted_data
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, session_token)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return {
            'hash': password_hash.hex(),
            'salt': salt
        }
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password"""
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(new_hash.hex(), password_hash)
    
    def sanitize_input(self, input_str: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not isinstance(input_str, str):
            return ""
        # Remove potentially dangerous characters
        sanitized = input_str.strip()[:max_length]
        # Remove script tags and other HTML
        import re
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        return sanitized
    
    def validate_symbol(self, symbol: str, asset_type: str = 'stock') -> bool:
        """Validate asset symbol"""
        import re
        if not symbol or len(symbol) > 20:
            return False
        
        # Basic validation - alphanumeric and some special chars
        if asset_type == 'crypto':
            # Crypto: BTC, ETH, etc. or BTC-USD format
            return bool(re.match(r'^[A-Z0-9-]+$', symbol.upper()))
        elif asset_type == 'commodity':
            # Commodities: GC=F, CL=F, etc.
            return bool(re.match(r'^[A-Z0-9=]+$', symbol.upper()))
        else:
            # Stocks/ETFs: alphanumeric
            return bool(re.match(r'^[A-Z0-9]+$', symbol.upper()))
