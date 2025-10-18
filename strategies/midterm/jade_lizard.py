"""jade_lizard - Midterm strategy"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class JadeLizardStrategy(BaseStrategy):
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.dte_entry = config.parameters.get('dte_entry', 45)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        if not self.positions and current_time.weekday() == 0:
            strike = round(current_price / 5) * 5 if self.config.symbol == 'SPY' else round(current_price / 10) * 10
            expiration = datetime.now() + timedelta(days=self.dte_entry)
            signals.append({'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                'expiration': expiration, 'quantity': 1, 'price': current_price * 0.03, 'signal_type': 'ENTRY'})
        
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (position.expiration - current_time).days <= 21:
                    signals.append({'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'})
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'dte': f'{self.dte_entry} days'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'dte_exit': '21 days'}
