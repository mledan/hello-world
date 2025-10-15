"""Gamma Squeeze Detection Strategy (0DTE)"""
import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class GammaSqueezeStrategy(BaseStrategy):
    """Detect and trade gamma squeezes from high dealer gamma exposure"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.volume_spike_threshold = config.parameters.get('volume_spike_threshold', 2.0)
        self.price_acceleration = config.parameters.get('price_acceleration', 0.01)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        # Simplified gamma squeeze detection
        signals = []
        if len(market_data) < 20:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        avg_volume = market_data['volume'].rolling(20).mean().iloc[-1]
        current_volume = market_data['volume'].iloc[-1]
        
        # Detect potential gamma squeeze conditions
        volume_spike = current_volume > avg_volume * self.volume_spike_threshold
        price_momentum = (current_price - market_data['close'].iloc[-10]) / market_data['close'].iloc[-10]
        
        if not self.positions and volume_spike and abs(price_momentum) > self.price_acceleration and current_time.hour >= 10:
            if price_momentum > 0:
                strike = self._get_otm_strike(current_price, 'call', 0.02)
                signals.append({
                    'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call',
                    'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                    'price': current_price * 0.02, 'signal_type': 'ENTRY_GAMMA_SQUEEZE'
                })
        
        # Exit on reversal or time
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= 70 or (current_time.hour == 15 and current_time.minute >= 45):
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'volume_spike': f'{self.volume_spike_threshold}x avg', 'price_acceleration': f'{self.price_acceleration * 100}%'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': '70%', 'time_exit': '3:45 PM'}
    
    def _get_otm_strike(self, price: float, option_type: str, otm_pct: float) -> float:
        target = price * (1 + otm_pct) if option_type == 'call' else price * (1 - otm_pct)
        return round(target / 5) * 5 if self.config.symbol == 'SPY' else round(target / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
