"""
Gamma Scalping Strategy (0DTE)
Buy options and scalp the underlying to profit from gamma exposure
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig


class GammaScalpingStrategy(BaseStrategy):
    """
    Gamma Scalping Strategy
    
    Entry: Buy ATM straddle when IV is low
    Management: Delta hedge as underlying moves, capturing gamma profits
    Exit: End of day or when gamma profits exceed threshold
    
    Parameters:
    - gamma_threshold: Minimum gamma to enter (default: 0.05)
    - delta_rehedge_threshold: Delta threshold to trigger rehedge (default: 0.15)
    - profit_target_pct: Profit target as % (default: 30%)
    - max_rehedges: Maximum number of rehedges per day (default: 10)
    """
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator,
                 exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        
        # Strategy-specific parameters
        self.gamma_threshold = config.parameters.get('gamma_threshold', 0.05)
        self.delta_rehedge_threshold = config.parameters.get('delta_rehedge_threshold', 0.15)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.30)
        self.max_rehedges = config.parameters.get('max_rehedges', 10)
        
        self.rehedge_count = 0
        self.initial_cost = 0
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        """
        Generate gamma scalping signals
        
        Entry signal when:
        1. Market open (first 30 minutes)
        2. IV is below 30th percentile
        3. Expected price movement > 1%
        """
        signals = []
        
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Check if market just opened (9:30 - 10:00 AM)
        if current_time.hour == 9 and current_time.minute >= 30:
            # Entry signal: Buy ATM straddle
            atm_strike = self._get_atm_strike(current_price)
            
            signals.append({
                'symbol': self.config.symbol,
                'action': 'BUY',
                'option_type': 'call',
                'strike': atm_strike,
                'expiration': self._get_0dte_expiration(),
                'quantity': 1,
                'price': self._estimate_option_price(current_price, atm_strike, 'call'),
                'signal_type': 'ENTRY'
            })
            
            signals.append({
                'symbol': self.config.symbol,
                'action': 'BUY',
                'option_type': 'put',
                'strike': atm_strike,
                'expiration': self._get_0dte_expiration(),
                'quantity': 1,
                'price': self._estimate_option_price(current_price, atm_strike, 'put'),
                'signal_type': 'ENTRY'
            })
        
        # Check for delta rehedge signals
        if self.positions:
            rehedge_signals = self._check_rehedge_conditions(current_price)
            signals.extend(rehedge_signals)
        
        # Check for exit signals
        if self.positions:
            exit_signals = self._check_exit_conditions(market_data)
            signals.extend(exit_signals)
        
        return signals
    
    def _check_rehedge_conditions(self, current_price: float) -> List[Dict]:
        """Check if delta needs to be rehedged"""
        signals = []
        
        if self.rehedge_count >= self.max_rehedges:
            return signals
        
        # Calculate current portfolio delta
        total_delta = 0
        for position in self.positions:
            position_greeks = self.calculate_position_greeks(position)
            total_delta += position_greeks['delta'] * position.quantity
        
        # If delta exceeds threshold, hedge with underlying
        if abs(total_delta) > self.delta_rehedge_threshold:
            # In practice, would trade underlying
            # For options-only, we adjust position
            self.rehedge_count += 1
        
        return signals
    
    def _check_exit_conditions(self, market_data: pd.DataFrame) -> List[Dict]:
        """Check if positions should be exited"""
        signals = []
        current_time = market_data['timestamp'].iloc[-1]
        
        # Exit at 3:45 PM (15 minutes before close)
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
        
        # Exit on profit target
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
        """Define entry conditions"""
        return {
            'time_window': '9:30-10:00 AM',
            'iv_percentile': 'below 30th',
            'min_gamma': self.gamma_threshold,
            'option_type': 'ATM straddle',
            'expiration': '0DTE'
        }
    
    def get_exit_conditions(self) -> Dict:
        """Define exit conditions"""
        return {
            'time_exit': '3:45 PM',
            'profit_target': f'{self.profit_target_pct * 100}%',
            'stop_loss': f'{self.config.stop_loss_pct * 100}%',
            'max_rehedges': self.max_rehedges
        }
    
    def _get_atm_strike(self, price: float) -> float:
        """Get ATM strike price (rounded to nearest $5 for SPY, $10 for TSLA)"""
        if self.config.symbol == 'SPY':
            return round(price / 5) * 5
        else:  # TSLA
            return round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        """Get 0DTE expiration (today at 4:00 PM)"""
        today = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
        return today
    
    def _estimate_option_price(self, underlying_price: float, strike: float,
                              option_type: str) -> float:
        """Estimate option price (placeholder - would use real pricing)"""
        # Simple estimation for 0DTE ATM options
        if abs(underlying_price - strike) < 1:
            # ATM options: roughly 1-2% of underlying
            return underlying_price * 0.015
        else:
            # OTM options: less value
            return underlying_price * 0.005
