import logging
from typing import Dict, Any, Tuple
from modules.algo.signal_generator import SignalGenerator

logger = logging.getLogger(__name__)

class Scorer:
    def __init__(self, kite_client, global_bias_score: int):
        self.generator = SignalGenerator(kite_client)
        self.global_bias_score = global_bias_score
        
        # Default thresholds
        self.buy_threshold = 85
        self.sell_threshold = 85
        
        self._apply_global_filters()

    def _apply_global_filters(self):
        """
        Adjusts thresholds based on Global Bias.
        Max global score logic: 
         > 15 = Strong Bullish
         < -15 = Strong Bearish
        """
        if self.global_bias_score > 15:
            logger.info("Strong Global Bullish: Decreasing BUY threshold, Increasing SELL threshold.")
            self.buy_threshold = 75
            self.sell_threshold = 92
        elif self.global_bias_score < -15:
            logger.info("Strong Global Bearish: Decreasing SELL threshold, Increasing BUY threshold.")
            self.buy_threshold = 92
            self.sell_threshold = 75
        else:
            logger.info("Global Neutral: Keeping standard 85 thresholds.")
            self.buy_threshold = 85
            self.sell_threshold = 85

    def evaluate(self, 
                 df_15m, df_1h, 
                 ce_data, pe_data, 
                 spot_price, key_levels, 
                 current_time) -> Tuple[Dict[str, Any], str]:
        """
        Runs all 4 steps and compiles the final 110-point score.
        """
        # Step 1: Trend
        step1_score, direction = self.generator.step1_trend_alignment(df_15m, df_1h)
        if direction == "NEUTRAL" or step1_score == 0:
            return {"total": 0, "msg": "Failed Step 1 (Trend Alignment)"}, "NONE"
            
        # Step 2: Momentum
        step2_score = self.generator.step2_momentum_volume(df_15m, direction)
        
        # Step 3: Options
        step3_score = self.generator.step3_options_chain(ce_data, pe_data, spot_price, direction)
        
        # Step 4: Levels & Time
        step4_score = self.generator.step4_key_levels_time(spot_price, key_levels, current_time)
        
        # Global Bonus
        global_bonus = 0
        if direction == "BUY" and self.global_bias_score >= 5:
            # Scale bonus up to 10 points
            global_bonus = min(10, self.global_bias_score)
        elif direction == "SELL" and self.global_bias_score <= -5:
            global_bonus = min(10, abs(self.global_bias_score))

        total_score = step1_score + step2_score + step3_score + step4_score + global_bonus
        
        # Evaluate Thresholds
        signal_strength = "NO SIGNAL"
        action = "WAIT"
        trade_size = "NONE"
        
        threshold = self.buy_threshold if direction == "BUY" else self.sell_threshold
        
        if total_score >= threshold:
            signal_strength = "STRONG SIGNAL"
            action = "EXECUTE"
            trade_size = "FULL"
        elif total_score >= 70:
            signal_strength = "GOOD SIGNAL"
            action = "EXECUTE"
            trade_size = "HALF"
            
            # Additional Rule 4 Logic for conflicts
            if direction == "BUY" and self.global_bias_score < -15:
                signal_strength = "CONFLICT (Strong Bearish Global) - REDUCED SIZE"
                trade_size = "HALF"
            elif direction == "SELL" and self.global_bias_score > 15:
                signal_strength = "CONFLICT (Strong Bullish Global) - REDUCED SIZE"
                trade_size = "HALF"
                
        elif total_score >= 55:
            signal_strength = "WEAK SIGNAL"
            action = "ALERT_ONLY"
            trade_size = "NONE"

        result = {
            "direction": direction,
            "total_score": total_score,
            "step1_score": step1_score,
            "step2_score": step2_score,
            "step3_score": step3_score,
            "step4_score": step4_score,
            "global_bonus": global_bonus,
            "signal_strength": signal_strength,
            "trade_size": trade_size,
            "action": action
        }
        
        # Send Telegram notification if actionable
        if action in ["EXECUTE", "ALERT_ONLY"]:
            from modules.algo.telegram_bot import send_telegram_message
            emoji = "🟢" if direction == "BUY" else "🔴"
            msg = f"<b>{emoji} NIFTY {direction} SIGNAL: {action}</b>\n"
            msg += f"Strength: {signal_strength}\n"
            msg += f"Total Score: {total_score}/110\n"
            msg += f"1️⃣ Trend: {step1_score}/25 | 2️⃣ Mom/Vol: {step2_score}/25\n"
            msg += f"3️⃣ Options: {step3_score}/25 | 4️⃣ Levels: {step4_score}/25\n"
            msg += f"🌍 Global Bonus: {global_bonus}\n"
            msg += f"Recommended Size: {trade_size}\n"
            msg += f"Spot Price (approx): {spot_price}"
            send_telegram_message(msg)
            
        return result, action
