"""
Delta Neutral Straddle Strategy (0DTE)
Buy ATM straddle and maintain delta neutrality throughout the day
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig


class DeltaNeutralStraddleStrategy(BaseStrategy):
    """
    Delta Neutral Straddle - profit from volatility without directional bias
    
    Entry: Buy ATM straddle when IV is below historical average
    Management: Rebalance to maintain delta neutrality
    Exit: Profit target or end of day
    
    Parameters:
    - iv_entry_threshold: Max IV percentile to enter (default: 40)
    - delta_neutral_tolerance: Max delta deviation (default: 0.10)
    - profit_target_pct: Target profit (default: 40%)
    - rebalance_frequency: Minutes between rebalances (default: 30)
    """
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator,
                 exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        
        self.iv_entry_threshold = config.parameters.get('iv_entry_threshold', 40)
        self.delta_neutral_tolerance = config.parameters.get('delta_neutral_tolerance', 0.10)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.40)
        self.rebalance_frequency = config.parameters.get('rebalance_frequency', 30)
        
        self.last_rebalance_time = None
        self.entry_time = None
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        """Generate delta neutral straddle signals"""
        signals = []
        
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Entry logic - early morning (9:30-10:00)
        if not self.positions and current_time.hour == 9 and current_time.minute >= 30:
            atm_strike = self._get_atm_strike(current_price)
            
            # Buy straddle
            signals.append({
                'symbol': self.config.symbol,
                'action': 'BUY',
                'option_type': 'call',
                'strike': atm_strike,
                'expiration': self._get_0dte_expiration(),
                'quantity': 1,
                'price': self._estimate_option_price(current_price, atm_strike, 'call', 0.25),
                'signal_type': 'ENTRY_STRADDLE'
            })
            
            signals.append({
                'symbol': self.config.symbol,
                'action': 'BUY',
                'option_type': 'put',
                'strike': atm_strike,
                'expiration': self._get_0dte_expiration(),
                'quantity': 1,
                'price': self._estimate_option_price(current_price, atm_strike, 'put', 0.25),
                'signal_type': 'ENTRY_STRADDLE'
            })
            
            self.entry_time = current_time
        
        # Rebalancing logic
        if self.positions and self._should_rebalance(current_time):
            rebalance_signals = self._generate_rebalance_signals(current_price)
            signals.extend(rebalance_signals)
        
        # Exit logic
        if self.positions:
            exit_signals = self._check_exit_conditions(market_data)
            signals.extend(exit_signals)
        
        return signals
    
    def _should_rebalance(self, current_time: datetime) -> bool:
        """Check if it's time to rebalance"""
        if self.last_rebalance_time is None:
            self.last_rebalance_time = current_time
            return True
        
        minutes_since_rebalance = (current_time - self.last_rebalance_time).seconds / 60
        return minutes_since_rebalance >= self.rebalance_frequency
    
    def _generate_rebalance_signals(self, current_price: float) -> List[Dict]:
        """Generate signals to maintain delta neutrality"""
        signals = []
        
        # Calculate portfolio delta
        total_delta = sum(
            self.calculate_position_greeks(p)['delta'] * p.quantity 
            for p in self.positions
        )
        
        # If delta is outside tolerance, adjust
        if abs(total_delta) > self.delta_neutral_tolerance:
            # Adjust by trading additional options
            # If delta is positive (too bullish), buy puts or sell calls
            # If delta is negative (too bearish), buy calls or sell puts
            
            if total_delta > self.delta_neutral_tolerance:
                # Need to reduce delta - buy puts
                adjustment_quantity = int(abs(total_delta) / 0.5)  # Approx delta per ATM put
                
                signals.append({
                    'symbol': self.config.symbol,
                    'action': 'BUY',
                    'option_type': 'put',
                    'strike': self._get_atm_strike(current_price),
                    'expiration': self._get_0dte_expiration(),
                    'quantity': adjustment_quantity,
                    'price': self._estimate_option_price(current_price, 
                                                        self._get_atm_strike(current_price), 
                                                        'put', 0.25),
                    'signal_type': 'REBALANCE_DELTA'
                })
            
            elif total_delta < -self.delta_neutral_tolerance:
                # Need to increase delta - buy calls
                adjustment_quantity = int(abs(total_delta) / 0.5)
                
                signals.append({
                    'symbol': self.config.symbol,
                    'action': 'BUY',
                    'option_type': 'call',
                    'strike': self._get_atm_strike(current_price),
                    'expiration': self._get_0dte_expiration(),
                    'quantity': adjustment_quantity,
                    'price': self._estimate_option_price(current_price,
                                                        self._get_atm_strike(current_price),
                                                        'call', 0.25),
                    'signal_type': 'REBALANCE_DELTA'
                })
        
        self.last_rebalance_time = datetime.now()
        return signals
    
    def _check_exit_conditions(self, market_data: pd.DataFrame) -> List[Dict]:
        """Check exit conditions"""
        signals = []
        current_time = market_data['timestamp'].iloc[-1]
        
        # Time-based exit (3:45 PM)
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
        
        # Profit target exit
        total_pnl_pct = sum(p.pnl_pct for p in self.positions) / len(self.positions) if self.positions else 0
        
        if total_pnl_pct >= self.profit_target_pct * 100:
            for position in self.positions:
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
            'iv_percentile': f'below {self.iv_entry_threshold}th',
            'option_structure': 'ATM straddle',
            'expiration': '0DTE',
            'delta_target': '0 (neutral)'
        }
    
    def get_exit_conditions(self) -> Dict:
        """Define exit conditions"""
        return {
            'time_exit': '3:45 PM',
            'profit_target': f'{self.profit_target_pct * 100}%',
            'stop_loss': f'{self.config.stop_loss_pct * 100}%',
            'delta_tolerance': self.delta_neutral_tolerance
        }
    
    def _get_atm_strike(self, price: float) -> float:
        """Get ATM strike"""
        if self.config.symbol == 'SPY':
            return round(price / 5) * 5
        else:
            return round(price / 10) * 10
    
    def _get_0dte_expiration(self) -> datetime:
        """Get 0DTE expiration"""
        return datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
    
    def _estimate_option_price(self, underlying: float, strike: float, 
                              option_type: str, iv: float) -> float:
        """Estimate option price"""
        T = 6.5 / 252  # Hours left in trading day / trading days per year
        
        price = self.greeks_calculator.calculate_option_price(
            S=underlying,
            K=strike,
            T=T,
            r=0.05,
            sigma=iv,
            option_type=option_type,
            q=0.0125 if self.config.symbol == 'SPY' else 0.0
        )
        
        return price
