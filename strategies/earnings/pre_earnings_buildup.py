"""Pre-Earnings Buildup Strategy - Ride momentum into earnings"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class PreEarningsBuildupStrategy(BaseStrategy):
    """Buy options 3-5 days before earnings on positive momentum"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.entry_days_before = config.parameters.get('entry_days_before', 3)
        self.momentum_threshold = config.parameters.get('momentum_threshold', 0.02)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.40)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if len(market_data) < 5 or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        days_to_earnings = (self.earnings_date - current_time).days
        
        # Enter if positive momentum 3-5 days before earnings
        if not self.positions and days_to_earnings == self.entry_days_before:
            week_ago_price = market_data['close'].iloc[-5]
            momentum = (current_price - week_ago_price) / week_ago_price
            
            if momentum > self.momentum_threshold:  # Bullish momentum
                strike = self._get_strike(current_price * 1.02)
                signals.append({
                    'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                    'expiration': self.earnings_date + timedelta(days=7), 'quantity': 1,
                    'price': current_price * 0.03, 'signal_type': 'ENTRY_PRE_EARNINGS_BUILDUP'
                })
        
        # Exit day before earnings or on profit
        if self.positions:
            for position in self.positions:
                if days_to_earnings <= 1 or position.pnl_pct >= self.profit_target_pct * 100:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT_PRE_EARNINGS'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': f'{self.entry_days_before} days before earnings', 'momentum_required': f'{self.momentum_threshold * 100}%'}
    
    def get_exit_conditions(self) -> Dict:
        return {'exit_timing': '1 day before earnings', 'profit_target': f'{self.profit_target_pct * 100}%'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
