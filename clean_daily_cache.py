import sqlite3
conn = sqlite3.connect("data/market_cache.db")
c = conn.cursor()
c.execute("DELETE FROM fetch_log")
c.execute("DELETE FROM market_data")
conn.commit()
conn.close()
print("Daily cache flushed.")
