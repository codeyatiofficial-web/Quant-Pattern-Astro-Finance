import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.technical_analysis import TechnicalAnalyzer
import pandas as pd
from datetime import datetime, timedelta

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")

historical_period = "10y"
years = int(historical_period.replace('y','').replace('Max','30')) if any(char.isdigit() for char in historical_period) else 5
cutoff_date = datetime.now() - timedelta(days=years * 365)
try:
    if list(df.index)[0].tzinfo is not None:
        cutoff_date = cutoff_date.replace(tzinfo=list(df.index)[0].tzinfo)
except:
    pass
    
print(f"Original Cutoff: {cutoff_date}")

# Let's inspect df dates
print(f"DF Min Date: {df.index.min()}")
print(f"DF Max Date: {df.index.max()}")

test_df = df[df.index >= cutoff_date]
print(f"Len After Filter: {len(test_df)}")

