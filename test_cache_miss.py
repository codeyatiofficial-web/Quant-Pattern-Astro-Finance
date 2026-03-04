import pandas as pd
start_date = "2000-01-01"
min_date = "2021-03-01"

print(pd.to_datetime(min_date) > pd.to_datetime(start_date) + pd.Timedelta(days=7))
