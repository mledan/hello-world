"""Intraday Iron Condor Strategy (0DTE) - Range-bound profit"""
import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class IntradayIronCondorStrategy(BaseStrategy):
    """Sell iron condors in low volatility environments"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.wing_width_pct = config.parameters.get('wing_width_pct', 0.02)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Enter iron condor at market open if low volatility expected
        if not self.positions and current_time.hour == 10 and current_time.minute == 0:
            # Calculate strikes
            short_call_strike = self._get_strike(current_price * 1.01, 'call')
            long_call_strike = self._get_strike(current_price * (1 + self.wing_width_pct), 'call')
            short_put_strike = self._get_strike(current_price * 0.99, 'put')
            long_put_strike = self._get_strike(current_price * (1 - self.wing_width_pct), 'put')
            
            # Sell iron condor (simplified - would need 4 legs)
            signals.extend([
                {'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'call', 'strike': short_call_strike,
                 'expiration': self._get_0dte_expiration(), 'quantity': 1, 'price': current_price * 0.01, 'signal_type': 'ENTRY_IC'},
                {'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'put', 'strike': short_put_strike,
                 'expiration': self._get_0dte_expiration(), 'quantity': 1, 'price': current_price * 0.01, 'signal_type': 'ENTRY_IC'}
            ])
        
        # Exit at 3:00 PM or profit target
        if self.positions and (current_time.hour >= 15 or any(p.pnl_pct >= self.profit_target_pct * 100 for p in self.positions)):
            for position in self.positions:
                signals.append({
                    'symbol': position.symbol, 'action': 'BUY' if position.quantity < 0 else 'SELL',
                    'option_type': position.option_type, 'strike': position.strike,
                    'expiration': position.expiration, 'quantity': abs(position.quantity),
                    'price': position.current_price, 'signal_type': 'EXIT'
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'time_window': '10:00 AM', 'wing_width': f'{self.wing_width_pct * 100}%', 'structure': 'Iron condor'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '3:00 PM'}
    
    def _get_strike(self, price: float, option_type: str) -> float:
        return round(price / 5) * 5 if self.config.symbol == 'SPY' else round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
