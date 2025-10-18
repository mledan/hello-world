# Automated Trading Strategies Library for SPY & TSLA

A comprehensive library of 48+ options trading strategies for SPY and TSLA, designed for automated backtesting using Polygon.io APIs.

## 📊 Strategy Overview

### Summary
- **Total Strategies**: 48+
- **Symbols**: SPY, TSLA
- **Data Source**: Polygon.io (Index API, Options API, Stocks API)
- **Focus**: Options trading across multiple time horizons

### Strategy Categories

#### 1. Intraday Strategies (0DTE) - 12 Strategies
Zero days to expiration strategies for quick intraday profits.

1. **Gamma Scalping** - Buy ATM straddle and scalp underlying for gamma profits
2. **Delta Neutral Straddle** - Maintain delta neutrality while profiting from volatility
3. **Momentum Breakout** - Trade breakouts from key intraday levels
4. **VWAP Reversion** - Mean reversion when price deviates from VWAP
5. **Opening Range Breakout** - Trade breakouts from first 30-minute range
6. **RSI Extreme** - Fade extreme RSI readings (oversold/overbought)
7. **Bollinger Squeeze** - Trade volatility expansion from BB squeezes
8. **Power Hour Momentum** - Capture momentum in final trading hour
9. **Gamma Squeeze** - Detect and trade gamma squeeze conditions
10. **Intraday Iron Condor** - Range-bound profit in low volatility
11. **Market Maker Scalp** - High-frequency scalping for small profits
12. **Volatility Spike** - Trade sudden IV expansion

**Key Parameters**:
- Entry: 9:30 AM - 10:00 AM (most strategies)
- Exit: 3:45 PM or profit target (typically 30-50%)
- Greeks Focus: High gamma exposure for scalping

#### 2. Earnings-Focused Strategies (0DTE, TSLA Only) - 12 Strategies
Strategies specifically designed for TSLA earnings events.

1. **Long Straddle Earnings** - ATM straddle for big earnings moves
2. **IV Crush Play** - Short premium before earnings, profit from IV crush
3. **Post-Earnings Fade** - Fade initial earnings move, bet on reversal
4. **Pre-Earnings Buildup** - Ride momentum into earnings (3-5 days before)
5. **Earnings Strangle** - OTM strangle (cheaper than straddle)
6. **Directional Earnings Call** - Directional bet based on fundamentals
7. **Earnings Iron Butterfly** - Bet on minimal post-earnings move
8. **Post-Earnings Momentum** - Ride continuation of earnings move
9. **Earnings Calendar Spread** - Profit from IV crush differential
10. **Whisper Number Play** - Trade based on whisper vs consensus
11. **Earnings Gap Fill** - Bet on gap fill after earnings
12. **Analyst Surprise Strategy** - Enter based on surprise magnitude

**Key Parameters**:
- Entry: 1-5 days before earnings or immediately after
- Exit: 1-3 days post-earnings or profit target (40-80%)
- IV Focus: High IV pre-earnings, IV crush post-earnings

**Historical TSLA Price Ranges**:
- Daily: $417.86 - $434.20
- Monthly: $408.00 - $461.40  
- Yearly: $212.11 - $461.40

#### 3. Mid-Term Strategies (30-50 Days) - 12 Strategies
Theta-selling strategies for consistent income generation.

1. **Iron Condor 30D** - Classic theta decay play in range-bound market
2. **Credit Put Spread** - Bullish theta strategy
3. **Covered Call 30D** - Income generation on stock positions
4. **Short Strangle Midterm** - High IV premium selling
5. **Butterfly Spread** - Low-risk neutral strategy
6. **Ratio Spread** - Unbalanced spread for directional bias
7. **Jade Lizard** - Undefined risk upside, defined risk downside
8. **Poor Man's Covered Call** - LEAP + short call diagonal
9. **Diagonal Calendar Spread** - Time decay + volatility play
10. **Reverse Iron Condor** - Profit from large moves
11. **Wheel Strategy** - Sell puts, get assigned, sell calls
12. **Broken Wing Butterfly** - Directional butterfly spread

