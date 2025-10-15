"""Covered Call 30-Day - Income generation strategy"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class CoveredCall30DStrategy(BaseStrategy):
    """Sell covered calls for income on existing stock position"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.dte_entry = config.parameters.get('dte_entry', 45)
        self.call_delta = config.parameters.get('call_delta', 0.30)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.60)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Sell call against stock position
        if not self.positions and current_time.weekday() == 0:
            call_strike = self._get_strike(current_price * 1.05)
            expiration = self._get_expiration(self.dte_entry)
            
            signals.append({
                'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'call', 'strike': call_strike,
                'expiration': expiration, 'quantity': 1, 'price': current_price * 0.025, 'signal_type': 'ENTRY_COVERED_CALL'
            })
        
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (position.expiration - current_time).days <= 14:
                    signals.append({
                        'symbol': position.symbol, 'action': 'BUY', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': abs(position.quantity),
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'dte': f'{self.dte_entry} days', 'call_strike': f'{self.call_delta} delta', 'requirement': 'Long stock position'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'dte_exit': '14 days', 'roll': 'If threatened'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 5) * 5 if self.config.symbol == 'SPY' else round(price / 10) * 10
    
    def _get_expiration(self, days: int) -> datetime:
        return datetime.now() + timedelta(days=days)
