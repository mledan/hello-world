"""Long Straddle Earnings Strategy - Classic volatility play"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class LongStraddleEarningsStrategy(BaseStrategy):
    """Buy ATM straddle before earnings to profit from large price swing"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.entry_days_before = config.parameters.get('entry_days_before', 1)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.60)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        days_to_earnings = (self.earnings_date - current_time).days
        
        # Enter 1 day before earnings
        if not self.positions and days_to_earnings == self.entry_days_before:
            strike = self._get_atm_strike(current_price)
            signals.extend([
                {'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                 'expiration': self.earnings_date + timedelta(days=2), 'quantity': 1,
                 'price': current_price * 0.04, 'signal_type': 'ENTRY_EARNINGS_STRADDLE'},
                {'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'put', 'strike': strike,
                 'expiration': self.earnings_date + timedelta(days=2), 'quantity': 1,
                 'price': current_price * 0.04, 'signal_type': 'ENTRY_EARNINGS_STRADDLE'}
            ])
        
        # Exit post-earnings on profit or next day
        if self.positions and current_time > self.earnings_date:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (current_time - self.earnings_date).days >= 1:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT_EARNINGS'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': f'{self.entry_days_before} day before earnings', 'structure': 'ATM straddle', 'symbol': 'TSLA'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '1 day post-earnings'}
    
    def _get_atm_strike(self, price: float) -> float:
        return round(price / 10) * 10
