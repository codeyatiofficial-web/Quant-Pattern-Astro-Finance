import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.technical_analysis import TechnicalAnalyzer
import pandas as pd
from datetime import datetime, timedelta

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")

historical_period = "10y"
pattern_name = "Bear Flag"

default_return = {"rate": 50.0, "trades": [], "total_wins": 0, "total_losses": 0}

years = int(historical_period.replace('y','').replace('Max','30')) if any(char.isdigit() for char in historical_period) else 5
cutoff_date = datetime.now() - timedelta(days=years * 365)

try:
    if hasattr(df.index, 'tzinfo') and df.index.tzinfo is not None:
        import pytz
        # Convert the naive cutoff date to match the exact tz of the dataframe index
        cutoff_date = cutoff_date.replace(tzinfo=pytz.utc).astimezone(df.index.tzinfo)
except Exception as e:
    pass
    
if not isinstance(df.index, pd.DatetimeIndex):
    if 'date' in df.columns:
        df.index = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df.index = pd.to_datetime(df['Date'])
    else:
        print("RETURN DEFAULT 1")
    
test_df = df[df.index >= cutoff_date].copy()
if len(test_df) < 100:
    print("RETURN DEFAULT 2")
    
trades = []
wins = 0
losses = 0

prices = test_df['close'].values
dates = test_df.index

is_bullish = ("Bull" in pattern_name)
target_name_normalized = pattern_name.replace("Bullish ", "").replace("Bearish ", "").replace("Bull ", "").replace("Bear ", "")

step = 1
i = 50
while i < len(test_df) - 10:
    window_df = test_df.iloc[:i]
    curr_price = prices[i-1]
    hist_date = dates[i-1]
    
    hist_pattern = scanner._detect_harmonics(window_df, curr_price)
    hist_name = hist_pattern.get('name', 'Consolidation')
    
    hist_is_bullish = ("Bull" in hist_name)
    hist_name_normalized = hist_name.replace("Bullish ", "").replace("Bearish ", "").replace("Bull ", "").replace("Bear ", "")
    
    if hist_is_bullish == is_bullish and hist_name_normalized == target_name_normalized:
        prz = float(hist_pattern.get('prz', 0))
        target = float(hist_pattern.get('target', 0))
        stop = float(hist_pattern.get('stop', 0))
        
        if prz != 0 and target != 0 and stop != 0 and prz != target and prz != stop:
            look_forward = prices[i:min(i+100, len(prices))] # Max 100 bars holding duration
            
            trade_result = None
            exit_price = 0
            
            for future_price in look_forward:
                if is_bullish:
                    if future_price >= target:
                        trade_result = "Win"
                        exit_price = future_price
                        break
                    elif future_price <= stop:
                        trade_result = "Loss"
                        exit_price = future_price
                        break
                else: # Bearish logic (Prices dropping is Win)
                    if future_price <= target:
                        trade_result = "Win"
                        exit_price = future_price
                        break
                    elif future_price >= stop:
                        trade_result = "Loss"
                        exit_price = future_price
                        break
            
            if trade_result is None:
                if len(look_forward) > 0:
                    exit_price = look_forward[-1]
                    trade_result = "Time Exit"
                    
            if trade_result:
                pct_return = ((exit_price - curr_price) / curr_price) * 100
                if not is_bullish:
                    pct_return = -pct_return
                    
                sign = "+" if pct_return > 0 else ""
                res_label = "Win" if (trade_result == "Win" or (trade_result == "Time Exit" and pct_return > 0)) else "Loss"
                
                trades.append({
                    "date": hist_date.strftime("%Y-%m-%d %H:%M"),
                    "result": res_label,
                    "return": f"{sign}{pct_return:.2f}%"
                })
                
                if res_label == "Win":
                    wins += 1
                else:
                    losses += 1
                    
                i += 15 # Skip ahead to avoid double-counting same geometric swing
                continue
    i += step

print("Wins:", wins, "Losses:", losses)
