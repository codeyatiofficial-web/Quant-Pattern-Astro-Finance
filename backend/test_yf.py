import yfinance as yf
import pandas as pd
symbols = {"NIFTY 50": "^NSEI", "OIL": "CL=F"}
data = yf.download(" ".join(symbols.values()), period="5d", progress=False)
print(data.columns)
print("nlevels:", getattr(data.columns, 'nlevels', 1))
print("Is tuple in cols ('Close', '^NSEI') :", ('Close', '^NSEI') in data.columns)
print("Is tuple in cols ('Close', 'CL=F')  :", ('Close', 'CL=F') in data.columns)
# Let's see what data.columns really is natively
for col in data.columns:
    print(repr(col))
