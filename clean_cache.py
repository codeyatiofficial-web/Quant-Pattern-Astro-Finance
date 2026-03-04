import sqlite3
conn = sqlite3.connect("data/market_cache.db")
c = conn.cursor()
c.execute("DELETE FROM intraday_fetch_log")
c.execute("DELETE FROM intraday_market_data")
conn.commit()
conn.close()
print("Cache flushed.")
