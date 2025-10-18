"""
Centralized data fetching module for Polygon.io API
Handles all data retrieval for SPY and TSLA
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time


class DataFetcher:
    """
    Centralized data fetching class for efficient API calls to Polygon.io
    Caches data to minimize API calls and optimize performance
    """
    
    def __init__(self, api_key: str):
        """
        Initialize DataFetcher with Polygon.io API key
        
        Args:
            api_key: Polygon.io API key
        """
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.cache = {}
        self.rate_limit_delay = 0.2  # 200ms between requests (Free tier: 5 req/min)
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make API request with rate limiting and error handling
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        if params is None:
            params = {}
        params['apiKey'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str, 
                       timespan: str = "minute", multiplier: int = 1) -> pd.DataFrame:
        """
        Fetch historical stock data
        
        Args:
            symbol: Stock symbol (SPY or TSLA)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timespan: Timespan (minute, hour, day, week, month, quarter, year)
            multiplier: Multiplier for timespan
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"stock_{symbol}_{start_date}_{end_date}_{timespan}_{multiplier}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
        data = self._make_request(endpoint, {"adjusted": "true", "sort": "asc"})
        
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
            df = df.rename(columns={
                'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 
                'v': 'volume', 'vw': 'vwap', 'n': 'transactions'
            })
            self.cache[cache_key] = df
            return df
        
        return pd.DataFrame()
    
    def get_options_chain(self, symbol: str, expiration_date: Optional[str] = None,
                          strike_price: Optional[float] = None) -> pd.DataFrame:
        """
        Fetch options chain for a symbol
        
        Args:
            symbol: Underlying symbol (SPY or TSLA)
            expiration_date: Filter by expiration date (YYYY-MM-DD)
            strike_price: Filter by strike price
            
        Returns:
            DataFrame with options contracts
        """
        cache_key = f"options_{symbol}_{expiration_date}_{strike_price}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        params = {
            "underlying_ticker": symbol,
            "limit": 1000
        }
        
        if expiration_date:
            params["expiration_date"] = expiration_date
        if strike_price:
            params["strike_price"] = strike_price
        
        endpoint = "/v3/reference/options/contracts"
        data = self._make_request(endpoint, params)
        
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            self.cache[cache_key] = df
            return df
        
        return pd.DataFrame()
    
    def get_options_snapshot(self, option_ticker: str) -> Dict:
        """
        Get real-time snapshot of an option contract
        
        Args:
            option_ticker: Option ticker (OCC format)
            
        Returns:
            Dictionary with option snapshot data
        """
        endpoint = f"/v3/snapshot/options/{option_ticker}"
        return self._make_request(endpoint)
    
    def get_historical_iv(self, symbol: str, lookback_days: int = 365) -> pd.DataFrame:
        """
        Calculate historical implied volatility from options data
        
        Args:
            symbol: Stock symbol
            lookback_days: Number of days to look back
            
        Returns:
            DataFrame with IV data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # This is a placeholder - actual IV calculation would require
        # fetching options data and calculating IV from prices
        # For now, return a structure that can be filled with calculated IV
        
        dates = pd.date_range(start_date, end_date, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'iv_30d': None,  # To be calculated from ATM options
            'iv_60d': None,
            'iv_90d': None,
            'iv_mean': None,
            'iv_percentile': None
        })
        
        return df
    
    def get_earnings_dates(self, symbol: str) -> List[str]:
        """
        Get upcoming and historical earnings dates for TSLA
        
        Args:
            symbol: Stock symbol (TSLA)
            
        Returns:
            List of earnings dates
        """
        # Placeholder - would integrate with financial calendar API
        # or scrape from financial websites
        
        # Typical TSLA earnings schedule (quarterly, ~3rd week of month)
        # This should be fetched from an actual API
        
        return [
            "2025-01-22",  # Q4 2024
            "2025-04-23",  # Q1 2025
            "2025-07-23",  # Q2 2025
            "2025-10-22",  # Q3 2025
        ]
    
    def get_intraday_data(self, symbol: str, date: str) -> pd.DataFrame:
        """
        Get high-frequency intraday data (1-minute bars)
        
        Args:
            symbol: Stock symbol
            date: Date (YYYY-MM-DD)
            
        Returns:
            DataFrame with 1-minute OHLCV data
        """
        return self.get_stock_data(symbol, date, date, timespan="minute", multiplier=1)
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol (mock with cached prices for backtesting)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price
        """
        # In production, this would fetch real-time data
        # For backtesting, use configured prices
        from config.config import CURRENT_PRICES
        return CURRENT_PRICES.get(symbol, 0.0)
    
    def get_options_quotes(self, option_ticker: str, start_date: str, 
                          end_date: str) -> pd.DataFrame:
        """
        Get historical options quotes
        
        Args:
            option_ticker: Option ticker (OCC format)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with historical options quotes
        """
        cache_key = f"options_quotes_{option_ticker}_{start_date}_{end_date}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        endpoint = f"/v3/quotes/{option_ticker}"
        params = {
            "timestamp.gte": start_date,
            "timestamp.lte": end_date,
            "order": "asc",
            "limit": 50000
        }
        
        data = self._make_request(endpoint, params)
        
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            self.cache[cache_key] = df
            return df
        
        return pd.DataFrame()
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
    
    def batch_fetch_options_data(self, symbol: str, expiration_dates: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Efficiently batch fetch options data for multiple expiration dates
        
        Args:
            symbol: Stock symbol
            expiration_dates: List of expiration dates
            
        Returns:
            Dictionary mapping expiration dates to options DataFrames
        """
        results = {}
        
        for exp_date in expiration_dates:
            results[exp_date] = self.get_options_chain(symbol, expiration_date=exp_date)
            
        return results
