"""Bollinger Band Squeeze Strategy (0DTE) - Trade volatility expansion"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class BollingerSqueezeStrategy(BaseStrategy):
    """Trade breakouts from Bollinger Band squeezes"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.bb_period = config.parameters.get('bb_period', 20)
        self.bb_std = config.parameters.get('bb_std', 2.0)
        self.squeeze_threshold = config.parameters.get('squeeze_threshold', 0.01)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        if len(market_data) < self.bb_period:
            return []
        
        bb_upper, bb_lower, bb_mid = self._calculate_bollinger_bands(market_data['close'])
        bb_width = (bb_upper - bb_lower) / bb_mid
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        signals = []
        
        # Entry: Breakout from squeeze
        if not self.positions and bb_width < self.squeeze_threshold and current_time.hour >= 10:
            if current_price > bb_upper:
                strike = self._get_otm_strike(current_price, 'call', 0.015)
                signals.append({
                    'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call',
                    'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                    'price': current_price * 0.015, 'signal_type': 'ENTRY_BB_BREAKOUT_BULLISH'
                })
            elif current_price < bb_lower:
                strike = self._get_otm_strike(current_price, 'put', 0.015)
                signals.append({
                    'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'put',
                    'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                    'price': current_price * 0.015, 'signal_type': 'ENTRY_BB_BREAKOUT_BEARISH'
                })
        
        # Exit logic
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (current_time.hour == 15 and current_time.minute >= 45):
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def _calculate_bollinger_bands(self, prices):
        sma = prices.rolling(window=self.bb_period).mean().iloc[-1]
        std = prices.rolling(window=self.bb_period).std().iloc[-1]
        return sma + (self.bb_std * std), sma - (self.bb_std * std), sma
    
    def get_entry_conditions(self) -> Dict:
        return {'bb_squeeze_threshold': self.squeeze_threshold, 'breakout_trigger': 'Price outside bands'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '3:45 PM'}
    
    def _get_otm_strike(self, price: float, option_type: str, otm_pct: float) -> float:
        target = price * (1 + otm_pct) if option_type == 'call' else price * (1 - otm_pct)
        return round(target / 5) * 5 if self.config.symbol == 'SPY' else round(target / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
