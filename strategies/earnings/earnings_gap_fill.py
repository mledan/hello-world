"""Earnings Gap Fill - Trade the gap fill after earnings"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class EarningsGapFillStrategy(BaseStrategy):
    """Bet on gap fill within days after earnings"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.min_gap_pct = config.parameters.get('min_gap_pct', 0.03)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Enter day after earnings if there's a gap
        if current_time.date() == (self.earnings_date + timedelta(days=1)).date() and current_time.hour == 10 and not self.positions:
            pre_earnings_close = market_data[market_data['timestamp'] < self.earnings_date]['close'].iloc[-1]
            gap_pct = (current_price - pre_earnings_close) / pre_earnings_close
            
            if abs(gap_pct) > self.min_gap_pct:
                if gap_pct > 0:  # Gap up - fade to fill gap
                    strike = self._get_strike(pre_earnings_close * 1.01)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'put', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.025, 'signal_type': 'ENTRY_GAP_FILL_DOWN'
                    })
                else:  # Gap down - buy for fill
                    strike = self._get_strike(pre_earnings_close * 0.99)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.025, 'signal_type': 'ENTRY_GAP_FILL_UP'
                    })
        
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (current_time - position.entry_time).days >= 5:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': '1 day post-earnings', 'min_gap': f'{self.min_gap_pct * 100}%'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '5 days'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
    
    def _get_weekly_expiration(self) -> datetime:
        return datetime.now() + timedelta(days=7)
