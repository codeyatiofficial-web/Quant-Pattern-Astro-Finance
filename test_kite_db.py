from modules.market_data import MarketDataFetcher
m = MarketDataFetcher()
df = m.fetch_intraday_data("^NSEI")
print("Intraday rows from DB/Kite:", len(df))
if not df.empty:
    print(df.head())
