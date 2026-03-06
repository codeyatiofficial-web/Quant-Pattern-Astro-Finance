import sys
import os
from datetime import datetime

os.chdir('/Users/anitarawat/nakshatranse/backend')
sys.path.append(os.path.abspath('/Users/anitarawat/nakshatranse'))

try:
    from modules.kite_client import KiteDataClient
except ImportError as e:
    print(f"Error importing: {e}")
    sys.exit(1)

client = KiteDataClient()

if not client.is_authenticated():
    print("Kite is NOT authenticated.")
    sys.exit(1)

print("Kite is authenticated.")
try:
    df = client.fetch_historical_data('^NSEI', interval='day', days_back=10)
    print("\nHistorical NIFTY 50 Data:")
    print(df.tail(2))
except Exception as e:
    print(f"Error fetching: {e}")
