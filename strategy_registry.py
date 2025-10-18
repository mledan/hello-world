"""
Central registry for all trading strategies
Maps strategy names to their implementations
"""

from typing import Dict, Type
from core.base_strategy import BaseStrategy

# Import all strategies
from strategies.intraday import (
    GammaScalpingStrategy, DeltaNeutralStraddleStrategy, MomentumBreakoutStrategy,
    VWAPReversionStrategy, OpeningRangeBreakoutStrategy, RSIExtremeStrategy,
    BollingerSqueezeStrategy, PowerHourMomentumStrategy, GammaSqueezeStrategy,
    IntradayIronCondorStrategy, MarketMakerScalpStrategy, VolatilitySpikeStrategy
)

from strategies.earnings import (
    LongStraddleEarningsStrategy, IVCrushPlayStrategy, PostEarningsFadeStrategy,
    PreEarningsBuildupStrategy, EarningsStrangleStrategy, DirectionalEarningsCallStrategy,
    EarningsIronButterflyStrategy, PostEarningsMomentumStrategy, EarningsCalendarSpreadStrategy,
    WhisperNumberPlayStrategy, EarningsGapFillStrategy, AnalystSurpriseStrategy
)

from strategies.midterm import (
    IronCondor30DStrategy, CreditPutSpreadStrategy, CoveredCall30DStrategy,
    ShortStrangleMidtermStrategy, ButterflySpreadStrategy, RatioSpreadStrategy,
    JadeLizardStrategy, PoorMansCoveredCallStrategy, DiagonalCalendarSpreadStrategy,
    ReverseIronCondorStrategy, WheelStrategy, BrokenWingButterflyStrategy
)

from strategies.longterm import (
    DeepITMCallsStrategy, LEAPSDiagonalSpreadStrategy, ProtectivePutsLEAPSStrategy,
    PoorMansCoveredCallLEAPSStrategy, SyntheticLongStockStrategy, CalendarSpreadLEAPSStrategy,
    RatioBackspreadLEAPSStrategy, LowIVLEAPCallsStrategy, LEAPReplacementStrategy,
    LongTermHedgeStrategy, LEAPsCondorStrategy, BuyWriteLEAPSStrategy
)


