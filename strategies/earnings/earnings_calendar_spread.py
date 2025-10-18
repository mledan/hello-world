"""Earnings Calendar Spread - Profit from IV crush differential"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class EarningsCalendarSpreadStrategy(BaseStrategy):
    """Sell near-term, buy longer-term to profit from IV crush"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.35)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        days_to_earnings = (self.earnings_date - current_time).days
        
        if not self.positions and days_to_earnings == 2:
            strike = self._get_strike(current_price)
            signals.extend([
                {'symbol': 'TSLA', 'action': 'SELL', 'option_type': 'call', 'strike': strike,
                 'expiration': self.earnings_date + timedelta(days=1), 'quantity': 1,
                 'price': current_price * 0.035, 'signal_type': 'ENTRY_CALENDAR_SHORT'},
                {'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                 'expiration': self.earnings_date + timedelta(days=14), 'quantity': 1,
                 'price': current_price * 0.045, 'signal_type': 'ENTRY_CALENDAR_LONG'}
            ])
        
        if self.positions and current_time > self.earnings_date and current_time.hour >= 11:
            for position in self.positions:
                action = 'BUY' if position.quantity < 0 else 'SELL'
                signals.append({
                    'symbol': position.symbol, 'action': action, 'option_type': position.option_type,
                    'strike': position.strike, 'expiration': position.expiration, 'quantity': abs(position.quantity),
                    'price': position.current_price, 'signal_type': 'EXIT'
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': '2 days before earnings', 'structure': 'Calendar spread'}
    
    def get_exit_conditions(self) -> Dict:
        return {'exit_timing': 'Morning after earnings', 'profit_target': f'{self.profit_target_pct * 100}%'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
