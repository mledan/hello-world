"""Analyst Surprise Strategy - Trade on earnings surprise magnitude"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class AnalystSurpriseStrategy(BaseStrategy):
    """Enter immediately after earnings based on surprise magnitude"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.surprise_threshold_pct = config.parameters.get('surprise_threshold_pct', 0.10)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.60)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Enter within 30 min after earnings release
        if (current_time > self.earnings_date and (current_time - self.earnings_date).seconds <= 1800 and not self.positions):
            # Placeholder: Would fetch actual vs expected earnings from API
            # For now, assume positive surprise scenario
            pre_earnings_price = market_data[market_data['timestamp'] < self.earnings_date]['close'].iloc[-1]
            surprise_move = (current_price - pre_earnings_price) / pre_earnings_price
            
            if abs(surprise_move) > self.surprise_threshold_pct:
                if surprise_move > 0:  # Positive surprise
                    strike = self._get_strike(current_price * 1.02)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.03, 'signal_type': 'ENTRY_POSITIVE_SURPRISE'
                    })
                else:  # Negative surprise
                    strike = self._get_strike(current_price * 0.98)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'put', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.03, 'signal_type': 'ENTRY_NEGATIVE_SURPRISE'
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
        return {'entry_timing': 'Within 30 min of earnings', 'surprise_threshold': f'{self.surprise_threshold_pct * 100}%'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '3 days'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
    
    def _get_weekly_expiration(self) -> datetime:
        return datetime.now() + timedelta(days=7)
