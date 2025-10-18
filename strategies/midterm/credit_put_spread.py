"""Credit Put Spread - Bullish theta strategy"""
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import sys
sys.path.append('/workspace')
from core.base_strategy import BaseStrategy, StrategyConfig

class CreditPutSpreadStrategy(BaseStrategy):
    """Sell put spread for credit in bullish/neutral outlook"""
    
    def __init__(self, config: StrategyConfig, data_fetcher, greeks_calculator, exposure_calculator):
        super().__init__(config, data_fetcher, greeks_calculator, exposure_calculator)
        self.dte_entry = config.parameters.get('dte_entry', 45)
        self.short_delta = config.parameters.get('short_delta', 0.30)
        self.spread_width = config.parameters.get('spread_width', 5)
        self.profit_target_pct = config.parameters.get('profit_target_pct', 0.50)
        
    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        signals = []
        if len(market_data) < 20:
            return signals
        
        current_price = market_data['close'].iloc[-1]
        current_time = market_data['timestamp'].iloc[-1]
        
        # Check bullish conditions (price above 20-day MA)
        ma_20 = market_data['close'].rolling(20).mean().iloc[-1]
        
        if not self.positions and current_price > ma_20 and current_time.weekday() == 0:
            short_strike = self._get_strike(current_price * 0.95)
            long_strike = short_strike - self.spread_width
            expiration = self._get_expiration(self.dte_entry)
            
            signals.extend([
                {'symbol': self.config.symbol, 'action': 'SELL', 'option_type': 'put', 'strike': short_strike,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.025, 'signal_type': 'ENTRY_CREDIT_PUT'},
                {'symbol': self.config.symbol, 'action': 'BUY', 'option_type': 'put', 'strike': long_strike,
                 'expiration': expiration, 'quantity': 1, 'price': current_price * 0.015, 'signal_type': 'ENTRY_CREDIT_PUT'}
            ])
        
        if self.positions:
            for position in self.positions:
                if position.pnl_pct >= self.profit_target_pct * 100 or (position.expiration - current_time).days <= 21:
                    action = 'BUY' if position.quantity < 0 else 'SELL'
                    signals.append({
                        'symbol': position.symbol, 'action': action, 'option_type': position.option_type,
                        'strike': position.strike, 'expiration': position.expiration, 'quantity': abs(position.quantity),
                        'price': position.current_price, 'signal_type': 'EXIT'
                    })
        
        return signals
    
    def get_entry_conditions(self) -> Dict:
        return {'dte': f'{self.dte_entry} days', 'condition': 'Price > 20-day MA', 'short_strike': f'{self.short_delta} delta'}
    
    def get_exit_conditions(self) -> Dict:
        return {'profit_target': f'{self.profit_target_pct * 100}%', 'dte_exit': '21 days'}
    
    def _get_strike(self, price: float) -> float:
        return round(price / 5) * 5 if self.config.symbol == 'SPY' else round(price / 10) * 10
    
    def _get_expiration(self, days: int) -> datetime:
        return datetime.now() + timedelta(days=days)
