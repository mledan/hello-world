"""Post-Earnings Momentum - Ride the continuation move"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class PostEarningsMomentumStrategy(BaseStrategy):
    """Buy in direction of initial earnings move, betting on continuation"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.min_move_pct = config.parameters.get('min_move_pct', 0.04)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.60)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        if current_time.date() == (self.earnings_date + timedelta(days=1)).date() and current_time.hour == 10 and not self.positions:
            pre_earnings_price = market_data[market_data['timestamp'] < self.earnings_date]['close'].iloc[-1]
            move_pct = (current_price - pre_earnings_price) / pre_earnings_price
            
            if abs(move_pct) > self.min_move_pct:
                if move_pct > 0:  # Continue bullish
                    strike = self._get_strike(current_price * 1.02)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.025, 'signal_type': 'ENTRY_MOMENTUM_BULLISH'
                    })
                else:  # Continue bearish
                    strike = self._get_strike(current_price * 0.98)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'put', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.025, 'signal_type': 'ENTRY_MOMENTUM_BEARISH'
                    })
        
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (current_time - position.entry_time).days >= 3:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': 'Day after earnings', 'min_move': f'{self.min_move_pct * 100}%', 'direction': 'With momentum'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '3 days'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
    
    def _get_weekly_expiration(self) -> datetime:
        return datetime.now() + timedelta(days=7)
