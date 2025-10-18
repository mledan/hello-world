"""Earnings Strangle - OTM straddle for big moves"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class EarningsStrangleStrategy(BaseStrategy):
    """Buy OTM strangle (cheaper than straddle) for earnings volatility"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.otm_pct = config.parameters.get('otm_pct', 0.05)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.70)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        days_to_earnings = (self.earnings_date - current_time).days
        
        if not self.positions and days_to_earnings == 1:
            call_strike = self._get_strike(current_price * (1 + self.otm_pct))
            put_strike = self._get_strike(current_price * (1 - self.otm_pct))
            signals.extend([
                {'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': call_strike,
                 'expiration': self.earnings_date + timedelta(days=2), 'quantity': 1,
                 'price': current_price * 0.025, 'signal_type': 'ENTRY_STRANGLE'},
                {'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'put', 'strike': put_strike,
                 'expiration': self.earnings_date + timedelta(days=2), 'quantity': 1,
                 'price': current_price * 0.025, 'signal_type': 'ENTRY_STRANGLE'}
            ])
        
        if self.positions and current_time > self.earnings_date:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (current_time - self.earnings_date).days >= 1:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': '1 day before earnings', 'structure': f'{self.otm_pct * 100}% OTM strangle'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '1 day post-earnings'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
