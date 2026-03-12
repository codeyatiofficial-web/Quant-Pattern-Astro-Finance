import yfinance as yf
import json

symbols = ["^NSEI", "NQ=F"]
tickers = yf.Tickers(" ".join(symbols))

results = []
for sym in symbols:
    info = tickers.tickers[sym].info
    curr = info.get("currentPrice") or info.get("regularMarketPrice")
    prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
    results.append({"symbol": sym, "currentPrice": curr, "previousClose": prev})

print(json.dumps(results, indent=2))
