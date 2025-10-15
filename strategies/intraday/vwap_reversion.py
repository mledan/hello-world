"""
VWAP Mean Reversion Strategy (0DTE)
Trade reversions when price deviates significantly from VWAP
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig


class VWAPReversionStrategy(BaseStrategy):
    """
    VWAP Mean Reversion - fade extreme moves away from VWAP
    
    Entry: Price >2 std deviations from VWAP
    Exit: Return to VWAP or profit target
    
    Parameters:
    - std_dev_threshold: Std devs from VWAP (default: 2.0)
    - profit_target_pct: Target profit (default: 40%)
    - max_hold_minutes: Max hold time (default: 120 min)
    """
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator,
                 exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        
        self.std_dev_threshold = config.parameters.get('std_dev_threshold', 2.0)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.40)
        self.max_hold_minutes = config.parameters.get('max_hold_minutes', 120)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        """Generate VWAP reversion signals"""
        signals = []
        
        if len(market_data) < 30:
            return signals
        
        # Calculate VWAP and standard deviation
        vwap = self._calculate_vwap(market_data)
        vwap_std = self._calculate_vwap_std(market_data, vwap)
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Only trade during 10 AM - 2 PM
        if current_time.hour < 10 or current_time.hour >= 14:
            return signals
        
        # Entry: Price is +2 std devs above VWAP (overbought - buy puts)
        if not self.positions and current_price > vwap + (self.std_dev_threshold * vwap_std):
            atm_strike = self._get_atm_strike(current_price)
            
            signals.append({
                'symbol': self.config.symbol,
                'action': 'BUY',
                'option_type': 'put',
                'strike': atm_strike,
                'expiration': self._get_0dte_expiration(),
                'quantity': 1,
                'price': self._estimate_option_price(current_price, atm_strike, 'put'),
                'signal_type': 'ENTRY_VWAP_REVERSION_SHORT',
                'vwap': vwap,
                'deviation': (current_price - vwap) / vwap_std
            })
        
        # Entry: Price is -2 std devs below VWAP (oversold - buy calls)
        elif not self.positions and current_price < vwap - (self.std_dev_threshold * vwap_std):
            atm_strike = self._get_atm_strike(current_price)
            
            signals.append({
                'symbol': self.config.symbol,
                'action': 'BUY',
                'option_type': 'call',
                'strike': atm_strike,
                'expiration': self._get_0dte_expiration(),
                'quantity': 1,
                'price': self._estimate_option_price(current_price, atm_strike, 'call'),
                'signal_type': 'ENTRY_VWAP_REVERSION_LONG',
                'vwap': vwap,
                'deviation': (current_price - vwap) / vwap_std
            })
        
        # Exit logic
        if self.positions:
            exit_signals = self._check_exit_conditions(market_data, vwap)
            signals.extend(exit_signals)
        
        return signals
    
    def _calculate_vwap(self, market_data: pd.DataFrame) -> float:
        """Calculate Volume Weighted Average Price"""
        typical_price = (market_data['high'] + market_data['low'] + market_data['close']) / 3
        vwap = (typical_price * market_data['volume']).sum() / market_data['volume'].sum()
        return vwap
    
    def _calculate_vwap_std(self, market_data: pd.DataFrame, vwap: float) -> float:
        """Calculate standard deviation from VWAP"""
        typical_price = (market_data['high'] + market_data['low'] + market_data['close']) / 3
        squared_diff = (typical_price - vwap) ** 2
        variance = (squared_diff * market_data['volume']).sum() / market_data['volume'].sum()
        return np.sqrt(variance)
    
    def _check_exit_conditions(self, market_data: pd.DataFrame, vwap: float) -> List[Dict]:
        """Check exit conditions"""
        signals = []
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        for position in self.positions:
            # Exit if price returned to VWAP
            price_near_vwap = abs(current_price - vwap) < (vwap * 0.002)  # Within 0.2% of VWAP
            
            # Exit if max hold time exceeded
            hold_time_minutes = (current_time - position.entry_time).seconds / 60
            max_hold_exceeded = hold_time_minutes >= self.max_hold_minutes
            
            # Exit if profit target hit
            profit_target_hit = position.pnl_pct >= self.profit_target_pct * 100
            
            # Exit at end of day
            end_of_day = current_time.hour == 15 and current_time.minute >= 45
            
            if price_near_vwap or max_hold_exceeded or profit_target_hit or end_of_day:
                signals.append({
                    'symbol': position.symbol,
                    'action': 'SELL',
                    'option_type': position.option_type,
                    'strike': position.strike,
                    'expiration': position.expiration,
                    'quantity': position.quantity,
                    'price': position.current_price,
                    'signal_type': ('EXIT_VWAP_RETURN' if price_near_vwap else
                                  'EXIT_TIME' if max_hold_exceeded or end_of_day else
                                  'EXIT_PROFIT')
                })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {
            'time_window': '10:00 AM - 2:00 PM',
            'entry_trigger': f'{self.std_dev_threshold} std devs from VWAP',
            'option_strike': 'ATM',
            'expiration': '0DTE'
        }
    
    def get_exit_conditions(self) -> Dict:
        return {
            'vwap_return': 'Price within 0.2% of VWAP',
            'profit_target': f'{self.profit_target_pct * 100}%',
            'max_hold_time': f'{self.max_hold_minutes} minutes',
            'time_exit': '3:45 PM'
        }
    
    def _get_atm_strike(self, price: float) -> float:
        if self.config.symbol == 'SPY':
            return round(price / 5) * 5
        else:
            return round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
    
    def _estimate_option_price(self, underlying: float, strike: float, option_type: str) -> float:
        return underlying * 0.015
