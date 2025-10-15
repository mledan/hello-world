"""
Long-term strategies using LEAPs (1-2 years to expiration)
Focus on cheap options with low IV
"""

from .deep_itm_calls import DeepITMCallsStrategy
from .leaps_diagonal_spread import LEAPSDiagonalSpreadStrategy
from .protective_puts_leaps import ProtectivePutsLEAPSStrategy
from .poor_mans_covered_call_leaps import PoorMansCoveredCallLEAPSStrategy
from .synthetic_long_stock import SyntheticLongStockStrategy
from .calendar_spread_leaps import CalendarSpreadLEAPSStrategy
from .ratio_backspread_leaps import RatioBackspreadLEAPSStrategy
from .low_iv_leap_calls import LowIVLEAPCallsStrategy
from .leap_replacement import LEAPReplacementStrategy
from .long_term_hedge import LongTermHedgeStrategy
from .leaps_condor import LEAPsCondorStrategy
from .buy_write_leaps import BuyWriteLEAPSStrategy

__all__ = [
    'DeepITMCallsStrategy',
    'LEAPSDiagonalSpreadStrategy',
    'ProtectivePutsLEAPSStrategy',
    'PoorMansCoveredCallLEAPSStrategy',
    'SyntheticLongStockStrategy',
    'CalendarSpreadLEAPSStrategy',
    'RatioBackspreadLEAPSStrategy',
    'LowIVLEAPCallsStrategy',
    'LEAPReplacementStrategy',
    'LongTermHedgeStrategy',
    'LEAPsCondorStrategy',
    'BuyWriteLEAPSStrategy'
]
