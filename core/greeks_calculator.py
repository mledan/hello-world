"""
Greeks calculation engine using Black-Scholes model
Calculates delta, gamma, theta, vega, and rho for options
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class Greeks:
    """Data class to store all Greeks for an option"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    

class GreeksCalculator:
    """
    Centralized Greeks calculation using Black-Scholes model
    Optimized for batch calculations across multiple strategies
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize GreeksCalculator
        
        Args:
            risk_free_rate: Annual risk-free rate (default 5%)
        """
        self.risk_free_rate = risk_free_rate
        
    def calculate_all_greeks(self, S: float, K: float, T: float, r: float,
                            sigma: float, option_type: str = 'call',
                            q: float = 0.0) -> Greeks:
        """
        Calculate all Greeks for an option
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Implied volatility (annualized)
            option_type: 'call' or 'put'
            q: Dividend yield (default 0)
            
        Returns:
            Greeks object with all calculated Greeks
        """
        if T <= 0:
            # At expiration or expired
            return self._calculate_greeks_at_expiration(S, K, option_type)
        
        d1 = self._calculate_d1(S, K, T, r, sigma, q)
        d2 = self._calculate_d2(d1, sigma, T)
        
        delta = self._calculate_delta(d1, option_type, T, q)
        gamma = self._calculate_gamma(S, d1, T, sigma, q)
        theta = self._calculate_theta(S, K, T, r, sigma, d1, d2, option_type, q)
        vega = self._calculate_vega(S, d1, T, q)
        rho = self._calculate_rho(K, T, r, d2, option_type, q)
        
        return Greeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )
    
    def _calculate_d1(self, S: float, K: float, T: float, r: float,
                      sigma: float, q: float = 0.0) -> float:
        """Calculate d1 parameter for Black-Scholes"""
        return (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    def _calculate_d2(self, d1: float, sigma: float, T: float) -> float:
        """Calculate d2 parameter for Black-Scholes"""
        return d1 - sigma * np.sqrt(T)
    
    def _calculate_delta(self, d1: float, option_type: str, T: float, q: float) -> float:
        """
        Calculate delta (rate of change of option price w.r.t. underlying price)
        
        Returns:
            Delta value (-1 to 1)
        """
        if option_type.lower() == 'call':
            return np.exp(-q * T) * norm.cdf(d1)
        else:  # put
            return -np.exp(-q * T) * norm.cdf(-d1)
    
    def _calculate_gamma(self, S: float, d1: float, T: float, sigma: float, q: float) -> float:
        """
        Calculate gamma (rate of change of delta w.r.t. underlying price)
        
        Returns:
            Gamma value (always positive)
        """
        return (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * np.sqrt(T))
    
    def _calculate_theta(self, S: float, K: float, T: float, r: float, sigma: float,
                        d1: float, d2: float, option_type: str, q: float) -> float:
        """
        Calculate theta (rate of change of option price w.r.t. time)
        
        Returns:
            Theta value per day (usually negative)
        """
        first_term = -(S * norm.pdf(d1) * sigma * np.exp(-q * T)) / (2 * np.sqrt(T))
        
        if option_type.lower() == 'call':
            second_term = r * K * np.exp(-r * T) * norm.cdf(d2)
            third_term = -q * S * np.exp(-q * T) * norm.cdf(d1)
            theta = first_term - second_term + third_term
        else:  # put
            second_term = r * K * np.exp(-r * T) * norm.cdf(-d2)
            third_term = -q * S * np.exp(-q * T) * norm.cdf(-d1)
            theta = first_term + second_term + third_term
        
        # Return daily theta (divide by 365)
        return theta / 365
    
    def _calculate_vega(self, S: float, d1: float, T: float, q: float) -> float:
        """
        Calculate vega (rate of change of option price w.r.t. volatility)
        
        Returns:
            Vega value per 1% change in IV
        """
        vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)
        # Return vega per 1% change (divide by 100)
        return vega / 100
    
    def _calculate_rho(self, K: float, T: float, r: float, d2: float,
                       option_type: str, q: float) -> float:
        """
        Calculate rho (rate of change of option price w.r.t. interest rate)
        
        Returns:
            Rho value per 1% change in interest rate
        """
        if option_type.lower() == 'call':
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
        
        # Return rho per 1% change (divide by 100)
        return rho / 100
    
    def _calculate_greeks_at_expiration(self, S: float, K: float,
                                       option_type: str) -> Greeks:
        """
        Calculate Greeks at expiration (T=0)
        
        Returns:
            Greeks object with values at expiration
        """
        if option_type.lower() == 'call':
            delta = 1.0 if S > K else 0.0
        else:
            delta = -1.0 if S < K else 0.0
        
        return Greeks(
            delta=delta,
            gamma=0.0,  # No gamma at expiration
            theta=0.0,  # No theta at expiration
            vega=0.0,   # No vega at expiration
            rho=0.0     # No rho at expiration
        )
    
    def calculate_option_price(self, S: float, K: float, T: float, r: float,
                              sigma: float, option_type: str = 'call',
                              q: float = 0.0) -> float:
        """
        Calculate option price using Black-Scholes
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            q: Dividend yield
            
        Returns:
            Option price
        """
        if T <= 0:
            # At expiration
            if option_type.lower() == 'call':
                return max(S - K, 0)
            else:
                return max(K - S, 0)
        
        d1 = self._calculate_d1(S, K, T, r, sigma, q)
        d2 = self._calculate_d2(d1, sigma, T)
        
        if option_type.lower() == 'call':
            price = (S * np.exp(-q * T) * norm.cdf(d1) -
                    K * np.exp(-r * T) * norm.cdf(d2))
        else:  # put
            price = (K * np.exp(-r * T) * norm.cdf(-d2) -
                    S * np.exp(-q * T) * norm.cdf(-d1))
        
        return price
    
    def calculate_implied_volatility(self, market_price: float, S: float, K: float,
                                    T: float, r: float, option_type: str = 'call',
                                    q: float = 0.0, max_iterations: int = 100,
                                    tolerance: float = 1e-5) -> float:
        """
        Calculate implied volatility using Newton-Raphson method
        
        Args:
            market_price: Observed market price of option
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            option_type: 'call' or 'put'
            q: Dividend yield
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance
            
        Returns:
            Implied volatility (annualized)
        """
        # Initial guess
        sigma = 0.3
        
        for i in range(max_iterations):
            price = self.calculate_option_price(S, K, T, r, sigma, option_type, q)
            diff = market_price - price
            
            if abs(diff) < tolerance:
                return sigma
            
            # Calculate vega for Newton-Raphson
            d1 = self._calculate_d1(S, K, T, r, sigma, q)
            vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)
            
            if vega < 1e-10:
                break
            
            # Update sigma
            sigma = sigma + diff / vega
            
            # Ensure sigma stays positive
            if sigma <= 0:
                sigma = 0.01
        
        return sigma
    
    def batch_calculate_greeks(self, positions: list) -> list:
        """
        Calculate Greeks for multiple positions efficiently
        
        Args:
            positions: List of dicts with position parameters
                      [{S, K, T, r, sigma, option_type, q, quantity}, ...]
        
        Returns:
            List of Greeks objects
        """
        results = []
        
        for position in positions:
            greeks = self.calculate_all_greeks(
                S=position['S'],
                K=position['K'],
                T=position['T'],
                r=position.get('r', self.risk_free_rate),
                sigma=position['sigma'],
                option_type=position['option_type'],
                q=position.get('q', 0.0)
            )
            results.append(greeks)
        
        return results
