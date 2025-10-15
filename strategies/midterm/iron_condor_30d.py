"""Iron Condor 30-Day Strategy - Classic theta decay play"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class IronCondor30DStrategy(BaseStrategy):
    """Sell OTM iron condor for theta decay in range-bound market"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.dte_entry = config.parameters.get('dte_entry', 45)
        self.delta_short = config.parameters.get('delta_short', 0.20)
        self.wing_width = config.parameters.get('wing_width', 10)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        self.dte_exit = config.parameters.get('dte_exit', 21)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Enter iron condor if no position
        if not self.positions and current_time.weekday() == 0:  # Monday
            # Calculate strikes based on ~20 delta
            short_call_strike = self._get_strike(current_price * 1.05)
            long_call_strike = short_call_strike + self.wing_width
            short_put_strike = self._get_strike(current_price * 0.95)
            long_put_strike = short_put_strike - self.wing_width
            
            expiration = self._get_expiration(self.dte_entry)
            
            signals.extend([
                {'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'call', 'strike': short_call_strike,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.02, 'signal_type': 'ENTRY_IC_SHORT_CALL'},
                {'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call', 'strike': long_call_strike,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.01, 'signal_type': 'ENTRY_IC_LONG_CALL'},
                {'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'put', 'strike': short_put_strike,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.02, 'signal_type': 'ENTRY_IC_SHORT_PUT'},
                {'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'put', 'strike': long_put_strike,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.01, 'signal_type': 'ENTRY_IC_LONG_PUT'}
            ])
        
        # Exit at profit target or DTE threshold
        if self.positions:
            for position in self.positions:
                dte = (position.expiration - current_time).days
                if position.pnl_pct >= self.profit_target_pct * 100 or dte <= self.dte_exit:
                    action = 'BUY' if position.quantity < 0 else 'SELL'
                    signals.append({
                        'symbol': position.symbol, 'action': action, 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': abs(position.quantity),
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'dte': f'{self.dte_entry} days', 'short_strikes': f'~{self.delta_short} delta', 'wing_width': f'${self.wing_width}'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'dte_exit': f'{self.dte_exit} days'}
    
    def _get_strike(self, price: float) -> float:
        if self.config.symbol == 'SPY':
            return round(price / 5) * 5
        return round(price / 10) * 10
    
    def _get_expiration(self, days: int) -> datetime:
        return datetime.now() + timedelta(days=days)
