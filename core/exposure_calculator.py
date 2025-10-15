"""
Portfolio exposure calculator for delta, gamma, and other Greeks
Aggregates exposures across all positions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PortfolioExposure:
    """Portfolio-level exposure metrics"""
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float
    total_rho: float
    net_delta_dollars: float
    net_gamma_dollars: float
    delta_exposure_pct: float  # As % of portfolio
    gamma_exposure_pct: float
    

class ExposureCalculator:
    """
    Calculate and manage portfolio-level exposures
    Tracks delta, gamma, and other Greek exposures across all positions
    """
    
    def __init__(self, portfolio_value: float):
        """
        Initialize ExposureCalculator
        
        Args:
            portfolio_value: Total portfolio value
        """
        self.portfolio_value = portfolio_value
        self.positions = []
        
    def add_position(self, position: Dict):
        """
        Add a position to the portfolio
        
        Args:
            position: Dictionary with position details
                     {symbol, strike, expiration, option_type, quantity,
                      greeks, underlying_price, contract_multiplier}
        """
        self.positions.append(position)
    
    def calculate_portfolio_exposure(self) -> PortfolioExposure:
        """
        Calculate aggregate portfolio exposure
        
        Returns:
            PortfolioExposure object with all metrics
        """
        if not self.positions:
            return PortfolioExposure(0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        
        for position in self.positions:
            quantity = position['quantity']
            greeks = position['greeks']
            multiplier = position.get('contract_multiplier', 100)  # Standard options multiplier
            
            # Aggregate Greeks (per contract * quantity)
            total_delta += greeks.delta * quantity
            total_gamma += greeks.gamma * quantity
            total_theta += greeks.theta * quantity
            total_vega += greeks.vega * quantity
            total_rho += greeks.rho * quantity
        
        # Calculate dollar exposures
        # Delta exposure = total_delta * underlying_price * multiplier
        # For simplicity, we'll use average underlying price across positions
        avg_underlying_price = np.mean([p['underlying_price'] for p in self.positions])
        multiplier = 100  # Standard options multiplier
        
        net_delta_dollars = total_delta * avg_underlying_price * multiplier
        net_gamma_dollars = total_gamma * avg_underlying_price * multiplier
        
        # Calculate exposures as % of portfolio
        delta_exposure_pct = (net_delta_dollars / self.portfolio_value) * 100 if self.portfolio_value > 0 else 0
        gamma_exposure_pct = (net_gamma_dollars / self.portfolio_value) * 100 if self.portfolio_value > 0 else 0
        
        return PortfolioExposure(
            total_delta=total_delta,
            total_gamma=total_gamma,
            total_theta=total_theta,
            total_vega=total_vega,
            total_rho=total_rho,
            net_delta_dollars=net_delta_dollars,
            net_gamma_dollars=net_gamma_dollars,
            delta_exposure_pct=delta_exposure_pct,
            gamma_exposure_pct=gamma_exposure_pct
        )
    
    def calculate_intraday_gamma_exposure(self, price_moves: List[float]) -> pd.DataFrame:
        """
        Calculate expected gamma exposure for different intraday price moves
        
        Args:
            price_moves: List of potential price moves (e.g., [-1%, -0.5%, 0%, 0.5%, 1%])
        
        Returns:
            DataFrame with gamma exposure analysis
        """
        exposure = self.calculate_portfolio_exposure()
        base_delta = exposure.total_delta
        
        results = []
        
        for move in price_moves:
            # Approximate delta change using gamma
            # New Delta ≈ Old Delta + Gamma * Price Change
            price_change_pct = move / 100
            
            # Get average underlying price
            if self.positions:
                avg_price = np.mean([p['underlying_price'] for p in self.positions])
                price_change = avg_price * price_change_pct
                
                new_delta = base_delta + (exposure.total_gamma * price_change)
                delta_change = new_delta - base_delta
                
                results.append({
                    'price_move_pct': move,
                    'price_move_dollars': price_change,
                    'initial_delta': base_delta,
                    'new_delta': new_delta,
                    'delta_change': delta_change,
                    'gamma_effect': exposure.total_gamma * price_change
                })
        
        return pd.DataFrame(results)
    
    def calculate_delta_hedge_ratio(self) -> float:
        """
        Calculate the number of shares needed to delta hedge the portfolio
        
        Returns:
            Number of shares (positive = buy, negative = sell)
        """
        exposure = self.calculate_portfolio_exposure()
        # To hedge, we need opposite delta
        # Since each share has delta of 1, we need -total_delta shares
        return -exposure.total_delta * 100  # *100 for contract multiplier
    
    def check_risk_limits(self, max_delta: float, max_gamma: float) -> Dict[str, bool]:
        """
        Check if portfolio exposures are within risk limits
        
        Args:
            max_delta: Maximum allowed delta exposure
            max_gamma: Maximum allowed gamma exposure
            
        Returns:
            Dictionary with limit check results
        """
        exposure = self.calculate_portfolio_exposure()
        
        return {
            'delta_within_limits': abs(exposure.total_delta) <= max_delta,
            'gamma_within_limits': abs(exposure.total_gamma) <= max_gamma,
            'delta_value': exposure.total_delta,
            'gamma_value': exposure.total_gamma,
            'delta_limit': max_delta,
            'gamma_limit': max_gamma
        }
    
    def calculate_position_sizing(self, strategy_delta: float, strategy_gamma: float,
                                 max_position_size_pct: float = 0.10) -> int:
        """
        Calculate optimal position size based on risk limits
        
        Args:
            strategy_delta: Delta per contract of the strategy
            strategy_gamma: Gamma per contract of the strategy
            max_position_size_pct: Maximum position size as % of portfolio
            
        Returns:
            Number of contracts to trade
        """
        max_position_value = self.portfolio_value * max_position_size_pct
        
        # Calculate based on delta exposure
        max_contracts_delta = max_position_value / (abs(strategy_delta) * 100)
        
        # Calculate based on gamma exposure
        max_contracts_gamma = max_position_value / (abs(strategy_gamma) * 100)
        
        # Take the minimum to ensure we don't exceed either limit
        max_contracts = min(max_contracts_delta, max_contracts_gamma)
        
        return int(max_contracts)
    
    def get_exposure_by_symbol(self) -> pd.DataFrame:
        """
        Get exposure breakdown by underlying symbol
        
        Returns:
            DataFrame with exposures by symbol
        """
        symbol_exposures = {}
        
        for position in self.positions:
            symbol = position['symbol']
            greeks = position['greeks']
            quantity = position['quantity']
            
            if symbol not in symbol_exposures:
                symbol_exposures[symbol] = {
                    'delta': 0,
                    'gamma': 0,
                    'theta': 0,
                    'vega': 0,
                    'positions': 0
                }
            
            symbol_exposures[symbol]['delta'] += greeks.delta * quantity
            symbol_exposures[symbol]['gamma'] += greeks.gamma * quantity
            symbol_exposures[symbol]['theta'] += greeks.theta * quantity
            symbol_exposures[symbol]['vega'] += greeks.vega * quantity
            symbol_exposures[symbol]['positions'] += 1
        
        return pd.DataFrame.from_dict(symbol_exposures, orient='index')
    
    def clear_positions(self):
        """Clear all positions"""
        self.positions = []
    
    def get_net_delta_dollars_by_strike(self, symbol: str) -> pd.DataFrame:
        """
        Calculate net delta dollars by strike price for a given symbol
        Useful for understanding pin risk and concentration
        
        Args:
            symbol: Underlying symbol
            
        Returns:
            DataFrame with delta exposure by strike
        """
        strike_data = {}
        
        for position in self.positions:
            if position['symbol'] == symbol:
                strike = position['strike']
                delta = position['greeks'].delta
                quantity = position['quantity']
                underlying_price = position['underlying_price']
                
                delta_dollars = delta * quantity * underlying_price * 100
                
                if strike not in strike_data:
                    strike_data[strike] = {
                        'delta_dollars': 0,
                        'positions': 0
                    }
                
                strike_data[strike]['delta_dollars'] += delta_dollars
                strike_data[strike]['positions'] += 1
        
        df = pd.DataFrame.from_dict(strike_data, orient='index')
        df.index.name = 'strike'
        return df.sort_index()
