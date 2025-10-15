"""
Main entry point for running trading strategies
Example usage and demonstration
"""

import sys
import pandas as pd
from datetime import datetime, timedelta

from config.config import POLYGON_CONFIG, SPY_DATA, TSLA_DATA
from core.data_fetcher import DataFetcher
from core.greeks_calculator import GreeksCalculator
from core.exposure_calculator import ExposureCalculator
from core.base_strategy import StrategyConfig
from backtest.backtest_engine import BacktestEngine
from strategy_registry import StrategyRegistry
from utils.risk_manager import RiskManager


def run_single_strategy(strategy_name: str, symbol: str, start_date: str, end_date: str):
    """
    Run a single strategy backtest
    
    Args:
        strategy_name: Name of strategy from registry
        symbol: SPY or TSLA
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
    """
    print(f"\n{'='*80}")
    print(f"Running Backtest: {strategy_name} on {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*80}\n")
    
    # Initialize components
    data_fetcher = DataFetcher(POLYGON_CONFIG['api_key'])
    greeks_calculator = GreeksCalculator()
    exposure_calculator = ExposureCalculator(portfolio_value=100000)
    
    # Get strategy class from registry
    StrategyClass = StrategyRegistry.get_strategy(strategy_name)
    
    # Determine strategy type
    if strategy_name in StrategyRegistry.INTRADAY_STRATEGIES:
        strategy_type = 'intraday'
        time_horizon = 0
    elif strategy_name in StrategyRegistry.EARNINGS_STRATEGIES:
        strategy_type = 'earnings'
        time_horizon = 0
    elif strategy_name in StrategyRegistry.MIDTERM_STRATEGIES:
        strategy_type = 'midterm'
        time_horizon = 45
    else:
        strategy_type = 'longterm'
        time_horizon = 547
    
    # Create strategy config
    config = StrategyConfig(
        name=strategy_name,
        symbol=symbol,
        strategy_type=strategy_type,
        time_horizon=time_horizon,
        max_risk=5000,
        max_position_size=0.10,
        parameters={}
    )
    
    # Initialize strategy
    strategy = StrategyClass(config, data_fetcher, greeks_calculator, exposure_calculator)
    
    # Generate sample market data (in production, would fetch real data)
    market_data = generate_sample_data(symbol, start_date, end_date)
    
    # Run backtest
    backtest_engine = BacktestEngine(initial_capital=100000)
    result = backtest_engine.run_backtest(strategy, market_data, start_date, end_date)
    
    # Print results
    print_backtest_results(result)
    
    return result


def run_all_strategies(symbol: str, start_date: str, end_date: str):
    """
    Run all strategies and compare performance
    
    Args:
        symbol: SPY or TSLA
        start_date: Backtest start date
        end_date: Backtest end date
    """
    print(f"\n{'='*80}")
    print(f"Running All Strategies on {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*80}\n")
    
    all_strategies = StrategyRegistry.get_all_strategies()
    results = []
    
    for strategy_name in all_strategies.keys():
        try:
            result = run_single_strategy(strategy_name, symbol, start_date, end_date)
            results.append({
                'strategy': strategy_name,
                'sharpe_ratio': result.sharpe_ratio,
                'total_return': result.total_return,
                'win_rate': result.win_rate,
                'max_drawdown': result.max_drawdown
            })
        except Exception as e:
            print(f"Error running {strategy_name}: {e}")
    
    # Print comparison
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('sharpe_ratio', ascending=False)
    print(results_df.to_string(index=False))
    
    return results_df


def generate_sample_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Generate sample market data for demonstration
    In production, would fetch real data from Polygon.io
    """
    from config.config import CURRENT_PRICES
    
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Generate daily data
    dates = pd.date_range(start, end, freq='B')  # Business days
    
    base_price = CURRENT_PRICES[symbol]
    
    # Generate random walk price data
    import numpy as np
    returns = np.random.normal(0.0005, 0.02, len(dates))  # Small positive drift with volatility
    prices = base_price * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * np.random.uniform(0.995, 1.005, len(dates)),
        'high': prices * np.random.uniform(1.005, 1.015, len(dates)),
        'low': prices * np.random.uniform(0.985, 0.995, len(dates)),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates)),
        'vwap': prices * np.random.uniform(0.998, 1.002, len(dates))
    })
    
    return data


def print_backtest_results(result):
    """Print formatted backtest results"""
    print("\n" + "="*80)
    print(f"BACKTEST RESULTS: {result.strategy_name}")
    print("="*80)
    print(f"Total Return:        {result.total_return * 100:>8.2f}%")
    print(f"Annualized Return:   {result.annualized_return * 100:>8.2f}%")
    print(f"Sharpe Ratio:        {result.sharpe_ratio:>8.2f}")
    print(f"Sortino Ratio:       {result.sortino_ratio:>8.2f}")
    print(f"Max Drawdown:        {result.max_drawdown * 100:>8.2f}%")
    print(f"Calmar Ratio:        {result.calmar_ratio:>8.2f}")
    print(f"Win Rate:            {result.win_rate * 100:>8.2f}%")
    print(f"Profit Factor:       {result.profit_factor:>8.2f}")
    print(f"Total Trades:        {result.total_trades:>8}")
    print(f"Avg Trade PnL:       ${result.avg_trade_pnl:>8.2f}")
    print(f"Volatility:          {result.volatility * 100:>8.2f}%")
    print("="*80 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("AUTOMATED TRADING STRATEGIES LIBRARY")
    print("SPY & TSLA Options Trading")
    print("="*80)
    
    # Print strategy counts
    counts = StrategyRegistry.get_strategy_count()
    print(f"\nAvailable Strategies:")
    print(f"  - Intraday (0DTE):        {counts['intraday']} strategies")
    print(f"  - Earnings (TSLA 0DTE):   {counts['earnings']} strategies")
    print(f"  - Mid-term (30-50 days):  {counts['midterm']} strategies")
    print(f"  - Long-term (LEAPs):      {counts['longterm']} strategies")
    print(f"  - TOTAL:                  {counts['total']} strategies\n")
    
    # Example: Run a single strategy
    print("\nExample: Running Gamma Scalping Strategy on SPY")
    result = run_single_strategy(
        strategy_name='gamma_scalping',
        symbol='SPY',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    # Example: List all available strategies
    print("\n" + "="*80)
    print("AVAILABLE STRATEGIES BY CATEGORY")
    print("="*80)
    strategies_by_category = StrategyRegistry.list_strategies_by_category()
    for category, strategies in strategies_by_category.items():
        print(f"\n{category.upper()}:")
        for strategy in strategies:
            print(f"  - {strategy}")
    
    print("\n" + "="*80)
    print("Setup complete! Use the functions above to backtest strategies.")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