**Key Parameters**:
- Entry: 45 days to expiration
- Exit: 50% profit or 21 days to expiration
- Greeks Focus: Theta decay, manage delta exposure
- Strike Selection: ~20-30 delta for short strikes

**SPY Price Ranges**:
- Daily: $660.35 - $665.83
- Monthly: $652.15 - $673.78
- Yearly: $481.80 - $673.78

#### 4. Long-Term Strategies (LEAPs) - 12 Strategies
1-2 year options for capital efficiency and leverage.

1. **Deep ITM Calls** - 0.80+ delta calls as stock replacement
2. **LEAPs Diagonal Spread** - Long LEAP + monthly short calls
3. **Protective Puts LEAPs** - Long-term portfolio protection
4. **Poor Man's Covered Call (LEAP)** - LEAP call + short calls
5. **Synthetic Long Stock** - Long call + short put at same strike
6. **Calendar Spread LEAPs** - Long LEAP + short near-term
7. **Ratio Backspread LEAPs** - Unlimited upside, limited risk
8. **Low IV LEAP Calls** - Buy when IV < 20th percentile
9. **LEAP Replacement** - Replace stock positions with LEAPs
10. **Long-Term Hedge** - Protection for long-term portfolios
11. **LEAPs Condor** - Long-term range strategy
12. **Buy-Write LEAPs** - LEAP purchase + covered call writing

**Key Parameters**:
- Entry: 365-730 days to expiration
- Exit: 50% profit or 180 days before expiration
- IV Watermark: IV below 20th percentile or IV/HV ratio < 1
- Strike Selection: Deep ITM (0.80 delta) or ATM based on strategy

**LEAP Strike Examples**:
- SPY: ~$500 strikes (given 1-year low of $481.80)
- TSLA: ~$300 strikes (given 1-year low of $212.11)

## 🏗️ Architecture

### Centralized System Design

The library uses a modular architecture with centralized components:

```
├── config/                 # Configuration files
│   └── config.py          # Market data, API keys, risk parameters
├── core/                  # Core calculation engines
│   ├── data_fetcher.py   # Polygon.io API integration
│   ├── greeks_calculator.py  # Black-Scholes Greeks
│   ├── exposure_calculator.py # Portfolio exposure
│   └── base_strategy.py  # Base strategy class
├── strategies/           # Strategy implementations
│   ├── intraday/        # 0DTE strategies
│   ├── earnings/        # Earnings strategies
│   ├── midterm/         # 30-50 day strategies
│   └── longterm/        # LEAP strategies
├── backtest/            # Backtesting framework
│   ├── backtest_engine.py
│   ├── performance_metrics.py
│   └── portfolio.py
├── utils/               # Utility modules
│   └── risk_manager.py # Risk management
├── strategy_registry.py # Central strategy registry
└── main.py             # Main execution script
```

### Core Modules

#### 1. Data Fetcher (`core/data_fetcher.py`)
- **Purpose**: Centralized data retrieval from Polygon.io
- **Features**:
  - Caching to minimize API calls
  - Rate limiting (respects API limits)
  - Historical stock data (OHLCV)
  - Options chain data
  - Options snapshots
  - Historical IV calculation
  - Earnings dates (TSLA)

**Key Methods**:
```python
get_stock_data(symbol, start_date, end_date, timespan)
get_options_chain(symbol, expiration_date, strike_price)
get_options_snapshot(option_ticker)
get_intraday_data(symbol, date)
batch_fetch_options_data(symbol, expiration_dates)
```

#### 2. Greeks Calculator (`core/greeks_calculator.py`)
- **Purpose**: Calculate all Greeks using Black-Scholes model
- **Greeks Calculated**:
  - **Delta**: Rate of change of option price w.r.t. underlying
  - **Gamma**: Rate of change of delta w.r.t. underlying
  - **Theta**: Time decay (per day)
  - **Vega**: Sensitivity to IV changes (per 1%)
  - **Rho**: Sensitivity to interest rate changes (per 1%)

