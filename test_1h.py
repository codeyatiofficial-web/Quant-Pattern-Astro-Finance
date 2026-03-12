import yfinance as yf
import pandas as pd
from datetime import datetime

tdf = yf.download("^NSEI", period="60d", interval="1h", auto_adjust=True)
if isinstance(tdf.columns, pd.MultiIndex):
    tdf.columns = tdf.columns.get_level_values(0)

target_ret = tdf["Close"].pct_change().dropna()
if getattr(target_ret.index, 'tz', None) is not None:
    target_ret.index = target_ret.index.tz_convert('UTC')
target_ret.index = target_ret.index.floor('h')
target_ret = target_ret[~target_ret.index.duplicated(keep='last')]

ref_df = yf.download("ES=F", period="60d", interval="1h", auto_adjust=True)
if isinstance(ref_df.columns, pd.MultiIndex):
    ref_df.columns = ref_df.columns.get_level_values(0)

ref_ret = ref_df["Close"].pct_change().dropna()

if getattr(ref_ret.index, 'tz', None) is not None:
    ref_ret.index = ref_ret.index.tz_convert('UTC')
ref_ret.index = ref_ret.index.floor('h')
ref_ret = ref_ret[~ref_ret.index.duplicated(keep='last')]

combined = pd.DataFrame({"target": target_ret, "ref": ref_ret}).dropna()
rolling_corr = combined["target"].rolling(window=20).corr(combined["ref"]).dropna()
print("Rolling corr length:", len(rolling_corr))
print("Last 5 rolling corr:", rolling_corr.tail())

if len(rolling_corr) > 0:
    current_corr = round(float(rolling_corr.iloc[-1]), 4)
    latest_return = round(float(combined["ref"].iloc[-1]) * 100, 4)
    print("current_corr:", current_corr, "latest_return:", latest_return)
    print("Combined contribution:", current_corr * latest_return)

