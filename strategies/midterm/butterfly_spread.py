"""Butterfly Spread - Low risk neutral strategy"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class ButterflySpreadStrategy(BaseStrategy):
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.dte_entry = config.parameters.get('dte_entry', 45)
        self.wing_width = config.parameters.get('wing_width', 10)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        if not self.positions and current_time.weekday() == 0:
            atm = round(current_price / 5) * 5 if self.config.symbol == 'SPY' else round(current_price / 10) * 10
            lower = atm - self.wing_width
            upper = atm + self.wing_width
            expiration = datetime.now() + timedelta(days=self.dte_entry)
            signals.extend([
                {'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call', 'strike': lower,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.03, 'signal_type': 'ENTRY_BUTTERFLY'},
                {'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'call', 'strike': atm,
                 'expiration': expiration, 'quantity': 2, 'price': current_price * 0.02, 'signal_type': 'ENTRY_BUTTERFLY'},
                {'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call', 'strike': upper,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.01, 'signal_type': 'ENTRY_BUTTERFLY'}
            ])
        
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100:
                    action = 'SELL' if position.quantity > 0 else 'BUY'
                    signals.append({'symbol': position.symbol, 'action': action, 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': abs(position.quantity),
                        'price': position.current_price, 'signal_type': 'EXIT'})
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'dte': f'{self.dte_entry} days', 'structure': 'ATM butterfly'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%'}
