import yfinance as yf
import pandas as pd
symbols = {"NIFTY": "^NSEI", "NASDAQ": "NQ=F"}
data_1m = yf.download(" ".join(symbols.values()), period="1d", interval="1m", progress=False)
data_1d = yf.download(" ".join(symbols.values()), period="5d", progress=False)

for name, sym in symbols.items():
    try:
        cur = data_1m['Close'][sym].dropna().iloc[-1]
    except:
        cur = data_1m['Close'].dropna().iloc[-1]
    
    try:
        hist = data_1d['Close'][sym].dropna().iloc[-2]
    except:
        hist = data_1d['Close'].dropna().iloc[-2]
    
    print(name, "Cur:", cur, "Prev:", hist)
