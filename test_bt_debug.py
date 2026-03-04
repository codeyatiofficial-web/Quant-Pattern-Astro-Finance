import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.technical_analysis import TechnicalAnalyzer

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")

print(f"Total Rows fetched: {len(df)}")
res = scanner._calculate_historical_success(df, "Bear Flag", "10y")
print("Bear Flag 10y Backtest:", res)

res2 = scanner._calculate_historical_success(df, "Bull Flag", "10y")
print("Bull Flag 10y Backtest:", res2)

