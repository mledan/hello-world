"""
Opening Range Breakout Strategy (0DTE)
Trade breakouts from first 30-minute range
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig


class OpeningRangeBreakoutStrategy(BaseStrategy):
    """
    Opening Range Breakout - classic intraday momentum strategy
    
    Entry: Breakout from first 30-min range
    Exit: Profit target or end of day
    
    Parameters:
    - range_period_minutes: Opening range period (default: 30)
    - min_range_pct: Min range size to trade (default: 0.3%)
    - profit_target_pct: Target profit (default: 60%)
    """
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator,
                 exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        
        self.range_period_minutes = config.parameters.get('range_period_minutes', 30)
        self.min_range_pct = config.parameters.get('min_range_pct', 0.003)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.60)
        
        self.opening_high = None
        self.opening_low = None
        self.range_set = False
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Set opening range (9:30-10:00 AM)
        if (current_time.hour == 10 and current_time.minute == 0 and not self.range_set):
            range_data = market_data[
                (market_data['timestamp'].dt.hour == 9) & 
                (market_data['timestamp'].dt.minute >= 30)
            ]
            
            if not range_data.empty:
                self.opening_high = range_data['high'].max()
                self.opening_low = range_data['low'].min()
                self.range_set = True
                
                # Check if range is large enough
                range_size = (self.opening_high - self.opening_low) / self.opening_low
                if range_size < self.min_range_pct:
                    self.opening_high = None
                    self.opening_low = None
                    self.range_set = False
        
        # Trade breakouts (10:00 AM - 3:00 PM)
        if self.range_set and not self.positions and current_time.hour >= 10 and current_time.hour < 15:
            # Bullish breakout
            if current_price > self.opening_high:
                strike = self._get_otm_strike(current_price, 'call', 0.01)
                
                signals.append({
                    'symbol': self.config.symbol,
                    'action': 'BUY',
                    'option_type': 'call',
                    'strike': strike,
                    'expiration': self._get_0dte_expiration(),
                    'quantity': 1,
                    'price': self._estimate_option_price(current_price, strike, 'call'),
                    'signal_type': 'ENTRY_ORB_BULLISH',
                    'opening_high': self.opening_high
                })
            
            # Bearish breakout
            elif current_price < self.opening_low:
                strike = self._get_otm_strike(current_price, 'put', 0.01)
                
                signals.append({
                    'symbol': self.config.symbol,
                    'action': 'BUY',
                    'option_type': 'put',
                    'strike': strike,
                    'expiration': self._get_0dte_expiration(),
                    'quantity': 1,
                    'price': self._estimate_option_price(current_price, strike, 'put'),
                    'signal_type': 'ENTRY_ORB_BEARISH',
                    'opening_low': self.opening_low
                })
        
        # Exit logic
        if self.positions:
            exit_signals = self._check_exit_conditions(market_data)
            signals.extend(exit_signals)
        
        return signals
    
    def _check_exit_conditions(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        current_time = market_data['timestamp'].iloc[-1]
        
        # Time exit
        if current_time.hour == 15 and current_time.minute >= 45:
            for position in self.positions:
                signals.append({
                    'symbol': position.symbol,
                    'action': 'SELL',
                    'option_type': position.option_type,
                    'strike': position.strike,
                    'expiration': position.expiration,
                    'quantity': position.quantity,
                    'price': position.current_price,
                    'signal_type': 'EXIT_TIME'
                })
        
        # Profit target
        for position in self.positions:
            if position.pnl_pct >= self.profit_target_pct * 100:
                signals.append({
                    'symbol': position.symbol,
                    'action': 'SELL',
                    'option_type': position.option_type,
                    'strike': position.strike,
                    'expiration': position.expiration,
                    'quantity': position.quantity,
                    'price': position.current_price,
                    'signal_type': 'EXIT_PROFIT'
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {
            'opening_range': f'First {self.range_period_minutes} minutes (9:30-10:00)',
            'min_range_size': f'{self.min_range_pct * 100}%',
            'entry_trigger': 'Breakout above high or below low',
            'option_strike': '1% OTM',
            'expiration': '0DTE'
        }
    
    def get_exit_conditions(self) -> Dict:
        return {
            'profit_target': f'{self.profit_target_pct * 100}%',
            'stop_loss': f'{self.config.stop_loss_pct * 100}%',
            'time_exit': '3:45 PM'
        }
    
    def _get_otm_strike(self, price: float, option_type: str, otm_pct: float) -> float:
        target = price * (1 + otm_pct) if option_type == 'call' else price * (1 - otm_pct)
        if self.config.symbol == 'SPY':
            return round(target / 5) * 5
        else:
            return round(target / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
    
    def _estimate_option_price(self, underlying: float, strike: float, option_type: str) -> float:
        return underlying * 0.012