**Key Methods**:
```python
calculate_all_greeks(S, K, T, r, sigma, option_type, q)
calculate_option_price(S, K, T, r, sigma, option_type, q)
calculate_implied_volatility(market_price, S, K, T, r, option_type, q)
batch_calculate_greeks(positions)
```

**Formula**: Black-Scholes with dividends
- Call: C = S·e^(-qT)·N(d1) - K·e^(-rT)·N(d2)
- Put: P = K·e^(-rT)·N(-d2) - S·e^(-qT)·N(-d1)

#### 3. Exposure Calculator (`core/exposure_calculator.py`)
- **Purpose**: Track portfolio-level Greek exposures
- **Metrics**:
  - Total delta/gamma/theta/vega/rho
  - Net delta/gamma dollars
  - Exposure as % of portfolio
  - Delta hedge ratio

**Key Methods**:
```python
calculate_portfolio_exposure()
calculate_intraday_gamma_exposure(price_moves)
calculate_delta_hedge_ratio()
check_risk_limits(max_delta, max_gamma)
calculate_position_sizing(strategy_delta, strategy_gamma)
```

#### 4. Risk Manager (`utils/risk_manager.py`)
- **Purpose**: Portfolio and position-level risk management
- **Features**:
  - Position sizing (Kelly Criterion)
  - VaR and CVaR calculation
  - Greeks-based position limits
  - Concentration risk checks
  - Dynamic stop losses
  - Sharpe/Sortino ratios

**Key Methods**:
```python
calculate_position_size(strategy_risk, win_rate, risk_reward_ratio)
calculate_var(returns, confidence_level)
calculate_cvar(returns, confidence_level)
calculate_max_position_size_greeks(delta, gamma, underlying_price)
calculate_sharpe_ratio(returns, risk_free_rate)
```

## 📈 Greeks & Exposure Management

### Intraday Gamma Exposure
Calculated for different price moves to understand risk:

```python
price_moves = [-1%, -0.5%, 0%, 0.5%, 1%]
exposure_df = exposure_calculator.calculate_intraday_gamma_exposure(price_moves)
```

Expected output:
```
price_move_pct | price_move_dollars | initial_delta | new_delta | delta_change | gamma_effect
-1.0%          | -6.62 (SPY)       | 0.50          | 0.35      | -0.15        | -0.15
0.0%           | 0.00              | 0.50          | 0.50      | 0.00         | 0.00
+1.0%          | +6.62 (SPY)       | 0.50          | 0.65      | +0.15        | +0.15
```

### Delta Exposure
- **Target**: Maintain delta-neutral (±0.10 tolerance) for non-directional strategies
- **Calculation**: Total delta = Σ(position_delta × quantity × multiplier)
- **Hedging**: Adjust by trading additional options or underlying

### Position Sizing Based on Greeks
```python
max_contracts = exposure_calculator.calculate_position_sizing(
    strategy_delta=0.50,
    strategy_gamma=0.05,
    max_position_size_pct=0.10
)
```

## 🔄 Backtesting Framework

### Backtest Engine (`backtest/backtest_engine.py`)

**Features**:
- Historical data simulation
- Commission modeling ($0.65/contract default)
- Slippage modeling (0.1% default)
- Position tracking
- Equity curve generation
- Comprehensive performance metrics

**Usage**:
```python
from backtest.backtest_engine import BacktestEngine
from core.base_strategy import StrategyConfig

# Initialize engine
engine = BacktestEngine(
    initial_capital=100000,
    commission_per_contract=0.65,
    slippage_pct=0.001
)

# Run backtest
result = engine.run_backtest(
    strategy=my_strategy,
    market_data=data,
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Access results
print(f"Sharpe Ratio: {result.sharpe_ratio}")
print(f"Max Drawdown: {result.max_drawdown}")
```

