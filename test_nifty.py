import yfinance as yf
ticker = "^NSEI"
hist = yf.download(ticker, period="6mo", progress=False, auto_adjust=True)
close = hist["Close"]
if hasattr(close, 'columns'):
    close = close.iloc[:, 0]
print(f"yfinance download ^NSEI close: {float(close.iloc[-1])}")
