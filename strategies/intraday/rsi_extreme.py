"""RSI Extreme Strategy (0DTE) - Fade extreme RSI readings"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class RSIExtremeStrategy(BaseStrategy):
    """Trade when RSI hits extreme levels (oversold/overbought)"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.rsi_period = config.parameters.get('rsi_period', 14)
        self.oversold_level = config.parameters.get('oversold_level', 30)
        self.overbought_level = config.parameters.get('overbought_level', 70)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.45)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        if len(market_data) < self.rsi_period + 1:
            return []
        
        rsi = self._calculate_rsi(market_data['close'], self.rsi_period)
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        signals = []
        
        # Entry: RSI oversold (buy calls)
        if not self.positions and rsi < self.oversold_level and current_time.hour >= 10 and current_time.hour < 15:
            strike = self._get_atm_strike(current_price)
            signals.append({
                'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call',
                'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                'price': current_price * 0.015, 'signal_type': 'ENTRY_RSI_OVERSOLD'
            })
        
        # Entry: RSI overbought (buy puts)
        elif not self.positions and rsi > self.overbought_level and current_time.hour >= 10 and current_time.hour < 15:
            strike = self._get_atm_strike(current_price)
            signals.append({
                'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'put',
                'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                'price': current_price * 0.015, 'signal_type': 'ENTRY_RSI_OVERBOUGHT'
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
    
    def _calculate_rsi(self, prices, period):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs.iloc[-1]))
    
    def get_entry_conditions(self) -> Dict:
        return {'rsi_oversold': self.oversold_level, 'rsi_overbought': self.overbought_level}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '3:45 PM'}
    
    def _get_atm_strike(self, price: float) -> float:
        return round(price / 5) * 5 if self.config.symbol == 'SPY' else round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
