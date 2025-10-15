"""Volatility Spike Strategy (0DTE) - Trade IV expansion"""
import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class VolatilitySpikeStrategy(BaseStrategy):
    """Capitalize on sudden volatility spikes"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.vol_spike_threshold = config.parameters.get('vol_spike_threshold', 1.5)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.40)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if len(market_data) < 20:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Calculate realized volatility
        returns = market_data['close'].pct_change().dropna()
        recent_vol = returns.tail(5).std()
        avg_vol = returns.tail(20).std()
        
        # Enter on volatility spike
        if not self.positions and recent_vol > avg_vol * self.vol_spike_threshold and 10 <= current_time.hour < 15:
            strike = self._get_atm_strike(current_price)
            # Buy straddle to profit from continued volatility
            signals.extend([
                {'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                 'expiration': self._get_0dte_expiration(), 'quantity': 1, 'price': current_price * 0.015, 'signal_type': 'ENTRY_VOL_SPIKE'},
                {'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'put', 'strike': strike,
                 'expiration': self._get_0dte_expiration(), 'quantity': 1, 'price': current_price * 0.015, 'signal_type': 'ENTRY_VOL_SPIKE'}
            ])
        
        # Exit on profit or time
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (current_time.hour == 15 and current_time.minute >= 45):
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'vol_spike_threshold': f'{self.vol_spike_threshold}x avg', 'structure': 'ATM straddle'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '3:45 PM'}
    
    def _get_atm_strike(self, price: float) -> float:
        return round(price / 5) * 5 if self.config.symbol == 'SPY' else round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
