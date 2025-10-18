# Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Polygon.io API key
# Edit config/config.py and replace with your API key:
# POLYGON_CONFIG["api_key"] = "YOUR_API_KEY_HERE"
```

## Running Your First Backtest

```bash
python main.py
```

This will:
1. Display all 48+ available strategies
2. Run an example backtest of Gamma Scalping on SPY
3. Show performance metrics

## Example: Run Specific Strategy

```python
from main import run_single_strategy

# Run a single strategy
result = run_single_strategy(
    strategy_name='momentum_breakout',
    symbol='SPY',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Total Return: {result.total_return * 100:.2f}%")
```

## Example: Compare All Strategies

```python
from main import run_all_strategies

# Compare all strategies
results = run_all_strategies(
    symbol='SPY',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Results are sorted by Sharpe Ratio
print(results.head(10))  # Top 10 strategies
```

## Strategy Categories

### Intraday (0DTE)
```python
# Available strategies
strategies = [
    'gamma_scalping',
    'delta_neutral_straddle',
    'momentum_breakout',
    'vwap_reversion',
    'opening_range_breakout',
    'rsi_extreme',
    'bollinger_squeeze',
    'power_hour_momentum',
    'gamma_squeeze',
    'intraday_iron_condor',
    'market_maker_scalp',
    'volatility_spike'
]
```

### Earnings (TSLA only)
```python
strategies = [
    'long_straddle_earnings',
    'iv_crush_play',
    'post_earnings_fade',
    'pre_earnings_buildup',
    'earnings_strangle',
    'directional_earnings_call',
    'earnings_iron_butterfly',
    'post_earnings_momentum',
    'earnings_calendar_spread',
    'whisper_number_play',
    'earnings_gap_fill',
    'analyst_surprise'
]
```

### Mid-term (30-50 days)
```python
strategies = [
    'iron_condor_30d',
    'credit_put_spread',
    'covered_call_30d',
    'short_strangle_midterm',
    'butterfly_spread',
    'ratio_spread',
    'jade_lizard',
    'poor_mans_covered_call',
    'diagonal_calendar_spread',
    'reverse_iron_condor',
    'wheel_strategy',
    'broken_wing_butterfly'
]
```

### Long-term (LEAPs)
```python
strategies = [
    'deep_itm_calls',
    'leaps_diagonal_spread',
    'protective_puts_leaps',
    'poor_mans_covered_call_leaps',
    'synthetic_long_stock',
    'calendar_spread_leaps',
    'ratio_backspread_leaps',
    'low_iv_leap_calls',
    'leap_replacement',
    'long_term_hedge',
    'leaps_condor',
    'buy_write_leaps'
]
```

## Custom Strategy Example

```python
from core.base_strategy import BaseStrategy, StrategyConfig
from core.data_fetcher import DataFetcher
from core.greeks_calculator import GreeksCalculator
from core.exposure_calculator import ExposureCalculator

class MyStrategy(BaseStrategy):
    def generate_signals(self, market_data):
        signals = []
        # Your logic here
        return signals
    
    def get_entry_conditions(self):
        return {'time': '10:00 AM', 'condition': 'Price > MA'}
    
    def get_exit_conditions(self):
        return {'profit_target': '50%', 'time': '3:45 PM'}

# Run it
config = StrategyConfig(
    name='my_strategy',
    symbol='SPY',
    strategy_type='intraday',
    time_horizon=0,
    max_risk=5000,
    max_position_size=0.10,
    parameters={}
)

data_fetcher = DataFetcher('YOUR_API_KEY')
greeks_calc = GreeksCalculator()
exposure_calc = ExposureCalculator(100000)

strategy = MyStrategy(config, data_fetcher, greeks_calc, exposure_calc)
```

## Next Steps

1. Read `STRATEGIES_README.md` for detailed strategy descriptions
2. Explore `examples/` folder for more examples
3. Customize parameters in `config/config.py`
4. Run backtests on your chosen strategies
5. Analyze results and optimize parameters

## Support

- Full Documentation: See `STRATEGIES_README.md`
- Examples: See `examples/` folder
- Issues: Create a GitHub issue
