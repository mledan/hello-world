"""
Risk management module for portfolio and position-level risk controls
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class RiskMetrics:
    """Risk metrics for a position or portfolio"""
    value_at_risk_95: float  # 95% VaR
    value_at_risk_99: float  # 99% VaR
    expected_shortfall: float  # CVaR
    max_loss: float
    position_size_pct: float
    leverage: float


class RiskManager:
    """
    Centralized risk management system
    Handles position sizing, risk limits, and portfolio risk metrics
    """
    
    def __init__(self, portfolio_value: float, max_portfolio_risk: float = 0.05):
        """
        Initialize RiskManager
        
        Args:
            portfolio_value: Total portfolio value
            max_portfolio_risk: Maximum portfolio risk as decimal (default 5%)
        """
        self.portfolio_value = portfolio_value
        self.max_portfolio_risk = max_portfolio_risk
        self.positions = []
        
    def calculate_position_size(self, strategy_risk: float, 
                               win_rate: float = 0.5,
                               risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate optimal position size using Kelly Criterion
        
        Args:
            strategy_risk: Risk per trade as decimal
            win_rate: Historical win rate (default 50%)
            risk_reward_ratio: Reward to risk ratio
            
        Returns:
            Position size as % of portfolio
        """
        # Kelly Criterion: f = (p * b - q) / b
        # where p = win rate, q = loss rate, b = win/loss ratio
        
        p = win_rate
        q = 1 - win_rate
        b = risk_reward_ratio
        
        kelly_fraction = (p * b - q) / b
        
        # Use fractional Kelly (25% of Kelly) for more conservative sizing
        fractional_kelly = kelly_fraction * 0.25
        
        # Ensure position size doesn't exceed max portfolio risk
        position_size = min(fractional_kelly, self.max_portfolio_risk)
        
        # Ensure position size is positive and reasonable
        return max(0.01, min(position_size, 0.10))  # Between 1% and 10%
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            returns: List of historical returns
            confidence_level: Confidence level (default 95%)
            
        Returns:
            VaR value
        """
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        var = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        return abs(var)
    
    def calculate_cvar(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall)
        
        Args:
            returns: List of historical returns
            confidence_level: Confidence level (default 95%)
            
        Returns:
            CVaR value
        """
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        var_threshold = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        # Calculate average of returns below VaR threshold
        tail_returns = returns_array[returns_array <= var_threshold]
        
        if len(tail_returns) > 0:
            cvar = np.mean(tail_returns)
        else:
            cvar = var_threshold
        
        return abs(cvar)
    
    def calculate_max_position_size_greeks(self, delta: float, gamma: float,
                                          underlying_price: float,
                                          max_delta_dollars: float = 50000,
                                          max_gamma_dollars: float = 10000) -> int:
        """
        Calculate maximum position size based on Greeks limits
        
        Args:
            delta: Delta per contract
            gamma: Gamma per contract
            underlying_price: Current underlying price
            max_delta_dollars: Maximum delta exposure in dollars
            max_gamma_dollars: Maximum gamma exposure in dollars
            
        Returns:
            Maximum number of contracts
        """
        # Calculate max contracts based on delta
        delta_dollars_per_contract = abs(delta) * underlying_price * 100
        max_contracts_delta = max_delta_dollars / delta_dollars_per_contract if delta_dollars_per_contract > 0 else float('inf')
        
        # Calculate max contracts based on gamma
        gamma_dollars_per_contract = abs(gamma) * underlying_price * 100
        max_contracts_gamma = max_gamma_dollars / gamma_dollars_per_contract if gamma_dollars_per_contract > 0 else float('inf')
        
        # Take minimum to respect both limits
        max_contracts = min(max_contracts_delta, max_contracts_gamma)
        
        return int(max_contracts)
    
    def check_concentration_risk(self, symbol: str, position_value: float,
                                threshold: float = 0.25) -> bool:
        """
        Check if adding a position would create concentration risk
        
        Args:
            symbol: Symbol to check
            position_value: Value of proposed position
            threshold: Maximum concentration threshold (default 25%)
            
        Returns:
            True if concentration risk is acceptable, False otherwise
        """
        # Calculate current exposure to symbol
        symbol_exposure = sum(p['value'] for p in self.positions if p['symbol'] == symbol)
        
        # Add proposed position
        new_exposure = symbol_exposure + position_value
        
        # Check if new exposure exceeds threshold
        concentration_pct = new_exposure / self.portfolio_value
        
        return concentration_pct <= threshold
    
    def calculate_stop_loss(self, entry_price: float, strategy_type: str,
                           volatility: float) -> float:
        """
        Calculate dynamic stop loss based on strategy type and volatility
        
        Args:
            entry_price: Entry price of position
            strategy_type: Type of strategy (intraday, midterm, longterm)
            volatility: Current volatility (annualized)
            
        Returns:
            Stop loss price
        """
        # Base stop loss percentages by strategy type
        base_stops = {
            'intraday': 0.20,    # 20% for 0DTE
            'earnings': 0.30,    # 30% for earnings (higher vol)
            'midterm': 0.25,     # 25% for mid-term
            'longterm': 0.35     # 35% for LEAPs (more room)
        }
        
        base_stop = base_stops.get(strategy_type, 0.20)
        
        # Adjust for volatility (higher vol = wider stop)
        vol_adjustment = 1 + (volatility - 0.30) / 0.30  # Normalize around 30% IV
        adjusted_stop = base_stop * vol_adjustment
        
        # Calculate stop loss price
        stop_loss = entry_price * (1 - adjusted_stop)
        
        return stop_loss
    
    def calculate_profit_target(self, entry_price: float, strategy_type: str,
                               risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate profit target based on risk-reward ratio
        
        Args:
            entry_price: Entry price of position
            strategy_type: Type of strategy
            risk_reward_ratio: Desired risk-reward ratio
            
        Returns:
            Profit target price
        """
        # Calculate stop loss
        stop_loss = self.calculate_stop_loss(entry_price, strategy_type, 0.30)
        
        # Calculate risk amount
        risk_amount = entry_price - stop_loss
        
        # Calculate profit target
        profit_target = entry_price + (risk_amount * risk_reward_ratio)
        
        return profit_target
    
    def calculate_portfolio_beta(self, positions: List[Dict],
                                market_returns: List[float]) -> float:
        """
        Calculate portfolio beta relative to market (SPY)
        
        Args:
            positions: List of positions with deltas
            market_returns: Historical market returns
            
        Returns:
            Portfolio beta
        """
        # Calculate portfolio delta
        total_delta = sum(p.get('delta', 0) * p.get('quantity', 0) for p in positions)
        
        # Beta approximation from delta
        # For options, beta ≈ delta * underlying_beta
        # Assuming SPY positions have beta of 1
        
        portfolio_beta = total_delta / 100  # Normalize by contract multiplier
        
        return portfolio_beta
    
    def calculate_sharpe_ratio(self, returns: List[float], 
                              risk_free_rate: float = 0.05) -> float:
        """
        Calculate Sharpe Ratio
        
        Args:
            returns: List of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        
        # Calculate excess returns
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
        
        # Calculate Sharpe ratio
        if np.std(excess_returns) > 0:
            sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        else:
            sharpe = 0.0
        
        return sharpe
    
    def calculate_sortino_ratio(self, returns: List[float],
                               risk_free_rate: float = 0.05) -> float:
        """
        Calculate Sortino Ratio (only considers downside volatility)
        
        Args:
            returns: List of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sortino ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        
        # Calculate excess returns
        excess_returns = returns_array - (risk_free_rate / 252)
        
        # Calculate downside deviation
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) > 0:
            downside_std = np.std(downside_returns)
            if downside_std > 0:
                sortino = np.mean(excess_returns) / downside_std * np.sqrt(252)
            else:
                sortino = 0.0
        else:
            sortino = 0.0
        
        return sortino
    
    def add_position(self, position: Dict):
        """Add a position to track"""
        self.positions.append(position)
    
    def remove_position(self, position_id: str):
        """Remove a position"""
        self.positions = [p for p in self.positions if p.get('id') != position_id]
    
    def get_total_risk_exposure(self) -> float:
        """
        Calculate total risk exposure across all positions
        
        Returns:
            Total risk as % of portfolio
        """
        total_risk = sum(p.get('risk_amount', 0) for p in self.positions)
        return total_risk / self.portfolio_value if self.portfolio_value > 0 else 0
