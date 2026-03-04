import yfinance as yf
from datetime import datetime, timedelta

# Test fetching 1h data for a period older than 730 days
end_date = datetime.now() - timedelta(days=800)
start_date = end_date - timedelta(days=50)

ticker = yf.Ticker("^NSEI")
try:
    df = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval="1h")
    print("Rows:", len(df))
    if len(df) > 0:
        print("Start:", df.index.min())
except Exception as e:
    print("Error:", e)
