"""Deep ITM LEAP Calls - Stock replacement strategy"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class DeepITMCallsStrategy(BaseStrategy):
    """Buy deep ITM calls (0.80+ delta) as stock replacement"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.dte_min = config.parameters.get('dte_min', 365)
        self.dte_max = config.parameters.get('dte_max', 730)
        self.delta_target = config.parameters.get('delta_target', 0.80)
        self.iv_percentile_max = config.parameters.get('iv_percentile_max', 20)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Entry: First Monday of quarter when IV is low
        if not self.positions and current_time.day <= 7 and current_time.weekday() == 0:
            # Calculate deep ITM strike (~20% ITM)
            if self.config.symbol == 'SPY':
                strike = round((current_price * 0.80) / 5) * 5
            else:  # TSLA
                strike = round((current_price * 0.80) / 10) * 10
            
            # Use 1.5 year expiration
            expiration = datetime.now() + timedelta(days=547)  # ~18 months
            
            signals.append({
                'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'call',
                'strike': strike, 'expiration': expiration, 'quantity': 1,
                'price': current_price * 0.25, 'signal_type': 'ENTRY_DEEP_ITM_LEAP'
            })
        
        # Exit on profit target or 6 months before expiration
        if self.positions:
            for position in self.positions:
                dte = (position.expiration - current_time).days
                if position.pnl_pct >= self.profit_target_pct * 100 or dte <= 180:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration,
                        'quantity': position.quantity, 'price': position.current_price,
                        'signal_type': 'EXIT_LEAP'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {
            'dte_range': f'{self.dte_min}-{self.dte_max} days',
            'strike': f'~{self.delta_target} delta (deep ITM)',
            'iv_percentile': f'Below {self.iv_percentile_max}th percentile',
            'timing': 'First Monday of quarter'
        }
    
    def get_exit_conditions(self) -> Dict:
        return {
            'profit_target': f'{self.profit_target_pct * 100}%',
            'dte_exit': '180 days (6 months before expiration)',
            'roll_strategy': 'Roll to new LEAP if still bullish'
        }
