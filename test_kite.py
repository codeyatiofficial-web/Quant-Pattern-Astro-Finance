from modules.kite_client import KiteDataClient
k = KiteDataClient()
print("Auth:", k.is_authenticated())
df = k.fetch_historical_data("^NSEI", interval="60minute", days_back=30)
print("Rows:", len(df))
if not df.empty:
    print(df.head())
