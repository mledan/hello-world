"""Market Maker Scalp Strategy (0DTE) - High frequency scalping"""
import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class MarketMakerScalpStrategy(BaseStrategy):
    """Scalp small profits from bid-ask spread and gamma"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.scalp_target_pct = config.parameters.get('scalp_target_pct', 0.10)
        self.max_hold_minutes = config.parameters.get('max_hold_minutes', 15)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Enter on small moves (10:00 AM - 3:00 PM)
        if not self.positions and 10 <= current_time.hour < 15:
            if len(market_data) > 5:
                short_term_move = (current_price - market_data['close'].iloc[-5]) / market_data['close'].iloc[-5]
                if abs(short_term_move) > 0.001:  # 0.1% move
                    strike = self._get_atm_strike(current_price)
                    option_type = 'call' if short_term_move > 0 else 'put'
                    signals.append({
                        'symbol': self.config.symbol, 'action': 'BUY', 'option_type': option_type,
                        'strike': strike, 'expiration': self._get_0dte_expiration(), 'quantity': 1,
                        'price': current_price * 0.008, 'signal_type': 'ENTRY_SCALP'
                    })
        
        # Quick exit on target or time
        if self.positions:
            for position in self.positions:
                hold_minutes = (current_time - position.entry_time).seconds / 60
                if position.pnl_pct >= self.scalp_target_pct * 100 or hold_minutes >= self.max_hold_minutes:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT_SCALP'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'min_move': '0.1%', 'time_window': '10:00 AM - 3:00 PM'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.scalp_target_pct * 100}%', 'max_hold': f'{self.max_hold_minutes} min'}
    
    def _get_atm_strike(self, price: float) -> float:
        return round(price / 5) * 5 if self.config.symbol == 'SPY' else round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
