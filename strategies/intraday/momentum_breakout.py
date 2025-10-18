"""
Momentum Breakout Strategy (0DTE)
Enter when price breaks key intraday levels with strong momentum
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig


class MomentumBreakoutStrategy(BaseStrategy):
    """
    Momentum Breakout - capitalize on strong intraday price movements
    
    Entry: Price breaks above/below key level with volume confirmation
    Exit: Profit target, stop loss, or end of day
    
    Parameters:
    - breakout_threshold_pct: Min % move to consider breakout (default: 0.5%)
    - volume_multiplier: Volume vs avg volume (default: 1.5x)
    - profit_target_pct: Target profit (default: 50%)
    - trail_stop_pct: Trailing stop (default: 30%)
    """
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator,
                 exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        
        self.breakout_threshold_pct = config.parameters.get('breakout_threshold_pct', 0.005)
        self.volume_multiplier = config.parameters.get('volume_multiplier', 1.5)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        self.trail_stop_pct = config.parameters.get('trail_stop_pct', 0.30)
        
        self.daily_high = None
        self.daily_low = None
        self.avg_volume = None
        self.highest_pnl = 0
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        """Generate momentum breakout signals"""
        signals = []
        
        if len(market_data) < 20:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        current_volume = market_data['volume'].iloc[-1]
        
        # Set daily levels from early session data
        if current_time.hour == 9 and current_time.minute >= 30 and current_time.minute < 35:
            self.daily_high = market_data['high'].max()
            self.daily_low = market_data['low'].min()
            self.avg_volume = market_data['volume'].mean()
        
        if self.daily_high is None or self.daily_low is None:
            return signals
        
        # Check for breakout entry (10:00 AM - 3:00 PM)
        if (not self.positions and current_time.hour >= 10 and current_time.hour < 15):
            
            # Bullish breakout above daily high
            if (current_price > self.daily_high * (1 + self.breakout_threshold_pct) and
                current_volume > self.avg_volume * self.volume_multiplier):
                
                otm_strike = self._get_otm_strike(current_price, 'call', 0.02)  # 2% OTM
                
                signals.append({
                    'symbol': self.config.symbol,
                    'action': 'BUY',
                    'option_type': 'call',
                    'strike': otm_strike,
                    'expiration': self._get_0dte_expiration(),
                    'quantity': 1,
                    'price': self._estimate_option_price(current_price, otm_strike, 'call'),
                    'signal_type': 'ENTRY_BULLISH_BREAKOUT',
                    'breakout_price': current_price
                })
            
            # Bearish breakout below daily low
            elif (current_price < self.daily_low * (1 - self.breakout_threshold_pct) and
                  current_volume > self.avg_volume * self.volume_multiplier):
                
                otm_strike = self._get_otm_strike(current_price, 'put', 0.02)  # 2% OTM
                
                signals.append({
                    'symbol': self.config.symbol,
                    'action': 'BUY',
                    'option_type': 'put',
                    'strike': otm_strike,
                    'expiration': self._get_0dte_expiration(),
                    'quantity': 1,
                    'price': self._estimate_option_price(current_price, otm_strike, 'put'),
                    'signal_type': 'ENTRY_BEARISH_BREAKOUT',
                    'breakout_price': current_price
                })
        
        # Exit logic
        if self.positions:
            exit_signals = self._check_exit_conditions(market_data)
            signals.extend(exit_signals)
        
        return signals
    
    def _check_exit_conditions(self, market_data: pd.DataFrame) -> List[Dict]:
        """Check exit conditions with trailing stop"""
        signals = []
        current_time = market_data['timestamp'].iloc[-1]
        
        # Time exit (3:45 PM)
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
            return signals
        
        # Profit target and trailing stop
        for position in self.positions:
            # Update highest PnL for trailing stop
            if position.pnl_pct > self.highest_pnl:
                self.highest_pnl = position.pnl_pct
            
            # Profit target
            if position.pnl_pct >= self.profit_target_pct * 100:
                signals.append({
                    'symbol': position.symbol,
                    'action': 'SELL',
                    'option_type': position.option_type,
                    'strike': position.strike,
                    'expiration': position.expiration,
                    'quantity': position.quantity,
                    'price': position.current_price,
                    'signal_type': 'EXIT_PROFIT_TARGET'
                })
            
            # Trailing stop
            elif (self.highest_pnl > 0 and 
                  position.pnl_pct < self.highest_pnl - self.trail_stop_pct * 100):
                signals.append({
                    'symbol': position.symbol,
                    'action': 'SELL',
                    'option_type': position.option_type,
                    'strike': position.strike,
                    'expiration': position.expiration,
                    'quantity': position.quantity,
                    'price': position.current_price,
                    'signal_type': 'EXIT_TRAILING_STOP'
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        """Define entry conditions"""
        return {
            'time_window': '10:00 AM - 3:00 PM',
            'breakout_threshold': f'{self.breakout_threshold_pct * 100}%',
            'volume_confirmation': f'{self.volume_multiplier}x average',
            'option_strike': '2% OTM',
            'expiration': '0DTE'
        }
    
    def get_exit_conditions(self) -> Dict:
        """Define exit conditions"""
        return {
            'time_exit': '3:45 PM',
            'profit_target': f'{self.profit_target_pct * 100}%',
            'trailing_stop': f'{self.trail_stop_pct * 100}%',
            'stop_loss': f'{self.config.stop_loss_pct * 100}%'
        }
    
    def _get_otm_strike(self, price: float, option_type: str, otm_pct: float) -> float:
        """Get OTM strike"""
        if option_type == 'call':
            target_price = price * (1 + otm_pct)
        else:
            target_price = price * (1 - otm_pct)
        
        if self.config.symbol == 'SPY':
            return round(target_price / 5) * 5
        else:
            return round(target_price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        """Get 0DTE expiration"""
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
    
    def _estimate_option_price(self, underlying: float, strike: float, 
                              option_type: str) -> float:
        """Estimate option price"""
        # Simplified pricing for OTM 0DTE
        intrinsic = max(0, underlying - strike if option_type == 'call' else strike - underlying)
        time_value = underlying * 0.01  # Rough estimate
        return intrinsic + time_value