### Performance Metrics

All backtests calculate:
1. **Total Return**: (Final Equity - Initial Capital) / Initial Capital
2. **Annualized Return**: Compound annual growth rate
3. **Sharpe Ratio**: (Return - Risk Free) / Volatility × √252
4. **Sortino Ratio**: (Return - Risk Free) / Downside Deviation × √252
5. **Max Drawdown**: Largest peak-to-trough decline
6. **Calmar Ratio**: Annual Return / |Max Drawdown|
7. **Win Rate**: Winning Trades / Total Trades
8. **Profit Factor**: Gross Profit / |Gross Loss|
9. **Volatility**: Standard deviation of returns (annualized)

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd workspace

# Install dependencies
pip install -r requirements.txt

# Configure API key
# Edit config/config.py and add your Polygon.io API key
POLYGON_CONFIG = {
    "api_key": "YOUR_API_KEY_HERE",
    ...
}
```

### Running a Single Strategy

```python
from main import run_single_strategy

result = run_single_strategy(
    strategy_name='gamma_scalping',
    symbol='SPY',
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### Running All Strategies (Comparison)

```python
from main import run_all_strategies

results_df = run_all_strategies(
    symbol='SPY',
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### Creating a Custom Strategy

```python
from core.base_strategy import BaseStrategy, StrategyConfig
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        # Custom parameters
        self.my_param = config.parameters.get('my_param', default_value)
    
    def generate_signals(self, market_data: pd.DataFrame):
        signals = []
        
        # Your strategy logic here
        if condition:
            signals.append({
                'symbol': self.config.symbol,
                'action': 'BUY',  # or 'SELL'
                'option_type': 'call',  # or 'put'
                'strike': strike_price,
                'expiration': expiration_date,
                'quantity': 1,
                'price': option_price,
                'signal_type': 'ENTRY'
            })
        
        return signals
    
    def get_entry_conditions(self):
        return {'condition1': 'value1', 'condition2': 'value2'}
    
    def get_exit_conditions(self):
        return {'profit_target': '50%', 'stop_loss': '20%'}
```

## 📊 Current Market Data (Reference)

### SPY (S&P 500 ETF)
- **Current Price**: $662.23
- **Daily Range**: $660.35 - $665.83
- **Monthly Range**: $652.15 - $673.78
- **52-Week Range**: $481.80 - $673.78
- **Dividend Yield**: ~1.25%
- **Volatility**: Low (relative to TSLA)

### TSLA (Tesla Inc.)
- **Current Price**: $429.24
- **Daily Range**: $417.86 - $434.20
- **Monthly Range**: $408.00 - $461.40
- **52-Week Range**: $212.11 - $461.40
- **Market Cap**: $1.37 trillion
- **Dividend Yield**: 0% (no dividend)
- **Volatility**: High (relative to SPY)

### Typical Earnings Schedule (TSLA)
- Q4 2024: January 22, 2025
- Q1 2025: April 23, 2025
- Q2 2025: July 23, 2025
- Q3 2025: October 22, 2025

## ⚙️ Configuration

### Risk Management Parameters (`config/config.py`)

```python
RISK_MANAGEMENT = {
    "max_portfolio_risk": 0.05,      # 5% max portfolio risk
    "max_position_size": 0.10,       # 10% max per position
    "stop_loss_pct": 0.20,           # 20% stop loss
    "profit_target_pct": 0.50,       # 50% profit target
    "max_gamma_exposure": 1000,      # Max gamma per position
    "max_delta_exposure": 5000       # Max delta per position
}
```

### LEAP Volatility Watermark

```python
LEAP_WATERMARK = {
    "iv_percentile_threshold": 20,   # Below 20th percentile
    "iv_hv_ratio_threshold": 1.0     # IV/HV < 1
}
```

## 📝 Strategy Parameters Reference

### Common Parameters Across Strategies

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dte_entry` | int | Varies | Days to expiration at entry |
| `profit_target_pct` | float | 0.50 | Profit target (50%) |
| `stop_loss_pct` | float | 0.20 | Stop loss (20%) |
| `max_position_size` | float | 0.10 | Max position size (10% of portfolio) |

### Strategy-Specific Parameters

#### Gamma Scalping
- `gamma_threshold`: 0.05 (min gamma to enter)
- `delta_rehedge_threshold`: 0.15 (delta threshold for rehedge)
- `max_rehedges`: 10 (max rehedges per day)

#### Iron Condor
- `delta_short`: 0.20 (delta for short strikes)
- `wing_width`: $10 (width between strikes)
- `dte_exit`: 21 (exit at 21 DTE)

#### LEAPs Diagonal Spread
- `leap_dte`: 547 days (~18 months)
- `short_dte`: 45 days (monthly short calls)

## 🔍 Strategy Selection Guide

### By Market Condition

**Bullish Market**:
- Credit Put Spread
- Covered Call
- Poor Man's Covered Call
- Deep ITM LEAP Calls

**Bearish Market**:
- Long Puts
- Bear Put Spread
- Protective Puts

**Neutral/Range-Bound**:
- Iron Condor
- Butterfly Spread
- Short Strangle
- Intraday Iron Condor

**High Volatility**:
- Short Strangles/Straddles
- Iron Condors
- Credit Spreads
- IV Crush Play (earnings)

**Low Volatility**:
- Long Straddles/Strangles
- LEAPs (cheap options)
- Ratio Spreads

### By Time Commitment

**Active (Intraday)**:
- All 0DTE strategies
- Require monitoring throughout trading day
- Higher win rate, smaller profits per trade

**Moderate (Weekly)**:
- Mid-term strategies
- Check 1-2x per week
- Theta decay focus

**Passive (Monthly/Quarterly)**:
- LEAP strategies
- Check monthly
- Long-term capital appreciation

## 📚 Additional Resources

### Polygon.io API Endpoints Used

1. **Options Contracts**: `/v3/reference/options/contracts`
2. **Options Snapshot**: `/v3/snapshot/options/{ticker}`
3. **Historical Aggregates**: `/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`
4. **Quotes**: `/v3/quotes/{ticker}`
5. **Trades**: `/v3/trades/{ticker}`

### Greeks Formulas

**d1**: `(ln(S/K) + (r - q + 0.5σ²)T) / (σ√T)`  
**d2**: `d1 - σ√T`

**Call Delta**: `e^(-qT) × N(d1)`  
**Put Delta**: `-e^(-qT) × N(-d1)`  

**Gamma**: `e^(-qT) × N'(d1) / (S × σ × √T)`  

**Theta (Call)**: `-(S × N'(d1) × σ × e^(-qT))/(2√T) - rK × e^(-rT) × N(d2) + qS × e^(-qT) × N(d1)`

**Vega**: `S × e^(-qT) × N'(d1) × √T / 100`

**Rho (Call)**: `K × T × e^(-rT) × N(d2) / 100`

Where:
- S = Underlying price
- K = Strike price
- T = Time to expiration (years)
- r = Risk-free rate
- q = Dividend yield
- σ = Implied volatility
- N(x) = Cumulative normal distribution
- N'(x) = Normal probability density function

## 🤝 Contributing

To add a new strategy:

1. Create strategy file in appropriate folder (`strategies/intraday`, `strategies/earnings`, etc.)
2. Inherit from `BaseStrategy`
3. Implement required methods:
   - `generate_signals()`
   - `get_entry_conditions()`
   - `get_exit_conditions()`
4. Add to `strategy_registry.py`
5. Test with backtest engine

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Support

For issues, questions, or contributions:
- GitHub Issues: [Create an issue]
- Documentation: See `/docs` folder
- Examples: See `/examples` folder

---

**Built with Python 3.8+ | Powered by Polygon.io | Options Trading Library**
