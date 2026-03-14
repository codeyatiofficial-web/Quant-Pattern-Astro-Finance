import yfinance as yf
import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Constants for Tickers
MARKETS = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "FTSE": "^FTSE",
    "DAX": "^GDAXI",
    "Nikkei": "^N225",
    "Hang Seng": "^HSI",
    "KOSPI": "^KS11",
    "ASX 200": "^AXJO",
    "Gold": "GC=F",
    "Crude Oil": "CL=F",
    "Silver": "SI=F",
    "USDINR": "INR=X",   # yfinance standard for USD to INR
    "DXY": "DX-Y.NYB",
    "US VIX": "^VIX"
}

def fetch_yfinance_change(symbol: str) -> float:
    """Fetch 1 day percentage change from yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        # We need historical data to get prev close and last close safely
        data = ticker.history(period="5d", interval="1d")
        if len(data) < 2:
            return 0.0
        
        last_close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        
        if prev_close == 0:
            return 0.0
            
        pct_change = ((last_close - prev_close) / prev_close) * 100.0
        return round(pct_change, 2)
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return 0.0

def fetch_yfinance_current(symbol: str) -> float:
    """Fetch current/last close price from yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1d")
        if len(data) == 0:
             return 0.0
        return round(float(data['Close'].iloc[-1]), 2)
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return 0.0

def calculate_global_bias() -> Dict[str, Any]:
    """
    Runs the 7:00 AM analysis for all global tickers 
    and returns the 30-point score block.
    """
    changes = {}
    for name, sym in MARKETS.items():
        if name in ["US VIX", "S&P BSE Sensex"]:
            changes[name] = fetch_yfinance_current(sym) # We need absolute value for VIX
        else:
             changes[name] = fetch_yfinance_change(sym)

    # 1. US Markets (Max 10 points)
    us_score = 0
    sp_chg = changes.get("S&P 500", 0)
    if sp_chg > 0.5: us_score += 4
    elif 0 < sp_chg <= 0.5: us_score += 2
    elif -0.5 <= sp_chg <= 0: us_score -= 2
    elif sp_chg < -0.5: us_score -= 4

    ndx_chg = changes.get("NASDAQ", 0)
    if ndx_chg > 0.5: us_score += 3
    elif ndx_chg < -0.5: us_score -= 3

    dji_chg = changes.get("Dow Jones", 0)
    if dji_chg > 0.5: us_score += 3
    elif dji_chg < -0.5: us_score -= 3

    # Ensure max bounds
    us_score = max(min(us_score, 10), -10)

    # 2. Asian Markets (Max 8 points)
    asian_score = 0
    if changes.get("Nikkei", 0) > 0.5: asian_score += 3
    elif changes.get("Nikkei", 0) < -0.5: asian_score -= 3
    
    if changes.get("Hang Seng", 0) > 0.5: asian_score += 2
    elif changes.get("Hang Seng", 0) < -0.5: asian_score -= 2
    
    if changes.get("KOSPI", 0) > 0.3: asian_score += 2
    elif changes.get("KOSPI", 0) < -0.3: asian_score -= 2
    
    if changes.get("ASX 200", 0) > 0.3: asian_score += 1

    # 3. European Markets (Max 6 points)
    eur_score = 0
    if changes.get("DAX", 0) > 0.5: eur_score += 3
    elif changes.get("DAX", 0) < -0.5: eur_score -= 3

    if changes.get("FTSE", 0) > 0.3: eur_score += 3
    elif changes.get("FTSE", 0) < -0.3: eur_score -= 3

    # 4. Commodities and Currencies (Max 6 points)
    com_curr_score = 0
    if changes.get("Crude Oil", 0) > 1.0: com_curr_score -= 2
    elif changes.get("Crude Oil", 0) < -1.0: com_curr_score += 2
    
    if changes.get("Gold", 0) > 0.5: com_curr_score -= 1
    elif changes.get("Gold", 0) < -0.5: com_curr_score += 1
    
    if changes.get("USDINR", 0) > 0: com_curr_score -= 2 # Rupee weakening
    elif changes.get("USDINR", 0) < 0: com_curr_score += 2 # Rupee strengthening
    
    if changes.get("DXY", 0) > 0.3: com_curr_score -= 1
    elif changes.get("DXY", 0) < 0: com_curr_score += 1

    # 5. US VIX Score (Max +2 / Min -4)
    vix = changes.get("US VIX", 0)
    vix_score = 0
    if vix > 0:
        if vix < 15: vix_score = 2
        elif 15 <= vix <= 20: vix_score = 0
        elif 20 < vix <= 25: vix_score = -2
        elif vix > 25: vix_score = -4

    total_global_score = us_score + asian_score + eur_score + com_curr_score + vix_score
    
    # Cap total between -30 and +30
    total_global_score = max(min(total_global_score, 30), -30)

    # Determine Bias Label
    bias_label = "GLOBAL NEUTRAL"
    if total_global_score >= 15: bias_label = "STRONG GLOBAL BULLISH"
    elif 5 <= total_global_score <= 14: bias_label = "MILD GLOBAL BULLISH"
    elif -14 <= total_global_score <= -5: bias_label = "MILD GLOBAL BEARISH"
    elif total_global_score <= -15: bias_label = "STRONG GLOBAL BEARISH"

    # Evaluate Gift Nifty Gap proxy (using BSE Sensex as proxy if Nifty unavailable premarket)
    try:
        prev_nifty = fetch_yfinance_current("^NSEI")
        proxy_current = fetch_yfinance_current("^BSESN")  # Proxying gap using BSE Sensex opening tick if applicable
        gap_points = proxy_current - prev_nifty if proxy_current > 0 and prev_nifty > 0 else 0
    except:
        gap_points = 0

    gap_score = 0
    gap_label = "NEUTRAL"
    if gap_points > 100: gap_score, gap_label = 10, "BULLISH bias"
    elif 50 <= gap_points <= 100: gap_score, gap_label = 5, "MILD BULLISH"
    elif 0 <= gap_points < 50: gap_score, gap_label = 2, "NEUTRAL"
    elif -50 <= gap_points < 0: gap_score, gap_label = -2, "NEUTRAL"
    elif -100 <= gap_points < -50: gap_score, gap_label = -5, "MILD BEARISH"
    elif gap_points < -100: gap_score, gap_label = -10, "BEARISH bias"

    # Assemble Report
    return {
        "score": total_global_score,
        "bias_label": bias_label,
        "market_changes": changes,
        "gap_points": gap_points,
        "gap_score": gap_score,
        "gap_label": gap_label,
        "vix_level": vix
    }

if __name__ == "__main__":
    # Test script execution
    res = calculate_global_bias()
    print("--- GLOBAL BIAS RESULT ---")
    for k, v in res.items():
        print(f"{k}: {v}")
