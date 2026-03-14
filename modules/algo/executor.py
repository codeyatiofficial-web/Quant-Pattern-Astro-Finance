import logging
import math
from typing import Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self, kite_client, db_session):
        self.kite = kite_client
        self.db = db_session
        self.base_rr_ratio = 1.5  # Base Reward/Risk ratio
        
    def calculate_sl_target(self, entry_price: float, atr: float, direction: str) -> Tuple[float, float]:
        """
        Calculates Stop Loss and Target prices based on Entry and ATR.
        For Options (CE/PE), 0.5 * ATR (of spot) is a basic placeholder.
        Real implementation would use Option Greeks or Delta-adjusted ATR.
        """
        # Simplistic placeholder logic: SL is ~15 points or 0.5 ATR
        sl_points = max(15.0, atr * 0.5 if atr else 15.0)
        target_points = sl_points * self.base_rr_ratio
        
        if direction == "BUY":
            sl_price = entry_price - sl_points
            target_price = entry_price + target_points
        else: # SELL
            sl_price = entry_price + sl_points
            target_price = entry_price - target_points
            
        return round(sl_price, 1), round(target_price, 1)

    async def execute_trade_for_users(self, signal: Dict[str, Any], symbol: str, base_quantity: int) -> list:
        """
        Main multi-tenant execution routing to place orders on Kite for all active users.
        """
        import asyncio
        from kiteconnect import KiteConnect
        from modules.auth_engine import get_active_broker_configs
        
        logger.info(f"Preparing multi-tenant trade: {signal['direction']} Base QTY: {base_quantity} x {symbol}")
        
        configs = get_active_broker_configs()
        if not configs:
            logger.warning("No active broker configs found for execution. Skipping trade.")
            return []
            
        async def _execute_single(config):
            def _place_sync_order():
                kite = KiteConnect(api_key=config['api_key'])
                kite.set_access_token(config['access_token'])
                
                # Apply the user's risk multiplier to the base quantity
                # e.g., Nifty base lot is 50. If multi=2.0 -> 100 qty.
                user_quantity = int(base_quantity * config['trade_multiplier'])
                
                transaction_type = kite.TRANSACTION_TYPE_BUY if signal["direction"] == "BUY" else kite.TRANSACTION_TYPE_SELL
                
                return kite.place_order(
                    tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NFO,
                    transaction_type=transaction_type,
                    quantity=user_quantity,
                    variety=kite.VARIETY_REGULAR,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    validity=kite.VALIDITY_DAY
                )
                
            try:
                # Run the synchronous kite network call in a thread pool to avoid blocking the asyncio loop
                order_id = await asyncio.to_thread(_place_sync_order)
                logger.info(f"User {config['user_id']} ({config['broker_name']}) Entry placed. Order ID: {order_id}")
                
                return {
                    "user_id": config['user_id'],
                    "status": "success",
                    "order_id": order_id,
                    "symbol": symbol,
                    "quantity": int(base_quantity * config['trade_multiplier']),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Failed to execute trade for User {config['user_id']}: {str(e)}", exc_info=False)
                return {
                    "user_id": config['user_id'],
                    "status": "error",
                    "message": str(e)
                }

        results = await asyncio.gather(*[_execute_single(c) for c in configs])
        logger.info(f"Multi-tenant execution complete for {len(results)} users.")
        return results
