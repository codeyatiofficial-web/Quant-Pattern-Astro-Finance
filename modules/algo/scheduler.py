import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from modules.algo.global_scoring import calculate_global_bias

logger = logging.getLogger(__name__)

class AlgoScheduler:
    def __init__(self, app_state: dict):
        self.scheduler = AsyncIOScheduler()
        self.app_state = app_state  # Should contain kite_client, db, global bias state, etc.
        
        # We can store the latest scores here to serve via API
        if "algo" not in self.app_state:
            self.app_state["algo"] = {
                "global_bias": 0,
                "pre_market_report": "Not generated yet.",
                "latest_signal": None,
                "is_active": False  # Toggle for live execution
            }

    def setup_jobs(self):
        """Sets up all cron jobs for the algorithmic trading system."""
        
        # 7:00 AM - Fetch global data and calculate bias
        self.scheduler.add_job(
            self._job_calculate_global_bias,
            trigger=CronTrigger(hour=7, minute=0, timezone="Asia/Kolkata"),
            id="global_bias_calc",
            name="Calculate Global Bias"
        )
        
        # 9:15 AM to 3:15 PM - Run Intraday 4-Step Scorer every 15 mins
        self.scheduler.add_job(
            self._job_intraday_scan,
            trigger=CronTrigger(day_of_week='mon-fri', hour='9-15', minute='15,30,45,0', timezone="Asia/Kolkata"),
            id="intraday_signal_scan",
            name="Intraday Signal Generation"
        )
        
        logger.info("AlgoScheduler jobs setup completed.")

    def start(self):
        self.scheduler.start()
        logger.info("AlgoScheduler started.")
        
    def stop(self):
        self.scheduler.shutdown()
        logger.info("AlgoScheduler stopped.")

    async def _job_calculate_global_bias(self):
        """Calculates pre-market global bias."""
        logger.info("Running scheduled Global Bias calculation...")
        try:
            res = calculate_global_bias()
            score = res.get("score", 0)
            bias_label = res.get("bias_label", "UNKNOWN")
            gap_label = res.get("gap_label", "UNKNOWN gap")
            report = f"Global bias is {bias_label} ({score}/30). Gap expected: {gap_label}."
            
            self.app_state["algo"]["global_bias"] = score
            self.app_state["algo"]["pre_market_report"] = report
            logger.info(f"Global Bias updated: {score} - {report}")
        except Exception as e:
            logger.error(f"Error calculating global bias: {e}")

    async def _job_intraday_scan(self):
        """Runs the 4-step validation logic if active."""
        if not self.app_state["algo"].get("is_active", False):
            logger.debug("Intraday scan skipped: Algo is inactive.")
            return
            
        logger.info("Running Intraday 4-Step Validation...")
        # To be implemented completely with live data:
        # 1. Fetch live df_15m, df_1h
        # 2. Extract spot, levels
        # 3. Use Scorer(global_bias).evaluate(...) 
        
        # 4. MOCK: If Execution Signal is generated, pass to Executor for Multi-Tenant Execution
        try:
            from modules.algo.executor import Executor
            exe = Executor(db_session=None)
            
            mock_signal = {"direction": "BUY", "strength": "STRONG SIGNAL"}
            
            # This background task queries all `is_active=True` users and fires the Kite trade order concurrently
            results = await exe.execute_trade_for_users(
                signal=mock_signal, 
                symbol="NIFTY24APR22500CE", 
                base_quantity=50
            )
            
            if results:
                logger.info(f"Intraday Multi-Tenant execution processed {len(results)} orders.")
                
        except Exception as e:
            logger.error(f"Error during Background Multi-User Execution: {e}")
