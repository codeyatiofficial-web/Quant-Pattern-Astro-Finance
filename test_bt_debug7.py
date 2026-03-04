import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.technical_analysis import TechnicalAnalyzer
import pandas as pd
from datetime import datetime, timedelta

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")

df.index = pd.to_datetime(df['date'])

cutoff_date = datetime.now() - timedelta(days=10 * 365)
if hasattr(df.index, 'tzinfo') and df.index.tzinfo is not None:
    print("TZ is aware!")
    import pytz
    cutoff_date = cutoff_date.replace(tzinfo=pytz.utc).astimezone(df.index.tzinfo)
else:
    print("TZ is naive!")
    
try:
    test_df = df[df.index >= cutoff_date]
    print(f"Len: {len(test_df)}")
except Exception as e:
    print(f"Error: {e}")
