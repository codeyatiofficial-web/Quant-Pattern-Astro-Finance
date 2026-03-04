import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.technical_analysis import TechnicalAnalyzer
import pandas as pd
from datetime import datetime, timedelta

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")

if 'date' in df.columns:
    df.index = pd.to_datetime(df['date'])

cutoff_date = datetime.now() - timedelta(days=10 * 365)
if hasattr(df.index, 'tzinfo') and df.index.tzinfo is not None:
    import pytz
    cutoff_date = cutoff_date.replace(tzinfo=pytz.utc).astimezone(df.index.tzinfo)

test_df = df[df.index >= cutoff_date].copy()

prices = test_df['close'].values
dates = test_df.index

pattern_name = "Bear Flag"
is_bullish = False
target_name_normalized = "Flag"

found = 0
step = 5
i = 50
while i < len(test_df) - 10:
    window_df = test_df.iloc[:i]
    curr_price = prices[i-1]
    
    hist_pattern = scanner._detect_harmonics(window_df, curr_price)
    hist_name = hist_pattern.get('name', 'Consolidation')
    hist_name_normalized = hist_name.replace("Bullish ", "").replace("Bearish ", "").replace("Bull ", "").replace("Bear ", "")
    
    if hist_name_normalized == target_name_normalized:
        found += 1
    i += step

print(f"Total Matches Found on subset (len {len(test_df)}): {found}")