class StrategyRegistry:
    """
    Central registry for all trading strategies
    Provides easy access to strategy classes and metadata
    """
    
    # Intraday strategies (0DTE)
    INTRADAY_STRATEGIES: Dict[str, Type[BaseStrategy]] = {
        'gamma_scalping': GammaScalpingStrategy,
        'delta_neutral_straddle': DeltaNeutralStraddleStrategy,
        'momentum_breakout': MomentumBreakoutStrategy,
        'vwap_reversion': VWAPReversionStrategy,
        'opening_range_breakout': OpeningRangeBreakoutStrategy,
        'rsi_extreme': RSIExtremeStrategy,
        'bollinger_squeeze': BollingerSqueezeStrategy,
        'power_hour_momentum': PowerHourMomentumStrategy,
        'gamma_squeeze': GammaSqueezeStrategy,
        'intraday_iron_condor': IntradayIronCondorStrategy,
        'market_maker_scalp': MarketMakerScalpStrategy,
        'volatility_spike': VolatilitySpikeStrategy
    }
    
    # Earnings strategies (0DTE, TSLA only)
    EARNINGS_STRATEGIES: Dict[str, Type[BaseStrategy]] = {
        'long_straddle_earnings': LongStraddleEarningsStrategy,
        'iv_crush_play': IVCrushPlayStrategy,
        'post_earnings_fade': PostEarningsFadeStrategy,
        'pre_earnings_buildup': PreEarningsBuildupStrategy,
        'earnings_strangle': EarningsStrangleStrategy,
        'directional_earnings_call': DirectionalEarningsCallStrategy,
        'earnings_iron_butterfly': EarningsIronButterflyStrategy,
        'post_earnings_momentum': PostEarningsMomentumStrategy,
        'earnings_calendar_spread': EarningsCalendarSpreadStrategy,
        'whisper_number_play': WhisperNumberPlayStrategy,
        'earnings_gap_fill': EarningsGapFillStrategy,
        'analyst_surprise': AnalystSurpriseStrategy
    }
    
    # Mid-term strategies (30-50 days)
    MIDTERM_STRATEGIES: Dict[str, Type[BaseStrategy]] = {
        'iron_condor_30d': IronCondor30DStrategy,
        'credit_put_spread': CreditPutSpreadStrategy,
        'covered_call_30d': CoveredCall30DStrategy,
        'short_strangle_midterm': ShortStrangleMidtermStrategy,
        'butterfly_spread': ButterflySpreadStrategy,
        'ratio_spread': RatioSpreadStrategy,
        'jade_lizard': JadeLizardStrategy,
        'poor_mans_covered_call': PoorMansCoveredCallStrategy,
        'diagonal_calendar_spread': DiagonalCalendarSpreadStrategy,
        'reverse_iron_condor': ReverseIronCondorStrategy,
        'wheel_strategy': WheelStrategy,
        'broken_wing_butterfly': BrokenWingButterflyStrategy
    }
    
    # Long-term strategies (LEAPs)
    LONGTERM_STRATEGIES: Dict[str, Type[BaseStrategy]] = {
        'deep_itm_calls': DeepITMCallsStrategy,
        'leaps_diagonal_spread': LEAPSDiagonalSpreadStrategy,
        'protective_puts_leaps': ProtectivePutsLEAPSStrategy,
        'poor_mans_covered_call_leaps': PoorMansCoveredCallLEAPSStrategy,
        'synthetic_long_stock': SyntheticLongStockStrategy,
        'calendar_spread_leaps': CalendarSpreadLEAPSStrategy,
        'ratio_backspread_leaps': RatioBackspreadLEAPSStrategy,
        'low_iv_leap_calls': LowIVLEAPCallsStrategy,
        'leap_replacement': LEAPReplacementStrategy,
        'long_term_hedge': LongTermHedgeStrategy,
        'leaps_condor': LEAPsCondorStrategy,
        'buy_write_leaps': BuyWriteLEAPSStrategy
    }
    
    @classmethod
    def get_all_strategies(cls) -> Dict[str, Type[BaseStrategy]]:
        """Get all strategies across all categories"""
        all_strategies = {}
        all_strategies.update(cls.INTRADAY_STRATEGIES)
        all_strategies.update(cls.EARNINGS_STRATEGIES)
        all_strategies.update(cls.MIDTERM_STRATEGIES)
        all_strategies.update(cls.LONGTERM_STRATEGIES)
        return all_strategies
    
    @classmethod
    def get_strategy(cls, strategy_name: str) -> Type[BaseStrategy]:
        """Get a specific strategy by name"""
        all_strategies = cls.get_all_strategies()
        if strategy_name not in all_strategies:
            raise ValueError(f"Strategy '{strategy_name}' not found in registry")
        return all_strategies[strategy_name]
    
    @classmethod
    def list_strategies_by_category(cls) -> Dict[str, list]:
        """List all strategies organized by category"""
        return {
            'intraday': list(cls.INTRADAY_STRATEGIES.keys()),
            'earnings': list(cls.EARNINGS_STRATEGIES.keys()),
            'midterm': list(cls.MIDTERM_STRATEGIES.keys()),
            'longterm': list(cls.LONGTERM_STRATEGIES.keys())
        }
    
    @classmethod
    def get_strategy_count(cls) -> Dict[str, int]:
        """Get count of strategies by category"""
        return {
            'intraday': len(cls.INTRADAY_STRATEGIES),
            'earnings': len(cls.EARNINGS_STRATEGIES),
            'midterm': len(cls.MIDTERM_STRATEGIES),
            'longterm': len(cls.LONGTERM_STRATEGIES),
            'total': len(cls.get_all_strategies())
        }
