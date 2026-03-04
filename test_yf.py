import yfinance as yf
ticker = yf.Ticker("^NSEI")
df = ticker.history(period="1500d", interval="1h")
print("Rows:", len(df))
print("Start:", df.index.min())
