"""Post-Earnings Fade Strategy - Bet on mean reversion after initial spike"""
import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class PostEarningsFadeStrategy(BaseStrategy):
    """Fade the initial post-earnings move, betting on reversal"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.fade_threshold_pct = config.parameters.get('fade_threshold_pct', 0.05)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Wait for initial post-earnings move (first hour after open)
        if current_time.date() == self.earnings_date.date() and current_time.hour == 10:
            pre_earnings_price = market_data[market_data['timestamp'] < self.earnings_date]['close'].iloc[-1]
            move_pct = (current_price - pre_earnings_price) / pre_earnings_price
            
            # If big move, fade it
            if abs(move_pct) > self.fade_threshold_pct and not self.positions:
                if move_pct > 0:  # Big up move - buy puts to fade
                    strike = self._get_strike(current_price * 0.98)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'put', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.02, 'signal_type': 'ENTRY_FADE_BEARISH'
                    })
                else:  # Big down move - buy calls to fade
                    strike = self._get_strike(current_price * 1.02)
                    signals.append({
                        'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                        'expiration': self._get_weekly_expiration(), 'quantity': 1,
                        'price': current_price * 0.02, 'signal_type': 'ENTRY_FADE_BULLISH'
                    })
        
        # Exit on profit or end of day
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or current_time.hour >= 15:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': '1 hour post-earnings', 'fade_threshold': f'{self.fade_threshold_pct * 100}%'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': 'End of day'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
    
    def _get_weekly_expiration(self) -> datetime:
        return datetime.now() + timedelta(days=7)
