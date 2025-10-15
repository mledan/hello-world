"""Whisper Number Play - Trade based on whisper vs consensus"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class WhisperNumberPlayStrategy(BaseStrategy):
    """Trade based on whisper number divergence from consensus"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.whisper_vs_consensus_pct = config.parameters.get('whisper_vs_consensus_pct', 0.05)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.70)
        self.earnings_date = config.parameters.get('earnings_date', None)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if market_data.empty or self.earnings_date is None:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        days_to_earnings = (self.earnings_date - current_time).days
        
        # Enter if whisper significantly higher than consensus
        if not self.positions and days_to_earnings == 0:
            # Placeholder: Would fetch actual whisper and consensus from API
            # For now, assume bullish whisper scenario
            strike = self._get_strike(current_price * 1.025)
            signals.append({
                'symbol': 'TSLA', 'action': 'BUY', 'option_type': 'call', 'strike': strike,
                'expiration': self.earnings_date + timedelta(days=7), 'quantity': 1,
                'price': current_price * 0.03, 'signal_type': 'ENTRY_WHISPER_BULLISH'
            })
        
        if self.positions and current_time > self.earnings_date:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (current_time - self.earnings_date).days >= 2:
                    signals.append({
                        'symbol': position.symbol, 'action': 'SELL', 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': position.quantity,
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'entry_timing': 'Earnings day', 'signal': 'Whisper divergence from consensus'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'time_exit': '2 days post'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 10) * 10
