"""IV Crush Strategy - Short premium before earnings"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class IVCrushPlayStrategy(BaseStrategy):
    """Sell premium pre-earnings, buy back post-earnings for IV crush profit"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.entry_hours_before = config.parameters.get('entry_hours_before', 4)
        self.iv_crush_target_pct = config.parameters.get('iv_crush_target_pct', 0.40)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        hours_to_earnings = (self.earnings_date - current_time).seconds / 3600
        
        # Sell OTM iron condor few hours before earnings
        if not self.positions and 2 <= hours_to_earnings <= self.entry_hours_before:
            call_strike = self._get_strike(current_price * 1.03)
            put_strike = self._get_strike(current_price * 0.97)
            signals.extend([
                {'symbol': 'TSLA', 'action': 'SELL', 'option_type': 'call', 'strike': call_strike,
                 'expiration': self.earnings_date + timedelta(days=1), 'quantity': 1,
                 'price': current_price * 0.025, 'signal_type': 'ENTRY_IV_CRUSH'},
                {'symbol': 'TSLA', 'action': 'SELL', 'option_type': 'put', 'strike': put_strike,
                 'expiration': self.earnings_date + timedelta(days=1), 'quantity': 1,
                 'price': current_price * 0.025, 'signal_type': 'ENTRY_IV_CRUSH'}
            ])
        
        # Exit morning after earnings
        if self.positions and current_time > self.earnings_date and current_time.hour >= 10:
            for position in self.positions:
                signals.append({
                    'symbol': position.symbol, 'action': 'BUY', 'option_type': position.option_type,
                    'strike': position.strike, 'expiration': position.expiration, 'quantity': abs(position.quantity),
                    'price': position.current_price, 'signal_type': 'EXIT_IV_CRUSH'
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': f'{self.entry_hours_before} hours before earnings', 'structure': 'Short iron condor'}
    
    def get_exit_conditions(self) -> Dict:
        return {'exit_timing': 'Morning after earnings', 'target': f'{self.iv_crush_target_pct * 100}% IV crush'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
