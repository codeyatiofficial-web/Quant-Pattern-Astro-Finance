import os
import time
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv

from modules.market_data import MarketDataFetcher

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
DB_URL = os.getenv("DATABASE_URL", "postgresql://localhost/quant_pattern")

# Global data fetcher
market = MarketDataFetcher()

def get_db_connection():
    try:
        return psycopg2.connect(DB_URL)
    except:
        return None

def fetch_magnitude_base(score):
    """Fetch expected magnitude from PostgreSQL based on score bracket."""
    if score >= 90: bracket = "90-100"
    elif score >= 80: bracket = "80-89"
    elif score >= 70: bracket = "70-79"
    else: bracket = "60-69"

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM magnitude_table WHERE score_range = %s", (bracket,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return {
                "base_magnitude": row["avg_points_moved"],
                "success_rate": row["success_rate"],
                "variance": row["std_deviation"]
            }
            
    # Fallback if DB not available or not seeded
    fallbacks = {
        "90-100": {"base": 65, "sr": 85, "var": 15},
        "80-89": {"base": 45, "sr": 75, "var": 20},
        "70-79": {"base": 30, "sr": 65, "var": 25},
        "60-69": {"base": 18, "sr": 55, "var": 35}
    }
    f = fallbacks.get(bracket, fallbacks["60-69"])
    return {"base_magnitude": f["base"], "success_rate": f["sr"], "variance": f["var"]}

def calculate_nifty_atr14_15m():
    """Fetch recent Nifty 15m candles and compute ATR array."""
    try:
        # Get last 5 days of 15 min data
        period = "5d"
        df = market.fetch_intraday_data("^NSEI", period=period, interval="15m")
        if df.empty:
            return 25.0, 35.0  # Safe defaults
            
        high = df['high']
        low = df['low']
        close = df['close']
        
        # TR calculation
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(14).mean()
        
        current_atr = atr.iloc[-1]
        historical_avg_atr = atr.mean() # simple mean over the period as baseline
        
        if pd.isna(current_atr) or pd.isna(historical_avg_atr):
            return 25.0, 35.0
            
        return current_atr, historical_avg_atr
    except Exception as e:
        print(f"ATR calculation error: {e}")
        return 25.0, 35.0
        
def calculate_global_strength_multiplier():
    """Calculate correlation strength multiplier from global signals."""
    predictors = {"Nasdaq": "NQ=F", "SP500": "ES=F", "USD_INR": "INR=X", "Oil": "CL=F", "Gold": "GC=F"}
    strong_signals = []
    weak_signals = []
    
    # Analyze last 90 days vs today
    start_dt = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    for name, sym in predictors.items():
        df = market.fetch_stock_data(sym, start_date=start_dt, market="Global")
        if len(df) > 10:
            returns = df['daily_return'].abs()
            avg_move = returns.mean()
            current_move = returns.iloc[-1]
            
            if avg_move > 0:
                ratio = current_move / avg_move
                if ratio > 1.0:
                    strong_signals.append(name)
                else:
                    weak_signals.append(name)
    
    strong_count = len(strong_signals)
    if strong_count == 5: mult = 1.3
    elif strong_count >= 3: mult = 1.1
    elif strong_count == 2: mult = 0.9
    else: mult = 0.7
    
    return mult, strong_signals, weak_signals

def compute_magnitude(direction, score, current_nifty):
    """
    Main orchestration function to generate the complete magnitude forecast object.
    direction: 'BUY', 'SELL', 'NEUTRAL'
    score: 0-100 derived from global model
    current_nifty: Latest traded price
    """
    if direction.upper() == "NEUTRAL" or score < 60:
        return {
           "direction": "NEUTRAL",
           "confidence": 0,
           "magnitude_points": 0,
           "target_price": current_nifty,
           "stop_loss": current_nifty,
           "risk_reward": 0,
        }

    # Step 1: Base magnitude
    base_data = fetch_magnitude_base(score)
    base_mag = base_data["base_magnitude"]
    variance = base_data["variance"]
    accuracy = base_data["success_rate"]
    
    # Step 2: ATR Adjustment
    curr_atr, avg_atr = calculate_nifty_atr14_15m()
    atr_multiplier = curr_atr / avg_atr if avg_atr > 0 else 1.0
    atr_multiplier = min(max(atr_multiplier, 0.5), 2.0) # Clamp multiplier
    adjusted_mag = base_mag * atr_multiplier
    
    # Step 3: Correlation Multiplier
    corr_mult, strong_sigs, weak_sigs = calculate_global_strength_multiplier()
    
    final_magnitude = int(adjusted_mag * corr_mult)
    final_magnitude = max(10, final_magnitude) # Floor at 10 pts
    
    # Determine Confidence level based on variance (std_dev)
    if variance < 18:
        mag_conf = "HIGH"
        band_spread = 15
    elif variance < 28:
        mag_conf = "MEDIUM"
        band_spread = 25
    else:
        mag_conf = "LOW"
        band_spread = 50
        
    range_low = final_magnitude - (band_spread // 2)
    range_high = final_magnitude + (band_spread // 2)
    
    # Direction mappings
    sl_points = int(final_magnitude / 2) # Risk reward 1:2
    
    if direction.upper() in ["BUY", "BULLISH"]:
        target = current_nifty + final_magnitude
        t_low = current_nifty + range_low
        t_high = current_nifty + range_high
        sl = current_nifty - sl_points
    else: # SELL or BEARISH
        target = current_nifty - final_magnitude
        t_low = current_nifty - range_high
        t_high = current_nifty - range_low
        sl = current_nifty + sl_points

    # Cap dates / intervals
    now = datetime.now()
    valid_until = now + timedelta(minutes=15)
    
    return {
        "direction": direction.upper(),
        "confidence": min(score + 5, 99), # Directional confidence proxy
        "current_nifty": current_nifty,
        "magnitude_points": final_magnitude,
        "magnitude_range_low": max(5, range_low),
        "magnitude_range_high": range_high,
        "target_price": target,
        "target_range_low": t_low,
        "target_range_high": t_high,
        "stop_loss": sl,
        "risk_reward": round(float(final_magnitude) / float(sl_points), 1) if sl_points > 0 else 0.0,
        "signal_valid_until": valid_until.isoformat(),
        "based_on_score": score,
        "historical_accuracy": round(accuracy, 1),
        "magnitude_confidence": mag_conf,
        "supporting_signals": strong_sigs,
        "conflicting_signals": weak_sigs
    }

if __name__ == "__main__":
    # Test script locally
    print("Testing Magnitude Calculator...")
    res = compute_magnitude("BUY", 87, 23170)
    for k, v in res.items():
        print(f"{k}: {v}")
