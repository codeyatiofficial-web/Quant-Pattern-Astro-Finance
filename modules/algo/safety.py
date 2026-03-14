import logging
from datetime import datetime, time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SafetySystem:
    def __init__(self, db_session):
        self.db = db_session
        self.daily_loss_limit = 3000.0  # Max loss per day in INR
        self.max_trades_per_day = 3
        self.max_lot_size = 2           # Cannot order more than 2 lots via Algo
        
    def _is_market_open(self) -> bool:
        """Safety 4: Market hours check (9:15 AM to 3:15 PM)"""
        now = datetime.now().time()
        market_open = time(9, 15)
        algo_cutoff = time(15, 15)
        return market_open <= now <= algo_cutoff

    def is_safe_to_trade(self, signal: Dict[str, Any], current_open_positions: list) -> tuple[bool, str]:
        """Runs all 5 safety checks."""
        from modules.algo.logger import TradeLog # Lazy import to avoid circular dep if needed
        import sqlalchemy as sa
        
        # 1. Market Hours
        if not self._is_market_open():
             return False, "Market is outside active algorithmic trading hours (9:15 - 3:15)."
             
        # 2. Order Size Check
        qty_lots = signal.get('lots', 1)
        if qty_lots > self.max_lot_size:
            return False, f"Order size {qty_lots} lots exceeds safety max ({self.max_lot_size})."
            
        # 3. Duplicate Position Check
        # Check against active Kite positions passed into the function
        # A simple check: if we already have an open option position, we don't open another.
        has_open_options = any(pos.get('product') == 'MIS' and pos.get('quantity', 0) != 0 for pos in current_open_positions)
        if has_open_options:
            return False, "Already hold an open MIS options position. No overlapping trades allowed."
            
        # 4 & 5. Daily Limits Check (Loss & Count)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_trades = self.db.query(TradeLog).filter(TradeLog.timestamp >= today_start).all()
        
        if len(today_trades) >= self.max_trades_per_day:
            return False, f"Daily trade limit reached ({self.max_trades_per_day})."
            
        daily_pnl = sum(t.pnl for t in today_trades if t.pnl is not None)
        if daily_pnl < -self.daily_loss_limit:
            return False, f"Daily loss limit breached (Current PnL: {daily_pnl}). Algo stopped."
            
        return True, "Safe to execute."
