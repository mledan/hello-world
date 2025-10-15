"""
Backtesting engine for strategy evaluation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import sys
sys.path.append('/workspace')


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    strategy_name: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_pnl: float
    volatility: float
    calmar_ratio: float
    trades: List[Dict]
    equity_curve: pd.DataFrame


class BacktestEngine:
    """
    Backtesting engine for evaluating trading strategies
    Simulates strategy execution on historical data
    """
    
    def __init__(self, initial_capital: float = 100000, 
                 commission_per_contract: float = 0.65,
                 slippage_pct: float = 0.001):
        """
        Initialize backtesting engine
        
        Args:
            initial_capital: Starting capital
            commission_per_contract: Commission per contract
            slippage_pct: Slippage as percentage
        """
        self.initial_capital = initial_capital
        self.commission_per_contract = commission_per_contract
        self.slippage_pct = slippage_pct
        
        self.current_capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
    def run_backtest(self, strategy, market_data: pd.DataFrame,
                    start_date: str, end_date: str) -> BacktestResult:
        """
        Run backtest for a strategy
        
        Args:
            strategy: Strategy instance to backtest
            market_data: Historical market data
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            BacktestResult with performance metrics
        """
        # Reset state
        self.current_capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        # Filter data by date range
        market_data = market_data[
            (market_data['timestamp'] >= start_date) &
            (market_data['timestamp'] <= end_date)
        ].copy()
        
        # Simulate trading day by day
        for idx, row in market_data.iterrows():
            current_time = row['timestamp']
            current_slice = market_data[market_data['timestamp'] <= current_time]
            
            # Update positions
            self._update_positions(row)
            
            # Generate signals from strategy
            signals = strategy.generate_signals(current_slice)
            
            # Execute signals
            for signal in signals:
                self._execute_signal(signal, row)
            
            # Record equity
            equity = self._calculate_equity(row)
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': equity,
                'cash': self.current_capital,
                'positions_value': equity - self.current_capital
            })
        
        # Calculate performance metrics
        result = self._calculate_performance_metrics(strategy.config.name)
        
        return result
    
    def _execute_signal(self, signal: Dict, market_row: pd.Series):
        """Execute a trading signal"""
        action = signal['action']
        price = signal['price']
        quantity = signal['quantity']
        
        # Apply slippage
        if action == 'BUY':
            execution_price = price * (1 + self.slippage_pct)
        else:
            execution_price = price * (1 - self.slippage_pct)
        
        # Calculate cost
        cost = execution_price * quantity * 100  # 100 shares per contract
        commission = self.commission_per_contract * quantity
        total_cost = cost + commission
        
        # Check if we have enough capital
        if action == 'BUY' and total_cost > self.current_capital:
            return  # Skip trade if insufficient capital
        
        # Execute trade
        if action == 'BUY':
            self.current_capital -= total_cost
            self.positions.append({
                'symbol': signal['symbol'],
                'option_type': signal['option_type'],
                'strike': signal['strike'],
                'expiration': signal['expiration'],
                'quantity': quantity,
                'entry_price': execution_price,
                'entry_time': market_row['timestamp'],
                'signal_type': signal['signal_type']
            })
        elif action == 'SELL':
            self.current_capital += cost - commission
            # Remove from positions
            self._close_position(signal, execution_price, market_row['timestamp'])
        
        # Record trade
        self.trades.append({
            'timestamp': market_row['timestamp'],
            'action': action,
            'symbol': signal['symbol'],
            'option_type': signal['option_type'],
            'strike': signal['strike'],
            'quantity': quantity,
            'price': execution_price,
            'commission': commission,
            'signal_type': signal.get('signal_type', 'UNKNOWN')
        })
    
    def _close_position(self, signal: Dict, exit_price: float, exit_time: datetime):
        """Close a position and record PnL"""
        # Find matching position
        for i, pos in enumerate(self.positions):
            if (pos['symbol'] == signal['symbol'] and
                pos['strike'] == signal['strike'] and
                pos['option_type'] == signal['option_type']):
                
                # Calculate PnL
                entry_price = pos['entry_price']
                pnl = (exit_price - entry_price) * signal['quantity'] * 100
                
                # Record closed position
                pos['exit_price'] = exit_price
                pos['exit_time'] = exit_time
                pos['pnl'] = pnl
                pos['holding_period'] = (exit_time - pos['entry_time']).days
                
                # Remove from active positions
                self.positions.pop(i)
                break
    
    def _update_positions(self, market_row: pd.Series):
        """Update position values"""
        # In a real backtest, would fetch option prices from data
        # For now, simplified update based on underlying movement
        pass
    
    def _calculate_equity(self, market_row: pd.Series) -> float:
        """Calculate total equity (cash + positions value)"""
        positions_value = sum(
            self._estimate_position_value(pos, market_row)
            for pos in self.positions
        )
        return self.current_capital + positions_value
    
    def _estimate_position_value(self, position: Dict, market_row: pd.Series) -> float:
        """Estimate current value of a position"""
        # Simplified valuation - in real backtest would use actual option prices
        underlying_price = market_row['close']
        strike = position['strike']
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        # Rough estimate based on intrinsic value
        if position['option_type'] == 'call':
            intrinsic = max(0, underlying_price - strike)
        else:
            intrinsic = max(0, strike - underlying_price)
        
        # Add time value estimate (simplified)
        time_value = entry_price * 0.5  # Assume 50% time value remaining
        
        estimated_value = (intrinsic + time_value) * quantity * 100
        return estimated_value
    
    def _calculate_performance_metrics(self, strategy_name: str) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        equity_df = pd.DataFrame(self.equity_curve)
        
        if equity_df.empty or len(self.trades) == 0:
            return BacktestResult(
                strategy_name=strategy_name,
                total_return=0, annualized_return=0, sharpe_ratio=0,
                sortino_ratio=0, max_drawdown=0, win_rate=0,
                profit_factor=0, total_trades=0, avg_trade_pnl=0,
                volatility=0, calmar_ratio=0, trades=[],
                equity_curve=equity_df
            )
        
        # Calculate returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        total_return = (equity_df['equity'].iloc[-1] - self.initial_capital) / self.initial_capital
        
        # Annualized return
        days = (equity_df['timestamp'].iloc[-1] - equity_df['timestamp'].iloc[0]).days
        years = days / 365.25
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Sharpe ratio
        risk_free_rate = 0.05 / 252  # Daily risk-free rate
        excess_returns = equity_df['returns'].dropna() - risk_free_rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
        
        # Sortino ratio
        downside_returns = excess_returns[excess_returns < 0]
        sortino_ratio = (excess_returns.mean() / downside_returns.std()) * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + equity_df['returns'].fillna(0)).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Trade statistics
        closed_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        wins = sum(1 for i in range(len(closed_trades)) if i % 2 == 1 and self._trade_pnl(i) > 0)
        total_trades = len(closed_trades) // 2 if len(closed_trades) > 0 else 0
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(self._trade_pnl(i) for i in range(len(closed_trades)) if self._trade_pnl(i) > 0)
        gross_loss = abs(sum(self._trade_pnl(i) for i in range(len(closed_trades)) if self._trade_pnl(i) < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Average trade PnL
        avg_trade_pnl = sum(self._trade_pnl(i) for i in range(len(closed_trades))) / total_trades if total_trades > 0 else 0
        
        # Volatility
        volatility = equity_df['returns'].std() * np.sqrt(252)
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            avg_trade_pnl=avg_trade_pnl,
            volatility=volatility,
            calmar_ratio=calmar_ratio,
            trades=self.trades,
            equity_curve=equity_df
        )
    
    def _trade_pnl(self, trade_idx: int) -> float:
        """Calculate PnL for a trade pair (entry and exit)"""
        if trade_idx >= len(self.trades) - 1:
            return 0
        
        entry = self.trades[trade_idx]
        exit_trade = self.trades[trade_idx + 1]
        
        if entry['action'] == 'BUY' and exit_trade['action'] == 'SELL':
            pnl = (exit_trade['price'] - entry['price']) * entry['quantity'] * 100
            pnl -= (entry['commission'] + exit_trade['commission'])
            return pnl
        
        return 0
    
    def plot_equity_curve(self, equity_df: pd.DataFrame, strategy_name: str):
        """Plot equity curve (placeholder - would use matplotlib)"""
        # In production, would create actual plot
        print(f"\nEquity Curve for {strategy_name}")
        print(equity_df.tail(10))
