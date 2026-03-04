import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.technical_analysis import TechnicalAnalyzer

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")
print("Columns:", df.columns)
print("Index Type:", type(df.index))
if 'Date' in df.columns or 'date' in df.columns:
    print("Date column exists")
else:
    print("NO date column")
