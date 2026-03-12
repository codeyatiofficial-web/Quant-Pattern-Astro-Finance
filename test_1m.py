import yfinance as yf
data = yf.download("NQ=F GC=F", period="1d", interval="1m", progress=False)
print("1m data tail:")
print(data['Close'].tail(2))
