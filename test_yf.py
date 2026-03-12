import yfinance as yf
data = yf.download("NQ=F", period="5d", progress=False)
print(data['Close'].dropna().tail(2))
