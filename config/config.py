"""
Configuration file for trading strategies library
"""

# Market Data Configuration
SYMBOLS = ["SPY", "TSLA"]
CURRENT_PRICES = {
    "SPY": 662.23,
    "TSLA": 429.24
}

# SPY Market Data (from finance card)
SPY_DATA = {
    "current_price": 662.23,
    "daily_high": 665.83,
    "daily_low": 660.35,
    "month_high": 673.78,
    "month_low": 652.15,
    "year_high": 673.78,
    "year_low": 481.80,
    "volatility": "low"  # Relative to TSLA
}

# TSLA Market Data (from finance card)
TSLA_DATA = {
    "current_price": 429.24,
    "daily_high": 434.20,
    "daily_low": 417.86,
    "month_high": 461.40,
    "month_low": 408.00,
    "year_high": 461.40,
    "year_low": 212.11,
    "market_cap": 1.37e12,  # $1.37T
    "volatility": "high"  # Relative to SPY
}

# Polygon.io API Configuration
POLYGON_CONFIG = {
    "api_key": "YOUR_POLYGON_API_KEY",  # Replace with actual API key
    "base_url": "https://api.polygon.io",
    "endpoints": {
        "options": "/v3/reference/options/contracts",
        "options_snapshot": "/v3/snapshot/options/{ticker}",
        "stocks": "/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}",
        "index": "/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}",
        "quotes": "/v3/quotes/{ticker}",
        "trades": "/v3/trades/{ticker}"
    }
}

# Strategy Time Horizons
STRATEGY_HORIZONS = {
    "0DTE": 0,  # Intraday
    "30_50_DAYS": (30, 50),  # Mid-term
    "LEAPS": (365, 730)  # Long-term (1-2 years)
}

# Greeks Calculation Parameters
GREEKS_CONFIG = {
    "risk_free_rate": 0.05,  # 5% annual risk-free rate
    "dividend_yield": {
        "SPY": 0.0125,  # ~1.25% for SPY
        "TSLA": 0.0     # TSLA doesn't pay dividends
    }
}

# LEAP Volatility Watermark
LEAP_WATERMARK = {
    "iv_percentile_threshold": 20,  # Below 20th percentile
    "iv_hv_ratio_threshold": 1.0    # IV/HV < 1
}

# Risk Management Parameters
RISK_MANAGEMENT = {
    "max_portfolio_risk": 0.05,  # 5% max portfolio risk
    "max_position_size": 0.10,   # 10% max per position
    "stop_loss_pct": 0.20,       # 20% stop loss
    "profit_target_pct": 0.50,   # 50% profit target
    "max_gamma_exposure": 1000,  # Max gamma exposure per position
    "max_delta_exposure": 5000   # Max delta exposure per position
}

# Backtesting Parameters
BACKTEST_CONFIG = {
    "initial_capital": 100000,
    "commission_per_contract": 0.65,
    "slippage_pct": 0.001,  # 0.1% slippage
    "margin_requirement": 0.25  # 25% margin requirement
}

# Performance Metrics
PERFORMANCE_METRICS = [
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
    "win_rate",
    "profit_factor",
    "total_return",
    "annualized_return",
    "volatility"
]
