import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.technical_analysis import TechnicalAnalyzer
import pandas as pd

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")

if 'date' in df.columns:
    df.index = pd.to_datetime(df['date'])
    
test_df = df.copy()

prices = test_df['close'].values
dates = test_df.index

pattern_name = "Bear Flag"
is_bullish = False
target_name_normalized = "Flag"

found = 0
wins = 0
losses = 0

step = 5
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
            look_forward = prices[i:min(i+100, len(prices))]
            trade_result = None
            exit_price = 0
            
            for future_price in look_forward:
                if future_price <= target:
                    trade_result = "Win"
                    exit_price = future_price
                    break
                elif future_price >= stop:
                    trade_result = "Loss"
                    exit_price = future_price
                    break
                    
            if trade_result is None and len(look_forward) > 0:
                trade_result = "Time Exit"
                exit_price = look_forward[-1]
                
            if trade_result:
                pct_return = ((exit_price - curr_price) / curr_price) * 100
                pct_return = -pct_return # bearish
                res_label = "Win" if (trade_result == "Win" or (trade_result == "Time Exit" and pct_return > 0)) else "Loss"
                if res_label == "Win":
                    wins += 1
                else:
                    losses += 1
                found += 1
                # print(f"[{found}] Matched at {hist_date} - Result: {res_label} ({trade_result}), Return: {pct_return:.2f}%")
                i += 15
                continue
    i += step

print(f"Total Matches Found: {found}")
print(f"Total Wins: {wins}, Losses: {losses}")
