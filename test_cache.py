from modules.market_data import MarketDataFetcher
import traceback
import pandas as pd

m = MarketDataFetcher()
mdf = m.fetch_nifty_data('2000-01-01', use_cache=False)
try:
    m._save_to_cache('^NSEI', mdf, '2000-01-01', '2026-02-28')
    print("Success! Cache saved.")
except Exception as e:
    print(e)
    traceback.print_exc()
