"""LEAPS Diagonal Spread - Long-term bullish income strategy"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class LEAPSDiagonalSpreadStrategy(BaseStrategy):
    """Buy LEAP call, sell near-term calls against it"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.leap_dte = config.parameters.get('leap_dte', 547)  # 18 months
        self.short_dte = config.parameters.get('short_dte', 45)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.40)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Buy LEAP if no position
        if not any(p for p in self.positions if (p.expiration - current_time).days > 365):
            leap_strike = round((current_price * 0.90) / 5) * 5 if self.config.symbol == 'SPY' else round((current_price * 0.90) / 10) * 10
            leap_expiration = datetime.now() + timedelta(days=self.leap_dte)
            
            signals.append({
                'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call',
                'strike': leap_strike, 'expiration': leap_expiration, 'quantity': 1,
                'price': current_price * 0.20, 'signal_type': 'ENTRY_LEAP_LONG'
            })
        
        # Sell short-term call monthly
        if any(p for p in self.positions if (p.expiration - current_time).days > 365):
            if not any(p for p in self.positions if (p.expiration - current_time).days < 90 and p.quantity < 0):
                if current_time.weekday() == 0:  # Monday
                    short_strike = round((current_price * 1.05) / 5) * 5 if self.config.symbol == 'SPY' else round((current_price * 1.05) / 10) * 10
                    short_expiration = datetime.now() + timedelta(days=self.short_dte)
                    
                    signals.append({
                        'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'call',
                        'strike': short_strike, 'expiration': short_expiration, 'quantity': 1,
                        'price': current_price * 0.025, 'signal_type': 'ENTRY_SHORT_CALL'
                    })
        
        # Exit short calls at 50% profit or 21 DTE
        if self.positions:
            for position in self.positions:
                dte = (position.expiration - current_time).days
                if position.quantity < 0:  # Short position
                    if position.pnl_pct >= 50 or dte <= 21:
                        signals.append({
                            'symbol': position.symbol, 'action': 'BUY', 'option_type': position.option_type,
                            'strike': position.strike, 'expiration': position.expiration,
                            'quantity': abs(position.quantity), 'price': position.current_price,
                            'signal_type': 'EXIT_SHORT_CALL'
                        })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {
            'leap_dte': f'{self.leap_dte} days (~18 months)',
            'leap_strike': '~0.70 delta (10% ITM)',
            'short_calls': f'{self.short_dte} days, 5% OTM',
            'frequency': 'Sell new call monthly'
        }
    
    def get_exit_conditions(self) -> Dict:
        return {
            'short_call_profit': '50%',
            'short_call_dte': '21 days',
            'leap_exit': '180 days before expiration'
        }
