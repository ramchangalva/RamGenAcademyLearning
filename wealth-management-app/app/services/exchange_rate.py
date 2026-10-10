"""
Exchange rate service for currency conversion (configurable pairs).
"""
import httpx
from typing import Optional
from datetime import datetime, timedelta
from app.core.config import settings
import json


class ExchangeRateService:
    """Service for fetching and caching exchange rates"""
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    async def get_exchange_rate(self, from_currency: str = "USD", to_currency: str = "INR") -> float:
        """
        Get exchange rate between currencies
        Returns rate to convert from_currency to to_currency
        """
        cache_key = f"{from_currency}_{to_currency}"
        now = datetime.utcnow()
        
        # Check cache
        if cache_key in self.cache:
            if now < self.cache_expiry.get(cache_key, datetime.min):
                return self.cache[cache_key]
        
        try:
            # Try primary API (exchangerate-api.com - free, no key required)
            if from_currency == "USD":
                url = settings.EXCHANGE_RATE_API_URL
            else:
                # For other base currencies, adjust URL
                url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if to_currency in data.get("rates", {}):
                    rate = data["rates"][to_currency]
                    self.cache[cache_key] = rate
                    self.cache_expiry[cache_key] = now + self.cache_duration
                    return rate
                else:
                    raise ValueError(f"Currency {to_currency} not found in response")
        
        except Exception as e:
            # Fallback to cached value if available
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Fallback rate (should be updated manually if API fails)
            print(f"Warning: Exchange rate API failed: {e}. Using fallback rate.")
            if from_currency == "USD" and to_currency == "INR":
                return 83.0  # Fallback USD to INR rate
            elif from_currency == "INR" and to_currency == "USD":
                return 1 / 83.0
            else:
                return 1.0
    
    async def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount from one currency to another"""
        if from_currency == to_currency:
            return amount
        
        rate = await self.get_exchange_rate(from_currency, to_currency)
        return amount * rate
    
    def get_cached_rate(self, from_currency: str = "USD", to_currency: str = "INR") -> Optional[float]:
        """Get cached exchange rate without API call"""
        cache_key = f"{from_currency}_{to_currency}"
        return self.cache.get(cache_key)


# Global instance
exchange_rate_service = ExchangeRateService()
