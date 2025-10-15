"""Power Hour Momentum Strategy (0DTE) - Trade the last hour momentum"""
import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class PowerHourMomentumStrategy(BaseStrategy):
    """Capture momentum in the final trading hour (3:00-4:00 PM)"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.momentum_threshold = config.parameters.get('momentum_threshold', 0.003)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.30)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Only trade during power hour (3:00-3:45 PM)
        if current_time.hour == 15 and 0 <= current_time.minute < 45 and not self.positions:
            # Calculate momentum from last 30 minutes
            recent_data = market_data.tail(30)
            if len(recent_data) > 10:
                momentum = (current_price - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
                
                if momentum > self.momentum_threshold:
                    strike = self._get_atm_strike(current_price)
                    signals.append({
                        'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call',
                        'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                        'price': current_price * 0.01, 'signal_type': 'ENTRY_POWER_HOUR_BULLISH'
                    })
                elif momentum < -self.momentum_threshold:
                    strike = self._get_atm_strike(current_price)
                    signals.append({
                        'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'put',
                        'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                        'price': current_price * 0.01, 'signal_type': 'ENTRY_POWER_HOUR_BEARISH'
                    })
        
        # Exit at 3:55 PM
        if self.positions and current_time.hour == 15 and current_time.minute >= 55:
            for position in self.positions:
                signals.append({
                    'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                    'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                    'price': position.current_price, 'signal_type': 'EXIT_TIME'
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'time_window': '3:00-3:45 PM', 'momentum_threshold': f'{self.momentum_threshold * 100}%'}
    
    def get_exit_conditions(self) -> Dict:
        return {'time_exit': '3:55 PM', 'profit_target': f'{self.profit_target_pct * 100}%'}
    
    def _get_atm_strike(self, price: float) -> float:
        return round(price / 5) * 5 if self.config.symbol == 'SPY' else round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
