"""Earnings Iron Butterfly - Bet on no large move"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class EarningsIronButterflyStrategy(BaseStrategy):
    """Sell iron butterfly betting on minimal post-earnings move"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.wing_width_pct = config.parameters.get('wing_width_pct', 0.05)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        hours_to_earnings = (self.earnings_date - current_time).seconds / 3600
        
        if not self.positions and 1 <= hours_to_earnings <= 3:
            atm_strike = self._get_strike(current_price)
            signals.extend([
                {'symbol': 'TSLA', 'action': 'SELL', 'option_type': 'call', 'strike': atm_strike,
                 'expiration': self.earnings_date + timedelta(days=1), 'quantity': 2,
                 'price': current_price * 0.03, 'signal_type': 'ENTRY_IRON_BUTTERFLY'},
                {'symbol': 'TSLA', 'action': 'SELL', 'option_type': 'put', 'strike': atm_strike,
                 'expiration': self.earnings_date + timedelta(days=1), 'quantity': 2,
                 'price': current_price * 0.03, 'signal_type': 'ENTRY_IRON_BUTTERFLY'}
            ])
        
        if self.positions and current_time > self.earnings_date and current_time.hour >= 10:
            for position in self.positions:
                signals.append({
                    'symbol': position.symbol, 'action': 'BUY', 'option_type': position.option_type,
                    'strike': position.strike, 'expiration': position.expiration, 'quantity': abs(position.quantity),
                    'price': position.current_price, 'signal_type': 'EXIT'
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': '1-3 hours before earnings', 'structure': 'Iron butterfly'}
    
    def get_exit_conditions(self) -> Dict:
        return {'exit_timing': 'Morning after earnings', 'profit_target': f'{self.profit_target_pct * 100}%'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
