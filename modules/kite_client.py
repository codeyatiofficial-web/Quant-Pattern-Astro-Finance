import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from kiteconnect import KiteConnect

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env'))

# Common yfinance symbols to Kite Trading Symbols mapping
YFINANCE_TO_KITE_MAP = {
    "^NSEI": "NIFTY 50",
    "^NSEBANK": "NIFTY BANK",
    "^CNXIT": "NIFTY IT",
    "^CNXAUTO": "NIFTY AUTO",
    "^CNXFMCG": "NIFTY FMCG",
    "^CNXPHARMA": "NIFTY PHARMA",
    "^CNXMETAL": "NIFTY METAL",
    "^CNXREALTY": "NIFTY REALTY",
    "^CNXENERGY": "NIFTY ENERGY",
    "^CNXINFRA": "NIFTY INFRA",
    "^INDIAVIX": "INDIA VIX",
}

TOKEN_FILE = "data/kite_token.json"
INSTRUMENTS_FILE = "data/kite_instruments.csv"

class KiteDataClient:
    def __init__(self):
        self.api_key = os.getenv("KITE_API_KEY")
        self.api_secret = os.getenv("KITE_API_SECRET")
        self.kite = None
        self.instruments_df = None
        
        if self.api_key:
            self.kite = KiteConnect(api_key=self.api_key)
            self._load_token()

    def _load_token(self):
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    access_token = data.get("access_token")
                    if access_token:
                        self.kite.set_access_token(access_token)
            except Exception as e:
                logging.error(f"Failed to load Kite token: {e}")

    def _save_token(self, access_token):
        try:
            os.makedirs("data", exist_ok=True)
            with open(TOKEN_FILE, 'w') as f:
                json.dump({"access_token": access_token, "date": datetime.now().isoformat()}, f)
        except Exception as e:
            logging.error(f"Failed to save Kite token: {e}")

    def get_login_url(self) -> str:
        if not self.kite:
            return ""
        return self.kite.login_url()

    def _load_instruments(self):
        """Load instrument tokens from cached CSV or download if missing/old."""
        try:
            os.makedirs("data", exist_ok=True)
            download_needed = True

            if os.path.exists(INSTRUMENTS_FILE):
                # Check file modification time
                mtime = os.path.getmtime(INSTRUMENTS_FILE)
                if datetime.now().timestamp() - mtime < 24 * 3600:
                    download_needed = False

            if download_needed:
                import requests
                logging.info("Downloading Kite instruments...")
                response = requests.get("https://api.kite.trade/instruments/NSE", timeout=10)
                if response.status_code == 200:
                    with open(INSTRUMENTS_FILE, 'wb') as f:
                        f.write(response.content)
                else:
                    logging.warning(f"Failed to download instruments. Status Code: {response.status_code}")

            if os.path.exists(INSTRUMENTS_FILE):
                # Load via pandas
                self.instruments_df = pd.read_csv(INSTRUMENTS_FILE)
            else:
                self.instruments_df = None
        except Exception as e:
            logging.error(f"Error loading instruments: {e}")
            self.instruments_df = None

    def get_instrument_token(self, symbol: str):
        if getattr(self, 'instruments_df', None) is None:
            self._load_instruments()
            
        if self.instruments_df is None:
            return None

        # 1. Map known yfinance symbols
        search_symbol = YFINANCE_TO_KITE_MAP.get(symbol, symbol)
        
        # 2. Strip .NS if it exists (e.g. RELIANCE.NS -> RELIANCE)
        if search_symbol.endswith('.NS'):
            search_symbol = search_symbol[:-3]

        # 3. Exact match in tradingsymbol
        match = self.instruments_df[self.instruments_df['tradingsymbol'] == search_symbol]
        
        if not match.empty:
            return int(match.iloc[0]['instrument_token'])
            
        return None

    def generate_session(self, request_token: str):
        if not self.kite or not self.api_secret:
            raise Exception("Kite API credentials not fully configured.")
        
        data = self.kite.generate_session(request_token, api_secret=self.api_secret)
        access_token = data["access_token"]
        self.kite.set_access_token(access_token)
        self._save_token(access_token)
        return data

    def is_authenticated(self) -> bool:
        """Check if we have an active session by making a lightweight API call."""
        if not self.kite or not self.kite.access_token:
            return False
            
        try:
            # Profile call is lightweight and confirms auth validity
            self.kite.profile()
            return True
        except Exception:
            return False

    def fetch_historical_data(self, symbol: str, interval: str = "60minute", days_back: int = 3000) -> pd.DataFrame:
        if not self.is_authenticated():
            raise Exception("Kite is not authenticated. Please log in first.")
            
        instrument_token = self.get_instrument_token(symbol)
        if not instrument_token:
            # Fallback or unknown symbol
            raise ValueError(f"Symbol {symbol} not mapped to a Kite instrument token.")

        # Kite restricts '60minute' to 400 days per request, but 'day' allows 2000 candles.
        if interval in ("day", "week"):
            chunk_size_days = 1800  # ~5 years per chunk for daily
        else:
            chunk_size_days = 350   # ~1 year per chunk for intraday
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        all_data = []
        current_end = end_date
        
        while current_end > start_date:
            current_start = max(start_date, current_end - timedelta(days=chunk_size_days))
            
            try:
                records = self.kite.historical_data(
                    instrument_token=instrument_token,
                    from_date=current_start.strftime("%Y-%m-%d"),
                    to_date=current_end.strftime("%Y-%m-%d"),
                    interval=interval,
                    continuous=False,
                    oi=False
                )
                if records:
                    all_data.extend(records)
            except Exception as e:
                logging.error(f"Kite historical fetch error for {current_start} to {current_end}: {e}")
                # We stop chunking if an error (like rate limit, or out of subscription bounds) occurs.
                break
                
            current_end = current_start - timedelta(days=1)
            
        if not all_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        
        # Rename date column to datetime and normalize TZ
        df['datetime'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        # Drop kite's 'date' key which overlaps with our structures
        df = df.drop(columns=['date'])
        
        # Sort values and deduplicate
        df = df.sort_values('datetime').drop_duplicates('datetime').reset_index(drop=True)
        return df

