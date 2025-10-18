"""
Portfolio management for backtesting
"""

from typing import Dict, List
from datetime import datetime


class Portfolio:
    """Manage portfolio state during backtesting"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = []
        self.closed_positions = []
        
    def add_position(self, position: Dict):
        """Add new position to portfolio"""
        self.positions.append(position)
        
    def remove_position(self, symbol: str, strike: float, expiration: datetime):
        """Remove position from portfolio"""
        for i, pos in enumerate(self.positions):
            if (pos['symbol'] == symbol and 
                pos['strike'] == strike and 
                pos['expiration'] == expiration):
                self.closed_positions.append(self.positions.pop(i))
                break
    
    def get_position_value(self) -> float:
        """Calculate total value of all positions"""
        return sum(p.get('current_value', 0) for p in self.positions)
    
    def get_total_equity(self) -> float:
        """Calculate total portfolio equity"""
        return self.cash + self.get_position_value()
    
    def update_cash(self, amount: float):
        """Update cash balance"""
        self.cash += amount
