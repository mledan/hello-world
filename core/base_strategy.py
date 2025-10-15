"""
Base strategy class that all trading strategies inherit from
Provides common functionality for strategy execution and management
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy"""
    name: str
    symbol: str
    strategy_type: str  # 'intraday', 'earnings', 'midterm', 'longterm'
    time_horizon: int  # Days to expiration
    max_risk: float  # Maximum $ risk per trade
    max_position_size: float  # Maximum position size as % of portfolio
    stop_loss_pct: float = 0.20
    profit_target_pct: float = 0.50
    parameters: Dict = field(default_factory=dict)


@dataclass
class Trade:
    """Represents a single trade execution"""
    timestamp: datetime
    symbol: str
    action: str  # 'BUY' or 'SELL'
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: datetime
    quantity: int
    price: float
    greeks: Dict = field(default_factory=dict)
    

@dataclass
class Position:
    """Represents a current position"""
    symbol: str
    option_type: str
    strike: float
    expiration: datetime
    quantity: int
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    greeks: Dict = field(default_factory=dict)
    pnl: float = 0.0
    pnl_pct: float = 0.0


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    All strategies must implement generate_signals and execute_trade methods
    """
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator,
                 exposure_calculator):
        """
        Initialize base strategy
        
        Args:
            config: Strategy configuration
            data_fetcher: DataFetcher instance
            greeks_calculator: GreeksCalculator instance
            exposure_calculator: ExposureCalculator instance
        """
        self.config = config
        self.data_fetcher = data_fetcher
        self.greeks_calculator = greeks_calculator
        self.exposure_calculator = exposure_calculator
        
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.closed_positions: List[Position] = []
        
        self.total_pnl = 0.0
        self.total_commissions = 0.0
        self.win_rate = 0.0
        self.sharpe_ratio = 0.0
        
    @abstractmethod
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on market data
        Must be implemented by each strategy
        
        Args:
            market_data: DataFrame with market data
            
        Returns:
            List of signal dictionaries
        """
        pass
    
    @abstractmethod
    def get_entry_conditions(self) -> Dict:
        """
        Define entry conditions for the strategy
        
        Returns:
            Dictionary with entry condition parameters
        """
        pass
    
    @abstractmethod
    def get_exit_conditions(self) -> Dict:
        """
        Define exit conditions for the strategy
        
        Returns:
            Dictionary with exit condition parameters
        """
        pass
    
    def calculate_position_greeks(self, position: Position) -> Dict:
        """
        Calculate Greeks for a position
        
        Args:
            position: Position object
            
        Returns:
            Dictionary with all Greeks
        """
        # Get current underlying price
        S = self.data_fetcher.get_current_price(position.symbol)
        
        # Calculate time to expiration in years
        now = datetime.now()
        T = (position.expiration - now).days / 365.0
        
        # Get dividend yield
        from config.config import GREEKS_CONFIG
        q = GREEKS_CONFIG['dividend_yield'].get(position.symbol, 0.0)
        
        # Calculate Greeks
        # Note: We need IV - in practice, this would come from market data
        # For now, use a placeholder
        sigma = 0.30  # 30% IV placeholder
        
        greeks = self.greeks_calculator.calculate_all_greeks(
            S=S,
            K=position.strike,
            T=max(T, 0),
            r=self.greeks_calculator.risk_free_rate,
            sigma=sigma,
            option_type=position.option_type,
            q=q
        )
        
        return {
            'delta': greeks.delta,
            'gamma': greeks.gamma,
            'theta': greeks.theta,
            'vega': greeks.vega,
            'rho': greeks.rho
        }
    
    def update_positions(self):
        """Update all positions with current prices and Greeks"""
        for position in self.positions:
            # Update current price (placeholder - would fetch from market data)
            position.current_price = self.calculate_option_value(position)
            
            # Update Greeks
            position.greeks = self.calculate_position_greeks(position)
            
            # Calculate PnL
            position.pnl = (position.current_price - position.entry_price) * position.quantity * 100
            position.pnl_pct = ((position.current_price - position.entry_price) / 
                               position.entry_price * 100 if position.entry_price > 0 else 0)
    
    def calculate_option_value(self, position: Position) -> float:
        """
        Calculate current value of an option position
        
        Args:
            position: Position object
            
        Returns:
            Current option price
        """
        S = self.data_fetcher.get_current_price(position.symbol)
        now = datetime.now()
        T = (position.expiration - now).days / 365.0
        
        from config.config import GREEKS_CONFIG
        q = GREEKS_CONFIG['dividend_yield'].get(position.symbol, 0.0)
        
        # Placeholder IV
        sigma = 0.30
        
        price = self.greeks_calculator.calculate_option_price(
            S=S,
            K=position.strike,
            T=max(T, 0),
            r=self.greeks_calculator.risk_free_rate,
            sigma=sigma,
            option_type=position.option_type,
            q=q
        )
        
        return price
    
    def check_exit_conditions(self, position: Position) -> bool:
        """
        Check if exit conditions are met for a position
        
        Args:
            position: Position to check
            
        Returns:
            True if should exit, False otherwise
        """
        # Stop loss check
        if position.pnl_pct <= -self.config.stop_loss_pct * 100:
            return True
        
        # Profit target check
        if position.pnl_pct >= self.config.profit_target_pct * 100:
            return True
        
        # Expiration check
        days_to_expiry = (position.expiration - datetime.now()).days
        if days_to_expiry <= 0:
            return True
        
        return False
    
    def execute_trade(self, signal: Dict) -> Optional[Trade]:
        """
        Execute a trade based on a signal
        
        Args:
            signal: Signal dictionary with trade parameters
            
        Returns:
            Trade object if executed, None otherwise
        """
        # Check risk limits
        if not self.check_risk_limits():
            return None
        
        trade = Trade(
            timestamp=datetime.now(),
            symbol=signal['symbol'],
            action=signal['action'],
            option_type=signal['option_type'],
            strike=signal['strike'],
            expiration=signal['expiration'],
            quantity=signal['quantity'],
            price=signal['price'],
            greeks=signal.get('greeks', {})
        )
        
        self.trades.append(trade)
        
        # Update positions
        if trade.action == 'BUY':
            self.open_position(trade)
        elif trade.action == 'SELL':
            self.close_position(trade)
        
        return trade
    
    def open_position(self, trade: Trade):
        """
        Open a new position from a trade
        
        Args:
            trade: Trade object
        """
        position = Position(
            symbol=trade.symbol,
            option_type=trade.option_type,
            strike=trade.strike,
            expiration=trade.expiration,
            quantity=trade.quantity,
            entry_price=trade.price,
            entry_time=trade.timestamp,
            current_price=trade.price,
            greeks=trade.greeks
        )
        
        self.positions.append(position)
    
    def close_position(self, trade: Trade):
        """
        Close an existing position
        
        Args:
            trade: Trade object (sell)
        """
        # Find matching position
        for i, position in enumerate(self.positions):
            if (position.symbol == trade.symbol and
                position.strike == trade.strike and
                position.expiration == trade.expiration and
                position.option_type == trade.option_type):
                
                # Calculate final PnL
                position.current_price = trade.price
                position.pnl = (trade.price - position.entry_price) * position.quantity * 100
                
                # Move to closed positions
                self.closed_positions.append(position)
                self.positions.pop(i)
                
                # Update total PnL
                self.total_pnl += position.pnl
                
                break
    
    def check_risk_limits(self) -> bool:
        """
        Check if risk limits allow new position
        
        Returns:
            True if can open new position, False otherwise
        """
        exposure = self.exposure_calculator.calculate_portfolio_exposure()
        
        from config.config import RISK_MANAGEMENT
        
        # Check delta and gamma limits
        if abs(exposure.total_delta) > RISK_MANAGEMENT['max_delta_exposure']:
            return False
        
        if abs(exposure.total_gamma) > RISK_MANAGEMENT['max_gamma_exposure']:
            return False
        
        return True
    
    def get_performance_metrics(self) -> Dict:
        """
        Calculate performance metrics for the strategy
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.closed_positions:
            return {
                'total_pnl': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_trades': 0
            }
        
        wins = [p.pnl for p in self.closed_positions if p.pnl > 0]
        losses = [p.pnl for p in self.closed_positions if p.pnl < 0]
        
        win_rate = len(wins) / len(self.closed_positions) * 100 if self.closed_positions else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0
        
        return {
            'total_pnl': self.total_pnl,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_trades': len(self.closed_positions),
            'open_positions': len(self.positions)
        }
    
    def reset(self):
        """Reset strategy state"""
        self.positions = []
        self.trades = []
        self.closed_positions = []
        self.total_pnl = 0.0
        self.total_commissions = 0.0
