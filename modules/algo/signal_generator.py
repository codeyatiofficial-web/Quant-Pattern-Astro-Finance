import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

# This requires the `ta` library (pip install ta)
from ta.trend import SuperTrend, EMAIndicator, MACD
from ta.momentum import RSIIndicator

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self, kite_client):
        self.kite = kite_client
        
    def step1_trend_alignment(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Tuple[int, str]:
        """
        Step 1: Trend Alignment (Max 25 points)
        - 15m Supertrend (10, 3)
        - 1h Supertrend (10, 3)
        - 1h EMA 20 and EMA 50
        """
        score = 0
        direction = "NEUTRAL"
        
        if df_15m.empty or df_1h.empty:
            return score, direction
            
        try:
            # Calculate 15m Supertrend
            st_15m = SuperTrend(high=df_15m['high'], low=df_15m['low'], close=df_15m['close'], window=10, multiplier=3)
            df_15m['st_dir'] = st_15m.super_trend_direction()  # 1 for uptrend, -1 for downtrend
            
            # Calculate 1h Supertrend
            st_1h = SuperTrend(high=df_1h['high'], low=df_1h['low'], close=df_1h['close'], window=10, multiplier=3)
            df_1h['st_dir'] = st_1h.super_trend_direction()
            
            # Calculate 1h EMAs
            df_1h['ema20'] = EMAIndicator(close=df_1h['close'], window=20).ema_indicator()
            df_1h['ema50'] = EMAIndicator(close=df_1h['close'], window=50).ema_indicator()
            
            last_15m = df_15m.iloc[-1]
            last_1h = df_1h.iloc[-1]
            
            is_15m_bull = last_15m['st_dir'] == 1
            is_1h_bull = last_1h['st_dir'] == 1
            is_ema_bull = last_1h['ema20'] > last_1h['ema50']
            
            is_15m_bear = last_15m['st_dir'] == -1
            is_1h_bear = last_1h['st_dir'] == -1
            is_ema_bear = last_1h['ema20'] < last_1h['ema50']
            
            if is_15m_bull and is_1h_bull and is_ema_bull:
                return 25, "BUY"
            elif is_15m_bear and is_1h_bear and is_ema_bear:
                return 25, "SELL"
            else:
                 # Conflict or mixed signals gives 0 points
                 return 0, "NEUTRAL"
                 
        except Exception as e:
             logger.error(f"Error in Step 1 Trend Alignment: {e}")
             return 0, "ERROR"
             

    def step2_momentum_volume(self, df_15m: pd.DataFrame, signal_direction: str) -> int:
        """
        Step 2: Momentum + Volume (Max 25 points)
        - RSI (14) on 15m
        - MACD (12, 26, 9) on 15m
        - Volume ratio (> 1.5x of 20-period avg)
        Requires direction from Step 1 to score properly.
        """
        if df_15m.empty or signal_direction == "NEUTRAL":
            return 0
            
        try:
            # RSI 14
            rsi_indicator = RSIIndicator(close=df_15m['close'], window=14)
            df_15m['rsi'] = rsi_indicator.rsi()
            
            # MACD 12 26 9
            macd_indicator = MACD(close=df_15m['close'], window_slow=26, window_fast=12, window_sign=9)
            df_15m['macd_hist'] = macd_indicator.macd_diff() # Histogram
            
            # Volume Ratio
            df_15m['vol_sma_20'] = df_15m['volume'].rolling(window=20).mean()
            df_15m['vol_ratio'] = df_15m['volume'] / df_15m['vol_sma_20']
            
            last_idx = df_15m.index[-1]
            prev_idx = df_15m.index[-2] if len(df_15m) > 1 else last_idx
            
            rsi = df_15m.loc[last_idx, 'rsi']
            macd_hist = df_15m.loc[last_idx, 'macd_hist']
            prev_macd_hist = df_15m.loc[prev_idx, 'macd_hist']
            vol_ratio = df_15m.loc[last_idx, 'vol_ratio']
            
            score = 0
            
            if signal_direction == "BUY":
                if 50 <= rsi <= 65: score += 10
                elif 45 <= rsi < 50: score += 5
                elif rsi < 30: score += 8 # Oversold bounce
                
                if macd_hist > 0 and macd_hist > prev_macd_hist:
                    score += 8
                    
            elif signal_direction == "SELL":
                if 35 <= rsi <= 50: score += 10
                elif 50 < rsi <= 55: score += 5
                elif rsi > 70: score += 8 # Overbought rejection
                
                if macd_hist < 0 and macd_hist < prev_macd_hist:
                    score += 8
                    
            if vol_ratio > 1.5:
                score += 7
                
            return min(score, 25) # Cap at 25
            
        except Exception as e:
            logger.error(f"Error in Step 2 Momentum: {e}")
            return 0

    def step3_options_chain(self, ce_data: pd.DataFrame, pe_data: pd.DataFrame, spot_price: float, signal_direction: str) -> int:
        """
        Step 3: Options Chain Confirmation (Max 25 points)
        - PCR, Max Pain, ATM strikes, Call Wall, Put Wall, IV Rank
        Requires separate CE and PE logic. 
        """
        if ce_data.empty or pe_data.empty or signal_direction == "NEUTRAL":
            return 0
            
        try:
            total_ce_oi = ce_data['oi'].sum()
            total_pe_oi = pe_data['oi'].sum()
            pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1.0
            
            # ATM Strike Logic
            closest_strike = pe_data.iloc[(pe_data['strike'] - spot_price).abs().argsort()[:1]]['strike'].values[0]
            
            atm_pe_row = pe_data[pe_data['strike'] == closest_strike]
            atm_ce_row = ce_data[ce_data['strike'] == closest_strike]
            
            pe_oi_change = atm_pe_row['oi_change'].values[0] if not atm_pe_row.empty else 0
            ce_oi_change = atm_ce_row['oi_change'].values[0] if not atm_ce_row.empty else 0
            
            # Put/Call Wall (Highest OI strikes)
            call_wall = ce_data.loc[ce_data['oi'].idxmax()]['strike'] if not ce_data.empty else 0
            put_wall = pe_data.loc[pe_data['oi'].idxmax()]['strike'] if not pe_data.empty else 0
            
            # Simple Max Pain calculation (Strike where total loss is minimum for option buyers, meaning min inner value)
            # Find strike that minimizes: Sum of (Spot - Strike) for ITM CE + Sum of (Strike - Spot) for ITM PE
            # Real options implementations can be heavier, using a basic proxy here
            max_pain = 0
            # For brevity, implementing dummy max pain fallback to Wall crossover logic:
            # We assume Max pain lies slightly toward Call wall if Bearish, Put wall if Bullish, or ATM.
            # In live, the caller passes down a pre-calculated max-pain or we loop through strikes.
            # Assuming max pain is close to ATM for now, usually it tracks VWAP/ATM tightly.
            max_pain = closest_strike 
            
            # Dummy IV rank for now:
            iv_rank = 50 
            
            score = 0
            
            if signal_direction == "BUY":
                if pcr > 1.2: score += 8
                if spot_price < max_pain: score += 7
                if pe_oi_change > 0: score += 5  # PE OI building up at ATM
                if iv_rank < 40: score += 5
                
            elif signal_direction == "SELL":
                if pcr < 0.8: score += 8
                if spot_price > max_pain: score += 7
                if ce_oi_change > 0: score += 5  # CE OI building up at ATM
                if iv_rank > 60: score += 5
                
            return min(score, 25)
            
        except Exception as e:
            logger.error(f"Error in Step 3 Options: {e}")
            return 0

    def step4_key_levels_time(self, spot_price: float, levels: Dict[str, float], current_time) -> int:
        """
        Step 4: Time Zone + Key Level proximity (Max 25 points)
        - Valid trading windows (9:15-9:45, 1:00-1:30, 2:30-3:15)
        - Within 0.2% of key level (+10), within 0.4% (+5)
        """
        # Time Window Logic (Indian Standard Time assumed for current_time)
        from datetime import time
        
        # Valid Windows
        window1 = (time(9, 15), time(9, 45))
        window2 = (time(13, 0), time(13, 30))
        window3 = (time(14, 30), time(15, 15))
        
        in_window = False
        if (window1[0] <= current_time <= window1[1]) or \
           (window2[0] <= current_time <= window2[1]) or \
           (window3[0] <= current_time <= window3[1]):
               in_window = True
               
        if not in_window:
            return 0 # 0 points outside valid windows
            
        score = 15 # +15 points for being inside valid window
        
        # Proximity to Key Levels
        # levels dict should contain: pdh, pdl, pdc, weekly_open, vwap, call_wall_strike, put_wall_strike
        added_level_score = 0
        
        for name, level_price in levels.items():
            if level_price is None or level_price == 0:
                continue
                
            dist_pct = abs(spot_price - level_price) / spot_price * 100
            
            if dist_pct <= 0.2:
                added_level_score = max(added_level_score, 10)
            elif dist_pct <= 0.4:
                added_level_score = max(added_level_score, 5)
                
        # Proximity to Round Numbers (like 21000, 21500)
        closest_round_num = round(spot_price / 500) * 500
        dist_round_pct = abs(spot_price - closest_round_num) / spot_price * 100
        if dist_round_pct <= 0.2:
            added_level_score = max(added_level_score, 10)
        elif dist_round_pct <= 0.4:
            added_level_score = max(added_level_score, 5)
            
        score += added_level_score
        
        return min(score, 25)
