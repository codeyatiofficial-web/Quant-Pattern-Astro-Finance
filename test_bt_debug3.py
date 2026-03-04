import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.technical_analysis import TechnicalAnalyzer

scanner = TechnicalAnalyzer()
df = scanner.market_fetcher.fetch_stock_data("^NSEI", "2010-01-01", market="NSE")

pattern_name = "Bear Flag"
is_bullish = ("Bull" in pattern_name)
target_name_normalized = pattern_name.replace("Bullish ", "").replace("Bearish ", "").replace("Bull ", "").replace("Bear ", "")

print(f"Target Normalized: '{target_name_normalized}'")

prices = df['close'].values
found = 0
for i in range(50, len(df)-10, 50): # check every 50 days to be fast
    hist_pattern = scanner._detect_harmonics(df.iloc[:i], prices[i-1])
    hist_name = hist_pattern.get('name', '')
    hist_is_bullish = ("Bull" in hist_name)
    hist_name_normalized = hist_name.replace("Bullish ", "").replace("Bearish ", "").replace("Bull ", "").replace("Bear ", "")
    
    if hist_is_bullish == is_bullish and hist_name_normalized == target_name_normalized:
        print(f"Matched at {df.index[i]} -> {hist_name} (PRZ: {hist_pattern.get('prz')}, Target: {hist_pattern.get('target')}, Stop: {hist_pattern.get('stop')})")
        found += 1

print(f"Total Matches Found: {found}")
