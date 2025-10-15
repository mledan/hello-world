"""Directional Earnings Call - Bet on direction based on fundamentals"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class DirectionalEarningsCallStrategy(BaseStrategy):
    """Take directional bet based on analyst estimates and sentiment"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.direction = config.parameters.get('direction', 'bullish')  # 'bullish' or 'bearish'
        self.confidence_level = config.parameters.get('confidence_level', 'high')
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.80)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        days_to_earnings = (self.earnings_date - current_time).days
        
        if not self.positions and days_to_earnings == 0:
            if self.direction == 'bullish':
                strike = self._get_strike(current_price * 1.02)
                option_type = 'call'
            else:
                strike = self._get_strike(current_price * 0.98)
                option_type = 'put'
            
            signals.append({
                'symbol': 'TSLA', 'action': 'BUY', 'option_type': option_type, 'strike': strike,
                'expiration': self.earnings_date + timedelta(days=7), 'quantity': 1,
                'price': current_price * 0.03, 'signal_type': f'ENTRY_DIRECTIONAL_{self.direction.upper()}'
            })
        
        if self.positions and current_time > self.earnings_date:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or position.pnl_pct <= -50 or (current_time - self.earnings_date).days >= 2:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': 'Earnings day', 'direction': self.direction, 'confidence': self.confidence_level}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'stop_loss': '50%', 'time_exit': '2 days post'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
