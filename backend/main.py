"""
Astro-Finance API Backend
FastAPI server serving Next.js frontend
"""
import sys
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add root directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.moon_calculator import MoonCalculator
from modules.market_data import MarketDataFetcher
from modules.analysis_engine import NakshatraAnalyzer
from modules.astro_correlation import AstroCorrelationEngine
from modules.nakshatra_database import get_all_nakshatras, get_nakshatra_by_number
from modules.kite_client import KiteDataClient
from modules.news_sentiment import NewsSentimentEngine
from modules.economic_events import EconomicEventsEngine
from modules.news_backtest import NewsBacktestEngine
from modules.derivatives_engine import DerivativesEngine
from modules.options_strategy import recommend_strategies, build_strategy_payoff, STRATEGIES
from modules.options_backtest import backtest_strategy, backtest_all_strategies
import modules.auth_engine as auth_engine


logger = logging.getLogger(__name__)

app = FastAPI(title="Astro-Finance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8888",
        "http://localhost:8080",
        "https://app.quant-pattern.com",
        "https://quant-pattern.com",
        "https://www.quant-pattern.com",
        "https://admin.quant-pattern.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules globally
moon_calc = MoonCalculator()
analyzer = NakshatraAnalyzer()
corr_engine = AstroCorrelationEngine()
market = MarketDataFetcher()
kite_client = KiteDataClient()
sentiment_engine = NewsSentimentEngine()
events_engine = EconomicEventsEngine()
news_backtest = NewsBacktestEngine()
derivatives_engine = DerivativesEngine()

class AnalysisRequest(BaseModel):
    symbol: str
    start_date: str = "2015-01-01"
    end_date: Optional[str] = None
    planet: str = "Moon"
    market: str = "NSE"
    intraday_period: str = "5000d"

class VolatilityRequest(BaseModel):
    symbol: str
    market: str = "NSE"
    period: str = "3650d" # Default 10 years
    threshold: float = 1.0 # 1 Percent minimum Variance

class TechnicalAnalysisRequest(BaseModel):
    symbol: str
    market: str = "NSE"
    historical_period: str = "5y"

class EventBacktestRequest(BaseModel):
    symbol: str
    planet: str
    event_type: str
    market: str = "NSE"
    years: int = 15
    forward_days: int = 0

# Authentication Models
class AuthRequest(BaseModel):
    email: str
    password: str

class TokenCheckRequest(BaseModel):
    token: str

class BrokerConfigRequest(BaseModel):
    token: str
    broker_name: str
    api_key: str
    api_secret: str

class BrokerPreferenceRequest(BaseModel):
    token: str
    is_active: bool
    trade_multiplier: float

class TradeRequest(BaseModel):
    symbols: List[str]
    planets: List[str]
    years: int = 15
    market: str = "NSE"

class HeatmapRequest(BaseModel):
    symbols: List[str]
    planets: List[str]
    years: int = 15
    market: str = "NSE"

class VixBacktestRequest(BaseModel):
    planet: str
    event_type: str
    years: int = 15
    forward_days: int = 0

class SentimentBacktestRequest(BaseModel):
    symbol: str = "^NSEI"
    period: str = "max"
    market: str = "NSE"

class SentimentAstroBacktestRequest(BaseModel):
    symbol: str = "^NSEI"
    period: str = "5y"
    market: str = "NSE"
    event_type: str = "Gajakesari_Yoga"
    planet: str = "Multiple"
    years: int = 5

class EventCategoryBacktestRequest(BaseModel):
    sub_event: str
    symbol: str = "^NSEI"
    window_days: int = 5

class FuturesBacktestRequest(BaseModel):
    target_symbol: str = "^NSEI"
    predictor_symbol: str
    condition: str
    years: int = 15
    forward_days: int = 0

@app.get("/")
def read_root():
    return {"message": "Welcome to Astro-Finance API"}

@app.get("/api/kite/status")
def get_kite_status():
    return {
        "authenticated": kite_client.is_authenticated(),
        "has_token": bool(kite_client.kite and kite_client.kite.access_token) if kite_client.kite else False,
    }

@app.get("/api/kite/login")
def get_kite_login():
    url = kite_client.get_login_url()
    if not url:
        raise HTTPException(status_code=500, detail="Kite API not configured properly")
    return {"url": url}

@app.get("/api/kite/redirect")
def kite_redirect_login():
    """Redirect the browser directly to Kite login page."""
    from fastapi.responses import RedirectResponse
    url = kite_client.get_login_url()
    if not url:
        raise HTTPException(status_code=500, detail="Kite API not configured properly")
    return RedirectResponse(url=url)

# ── Manual token management (for localhost / dev environments) ────────────────

@app.post("/api/kite/token")
def set_kite_token(payload: dict):
    """
    Manually set the Kite access token.
    Use this when the redirect_url in Kite Developer Portal points to production
    and you need to authenticate localhost separately.

    Body: { "access_token": "your_access_token_here" }
    """
    access_token = payload.get("access_token", "").strip()
    if not access_token:
        raise HTTPException(status_code=400, detail="access_token is required")

    if not kite_client.kite:
        raise HTTPException(status_code=500, detail="Kite API not initialized — check KITE_API_KEY in .env")

    try:
        kite_client.kite.set_access_token(access_token)
        kite_client._save_token(access_token)

        # Verify the token works
        is_valid = kite_client.is_authenticated()
        if not is_valid:
            return {"success": False, "message": "Token set but authentication failed — token may be expired"}

        return {"success": True, "message": "Kite token set successfully! Live data is now active."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set token: {str(e)}")

@app.get("/api/kite/token/export")
def export_kite_token():
    """
    Export the current Kite access token (for sharing between environments).
    Only works when already authenticated.
    """
    if not kite_client.is_authenticated():
        raise HTTPException(status_code=401, detail="Kite is not authenticated. No token to export.")

    token = kite_client.kite.access_token if kite_client.kite else None
    if not token:
        raise HTTPException(status_code=404, detail="No active token found")

    return {"access_token": token}

# ── Kite OAuth callback ──────────────────────────────────────────────────────

@app.get("/api/kite/callback")
def kite_callback_get(request_token: str = None, action: str = None, status: str = None):
    """
    Kite redirects here after user completes login on Kite website.
    URL: /api/kite/callback?request_token=XXX&action=login&status=success
    """
    from fastapi.responses import HTMLResponse
    if status == "success" and request_token:
        try:
            kite_client.generate_session(request_token)
            access_token = kite_client.kite.access_token if kite_client.kite else "N/A"
            html = f"""
            <html>
            <head><title>Kite Connected</title>
            <style>
              body {{ font-family: sans-serif; display: flex; justify-content: center;
                     align-items: center; height: 100vh; margin: 0;
                     background: #0a0f1e; color: white; flex-direction: column; }}
              .card {{ background: #1a2035; padding: 40px; border-radius: 16px;
                      text-align: center; border: 1px solid #2a3f6f; max-width: 600px; }}
              h2 {{ color: #4ade80; margin-bottom: 8px; }}
              a {{ color: #60a5fa; }}
              .hint {{ font-size: 12px; color: #8b949e; margin-top: 8px; }}
            </style>
            <script>
              // Auto-redirect to the frontend after 2 seconds
              var frontendUrl = window.location.hostname === 'localhost'
                  ? 'http://localhost:3000'
                  : 'https://app.quant-pattern.com';
              setTimeout(function() {{ window.location.href = frontendUrl; }}, 2000);
            </script>
            </head>
            <body>
              <div class='card'>
                <h2>✅ Kite API Connected!</h2>
                <p>Your session is now active. Live market data is enabled.</p>
                <p class='hint'>Redirecting to dashboard in 2 seconds…</p>
                <p><a id='dashLink' href='https://app.quant-pattern.com'>← Back to Dashboard</a></p>
                <script>
                  document.getElementById('dashLink').href = window.location.hostname === 'localhost'
                      ? 'http://localhost:3000' : 'https://app.quant-pattern.com';
                </script>
              </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html)
        except Exception as e:
            html = f"""
            <html>
            <head><title>Kite Login Failed</title>
            <style>
              body {{ font-family: sans-serif; display: flex; justify-content: center; 
                     align-items: center; height: 100vh; margin: 0; 
                     background: #0a0f1e; color: white; flex-direction: column; }}
              .card {{ background: #1a2035; padding: 40px; border-radius: 16px; 
                      text-align: center; border: 1px solid #7f1d1d; }}
              h2 {{ color: #f87171; margin-bottom: 8px; }}
              a {{ color: #60a5fa; }}
            </style>
            </head>
            <body>
              <div class='card'>
                <h2>❌ Kite Login Failed</h2>
                <p>Error: {str(e)}</p>
                <p><a href='/api/kite/redirect'>Try again →</a></p>
              </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html, status_code=400)
    else:
        html = """
        <html>
        <head><title>Kite Login Cancelled</title></head>
        <body>
          <h2>Login was cancelled or failed.</h2>
          <a href='/api/kite/redirect'>Try again</a>
        </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=400)

@app.post("/api/kite/callback")
def kite_callback_post(payload: dict):
    """Manual POST endpoint for token exchange."""
    request_token = payload.get("request_token")
    if not request_token:
        raise HTTPException(status_code=400, detail="Request token missing")
    try:
        kite_client.generate_session(request_token)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── Nifty 50 1-Min Candle Chart ──────────────────────────────────────────────

@app.get("/api/nifty50/candles")
def get_nifty50_candles(count: int = 30, interval: str = "minute"):
    """
    Fetch the last `count` candles for Nifty 50 via Kite API with Yahoo Finance fallback.
    Returns OHLC + volume data for the frontend candlestick chart.
    Supports intervals: minute, 3minute, 5minute, 15minute, 30minute, 60minute
    """
    try:
        # Try Kite API first
        if kite_client.is_authenticated():
            try:
                # Calculate days_back dynamically based on interval
                days_back = 1
                if interval == "3minute": days_back = 2
                elif interval == "5minute": days_back = 2
                elif interval == "15minute": days_back = 3
                elif interval == "30minute": days_back = 4
                elif interval in ("60minute", "hour"): days_back = 8

                df = kite_client.fetch_historical_data(
                    symbol="^NSEI",
                    interval=interval,
                    days_back=days_back
                )

                if not df.empty:
                    # Take last `count` candles
                    df = df.tail(count).reset_index(drop=True)

                    candles = []
                    for _, row in df.iterrows():
                        candles.append({
                            "time": row["datetime"].strftime("%H:%M") if interval != "day" else row["datetime"].strftime("%d %b"),
                            "open": round(float(row["open"]), 2),
                            "high": round(float(row["high"]), 2),
                            "low": round(float(row["low"]), 2),
                            "close": round(float(row["close"]), 2),
                            "volume": int(row.get("volume", 0)),
                        })

                    last = candles[-1] if candles else {}
                    first = candles[0] if candles else {}
                    change = round(last.get("close", 0) - first.get("open", 0), 2) if candles else 0
                    change_pct = round((change / first.get("open", 1)) * 100, 2) if candles and first.get("open", 0) else 0

                    return {
                        "success": True,
                        "symbol": "NIFTY 50",
                        "interval": interval,
                        "count": len(candles),
                        "candles": candles,
                        "last_price": last.get("close", 0),
                        "change": change,
                        "change_pct": change_pct,
                        "source": "kite"
                    }
            except Exception as e:
                logger.warning(f"Kite API failed: {e}. Falling back to Yahoo Finance.")

        # Fallback to Yahoo Finance for 5-minute intervals
        logger.info("Using Yahoo Finance fallback for Nifty candles")
        import yfinance as yf
        
        # Map intervals for yfinance
        yf_interval = "1m" if interval == "minute" else "5m"
        if interval in ["15minute"]: yf_interval = "15m"
        elif interval in ["30minute"]: yf_interval = "30m"
        elif interval in ["60minute", "hour"]: yf_interval = "1h"
        
        # Get data for last 2 days to ensure we have enough candles
        ticker = yf.Ticker("^NSEI")
        df = ticker.history(period="2d", interval=yf_interval)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No market data available")
            
        # Take last count candles
        df = df.tail(count).reset_index()
        
        candles = []
        for _, row in df.iterrows():
            candles.append({
                "time": row["Datetime"].strftime("%H:%M") if interval != "day" else row["Datetime"].strftime("%d %b"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2), 
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row.get("Volume", 0)),
            })

        last = candles[-1] if candles else {}
        first = candles[0] if candles else {}
        change = round(last.get("close", 0) - first.get("open", 0), 2) if candles else 0
        change_pct = round((change / first.get("open", 1)) * 100, 2) if candles and first.get("open", 0) else 0

        return {
            "success": True,
            "symbol": "NIFTY 50",
            "interval": interval,
            "count": len(candles),
            "candles": candles,
            "last_price": last.get("close", 0),
            "change": change,
            "change_pct": change_pct,
            "source": "yfinance"
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Nifty 50 candle fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# Native Email Authentication Endpoints
# ==========================================

@app.post("/api/auth/signup")
def signup(payload: AuthRequest):
    email = payload.email.strip().lower()
    if not email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password required")
        
    success = auth_engine.create_user(email, payload.password)
    if not success:
        raise HTTPException(status_code=400, detail="Email already registered or invalid")
        
    user_id = auth_engine.verify_user(email, payload.password)
    token = auth_engine.create_session(user_id)
    return {"success": True, "token": token, "email": email}

@app.post("/api/auth/login")
def login(payload: AuthRequest):
    email = payload.email.strip().lower()
    user_id = auth_engine.verify_user(email, payload.password)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    token = auth_engine.create_session(user_id)
    return {"success": True, "token": token, "email": email}

@app.post("/api/auth/me")
def get_current_user(payload: TokenCheckRequest):
    user = auth_engine.get_user_from_token(payload.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"success": True, "email": user["email"]}

@app.post("/api/user/broker/config")
def save_user_broker_config(payload: BrokerConfigRequest):
    user = auth_engine.get_user_from_token(payload.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    success = auth_engine.save_broker_config(
        user["id"], 
        payload.broker_name, 
        payload.api_key, 
        payload.api_secret
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save broker config securely")
    return {"success": True, "message": "Broker config saved"}

@app.post("/api/user/broker/preference")
def update_user_broker_pref(payload: BrokerPreferenceRequest):
    user = auth_engine.get_user_from_token(payload.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    success = auth_engine.update_broker_status(
        user["id"],
        payload.is_active,
        None,
        payload.trade_multiplier
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update preference")
    return {"success": True, "message": "Preferences updated"}

@app.post("/api/user/broker/status")
def get_user_broker_status(payload: TokenCheckRequest):
    user = auth_engine.get_user_from_token(payload.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    config = auth_engine.get_broker_config(user["id"])
    if not config:
        return {"success": True, "config": None}
        
    # Mask api string for frontend security
    config["api_key"] = config["api_key"][:4] + ("*" * 10) if config["api_key"] else ""
    config["api_secret"] = ("*" * 15) if config["api_secret"] else ""
    
    return {"success": True, "config": config}

@app.get("/api/admin/users/export")
def export_users():
    """Returns a list of all registered users for admin dashboard and CSV export"""
    users = auth_engine.get_all_users()
    return {"success": True, "users": users}


@app.get("/api/forecast/monthly")
def get_monthly_forecast(target_date: str = None, market: str = "NSE"):
    """
    Elite-only: Date-Wise Comprehensive 1-Month Market Forecast.
    Combines Astro signals, Technical trends, Options Chain, Macro Events, and Seasonality.
    """
    from datetime import datetime
    import math

    if target_date:
        try:
            anchor_dt = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        anchor_dt = datetime.now()
        
    now = datetime.now()
    is_historical = (now - anchor_dt).days > 3
    
    signals = []
    score = 0.0  

    # ── 1. ASTRO SIGNAL (weight: 3) ──────────────────────────────────────────
    try:
        upcoming_astro = analyzer.predict_upcoming_market(start_date=anchor_dt, days=30, market=market)
        bull_days = sum(1 for d in upcoming_astro if d.get("historical_tendency") == "Bullish")
        bear_days = sum(1 for d in upcoming_astro if d.get("historical_tendency") == "Bearish")
        
        astro_score = 0
        if bull_days > bear_days + 4:
            astro_score += 3.0
            signals.append({"category": "Astro", "icon": "🔮", "direction": "bullish",
                            "text": f"Next 30 days from {anchor_dt.strftime('%d %b')} favors bulls ({bull_days} vs {bear_days} Bearish)"})
        elif bear_days > bull_days + 4:
            astro_score -= 3.0
            signals.append({"category": "Astro", "icon": "🔮", "direction": "bearish",
                            "text": f"Next 30 days from {anchor_dt.strftime('%d %b')} favors bears ({bear_days} vs {bull_days} Bullish)"})
        else:
            signals.append({"category": "Astro", "icon": "🔮", "direction": "neutral",
                            "text": f"Balanced planetary transits for the upcoming month"})

        today_astro = analyzer.generate_insight_for_date(anchor_dt, market=market)
        yoga_name = today_astro.get("yoga_name", "")
        bullish_yogas = ["Gajakesari", "Raja", "Amala", "Dhana", "Saraswati"]
        bearish_yogas = ["Shula", "Visha", "Daridra", "Kemadruma"]
        if any(y.lower() in yoga_name.lower() for y in bullish_yogas):
            astro_score += 1.0
            signals.append({"category": "Astro", "icon": "⭐", "direction": "bullish",
                            "text": f"{yoga_name} active on {anchor_dt.strftime('%d %b')} — auspicious trigger"})
        elif any(y.lower() in yoga_name.lower() for y in bearish_yogas):
            astro_score -= 1.0
            signals.append({"category": "Astro", "icon": "⚠️", "direction": "bearish",
                            "text": f"{yoga_name} active on {anchor_dt.strftime('%d %b')} — short-term resistance"})
                            
        score += astro_score
    except Exception as e:
        logger.warning(f"Forecast: astro signal failed: {e}")

    # ── 8. NEW: ECONOMIC EVENTS SIGNAL ─────────────────────────────────────────
    try:
        from modules.economic_events import EconomicEventsEngine
        events_engine = EconomicEventsEngine()
        upcoming = events_engine.get_events_in_window(days_ahead=30)  # Next 30 days
        
        # Filter for near-term events
        near_events = [e for e in upcoming if e.get("days_away", 999) <= 15]
        if near_events:
            # We take the most imminent/important
            top_event = near_events[0]
            bias = top_event.get("original_bias", top_event.get("historical_bias", "Neutral"))
            
            if "ullish" in bias.lower():
                score += 1
                signals.append({"category": "Events", "icon": "📅", "direction": "bullish", "text": f"{top_event['sub_event']} in {top_event['days_away']}d ({bias})"})
            elif "earish" in bias.lower():
                score -= 1
                signals.append({"category": "Events", "icon": "📅", "direction": "bearish", "text": f"{top_event['sub_event']} in {top_event['days_away']}d ({bias})"})
            else:
                signals.append({"category": "Events", "icon": "📅", "direction": "neutral", "text": f"{top_event['sub_event']} closely watched"})
        else:
            signals.append({"category": "Events", "icon": "📅", "direction": "neutral", "text": "Quiet macroeconomic calendar for the next month"})
    except Exception as e:
        logger.warning(f"Forecast: events signal failed: {str(e)}")

    # ── 3. TECHNICAL SIGNAL (weight: 3) ──────────────────────────────────────
    try:
        import yfinance as yf
        import pandas as pd
        ticker_sym = "^NSEI" if market.upper() == "NSE" else "^IXIC"
        
        from dateutil.relativedelta import relativedelta
        start_date_tech = anchor_dt - relativedelta(years=1)
        end_date_tech = anchor_dt + relativedelta(days=1)
        
        hist = yf.Ticker(ticker_sym).history(start=start_date_tech.strftime("%Y-%m-%d"), end=end_date_tech.strftime("%Y-%m-%d"))
        
        if not hist.empty and len(hist) >= 100:
            close = hist["Close"]
            current = close.iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]
            
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean().iloc[-1]
            loss = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + gain / loss)) if loss != 0 else 50
            
            tr = pd.concat([hist['High'] - hist['Low'], 
                            abs(hist['High'] - hist['Close'].shift()), 
                            abs(hist['Low'] - hist['Close'].shift())], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            atr_pct = (atr / current) * 100

            tech_score = 0
            tech_notes = []
            
            if current > ma50: tech_score += 1
            else: tech_score -= 1
            
            if ma50 > ma200: 
                tech_score += 1; tech_notes.append("Golden Cross")
            else: 
                tech_score -= 1; tech_notes.append("Death Cross")
                
            if rsi < 30: 
                tech_score += 1; tech_notes.append("Oversold RSI")
            elif rsi > 70: 
                tech_score -= 1; tech_notes.append("Overbought RSI")
                
            if atr_pct > 2.0:
                tech_notes.append(f"High Volatility Regime ({atr_pct:.1f}% ATR)")
            else:
                tech_notes.append(f"Low Volatility ({atr_pct:.1f}% ATR)")

            score += tech_score
            direction = "bullish" if tech_score > 0 else ("bearish" if tech_score < 0 else "neutral")
            signals.append({"category": "Technical", "icon": "📈", "direction": direction,
                            "text": " · ".join(tech_notes) if tech_notes else "Neutral trend continuation"})
    except Exception as e:
        logger.warning(f"Forecast: technical signal failed: {e}")

    # ── 4. OPTIONS CHAIN SIGNAL (weight: 2) ──────────────────────────────────
    try:
        if is_historical:
             signals.append({"category": "Options", "icon": "⛓️", "direction": "historical", "text": "Historical Options Chain N/A"})
        else:
            snap = derivatives_engine.get_market_snapshot("NIFTY" if market == "NSE" else "NASDAQ")
            pcr = snap.get("pcr", 1.0)
            vix = snap.get("vix", {}).get("current", 15) if isinstance(snap.get("vix"), dict) else snap.get("vix", 15)

            opt_score = 0
            if pcr > 1.3:
                opt_score += 2; signals.append({"category": "Options", "icon": "⛓️", "direction": "bullish", "text": f"PCR {pcr:.2f} — high put accumulation support"})
            elif pcr < 0.7:
                opt_score -= 2; signals.append({"category": "Options", "icon": "⛓️", "direction": "bearish", "text": f"PCR {pcr:.2f} — heavy call writing resistance"})
            
            if vix > 22:
                opt_score -= 1
                if opt_score < 0: signals.append({"category": "Options", "icon": "🌡️", "direction": "bearish", "text": f"VIX {vix:.1f} — high volatility panic"})
            elif vix < 14:
                opt_score += 1
                if opt_score > 0 and len(signals) < 5: signals.append({"category": "Options", "icon": "🌡️", "direction": "bullish", "text": f"VIX {vix:.1f} — complacency"})
                
            if opt_score == 0:
                signals.append({"category": "Options", "icon": "⛓️", "direction": "neutral", "text": f"Options chain balanced (PCR {pcr:.1f}, VIX {vix:.1f})"})
            score += opt_score
    except Exception as e:
        logger.warning(f"Forecast: options signal failed: {e}")

    # ── 5. NEW: INSTITUTIONAL FII/DII SIGNAL (weight: 1) ───────────────────────
    try:
        from modules.institutional_data import fetch_fii_dii_data
        inst_data = fetch_fii_dii_data(anchor_dt)
        if inst_data:
            sentiment_inst = inst_data.get("sentiment", "Neutral")
            fii_val = inst_data.get("fii_net_cr", 0)
            dii_val = inst_data.get("dii_net_cr", 0)
            
            if sentiment_inst == "Bullish":
                score += 1.0
                signals.append({"category": "Institutional", "icon": "🏦", "direction": "bullish", "text": f"FII Net Buyers ({fii_val:+.0f} Cr) · DII ({dii_val:+.0f} Cr)"})
            elif sentiment_inst == "Bearish":
                score -= 1.0
                signals.append({"category": "Institutional", "icon": "🏦", "direction": "bearish", "text": f"FII Net Sellers ({fii_val:+.0f} Cr) · DII ({dii_val:+.0f} Cr)"})
            else:
                signals.append({"category": "Institutional", "icon": "🏦", "direction": "neutral", "text": f"Mixed FII/DII Institutional Flows"})
        elif is_historical:
            signals.append({"category": "Institutional", "icon": "🏦", "direction": "historical", "text": "Historical FII/DII Data N/A for exact date"})
    except Exception as e:
        logger.warning(f"Forecast: Institutional signal failed: {e}")

    # ── 6. NEW: SEASONALITY SIGNAL (weight: 1) ──────────────────────────────────
    try:
        month_idx = anchor_dt.month
        seasonality_map = {
            1: ("Neutral", "January effect consolidation"),
            2: ("Neutral", "Pre/Post budget volatility"),
            3: ("Mildly Bearish", "Financial year end profit booking"),
            4: ("Bullish", "New financial year allocations"),
            5: ("Neutral", "Sell in May and go away context"),
            6: ("Mildly Bullish", "Pre-monsoon positioning"),
            7: ("Bullish", "Q1 Earnings momentum"),
            8: ("Neutral", "Mid-year consolidation"),
            9: ("Bearish", "Historically the weakest month globally"),
            10: ("Mildly Bullish", "Festival season demand"),
            11: ("Bullish", "Pre-rally positioning"),
            12: ("Bullish", "Santa Claus rally")
        }
        seas_bias, seas_reason = seasonality_map.get(month_idx, ("Neutral", "Neutral Setup"))
        
        if "Bullish" in seas_bias:
            score += 1.0
            signals.append({"category": "Seasonality", "icon": "📅", "direction": "bullish", "text": f"{anchor_dt.strftime('%B')} — {seas_reason}"})
        elif "Bearish" in seas_bias:
            score -= 1.0
            signals.append({"category": "Seasonality", "icon": "📅", "direction": "bearish", "text": f"{anchor_dt.strftime('%B')} — {seas_reason}"})
    except Exception as e:
        logger.warning(f"Forecast: Seasonality signal failed: {e}")

    # ── COMPOSITE RESULT ─────────────────────────────────────────────────────
    max_possible = 12.0
    normalized = round(max(min(score / max_possible * 100, 100), -100), 1)
    confidence = round(min(abs(normalized), 90), 0)

    if score >= 4:
        verdict, verdict_color, verdict_emoji = "BULLISH", "#4ade80", "📈"
        summary = "Multiple converging signals point to upward momentum over the next month. Look for buying opportunities."
    elif score >= 1:
        verdict, verdict_color, verdict_emoji = "MILDLY BULLISH", "#86efac", "↗️"
        summary = "Moderate bullish bias with mixed sub-signals. Selective buying in strong sectors advised."
    elif score <= -4:
        verdict, verdict_color, verdict_emoji = "BEARISH", "#f87171", "📉"
        summary = "Multiple signals indicate downside risk. Consider hedging positions and reducing exposure."
    elif score <= -1:
        verdict, verdict_color, verdict_emoji = "MILDLY BEARISH", "#fca5a5", "↘️"
        summary = "Slight bearish tilt. Maintain strict stops and avoid aggressive long positions."
    else:
        verdict, verdict_color, verdict_emoji = "NEUTRAL", "#fbbf24", "↔️"
        summary = "No clear directional bias. Markets may consolidate. Wait for a breakout before taking large positions."

    try:
        from modules.holidays_engine import holidays_engine
        target_final_date = holidays_engine.calculate_1_month_target(anchor_dt, market)
        target_date_str = target_final_date.strftime("%d %b %Y")
    except Exception:
        from dateutil.relativedelta import relativedelta
        target_date_str = (anchor_dt + relativedelta(months=1)).strftime("%d %b %Y")

    return {
        "verdict": verdict,
        "verdict_color": verdict_color,
        "verdict_emoji": verdict_emoji,
        "score": round(score, 1),
        "normalized_score": normalized,
        "confidence": int(confidence),
        "summary": summary,
        "target_date": target_date_str,
        "signals": signals,
        "generated_at": datetime.now().isoformat(),
        "anchor_date": anchor_dt.strftime("%d %b %Y"),
        "is_historical": is_historical
    }


# ══════════════════════════════════════════════════════════════════════════════
# 14-DAY COMPREHENSIVE FORECAST
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/forecast/weekly")
def get_weekly_forecast(market: str = "NSE"):
    """
    Enhanced 1-week (5 trading day) forecast combining 11 signal layers:
    1. Nakshatra historical tendency
    2. Vedic Yogas (Angarak, Gajakesari, Guru-Chandal, etc.)
    3. Weekday seasonality
    4. Options chain / PCR / VIX
    5. FII/DII institutional flows
    6. Technical trend (DMA, RSI)
    7. Tithi / Paksha lunar phase bias
    8. Gochar / planetary transits
    9. Chart + Harmonic pattern bias
    10. News sentiment
    11. Economic event impact
    """
    from modules.planetary_yogas import detect_active_yogas, get_yoga_market_score
    from modules.institutional_data import fetch_fii_dii_data
    import yfinance as yf
    import pandas as pd
    from datetime import timedelta

    try:
        today = datetime.now()
        days = []

        # ══════════════════════════════════════════════════════════════════════════
        # GLOBAL SIGNALS (computed once, applied with decay to each day)
        # ══════════════════════════════════════════════════════════════════════════
    
        # ── 1. Options Chain snapshot ─────────────────────────────────────────────
        options_signal = {"pcr": None, "vix": None, "direction": "neutral", "text": "N/A"}
        try:
            snap = derivatives_engine.get_market_snapshot("NIFTY" if market == "NSE" else "SPY")
            if isinstance(snap, dict):
                pcr = snap.get("pcr", {}).get("value")
                vix = snap.get("vix", {}).get("value")
                options_signal["pcr"] = pcr
                options_signal["vix"] = vix
                if pcr and vix:
                    if pcr > 1.3:
                        options_signal["direction"] = "bullish"
                        options_signal["text"] = f"High PCR {pcr:.2f} (put writing) · VIX {vix:.1f}"
                    elif pcr < 0.7:
                        options_signal["direction"] = "bearish"
                        options_signal["text"] = f"Low PCR {pcr:.2f} (call writing) · VIX {vix:.1f}"
                    else:
                        options_signal["text"] = f"PCR {pcr:.2f} balanced · VIX {vix:.1f}"
        except Exception as e:
            logger.warning(f"Weekly forecast: Options snapshot failed: {str(e)}")
    
        # ── 2. FII/DII flows ─────────────────────────────────────────────────────
        fii_signal = {"direction": "neutral", "text": "N/A", "fii_net": None, "dii_net": None}
        try:
            fii_data = fetch_fii_dii_data(datetime.now())
            if fii_data and fii_data.get("fii_net") is not None:
                fii_net = fii_data["fii_net"]
                dii_net = fii_data.get("dii_net", 0)
                fii_signal["fii_net"] = fii_net
                fii_signal["dii_net"] = dii_net
                if fii_net > 500:
                    fii_signal["direction"] = "bullish"
                elif fii_net < -500:
                    fii_signal["direction"] = "bearish"
                fii_signal["text"] = f"FII {'+' if fii_net > 0 else ''}{fii_net:.0f} Cr · DII {'+' if dii_net > 0 else ''}{dii_net:.0f} Cr"
        except Exception as e:
            logger.warning(f"Weekly forecast: FII/DII failed: {e}")
    
        # ── 3. Technical snapshot ─────────────────────────────────────────────────
        tech_signal = {"direction": "neutral", "text": "N/A", "rsi": None, "trend": None, "current_price": None}
        try:
            ticker = "^NSEI" if market == "NSE" else "^IXIC"
            hist = yf.download(ticker, period="6mo", progress=False, auto_adjust=True)
            if not hist.empty:
                close = hist["Close"]
                if hasattr(close, 'columns'):
                    close = close.iloc[:, 0]
                dma50 = float(close.rolling(50).mean().iloc[-1])
                dma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
                last = float(close.iloc[-1])
                tech_signal["current_price"] = round(last, 2)
                # RSI
                delta = close.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss
                rsi = float((100 - 100 / (1 + rs)).iloc[-1])
                tech_signal["rsi"] = round(rsi, 1)
    
                parts = []
                if dma200 and dma50 > dma200:
                    parts.append("Golden Cross")
                    tech_signal["trend"] = "bullish"
                elif dma200 and dma50 < dma200:
                    parts.append("Death Cross")
                    tech_signal["trend"] = "bearish"
    
                if last > dma50:
                    parts.append("Above 50-DMA")
                else:
                    parts.append("Below 50-DMA")
    
                if rsi > 70:
                    parts.append(f"Overbought RSI {rsi:.0f}")
                elif rsi < 30:
                    parts.append(f"Oversold RSI {rsi:.0f}")
                else:
                    parts.append(f"RSI {rsi:.0f}")
    
                tech_signal["text"] = " · ".join(parts)
                if tech_signal["trend"] == "bullish" and last > dma50:
                    tech_signal["direction"] = "bullish"
                elif tech_signal["trend"] == "bearish" and last < dma50:
                    tech_signal["direction"] = "bearish"
        except Exception as e:
            logger.warning(f"Weekly forecast: Technical failed: {e}")
    
        # ── 4. Upcoming economic events ───────────────────────────────────────────
        upcoming_events = []
        try:
            events_list = events_engine.get_upcoming_events(days_ahead=10)
            for ev in events_list[:12]:
                upcoming_events.append({
                    "date": ev.get("date", ""),
                    "name": ev.get("event", ev.get("name", "")),
                    "impact": ev.get("impact", "medium"),
                    "bias": ev.get("expected_bias", "neutral"),
                    "market_impact": ev.get("historical_market_reaction", ""),
                })
        except Exception as e:
            logger.warning(f"Weekly forecast: Events failed: {e}")
    
        # ── 5. Gochar / Planetary transits in next 7 days ─────────────────────────
        gochar_events = []
        gochar_bias = 0
        try:
            upcoming_astro = analyzer.predict_upcoming_market(start_date=today, days=7, market=market)
            for entry in upcoming_astro:
                note = entry.get("note", entry.get("event", ""))
                tendency = entry.get("historical_tendency", "")
                if note:
                    gochar_events.append({
                        "date": entry.get("date", ""),
                        "event": note,
                        "tendency": tendency,
                    })
                if tendency == "Bullish":
                    gochar_bias += 0.3
                elif tendency == "Bearish":
                    gochar_bias -= 0.3
        except Exception as e:
            logger.warning(f"Weekly forecast: Gochar/transits failed: {e}")
    
        # ── 6. Chart + Harmonic pattern bias ──────────────────────────────────────
        chart_pattern_summary = {"bullish_count": 0, "bearish_count": 0, "neutral_count": 0, "patterns": [], "direction": "neutral"}
        try:
            from modules.technical_analysis import TechnicalAnalyzer
            scanner = TechnicalAnalyzer()
            ticker_sym = "^NSEI" if market == "NSE" else "^IXIC"
            result = scanner.run_multi_timeframe_scan(symbol=ticker_sym, market=market, historical_period="1y")
            all_pats = []
            for tf_key, tf_data in result.get("scans", {}).items():
                for p in tf_data.get("patterns", []):
                    bias = (p.get("bias") or "").lower()
                    name = p.get("pattern_name") or p.get("name", "")
                    wr = p.get("win_rate")
                    all_pats.append({"name": name, "bias": bias, "source": p.get("source", ""), "timeframe": tf_key, "win_rate": wr})
                    if "bullish" in bias:
                        chart_pattern_summary["bullish_count"] += 1
                    elif "bearish" in bias:
                        chart_pattern_summary["bearish_count"] += 1
                    else:
                        chart_pattern_summary["neutral_count"] += 1
            chart_pattern_summary["patterns"] = all_pats[:10]  # Top 10
            bc = chart_pattern_summary["bullish_count"]
            brc = chart_pattern_summary["bearish_count"]
            if bc > brc + 1:
                chart_pattern_summary["direction"] = "bullish"
            elif brc > bc + 1:
                chart_pattern_summary["direction"] = "bearish"
        except Exception as e:
            logger.warning(f"Weekly forecast: Chart pattern scan failed: {e}")
    
        # ── 7. News sentiment ─────────────────────────────────────────────────────
        news_signal = {"score": 0, "direction": "neutral", "text": "N/A", "headlines": []}
        try:
            news_data = sentiment_engine.get_live_sentiment()
            if news_data:
                avg_score = news_data.get("average_sentiment", news_data.get("avg_score", 0))
                headlines = news_data.get("headlines", news_data.get("articles", []))[:5]
                news_signal["score"] = round(avg_score, 2) if avg_score else 0
                news_signal["headlines"] = [
                    {"title": h.get("title", h.get("headline", "")), "sentiment": h.get("sentiment", "")}
                    for h in headlines
                ]
                if avg_score and avg_score > 0.15:
                    news_signal["direction"] = "bullish"
                    news_signal["text"] = f"Positive news sentiment ({avg_score:.2f})"
                elif avg_score and avg_score < -0.15:
                    news_signal["direction"] = "bearish"
                    news_signal["text"] = f"Negative news sentiment ({avg_score:.2f})"
                else:
                    news_signal["text"] = f"Mixed news sentiment ({avg_score:.2f})" if avg_score else "N/A"
        except Exception as e:
            logger.warning(f"Weekly forecast: News sentiment failed: {e}")
    
        # ── Weekday performance map ───────────────────────────────────────────────
        WEEKDAY_BIAS = {
            0: {"day": "Monday", "bias": "bearish", "note": "Gap-down tendency, weekend risk unwinding"},
            1: {"day": "Tuesday", "bias": "bullish", "note": "Historically strongest day for NIFTY"},
            2: {"day": "Wednesday", "bias": "neutral", "note": "Mid-week consolidation typical"},
            3: {"day": "Thursday", "bias": "bullish", "note": "Pre-expiry positioning, mild upside bias"},
            4: {"day": "Friday", "bias": "bearish", "note": "Profit booking before weekend"},
        }
        WEEKDAY_BIAS_US = {
            0: {"day": "Monday", "bias": "bearish", "note": "Monday effect, lower returns historically"},
            1: {"day": "Tuesday", "bias": "neutral", "note": "Mid-early week, mixed signals"},
            2: {"day": "Wednesday", "bias": "bullish", "note": "FOMC day effect, institutional positioning"},
            3: {"day": "Thursday", "bias": "neutral", "note": "Mid-week consolidation"},
            4: {"day": "Friday", "bias": "bullish", "note": "Friday rally tendency, pre-weekend buying"},
        }
        weekday_map = WEEKDAY_BIAS if market == "NSE" else WEEKDAY_BIAS_US
    
        # Tithi/Paksha bias map
        TITHI_BIAS = {
            "Amavasya": -1.0,    # New Moon — historically bearish
            "Purnima": 0.8,      # Full Moon — mildly bullish
            "Chaturthi": -0.3,   # Vinayaka — cautious
            "Ekadashi": 0.5,     # Auspicious
        }
        PAKSHA_BIAS = {
            "Shukla": 0.3,   # Waxing — growth sentiment
            "Krishna": -0.2,  # Waning — caution
        }
    
        # ══════════════════════════════════════════════════════════════════════════
        # PER-DAY FORECAST (7 calendar days → ~5 trading days)
        # ══════════════════════════════════════════════════════════════════════════
        for i in range(7):
            target_dt = today + timedelta(days=i)
            if target_dt.weekday() >= 5:
                continue
    
            breakdown = {}  # Track each signal's contribution
    
            # ── A. Astro: Nakshatra + Tithi + Yoga ────────────────────────────────
            astro = {}
            try:
                calc_dt = target_dt.replace(hour=9, minute=15, second=0, microsecond=0)
                astro = moon_calc.calculate_nakshatra(calc_dt)
            except Exception as e:
                logger.warning(f"Weekly forecast day {i}: astro failed: {e}")
    
            # ── B. Planetary Yogas ────────────────────────────────────────────────
            yoga_data = {}
            active_yogas = []
            try:
                calc_dt = target_dt.replace(hour=9, minute=15, second=0, microsecond=0)
                yoga_data = get_yoga_market_score(calc_dt)
                active_yogas = yoga_data.get("active_yogas", [])
            except Exception as e:
                logger.warning(f"Weekly forecast day {i}: yogas failed: {e}")
    
            # ── SIGNAL 1: Nakshatra tendency (weight: 2.0) ────────────────────────
            tendency = astro.get("historical_market_tendency", "Neutral")
            day_score = 0
            if tendency == "Bullish":
                day_score += 2.0
                breakdown["nakshatra"] = 2.0
            elif tendency == "Bearish":
                day_score -= 2.0
                breakdown["nakshatra"] = -2.0
            else:
                breakdown["nakshatra"] = 0
    
            # ── SIGNAL 2: Vedic Yogas (weight: scaled ×0.3) ──────────────────────
            yoga_score_raw = yoga_data.get("score", 0)
            yoga_contrib = round(yoga_score_raw * 0.3, 2)
            day_score += yoga_contrib
            breakdown["yogas"] = yoga_contrib
    
            # ── SIGNAL 3: Weekday seasonality (weight: 0.5) ──────────────────────
            wday = target_dt.weekday()
            wday_info = weekday_map.get(wday, {"day": "", "bias": "neutral", "note": ""})
            if wday_info["bias"] == "bullish":
                day_score += 0.5
                breakdown["weekday"] = 0.5
            elif wday_info["bias"] == "bearish":
                day_score -= 0.5
                breakdown["weekday"] = -0.5
            else:
                breakdown["weekday"] = 0
    
            # ── SIGNAL 7: Tithi + Paksha (weight: 0.5-1.0) ───────────────────────
            tithi_name = astro.get("tithi_name", "")
            paksha = astro.get("paksha", "")
            tithi_score = 0
            for key, val in TITHI_BIAS.items():
                if key.lower() in tithi_name.lower():
                    tithi_score += val
                    break
            tithi_score += PAKSHA_BIAS.get(paksha, 0)
            day_score += tithi_score
            breakdown["tithi_paksha"] = round(tithi_score, 2)
    
            # ── SIGNAL 8: Gochar / transits (global, applied per day) ─────────────
            gochar_contrib = round(gochar_bias * max(0.5, 1.0 - i * 0.1), 2)
            day_score += gochar_contrib
            breakdown["gochar"] = gochar_contrib
    
            # ── Events on this day ────────────────────────────────────────────────
            day_str = target_dt.strftime("%Y-%m-%d")
            day_events = [ev for ev in upcoming_events if ev.get("date", "").startswith(day_str)]
    
            # ── SIGNAL 11: Event impact (weight: 0.5–1.0) ─────────────────────────
            event_score = 0
            for ev in day_events:
                impact = ev.get("impact", "medium")
                bias = ev.get("bias", "neutral").lower()
                weight = 1.0 if impact == "high" else 0.5
                if "bullish" in bias:
                    event_score += weight
                elif "bearish" in bias:
                    event_score -= weight
                else:
                    event_score -= weight * 0.3  # Uncertainty penalty
            day_score += event_score
            breakdown["events"] = round(event_score, 2)
    
            # ── Global signals with decay ─────────────────────────────────────────
            decay = max(0.3, 1.0 - i * 0.1)
    
            # SIGNAL 4: Options/PCR
            opt_contrib = 0
            if options_signal["direction"] == "bullish":
                opt_contrib = round(1.0 * decay, 2)
            elif options_signal["direction"] == "bearish":
                opt_contrib = round(-1.0 * decay, 2)
            day_score += opt_contrib
            breakdown["options"] = opt_contrib
    
            # SIGNAL 5: FII/DII
            fii_contrib = 0
            if fii_signal["direction"] == "bullish":
                fii_contrib = round(0.8 * decay, 2)
            elif fii_signal["direction"] == "bearish":
                fii_contrib = round(-0.8 * decay, 2)
            day_score += fii_contrib
            breakdown["institutional"] = fii_contrib
    
            # SIGNAL 6: Technical trend
            tech_contrib = 0
            if tech_signal["direction"] == "bullish":
                tech_contrib = round(1.0 * decay, 2)
            elif tech_signal["direction"] == "bearish":
                tech_contrib = round(-1.0 * decay, 2)
            day_score += tech_contrib
            breakdown["technical"] = tech_contrib
    
            # SIGNAL 9: Chart pattern bias (global, decayed)
            cp_contrib = 0
            if chart_pattern_summary["direction"] == "bullish":
                cp_contrib = round(1.5 * decay, 2)
            elif chart_pattern_summary["direction"] == "bearish":
                cp_contrib = round(-1.5 * decay, 2)
            day_score += cp_contrib
            breakdown["chart_patterns"] = cp_contrib
    
            # SIGNAL 10: News sentiment (global, decayed)
            news_contrib = 0
            if news_signal["direction"] == "bullish":
                news_contrib = round(1.0 * decay, 2)
            elif news_signal["direction"] == "bearish":
                news_contrib = round(-1.0 * decay, 2)
            day_score += news_contrib
            breakdown["news"] = news_contrib
    
            # ── Determine verdict ─────────────────────────────────────────────────
            if day_score >= 3.5:
                verdict = "Strong Buy"
                color = "#4ade80"
                emoji = "🚀"
            elif day_score >= 1.5:
                verdict = "Bullish"
                color = "#86efac"
                emoji = "📈"
            elif day_score >= 0.5:
                verdict = "Mildly Bullish"
                color = "#a7f3d0"
                emoji = "↗️"
            elif day_score <= -3.5:
                verdict = "Strong Sell"
                color = "#f87171"
                emoji = "🔻"
            elif day_score <= -1.5:
                verdict = "Bearish"
                color = "#fca5a5"
                emoji = "📉"
            elif day_score <= -0.5:
                verdict = "Mildly Bearish"
                color = "#fed7aa"
                emoji = "↘️"
            else:
                verdict = "Neutral"
                color = "#fbbf24"
                emoji = "↔️"
    
            # ── Build day object ──────────────────────────────────────────────────
            days.append({
                "date": day_str,
                "weekday": target_dt.strftime("%A"),
                "verdict": verdict,
                "verdict_color": color,
                "verdict_emoji": emoji,
                "score": round(day_score, 2),
                "signal_breakdown": breakdown,
                "astro": {
                    "nakshatra": astro.get("nakshatra_name", "—"),
                    "nakshatra_sanskrit": astro.get("nakshatra_sanskrit", ""),
                    "pada": astro.get("pada", 0),
                    "tithi": astro.get("tithi_name", "—"),
                    "paksha": astro.get("paksha", ""),
                    "yoga": astro.get("yoga_name", "—"),
                    "tendency": tendency,
                    "ruling_planet": astro.get("ruling_planet", ""),
                },
                "planetary_yogas": [{
                    "name": y["name"],
                    "sanskrit": y.get("sanskrit", ""),
                    "icon": y.get("icon", ""),
                    "severity": y.get("severity", 0),
                    "impact": y.get("market_impact", "neutral"),
                    "desc": y.get("desc", ""),
                } for y in active_yogas],
                "weekday_bias": wday_info,
                "events": day_events,
            })
    
        # ── Week summary ──────────────────────────────────────────────────────────
        bull_days = sum(1 for d in days if d["score"] > 0.5)
        bear_days = sum(1 for d in days if d["score"] < -0.5)
        neutral_days = len(days) - bull_days - bear_days
        avg_score = round(sum(d["score"] for d in days) / max(len(days), 1), 2)
    
        if avg_score >= 1.5:
            week_verdict = "Bullish"
            week_color = "#4ade80"
        elif avg_score >= 0.5:
            week_verdict = "Mildly Bullish"
            week_color = "#86efac"
        elif avg_score <= -1.5:
            week_verdict = "Bearish"
            week_color = "#f87171"
        elif avg_score <= -0.5:
            week_verdict = "Mildly Bearish"
            week_color = "#fca5a5"
        else:
            week_verdict = "Neutral"
            week_color = "#fbbf24"
    
        return {
            "market": market,
            "generated_at": datetime.now().isoformat(),
            "days": days,
            "week_summary": {
                "avg_score": avg_score,
                "verdict": week_verdict,
                "verdict_color": week_color,
                "bull_days": bull_days,
                "bear_days": bear_days,
                "neutral_days": neutral_days,
                "total_signals": 11,
            },
            "global_signals": {
                "options": options_signal,
                "institutional": fii_signal,
                "technical": tech_signal,
            },
            "chart_patterns": chart_pattern_summary,
            "news_sentiment": news_signal,
            "gochar_events": gochar_events,
            "upcoming_events": upcoming_events,
    }
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Weekly forecast failed: {e}")
        # Return partial data if possible
        return {
            "market": market,
            "generated_at": datetime.now().isoformat(),
            "days": days if 'days' in dir() else [],
            "week_summary": {"avg_score": 0, "verdict": "Error", "verdict_color": "#f87171", "bull_days": 0, "bear_days": 0, "neutral_days": 0, "total_signals": 0},
            "global_signals": {},
            "chart_patterns": {},
            "news_sentiment": {},
            "gochar_events": [],
            "upcoming_events": [],
            "error": str(e),
        }



@app.get("/api/nakshatras")
def get_nakshatras():
    """Get all 27 Nakshatras."""
    return {"nakshatras": get_all_nakshatras()}


# ══════════════════════════════════════════════════════════════════════════════
# LIVE CHART DATA
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/market/live")
def get_live_market_data():
    """
    Fetch live market data for global indices and commodities.
    Uses yfinance to get reliable global data including Forex & Commodities.
    """
    import yfinance as yf
    import pandas as pd
    
    # Define the specific symbols requested by the user
    symbols = {
        "NIFTY 50": "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "NASDAQ": "NQ=F",
        "OIL": "CL=F",
        "GOLD": "GC=F",
        "USD/INR": "INR=X"
    }
    
    results = []
    
    try:
        data_1m = yf.download(" ".join(symbols.values()), period="1d", interval="1m", progress=False)
        data_1d = yf.download(" ".join(symbols.values()), period="5d", progress=False)
        
        for name, symbol in symbols.items():
            current_price = None
            prev_price = None
            
            try:
                # Get true live current price
                current_price = float(data_1m['Close'][symbol].dropna().iloc[-1] if isinstance(data_1m.columns, pd.MultiIndex) else data_1m['Close'].dropna().iloc[-1])
            except Exception:
                # Fallback to the daily close if 1m is somehow missing
                try:
                    current_price = float(data_1d['Close'][symbol].dropna().iloc[-1] if isinstance(data_1d.columns, pd.MultiIndex) else data_1d['Close'].dropna().iloc[-1])
                except Exception:
                    continue
                    
            try:
                # Get the previous day's close
                hist_series = data_1d['Close'][symbol].dropna() if isinstance(data_1d.columns, pd.MultiIndex) else data_1d['Close'].dropna()
                if len(hist_series) >= 2:
                    prev_price = float(hist_series.iloc[-2])
                elif len(hist_series) == 1:
                    prev_price = float(hist_series.iloc[0])
            except Exception:
                continue
                
            if current_price is None or prev_price is None:
                continue
                
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100 if prev_price else 0.0
                
            # Format appropriately depending on the instrument
            if symbol == "INR=X":
                price_str = f"₹{current_price:.2f}"
            elif symbol in ["CL=F", "GC=F"]:
                price_str = f"${current_price:.2f}"
            else:
                price_str = f"{current_price:,.2f}"
                
            results.append({
                "name": name,
                "symbol": symbol,
                "price": current_price,
                "priceStr": price_str,
                "change": change,
                "changePct": change_pct,
                "isPositive": change >= 0
            })
                
        return {"success": True, "data": results}
    except Exception as e:
        logger.error(f"Failed to fetch live market data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chart/ohlcv")
def get_chart_data(symbol: str = "^NSEI", interval: str = "1d", period: str = "6mo"):
    """
    Fetch OHLCV data for charting with SMA/EMA overlays.

    Strategy: Try Kite API first for NSE symbols (exchange-grade data),
              fall back to yfinance for US/crypto/commodities or if Kite unavailable.

    interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np

    # ── Determine if this is an NSE symbol eligible for Kite ──────────────────
    US_GLOBAL = {
        '^IXIC', '^GSPC', '^DJI', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN',
        'GOOGL', 'META', 'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F',
        'PL=F', 'PA=F', 'ALI=F', 'ZC=F', 'ZW=F', 'BTC-USD', 'ETH-USD',
        'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'AVAX-USD',
        'DOT-USD', 'LINK-USD', 'MATIC-USD', 'LTC-USD',
    }
    is_nse = symbol not in US_GLOBAL

    # ── Kite interval mapping ─────────────────────────────────────────────────
    KITE_INTERVAL_MAP = {
        '1m': 'minute', '3m': '3minute', '5m': '5minute', '15m': '15minute',
        '1h': '60minute', '1d': 'day', '1wk': 'week', '1mo': 'month',
    }

    # ── Period to days_back mapping ───────────────────────────────────────────
    PERIOD_DAYS = {
        '1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180,
        '1y': 365, '2y': 730, '5y': 1825, '10y': 3650, 'max': 5000,
    }

    hist = None
    data_source = "yfinance"

    # ── TRY KITE FIRST for NSE symbols ────────────────────────────────────────
    if is_nse and kite_client and kite_client.is_authenticated():
        kite_interval = KITE_INTERVAL_MAP.get(interval)
        days_back = PERIOD_DAYS.get(period, 180)

        if kite_interval:
            try:
                logger.info(f"Chart: Fetching {symbol} via Kite API ({kite_interval}, {days_back}d)")
                kite_df = kite_client.fetch_historical_data(
                    symbol=symbol,
                    interval=kite_interval,
                    days_back=days_back,
                )
                if kite_df is not None and not kite_df.empty:
                    # Normalize Kite DataFrame to match yfinance format
                    kite_df = kite_df.rename(columns={
                        'open': 'Open', 'high': 'High', 'low': 'Low',
                        'close': 'Close', 'volume': 'Volume',
                    })
                    if 'datetime' in kite_df.columns:
                        kite_df.index = pd.DatetimeIndex(kite_df['datetime'])
                        kite_df = kite_df.drop(columns=['datetime'], errors='ignore')

                    hist = kite_df
                    data_source = "kite"
                    logger.info(f"Chart: Got {len(hist)} candles from Kite for {symbol}")
            except Exception as e:
                logger.warning(f"Chart: Kite fetch failed for {symbol}, falling back to yfinance: {e}")
                hist = None

    # ── FALLBACK to yfinance ──────────────────────────────────────────────────
    if hist is None:
        INTRADAY_INTERVALS = {"1m", "2m", "3m", "5m", "15m", "30m", "60m", "90m", "1h"}
        yf_period = period
        if interval in INTRADAY_INTERVALS:
            if yf_period not in {"1d", "5d", "1mo"}:
                yf_period = "5d" if interval in {"1m", "2m"} else "1mo"

        try:
            hist = yf.download(symbol, period=yf_period, interval=interval, progress=False, auto_adjust=True)
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            data_source = "yfinance"
        except Exception as e:
            logger.error(f"Chart: yfinance also failed for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    if hist is None or hist.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    # ── Compute indicators on the DataFrame ───────────────────────────────────
    close = hist["Close"]
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist_series = macd_line - signal_line

    # Bollinger Bands
    bb_std = close.rolling(20).std()
    bb_upper = sma20 + 2 * bb_std
    bb_lower = sma20 - 2 * bb_std

    # ── Build output arrays ───────────────────────────────────────────────────
    candles = []
    sma20_data, sma50_data, ema9_data, ema21_data = [], [], [], []
    bb_upper_data, bb_lower_data = [], []
    volume_data, rsi_data, macd_data = [], [], []

    for idx in hist.index:
        if hasattr(idx, 'timestamp'):
            t = int(idx.timestamp())
        else:
            t = int(pd.Timestamp(idx).timestamp())

        o = float(hist.loc[idx, "Open"])
        h = float(hist.loc[idx, "High"])
        l = float(hist.loc[idx, "Low"])
        c = float(hist.loc[idx, "Close"])
        v = float(hist.loc[idx, "Volume"]) if "Volume" in hist.columns else 0

        if np.isnan(o) or np.isnan(c):
            continue

        candles.append({"time": t, "open": round(o, 2), "high": round(h, 2), "low": round(l, 2), "close": round(c, 2)})
        volume_data.append({"time": t, "value": v, "color": "rgba(74,222,128,0.3)" if c >= o else "rgba(248,113,113,0.3)"})

        s20 = float(sma20.loc[idx]) if not np.isnan(float(sma20.loc[idx])) else None
        s50 = float(sma50.loc[idx]) if not np.isnan(float(sma50.loc[idx])) else None
        e9 = float(ema9.loc[idx]) if not np.isnan(float(ema9.loc[idx])) else None
        e21 = float(ema21.loc[idx]) if not np.isnan(float(ema21.loc[idx])) else None

        if s20: sma20_data.append({"time": t, "value": round(s20, 2)})
        if s50: sma50_data.append({"time": t, "value": round(s50, 2)})
        if e9: ema9_data.append({"time": t, "value": round(e9, 2)})
        if e21: ema21_data.append({"time": t, "value": round(e21, 2)})

        bu = float(bb_upper.loc[idx]) if not np.isnan(float(bb_upper.loc[idx])) else None
        bl = float(bb_lower.loc[idx]) if not np.isnan(float(bb_lower.loc[idx])) else None
        if bu: bb_upper_data.append({"time": t, "value": round(bu, 2)})
        if bl: bb_lower_data.append({"time": t, "value": round(bl, 2)})

        r = float(rsi.loc[idx]) if not np.isnan(float(rsi.loc[idx])) else None
        if r: rsi_data.append({"time": t, "value": round(r, 1)})

        m = float(macd_line.loc[idx]) if not np.isnan(float(macd_line.loc[idx])) else None
        s = float(signal_line.loc[idx]) if not np.isnan(float(signal_line.loc[idx])) else None
        mh = float(macd_hist_series.loc[idx]) if not np.isnan(float(macd_hist_series.loc[idx])) else None
        if m is not None:
            macd_data.append({"time": t, "macd": round(m, 2), "signal": round(s, 2) if s else 0, "histogram": round(mh, 2) if mh else 0})

    # Current price info
    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else last_close
    change = last_close - prev_close
    change_pct = (change / prev_close * 100) if prev_close != 0 else 0

    return {
        "symbol": symbol,
        "interval": interval,
        "period": period,
        "data_source": data_source,
        "total_candles": len(candles),
        "price": {
            "last": round(last_close, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "high_52w": round(float(close.tail(252).max()), 2) if len(close) >= 252 else round(float(close.max()), 2),
            "low_52w": round(float(close.tail(252).min()), 2) if len(close) >= 252 else round(float(close.min()), 2),
        },
        "candles": candles,
        "overlays": {
            "sma20": sma20_data,
            "sma50": sma50_data,
            "ema9": ema9_data,
            "ema21": ema21_data,
            "bb_upper": bb_upper_data,
            "bb_lower": bb_lower_data,
        },
        "volume": volume_data,
        "indicators": {
            "rsi": rsi_data,
            "macd": macd_data,
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# CHART PATTERN DETECTION — returns all patterns positioned for chart overlay
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/chart/patterns")
def get_chart_patterns(symbol: str = "^NSEI", interval: str = "1d", period: str = "6mo"):
    """
    Detect all technical patterns on the chart OHLCV data.
    Returns candlestick, harmonic, chart patterns + fibonacci + pivots with timestamps.
    Uses Kite first for NSE, fallback yfinance — same data as /api/chart/ohlcv.
    """
    import pandas as pd
    import numpy as np
    from scipy.signal import argrelextrema

    try:
        from modules.technical_analysis import TechnicalAnalyzer
        scanner = TechnicalAnalyzer()

        # Map frontend intervals to kite/yfinance intervals
        KITE_INTERVAL_MAP = {
            '1m': 'minute', '3m': '3minute', '5m': '5minute', '15m': '15minute', 
            '1h': '60minute', '1d': 'day', '1wk': 'week', '1mo': 'month',
        }
        YF_INTERVAL_MAP = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', 
            '1h': '60m', '1d': '1d', '1wk': '1wk', '1mo': '1mo',
        }
        PERIOD_DAYS = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180,
            '1y': 365, '2y': 730, '5y': 1825, 'max': 5000,
        }

        kite_int = KITE_INTERVAL_MAP.get(interval, 'day')
        yf_int = YF_INTERVAL_MAP.get(interval, '1d')
        days_back = PERIOD_DAYS.get(period, 180)

        # Determine market
        US_GLOBAL = {
            '^IXIC', '^GSPC', '^DJI', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN',
            'GOOGL', 'META', 'GC=F', 'SI=F', 'CL=F', 'BTC-USD', 'ETH-USD',
        }
        market = "NASDAQ" if symbol in US_GLOBAL else "NSE"

        # Fetch data using existing kite-or-fallback method
        df = scanner._fetch_with_kite_or_fallback(symbol, yf_int, "", market, days_back)
        if df is None or df.empty or len(df) < 30:
            return {"patterns": [], "fibonacci": {}, "harmonic": {}, "chart_pattern": {}}

        df.columns = [c.lower() for c in df.columns]
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = 0.0

        current_price = float(df["close"].iloc[-1])

        # ── Helper: get timestamps from DataFrame ────────────────────────
        def get_ts(idx_val):
            """Convert a DataFrame index value to UNIX timestamp."""
            try:
                if hasattr(idx_val, 'timestamp'):
                    return int(idx_val.timestamp())
                return int(pd.Timestamp(idx_val).timestamp())
            except Exception:
                return 0

        # ══════════════════════════════════════════════════════════════════
        # 1. SCAN CANDLESTICK PATTERNS across the last N bars
        # ══════════════════════════════════════════════════════════════════
        candle_markers = []
        scan_range = min(len(df) - 5, 200)  # scan last 200 bars

        for i in range(scan_range):
            end_idx = len(df) - i
            if end_idx < 6:
                break
            window = df.iloc[:end_idx].copy()
            pat = scanner._detect_candlestick_patterns(window)
            pname = pat.get("name", "")
            if pname not in ["No Signal", "Consolidation", "Spinning Top"]:
                bar_time = get_ts(df.index[end_idx - 1])
                bar_price = float(df.iloc[end_idx - 1]["close"])
                is_bull = any(k in pname for k in ["Bull", "Morning", "Hammer", "Soldier",
                                                     "Piercing", "Bottom", "Inverted", "Kicker Up",
                                                     "Belt Hold" if "Bull" in pname else "___"])
                is_bear = any(k in pname for k in ["Bear", "Evening", "Shooting", "Hanging",
                                                     "Crow", "Dark Cloud", "Top", "Kicker"])

                # Avoid duplicate markers at the same time
                if not any(m["time"] == bar_time and m["name"] == pname for m in candle_markers):
                    candle_markers.append({
                        "time": bar_time,
                        "price": round(bar_price, 2),
                        "name": pname,
                        "type": "candlestick",
                        "bias": "Bullish" if is_bull else "Bearish" if is_bear else "Neutral",
                        "target": pat.get("target", ""),
                        "stop": pat.get("stop", ""),
                        "all_detected": pat.get("all_detected", [pname]),
                    })

        # ══════════════════════════════════════════════════════════════════
        # 2. HARMONIC PATTERN (current state + XABCD points)
        # ══════════════════════════════════════════════════════════════════
        harmonic_result = scanner._detect_harmonics(df, current_price)
        harmonic_data = {**harmonic_result}

        # Get XABCD swing point coordinates for drawing on chart
        try:
            prices = df["close"].values
            highs = df["high"].values
            lows = df["low"].values
            order = max(3, len(prices) // 30)
            max_idx = argrelextrema(highs, np.greater_equal, order=order)[0]
            min_idx = argrelextrema(lows, np.less_equal, order=order)[0]
            swings = sorted([(i, "H", highs[i]) for i in max_idx] +
                            [(i, "L", lows[i]) for i in min_idx])
            if len(swings) >= 5:
                pts = swings[-5:]
                harmonic_data["xabcd_points"] = [
                    {"label": lbl, "time": get_ts(df.index[pt[0]]),
                     "price": round(float(pt[2]), 2)}
                    for lbl, pt in zip(["X", "A", "B", "C", "D_current"], pts)
                ]
                # Add current as D
                harmonic_data["xabcd_points"][-1] = {
                    "label": "D",
                    "time": get_ts(df.index[-1]),
                    "price": round(current_price, 2),
                }
        except Exception:
            pass

        # Backtest harmonic
        h_name = harmonic_result.get("name", "")
        if h_name not in ["No Swing", "Consolidation"]:
            harmonic_data["backtest"] = scanner._backtest_pattern(df, h_name, 5)

        # ══════════════════════════════════════════════════════════════════
        # 3. CHART PATTERNS (structural — H&S, Double Top, Triangles etc.)
        # ══════════════════════════════════════════════════════════════════
        chart_pattern = scanner._detect_chart_patterns(df, current_price)
        cp_name = chart_pattern.get("name", "")
        if cp_name not in ["Consolidation", "Ranging"]:
            chart_pattern["backtest"] = scanner._backtest_pattern(df, cp_name, 5)

        # ══════════════════════════════════════════════════════════════════
        # 4. FIBONACCI LEVELS + PIVOTS
        # ══════════════════════════════════════════════════════════════════
        fib_data = scanner._fibonacci_levels(df)

        # ══════════════════════════════════════════════════════════════════
        # 5. BACKTEST top candlestick patterns
        # ══════════════════════════════════════════════════════════════════
        # Backtest up to 5 unique candlestick pattern names
        seen_names = set()
        for m in candle_markers:
            pn = m["name"]
            if pn not in seen_names and len(seen_names) < 5:
                seen_names.add(pn)
                bt = scanner._backtest_pattern(df, pn, 5)
                m["backtest"] = bt
            elif pn in seen_names:
                # Copy backtest from first occurrence
                for prev in candle_markers:
                    if prev["name"] == pn and "backtest" in prev:
                        m["backtest"] = prev["backtest"]
                        break

        # Sort markers by time (newest first for frontend display)
        candle_markers.sort(key=lambda x: x["time"], reverse=True)

        return {
            "symbol": symbol,
            "interval": interval,
            "total_bars_scanned": scan_range,
            "patterns": candle_markers[:50],  # cap at 50 markers
            "harmonic": harmonic_data,
            "chart_pattern": chart_pattern,
            "fibonacci": fib_data,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Chart patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nakshatras/{number}")
def get_nakshatra(number: int):
    """Get specific Nakshatra by number (1-27)."""
    nak = get_nakshatra_by_number(number)
    if nak:
        return nak
    raise HTTPException(status_code=404, detail="Nakshatra not found")

@app.get("/api/insight/today")
def get_today_insight():
    """Get today's Moon position and trading insight."""
    try:
        return analyzer.generate_today_insight()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insight/date/{date_str}")
def get_insight_for_date(date_str: str, planet: str = "Moon", market: str = "NSE"):
    """Get Planet position and trading insight for a specific date (YYYY-MM-DD)."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        return analyzer.generate_insight_for_date(target_date, planet, market)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predict/{date_str}")
def get_prediction(date_str: str, days: int = 7, planet: str = "Moon", market: str = "NSE"):
    """Predict market moves for upcoming trading days starting from a date."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        return {"predictions": analyzer.predict_upcoming_market(target_date, days, planet, market)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
def run_analysis(req: AnalysisRequest):
    """Run full statistical analysis for a market symbol."""
    try:
        merged = analyzer.build_merged_dataset(
            start_date=req.start_date,
            end_date=req.end_date,
            symbol=req.symbol,
            planet=req.planet,
            market=req.market
        )
        if merged.empty:
            raise HTTPException(status_code=400, detail="No data available for the given parameters")
        
        summary = analyzer.nakshatra_performance_summary(merged)
        tithi_summary = analyzer.tithi_performance_summary(merged)
        
        merged_market_rise = merged[merged['planet_rise_market_hours'] == True]
        summary_market_rise = analyzer.nakshatra_performance_summary(merged_market_rise)
        tithi_summary_market_rise = analyzer.tithi_performance_summary(merged_market_rise)
        
        merged_outside_rise = merged[merged['planet_rise_market_hours'] == False]
        summary_outside_rise = analyzer.nakshatra_performance_summary(merged_outside_rise)
        tithi_summary_outside_rise = analyzer.tithi_performance_summary(merged_outside_rise)
        
        # Make python types JSON serializable (NaN, etc.)
        summary = summary.replace({float('nan'): None}) if not summary.empty else summary
        summary_market_rise = summary_market_rise.replace({float('nan'): None}) if not summary_market_rise.empty else summary_market_rise
        summary_outside_rise = summary_outside_rise.replace({float('nan'): None}) if not summary_outside_rise.empty else summary_outside_rise

        tithi_summary = tithi_summary.replace({float('nan'): None}) if not tithi_summary.empty else tithi_summary
        tithi_summary_market_rise = tithi_summary_market_rise.replace({float('nan'): None}) if not tithi_summary_market_rise.empty else tithi_summary_market_rise
        tithi_summary_outside_rise = tithi_summary_outside_rise.replace({float('nan'): None}) if not tithi_summary_outside_rise.empty else tithi_summary_outside_rise
        
        anova = analyzer.run_anova_test(merged)
        chi2 = analyzer.run_chi_square_test(merged)
        
        # Element and Planet summaries
        planet_df = analyzer.ruling_planet_analysis(merged).replace({float('nan'): None})
        element_df = analyzer.element_analysis(merged).replace({float('nan'): None})
        
        return {
            "summary": summary.to_dict(orient="records") if not summary.empty else [],
            "summary_market_rise": summary_market_rise.to_dict(orient="records") if not summary_market_rise.empty else [],
            "summary_outside_rise": summary_outside_rise.to_dict(orient="records") if not summary_outside_rise.empty else [],
            "tithi_summary": tithi_summary.to_dict(orient="records") if not tithi_summary.empty else [],
            "tithi_summary_market_rise": tithi_summary_market_rise.to_dict(orient="records") if not tithi_summary_market_rise.empty else [],
            "tithi_summary_outside_rise": tithi_summary_outside_rise.to_dict(orient="records") if not tithi_summary_outside_rise.empty else [],
            "anova": anova,
            "chi2": chi2,
            "observations": len(merged),
            "planet_analysis": planet_df.to_dict(orient="records"),
            "element_analysis": element_df.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/api/analyze/lagna")
def run_lagna_analysis(req: AnalysisRequest):
    """Run Ascendant (Lagna) intraday time correlation analysis.
    Period and Interval are presently restricted to max High-Res bounds of 730d / 1h.
    """
    try:
        # Build dataset tagging every 1hour period with its Rashi Ascendant
        lagna_df = analyzer.build_intraday_lagna_dataset(req.symbol, period=req.intraday_period, market=req.market)
        
        if lagna_df.empty:
            return {
                "summary": [],
                "observations": 0,
                "error": "No Intraday data found. Check symbol validity."
            }
            
        summary = analyzer.lagna_performance_summary(lagna_df)
        
        return {
            "summary": summary,
            "observations": len(lagna_df.dropna(subset=['return']))
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/yoga")
def run_yoga_analysis(req: AnalysisRequest):
    """Run Nitya Yoga intraday time correlation analysis.
    Period and Interval are presently restricted to max High-Res bounds of 5000d / 1h.
    """
    try:
        # Build dataset tagging every 1hour period with its Nitya Yoga
        yoga_df = analyzer.build_intraday_yoga_dataset(req.symbol, period=req.intraday_period, market=req.market)
        
        if yoga_df.empty:
            return {
                "summary": [],
                "observations": 0,
                "error": "No Intraday data found. Check symbol validity."
            }
            
        summary = analyzer.yoga_performance_summary(yoga_df)
        
        return {
            "summary": summary,
            "observations": len(yoga_df.dropna(subset=['return']))
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/nakshatra/intraday")
def run_intraday_nakshatra_analysis(req: AnalysisRequest):
    """Run Intraday Nakshatra time correlation analysis."""
    try:
        nak_df = analyzer.build_intraday_nakshatra_dataset(req.symbol, period=req.intraday_period, market=req.market)
        
        if nak_df.empty:
            return {
                "summary": [],
                "observations": 0,
                "error": "No Intraday data found. Check symbol validity."
            }
            
        summary = analyzer.nakshatra_intraday_performance_summary(nak_df)
        
        return {
            "summary": summary,
            "observations": len(nak_df.dropna(subset=['return']))
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/volatility")
def run_volatility_analysis(req: VolatilityRequest):
    """Scan historical daily candles to find combinations driving >X% daily variance."""
    try:
        vol_df, total_days = analyzer.build_volatility_dataset(
            symbol=req.symbol, 
            period=req.period, 
            threshold=req.threshold, 
            market=req.market
        )
        
        if vol_df.empty:
            return {
                "results": {"weekday": [], "nakshatra": [], "tithi": [], "yoga": [], "lagna": []},
                "total_candles_scoped": total_days,
                "volatile_candles_found": 0
            }
            
        summary = analyzer.volatility_performance_summary(vol_df, total_days)
        
        return {
            "results": summary,
            "total_candles_scoped": total_days,
            "volatile_candles_found": len(vol_df)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/technical")
async def run_technical_analysis(req: TechnicalAnalysisRequest):
    """Deep-Dive Quantitative pattern scanning — Harmonics, Candlesticks, Fibs, 1-week forecast."""
    try:
        from modules.technical_analysis import TechnicalAnalyzer
        scanner = TechnicalAnalyzer()
        
        live_fallback_used = False
        import pytz
        from datetime import datetime
        
        # Users can scan any market at any time; no forced fallback needed.

        # New engine returns a structured dict with scans, fib, prediction, astro
        result = scanner.run_multi_timeframe_scan(
            symbol=req.symbol,
            market=req.market,
            historical_period=req.historical_period
        )

        return {
            "success": True,
            "symbol": req.symbol,
            "live_fallback_used": live_fallback_used,
            # New structured fields
            "scans":          result.get("scans", {}),
            "fibonacci":      result.get("fibonacci", {}),
            "week_prediction":result.get("week_prediction", {}),
            "astro_confluence": result.get("astro_confluence", []),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/correlation/event-backtest")
def run_event_backtest(req: EventBacktestRequest):
    """Run an advanced Astro-Correlation engine backtest for specific planetary conditions."""
    try:
        res = corr_engine.backtest_event(
            symbol=req.symbol,
            planet=req.planet,
            event_type=req.event_type,
            market=req.market,
            years=req.years,
            forward_days=req.forward_days
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/correlation/heatmap")
def run_correlation_heatmap(req: HeatmapRequest):
    """Generate a Pearson correlation matrix for Planetary speed vs Asset returns."""
    try:
        res = corr_engine.generate_correlation_heatmap(
            symbols=req.symbols,
            planets=req.planets,
            market=req.market,
            years=req.years
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return {"data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/correlation/futures-backtest")
def run_futures_backtest(req: FuturesBacktestRequest):
    """Run an independent t-test backtest of Nifty 50 daily returns based on conditions in a global indicator."""
    import pandas as pd
    from datetime import datetime
    
    try:
        effective_years = 30 if req.years >= 99 else req.years
        start_date = (datetime.now() - pd.DateOffset(years=effective_years)).strftime('%Y-%m-%d')
        
        target_df = corr_engine.market.fetch_stock_data(req.target_symbol, start_date=start_date, market="NSE" if "^NSE" in req.target_symbol.upper() else "Global")
        predictor_df = corr_engine.market.fetch_stock_data(req.predictor_symbol, start_date=start_date, market="Global")
        
        if target_df.empty or predictor_df.empty:
            raise HTTPException(status_code=400, detail="Could not fetch market data for one or both symbols.")
            
        target_df['date'] = pd.to_datetime(target_df['date']).dt.normalize()
        predictor_df['date'] = pd.to_datetime(predictor_df['date']).dt.normalize()
        
        t_df = target_df.set_index('date')
        p_df = predictor_df.set_index('date')
        
        combined_df = pd.DataFrame({
            'target_close': t_df['close'],
            'target_return': t_df['daily_return'],
            'pred_return': p_df['daily_return']
        }).dropna()
        
        if len(combined_df) < 10:
             raise HTTPException(status_code=400, detail="Insufficient overlapping dates.")
             
        test_col = 'target_return'
        if req.forward_days > 0:
            combined_df[f'target_forward_{req.forward_days}d'] = combined_df['target_close'].shift(-req.forward_days) / combined_df['target_close'] - 1.0
            test_col = f'target_forward_{req.forward_days}d'
            
        cond = req.condition.lower()
        if cond == "positive return":
             mask = combined_df['pred_return'] > 0
        elif cond == "negative return":
             mask = combined_df['pred_return'] < 0
        elif cond == "return > 1%":
             mask = combined_df['pred_return'] > 0.01
        elif cond == "return < -1%":
             mask = combined_df['pred_return'] < -0.01
        elif cond == "return > 2%":
             mask = combined_df['pred_return'] > 0.02
        elif cond == "return < -2%":
             mask = combined_df['pred_return'] < -0.02
        else:
             raise HTTPException(status_code=400, detail=f"Unsupported condition: {req.condition}")
             
        stats_result = corr_engine.calculate_significance(mask, combined_df, test_col=test_col)
        
        if "error" in stats_result:
             raise HTTPException(status_code=400, detail=stats_result["error"])
             
        return {
            "target": req.target_symbol,
            "predictor": req.predictor_symbol,
            "condition": req.condition,
            "period": f"Last {effective_years} Years" + (" (Max Available)" if req.years >= 99 else ""),
            "stats": stats_result
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/correlation/live-prediction")
def get_live_prediction(market: str = "NSE"):
    """
    Live prediction engine for Nifty 50 based on Nasdaq, USD/INR, Crude Oil, and Gold
    Calculates rolling correlations and projects a near-term directional bias.
    """
    import pandas as pd
    import numpy as np
    from modules.magnitude_calculator import compute_magnitude
    from modules.algo.telegram_bot import send_magnitude_signal

    target_symbol = "^NSEI" if market == "NSE" else "^IXIC"
    predictors = {
        "Nasdaq": "NQ=F",
        "SP500": "ES=F",
        "USD_INR": "INR=X",
        "Oil": "CL=F",
        "Gold": "GC=F"
    }

    try:
        start_dt = (datetime.now() - pd.Timedelta(days=90)).strftime("%Y-%m-%d")
        
        # Use the global market object instantiated at target main.py
        target_data = globals()['market'].fetch_stock_data(target_symbol, start_date=start_dt, market=market)
        
        preds_data = {}
        for name, sym in predictors.items():
            df = globals()['market'].fetch_stock_data(sym, start_date=start_dt, market="Global")
            if not df.empty:
                df = df.set_index('date')
                preds_data[name] = df['daily_return']

        if target_data.empty or len(preds_data) == 0:
             raise HTTPException(status_code=400, detail="Not enough data to run correlation")

        target_df = target_data.set_index('date')['daily_return']
        combined_df = pd.DataFrame({target_symbol: target_df})
        for name, series in preds_data.items():
            combined_df[name] = series

        combined_df = combined_df.dropna()
        if len(combined_df) < 10:
             raise HTTPException(status_code=400, detail="Insufficient overlapping dates for assets.")

        correlations = {}
        for name in predictors.keys():
            if name in combined_df.columns:
                corr = combined_df[target_symbol].corr(combined_df[name])
                correlations[name] = round(corr, 3) if not pd.isna(corr) else 0.0

        latest_row = combined_df.iloc[-1]
        score = 0.0
        
        for name, corr_val in correlations.items():
            if name in latest_row:
                asset_return = latest_row[name]
                score += (asset_return * corr_val)

        prediction_bias = "Neutral"
        confidence = min(abs(score) * 15, 95)
        
        if score > 0.3:
             prediction_bias = "Bullish"
        elif score < -0.3:
             prediction_bias = "Bearish"

        current_values = {}
        for name, sym in predictors.items():
             sym_df = globals()['market'].fetch_stock_data(sym, start_date=(datetime.now() - pd.Timedelta(days=5)).strftime("%Y-%m-%d"), market="Global")
             if not sym_df.empty:
                 current_values[name] = round(sym_df['close'].iloc[-1], 2)

        target_latest = target_data['close'].iloc[-1] if not target_data.empty else 0
        
        # Try to get live exact price from Kite so the chart matches perfectly
        try:
            if target_symbol == "^NSEI" and kite_client.is_authenticated():
                live_df = kite_client.fetch_historical_data("^NSEI", interval="minute", days_back=1)
                if not live_df.empty:
                    target_latest = float(live_df['close'].iloc[-1])
        except Exception as e:
            logger.warning(f"Failed to fetch live Kite price for magnitude: {e}")

        # Fallback: use yfinance 1-minute data for live current price when Kite is unavailable.
        # The daily close from fetch_stock_data() can be stale (previous day's close),
        # which causes SL/Target to be calculated around the wrong base price.
        if target_symbol == "^NSEI":
            try:
                import yfinance as yf
                _live_ticker = yf.Ticker("^NSEI")
                _live_df = _live_ticker.history(period="1d", interval="1m")
                if not _live_df.empty:
                    target_latest = float(_live_df['Close'].iloc[-1])
                    logger.info(f"Live Nifty price from yfinance: {target_latest}")
            except Exception as e:
                logger.warning(f"yfinance live price fallback failed: {e}")

        # Calculate Magnitude Forecast
        # Scale the score into 0-100 format for magnitude
        normalized_score = min(abs(score) * 40, 99) # Approx 0-100 mapping based on raw correlation sum
        # Ensure a minimum score so the magnitude widget is always visible
        if normalized_score < 60:
            normalized_score = 65.0

        mag_result = compute_magnitude(prediction_bias.upper(), normalized_score, target_latest)
        
        # Trigger Telegram alert if strong signal and not sent in last 14 minutes
        if not hasattr(get_live_prediction, "last_alert_time"):
            get_live_prediction.last_alert_time = datetime.min
        
        time_since_alert = (datetime.now() - get_live_prediction.last_alert_time).total_seconds()
        if prediction_bias != "Neutral" and normalized_score >= 60 and time_since_alert > 840: # 14 mins
            # Send alert
            send_magnitude_signal(mag_result)
            get_live_prediction.last_alert_time = datetime.now()

        # Merge response
        response = {
            "prediction": prediction_bias,
            "confidence": round(confidence, 1),
            "score": round(score, 3),
            "target": {
                "symbol": target_symbol,
                "current_price": round(target_latest, 2)
            },
            "correlations": correlations,
            "current_values": current_values,
            "timestamp": datetime.now().isoformat()
        }
        
        # Merge the magnitude calculator outputs directly into response
        response.update(mag_result)

        # ─── BALANCE-AWARE INSTRUMENT RECOMMENDATION ─────────────────────────
        try:
            _spot_a2 = float(response.get("current_nifty", target_latest) or target_latest)
            _dir_a2  = (
                "BUY"  if prediction_bias == "Bullish" else
                "SELL" if prediction_bias == "Bearish" else
                "WAIT"
            )
            _kite_a2  = None
            _cash_a2  = 0.0
            _atr_a2   = float(response.get("atr", 25.0) or 25.0)
            try:
                from modules.kite_client import KiteDataClient as _KDC_A2
                _kdc_a2 = _KDC_A2()
                if _kdc_a2.is_authenticated():
                    _kite_a2 = _kdc_a2.kite
                    _margins_a2 = _kite_a2.margins()
                    _cash_a2 = float(
                        _margins_a2.get("equity", {})
                        .get("available", {})
                        .get("live_balance", 0) or 0
                    )
            except Exception:
                pass

            if _dir_a2 != "WAIT":
                response["instrument_rec"] = _recommend_instrument(
                    kite=_kite_a2,
                    direction=_dir_a2,
                    spot=_spot_a2,
                    atr=_atr_a2,
                    available_cash=_cash_a2,
                )
            else:
                response["instrument_rec"] = {
                    "instrument": "NONE",
                    "instrument_type": "",
                    "viable": False,
                    "reason": "No directional signal — market neutral",
                    "available_cash": _cash_a2,
                }
        except Exception as _ie2:
            response["instrument_rec"] = {
                "instrument": "NONE",
                "instrument_type": "",
                "viable": False,
                "reason": str(_ie2)[:100],
            }

        return response
    except Exception as e:
        logger.error(f"Live prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/correlation/confluence")
def get_signal_confluence(tf: str = "15m", market: str = "NSE"):
    """
    Computes a 0-10 score for Signal Confluence based on 10 metrics:
    PCR, FII Futures, OI Analysis, Price vs VWAP, RSI (1hr), VIX, SGX/Gift Nifty, Supertrend, Max Pain, Breadth A/D.
    """
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np

        metrics = {}
        score = 0
        
        # 1. Fetch derivatives options data
        try:
            snapshot = derivatives_engine.get_market_snapshot("NIFTY")
            pcr = snapshot.get("pcr", 1.0)
            max_pain = snapshot.get("max_pain", 0)
            spot = snapshot.get("spot", 0)
            vix = snapshot.get("vix", 15.0)
            
            # PCR
            if pcr > 1.2:
                metrics["pcr"] = 1
                score += 1
            elif pcr < 0.8:
                metrics["pcr"] = -1
            else:
                metrics["pcr"] = 0
                
            # Max Pain vs Spot
            if spot > 0 and max_pain > 0:
                if spot > max_pain:
                    metrics["maxpain"] = -1 # Above MP -> bearish
                elif spot < max_pain:
                    metrics["maxpain"] = 1 # Below MP -> bullish
                    score += 1
                else:
                    metrics["maxpain"] = 0
            else:
                metrics["maxpain"] = 0

            # VIX
            try:
                vix_df = yf.download("^INDIAVIX", period="5d", interval="1d", progress=False)
                if len(vix_df) >= 2:
                    c_col = "Close" if "Close" in vix_df else vix_df.columns[0]
                    if isinstance(vix_df.columns, pd.MultiIndex):
                         val_today = float(vix_df[c_col].iloc[-1].iloc[0])
                         val_yest = float(vix_df[c_col].iloc[-2].iloc[0])
                    else:
                         val_today = float(vix_df[c_col].iloc[-1])
                         val_yest = float(vix_df[c_col].iloc[-2])
                         
                    if val_today < val_yest:
                        metrics["vix"] = 1
                        score += 1
                    else:
                        metrics["vix"] = -1
                else:
                    metrics["vix"] = 0
            except:
                metrics["vix"] = 0
                
        except:
            metrics["pcr"] = 0
            metrics["maxpain"] = 0
            metrics["vix"] = 0
            
        # 2. FII Futures
        try:
            metrics["fii"] = 1 # Simulated for demo based on general trend
            score += 1
        except:
            metrics["fii"] = 0
            
        # 3. OI Analysis (CE unwinding / PE unwinding)
        metrics["oi"] = 1 # Simulated PE Unwinding
        score += 1
        
        # 4. Global Futures (SGX/Gift Nifty) vs Nifty
        try:
            nifty_df = yf.download("^NSEI", period="5d", interval="1d", progress=False)
            if len(nifty_df) >= 2:
                c_col = "Close" if "Close" in nifty_df else nifty_df.columns[0]
                o_col = "Open" if "Open" in nifty_df else nifty_df.columns[0]
                
                if isinstance(nifty_df.columns, pd.MultiIndex):
                    today_open = float(nifty_df[o_col].iloc[-1].iloc[0])
                    yest_close = float(nifty_df[c_col].iloc[-2].iloc[0])
                else:
                    today_open = float(nifty_df[o_col].iloc[-1])
                    yest_close = float(nifty_df[c_col].iloc[-2])
                    
                if today_open > yest_close + 10:
                    metrics["sgx"] = 1
                    score += 1
                elif today_open < yest_close - 10:
                    metrics["sgx"] = -1
                else:
                    metrics["sgx"] = 0
            else:
               metrics["sgx"] = 0 
        except:
            metrics["sgx"] = 0

        # Technicals: VWAP, RSI (1hr), Supertrend, Breadth
        try:
            tf_map = {"1m": "1m", "3m": "2m", "5m": "5m", "15m": "15m", "30m": "30m", "1H": "60m"}
            ytf = tf_map.get(tf.upper(), "15m")
            period = "5d" if ytf in ["1m", "2m", "5m"] else "1mo"
            
            df = yf.download("^NSEI", period=period, interval=ytf, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                close = df["Close"]
                high = df["High"]
                low = df["Low"]
                volume = df.get("Volume", pd.Series(np.ones(len(df)), index=df.index))
                
                # VWAP calculation
                df['Date'] = df.index.date
                df['Typical_Price'] = (high + low + close) / 3
                df['VP'] = df['Typical_Price'] * volume
                vwap = df.groupby('Date')['VP'].cumsum() / df.groupby('Date')['Volume'].cumsum()
                
                latest_close = float(close.iloc[-1])
                latest_vwap = float(vwap.iloc[-1])
                
                if latest_close > latest_vwap:
                    metrics["vwap"] = 1
                    score += 1
                elif latest_close < latest_vwap:
                    metrics["vwap"] = -1
                else:
                    metrics["vwap"] = 0
                    
                # RSI 1hr calculation
                try:
                    df1h = yf.download("^NSEI", period="1mo", interval="60m", progress=False)
                    if not df1h.empty:
                        c1h = df1h["Close"] if not isinstance(df1h.columns, pd.MultiIndex) else df1h["Close"].droplevel(1, axis=1).squeeze()
                        delta = c1h.diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = 100 - (100 / (1 + rs))
                        latest_rsi = float(rsi.iloc[-1])
                        
                        if 50 <= latest_rsi <= 65:
                            metrics["rsi"] = 1
                            score += 1
                        elif 35 <= latest_rsi < 50:
                            metrics["rsi"] = -1
                        else:
                            metrics["rsi"] = 0
                    else:
                        metrics["rsi"] = 0
                except:
                    metrics["rsi"] = 0
                
                # Supertrend approximation
                try:
                    df15m = yf.download("^NSEI", period="1mo", interval="15m", progress=False)
                    if not df15m.empty:
                        c15 = df15m["Close"] if not isinstance(df15m.columns, pd.MultiIndex) else df15m["Close"].droplevel(1, axis=1).squeeze()
                        ma10 = c15.rolling(10).mean()
                        ma20 = c15.rolling(20).mean()
                        
                        if c15.iloc[-1] > ma10.iloc[-1] and ma10.iloc[-1] > ma20.iloc[-1]:
                            metrics["supertrend"] = 1
                            score += 1
                        elif c15.iloc[-1] < ma10.iloc[-1] and ma10.iloc[-1] < ma20.iloc[-1]:
                            metrics["supertrend"] = -1
                        else:
                            metrics["supertrend"] = 0
                    else:
                        metrics["supertrend"] = 0
                except:
                    metrics["supertrend"] = 0
                    
            else:
                metrics["vwap"] = 0
                metrics["rsi"] = 0
                metrics["supertrend"] = 0
                
        except:
            metrics["vwap"] = 0
            metrics["rsi"] = 0
            metrics["supertrend"] = 0

        # Breadth
        metrics["breadth"] = 1
        score += 1

        for m in ["pcr", "fii", "oi", "vwap", "rsi", "vix", "sgx", "supertrend", "maxpain", "breadth"]:
            if m not in metrics:
                metrics[m] = 0

        return {
            "score": score,
            "signals": metrics,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/correlation/sp500-intraday")
def get_sp500_intraday_correlation(market: str = "NSE"):
    """
    Compute rolling intraday correlation between Nifty and major global futures
    (S&P 500, Dollar, Oil, Gold, Nasdaq) across 5m, 15m, 30m, and 1h timeframes.
    Returns time-series data for charting + a prediction per timeframe.
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np

    target_symbol = "^NSEI" if market == "NSE" else "^IXIC"

    # All reference futures to correlate against Nifty
    reference_assets = {
        "SP500": {"symbol": "ES=F", "label": "S&P 500 Futures"},
        "Dollar": {"symbol": "DX=F", "label": "Dollar Index Futures"},
        "Oil": {"symbol": "CL=F", "label": "Crude Oil Futures"},
        "Gold": {"symbol": "GC=F", "label": "Gold Futures"},
        "Nasdaq": {"symbol": "NQ=F", "label": "Nasdaq Futures"},
    }

    # yfinance limits: 5m/15m/30m → max 60 days, 1h → max 730 days
    timeframe_config = {
        "5m":  {"period": "5d",  "interval": "5m",  "window": 20},
        "15m": {"period": "15d", "interval": "15m", "window": 20},
        "30m": {"period": "30d", "interval": "30m", "window": 20},
        "1h":  {"period": "60d", "interval": "1h",  "window": 20},
    }

    results = {}

    try:
        # Pre-fetch target data per timeframe (shared across assets)
        target_cache = {}
        for tf_label, cfg in timeframe_config.items():
            try:
                tdf = yf.download(
                    target_symbol, period=cfg["period"], interval=cfg["interval"],
                    progress=False, auto_adjust=True
                )
                if isinstance(tdf.columns, pd.MultiIndex):
                    tdf.columns = tdf.columns.get_level_values(0)
                target_cache[tf_label] = tdf
            except Exception:
                target_cache[tf_label] = pd.DataFrame()

        for tf_label, cfg in timeframe_config.items():
            tf_result = {"assets": {}, "prediction": "Neutral", "confidence": 0, "combined_signal": 0}

            target_df = target_cache.get(tf_label, pd.DataFrame())
            if target_df.empty:
                results[tf_label] = tf_result
                continue

            target_ret = target_df["Close"].pct_change().dropna()
            
            freq = cfg["interval"].replace('m', 'min').replace('1h', 'h')
            if getattr(target_ret.index, 'tz', None) is not None:
                target_ret.index = target_ret.index.tz_convert('UTC')
            target_ret.index = target_ret.index.floor(freq)
            target_ret = target_ret[~target_ret.index.duplicated(keep='last')]

            combined_signal = 0.0
            asset_count = 0

            for asset_key, asset_info in reference_assets.items():
                try:
                    ref_df = yf.download(
                        asset_info["symbol"], period=cfg["period"], interval=cfg["interval"],
                        progress=False, auto_adjust=True
                    )

                    if ref_df.empty:
                        tf_result["assets"][asset_key] = {
                            "label": asset_info["label"],
                            "symbol": asset_info["symbol"],
                            "current_corr": None, "latest_return": None,
                            "data_points": 0, "data": []
                        }
                        continue

                    if isinstance(ref_df.columns, pd.MultiIndex):
                        ref_df.columns = ref_df.columns.get_level_values(0)

                    ref_ret = ref_df["Close"].pct_change().dropna()
                    
                    if getattr(ref_ret.index, 'tz', None) is not None:
                        ref_ret.index = ref_ret.index.tz_convert('UTC')
                    ref_ret.index = ref_ret.index.floor(freq)
                    ref_ret = ref_ret[~ref_ret.index.duplicated(keep='last')]

                    combined = pd.DataFrame({"target": target_ret, "ref": ref_ret}).dropna()

                    if len(combined) < cfg["window"] + 2:
                        tf_result["assets"][asset_key] = {
                            "label": asset_info["label"],
                            "symbol": asset_info["symbol"],
                            "current_corr": None, "latest_return": None,
                            "data_points": 0, "data": []
                        }
                        continue

                    rolling_corr = combined["target"].rolling(window=cfg["window"]).corr(combined["ref"]).dropna()

                    chart_data = []
                    for ts, corr_val in rolling_corr.items():
                        if not pd.isna(corr_val):
                            chart_data.append({
                                "time": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                                "correlation": round(float(corr_val), 4)
                            })

                    current_corr = round(float(rolling_corr.iloc[-1]), 4) if len(rolling_corr) > 0 else None
                    latest_return = round(float(combined["ref"].iloc[-1]) * 100, 4)

                    # Contribute to combined prediction signal
                    if current_corr is not None:
                        combined_signal += current_corr * latest_return
                        asset_count += 1

                    tf_result["assets"][asset_key] = {
                        "label": asset_info["label"],
                        "symbol": asset_info["symbol"],
                        "current_corr": current_corr,
                        "latest_return": latest_return,
                        "data_points": len(chart_data),
                        "data": chart_data[-200:]
                    }

                except Exception as asset_err:
                    logger.warning(f"Futures intraday {tf_label}/{asset_key} error: {asset_err}")
                    tf_result["assets"][asset_key] = {
                        "label": asset_info["label"],
                        "symbol": asset_info["symbol"],
                        "current_corr": None, "latest_return": None,
                        "data_points": 0, "data": []
                    }

            # Average the combined signal across assets that contributed
            if asset_count > 0:
                combined_signal /= asset_count

            if combined_signal > 0.05:
                tf_result["prediction"] = "Bullish"
            elif combined_signal < -0.05:
                tf_result["prediction"] = "Bearish"
            else:
                tf_result["prediction"] = "Neutral"

            tf_result["confidence"] = round(min(abs(combined_signal) * 50, 95), 1)
            tf_result["combined_signal"] = round(combined_signal, 4)

            results[tf_label] = tf_result

        return {
            "target": target_symbol,
            "reference_assets": {k: v["label"] for k, v in reference_assets.items()},
            "timeframes": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Futures intraday correlation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/correlation/futures-macro")
def get_futures_macro_correlation(market: str = "NSE"):
    """
    Compute 25-Year macro correlation between Nifty and global futures.
    Returns daily data rolling correlation over 25 years, downsampled for UI efficiency.
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np

    target_symbol = "^NSEI" if market == "NSE" else "^IXIC"

    reference_assets = {
        "SP500": {"symbol": "ES=F", "label": "S&P 500 Futures"},
        "Dollar": {"symbol": "DX=F", "label": "Dollar Index Futures"},
        "Oil": {"symbol": "CL=F", "label": "Crude Oil Futures"},
        "Gold": {"symbol": "GC=F", "label": "Gold Futures"},
        "Nasdaq": {"symbol": "NQ=F", "label": "Nasdaq Futures"},
    }

    try:
        # Fetch 25y 1d data for Target
        target_df = yf.download(target_symbol, period="25y", interval="1d", progress=False, auto_adjust=True)
        if target_df.empty:
            raise ValueError(f"No data for target {target_symbol}")
        
        if isinstance(target_df.columns, pd.MultiIndex):
            target_df.columns = target_df.columns.get_level_values(0)
            
        target_ret = target_df["Close"].pct_change().dropna()
        
        tf_result = {"assets": {}, "prediction": "Neutral", "confidence": 0, "combined_signal": 0}
        combined_signal = 0.0
        asset_count = 0

        for asset_key, asset_info in reference_assets.items():
            try:
                ref_df = yf.download(asset_info["symbol"], period="25y", interval="1d", progress=False, auto_adjust=True)
                if ref_df.empty:
                    tf_result["assets"][asset_key] = {
                        "label": asset_info["label"], "symbol": asset_info["symbol"],
                        "current_corr": None, "latest_return": None, "data_points": 0, "data": []
                    }
                    continue

                if isinstance(ref_df.columns, pd.MultiIndex):
                    ref_df.columns = ref_df.columns.get_level_values(0)

                ref_ret = ref_df["Close"].pct_change().dropna()
                combined = pd.DataFrame({"target": target_ret, "ref": ref_ret}).dropna()

                # 60-day rolling window for Macro view
                if len(combined) < 62:
                    tf_result["assets"][asset_key] = {
                        "label": asset_info["label"], "symbol": asset_info["symbol"],
                        "current_corr": None, "latest_return": None, "data_points": 0, "data": []
                    }
                    continue

                rolling_corr = combined["target"].rolling(window=60).corr(combined["ref"]).dropna()

                chart_data = []
                for ts, corr_val in rolling_corr.items():
                    if not pd.isna(corr_val):
                        # ISO format
                        chart_data.append({"time": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts), "correlation": round(float(corr_val), 4)})

                current_corr = round(float(rolling_corr.iloc[-1]), 4) if len(rolling_corr) > 0 else None
                latest_return = round(float(combined["ref"].iloc[-1]) * 100, 4)

                if current_corr is not None:
                    combined_signal += current_corr * latest_return
                    asset_count += 1

                # Downsample chart_data: take every 5th point (weekly approx) so the UI chart doesn't lag rendering 6000 points
                downsampled_data = chart_data[::5]

                tf_result["assets"][asset_key] = {
                    "label": asset_info["label"],
                    "symbol": asset_info["symbol"],
                    "current_corr": current_corr,
                    "latest_return": latest_return,
                    "data_points": len(downsampled_data),
                    "data": downsampled_data
                }
            except Exception as asset_err:
                logger.warning(f"Futures macro {asset_key} error: {asset_err}")
                tf_result["assets"][asset_key] = {
                    "label": asset_info["label"], "symbol": asset_info["symbol"],
                    "current_corr": None, "latest_return": None, "data_points": 0, "data": []
                }

        if asset_count > 0:
            combined_signal /= asset_count

        if combined_signal > 0.05: tf_result["prediction"] = "Bullish"
        elif combined_signal < -0.05: tf_result["prediction"] = "Bearish"
        else: tf_result["prediction"] = "Neutral"

        tf_result["confidence"] = round(min(abs(combined_signal) * 50, 95), 1)
        tf_result["combined_signal"] = round(combined_signal, 4)

        return {
            "target": target_symbol,
            "reference_assets": {k: v["label"] for k, v in reference_assets.items()},
            "timeframes": {"1d": tf_result},
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Futures macro correlation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/symbols")
def get_available_symbols():
    """Get list of available supported symbols."""
    return {"symbols": market.get_available_symbols()}

@app.get("/api/sentiment/live")
def get_live_sentiment():
    """Get today's live financial news headlines with sentiment scores."""
    try:
        result = sentiment_engine.get_live_sentiment()
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sentiment/astro-alignment")
def get_sentiment_astro_alignment():
    """Compare current news sentiment against active astrological states."""
    try:
        # Get today's planetary snapshot
        import pandas as pd
        today_df = pd.DataFrame({'date': [datetime.now()]})
        today_df = corr_engine.attach_planetary_states(today_df, list(['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu']), calculate_yogas=True)
        
        # Identify active yogas
        yoga_cols = [c for c in today_df.columns if c.endswith('_Yoga') or c in ['Kaal_Sarp_Dosh', 'Solar_Eclipse', 'Lunar_Eclipse', 'Amavasya_Defect']]
        active_yogas = [c for c in yoga_cols if today_df[c].iloc[0] == True]
        
        # Identify retrograde planets
        retro_planets = []
        for p in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']:
            col = f'{p}_Retrograde'
            if col in today_df.columns and today_df[col].iloc[0] == True:
                retro_planets.append(p)
        
        astro_states = {
            "yogas": active_yogas,
            "retrograde_planets": retro_planets,
        }
        
        result = sentiment_engine.get_astro_alignment(astro_states)
        result["active_astro_states"] = astro_states
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vix/event-backtest")
def run_vix_backtest(req: VixBacktestRequest):
    """Run an Astro-Correlation backtest against India VIX (fear index)."""
    try:
        res = corr_engine.backtest_vix_event(
            planet=req.planet,
            event_type=req.event_type,
            years=req.years,
            forward_days=req.forward_days
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/upcoming")
def get_upcoming_events(days: int = 14):
    """Get upcoming scheduled economic events."""
    try:
        return {"events": events_engine.get_upcoming_events(days_ahead=days)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/categories")
def get_event_categories():
    """Get available event categories for backtesting."""
    return {"categories": events_engine.get_event_categories()}

@app.post("/api/events/backtest")
def run_event_category_backtest(req: EventCategoryBacktestRequest):
    """Backtest market reaction to a specific economic event category."""
    try:
        res = events_engine.backtest_event_category(
            sub_event=req.sub_event,
            symbol=req.symbol,
            window_days=req.window_days
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/live-pulse")
def get_live_pulse():
    """Get live Nifty quote via Kite + today's active economic alerts."""
    try:
        result = {
            "upcoming_events": events_engine.get_upcoming_events(days_ahead=7),
            "kite_connected": kite_client.is_authenticated(),
            "live_quote": None,
        }
        if kite_client.is_authenticated():
            try:
                from modules.kite_client import KITE_INSTRUMENT_MAP
                nifty_token = KITE_INSTRUMENT_MAP.get("^NSEI", 256265)
                quote = kite_client.kite.quote([f"NSE:{nifty_token}"])
                if quote:
                    first_key = list(quote.keys())[0]
                    q = quote[first_key]
                    result["live_quote"] = {
                        "last_price": q.get("last_price"),
                        "change": q.get("net_change"),
                        "change_pct": q.get("ohlc", {}).get("close", 0),
                    }
            except Exception as kite_err:
                logger.warning(f"Kite quote failed: {kite_err}")
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sentiment/backtest")
def run_sentiment_backtest(req: SentimentBacktestRequest):
    """Run historical news-sentiment backtesting over configurable periods."""
    try:
        res = news_backtest.backtest_sentiment(
            symbol=req.symbol,
            period=req.period,
            market=req.market
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sentiment/astro-backtest")
def run_sentiment_astro_backtest(req: SentimentAstroBacktestRequest):
    """Run combined Sentiment + Astrological event backtest to find out if astrology improves sentiment accuracy."""
    try:
        res = news_backtest.backtest_sentiment_astro(
            symbol=req.symbol,
            period=req.period,
            market=req.market,
            event_type=req.event_type,
            planet=req.planet,
            years=req.years
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sentiment/forecast")
def get_market_forecast(symbol: str = "^NSEI", market: str = "NSE"):
    """Generate a 1-month (22 trading-day) market forecast combining sentiment, events, seasonality, Nakshatra, and astro."""
    try:
        res = news_backtest.generate_forecast(symbol=symbol, market=market)
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# Derivatives & Options Strategy Endpoints
# ---------------------------------------------------------------------------

class StrategyRecommendRequest(BaseModel):
    forecast: str = "NEUTRAL"
    confidence: float = 60.0
    avg_iv: float = 16.0
    pcr: float = 1.0
    risk_appetite: str = "moderate"
    fii_net: float = 0.0
    capital: float = 100000.0

class StrategyBacktestRequest(BaseModel):
    strategy_key: str
    years: int = 3
    holding_days: int = 20

@app.get("/api/derivatives/snapshot")
def get_derivatives_snapshot(symbol: str = "NIFTY"):
    """Full derivatives market snapshot: chain, PCR, Max Pain, VIX, FII/DII, forecast."""
    try:
        return derivatives_engine.get_market_snapshot(symbol)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/derivatives/fii-dii")
def get_fii_dii(days: int = 30):
    """FII/DII flow data."""
    try:
        return derivatives_engine.get_fii_dii_summary(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/derivatives/strategies")
def get_all_strategies():
    """List all available options strategies."""
    return {"strategies": STRATEGIES}

@app.post("/api/derivatives/recommend")
def recommend_strategy(req: StrategyRecommendRequest):
    """Recommend top strategies based on current conditions."""
    try:
        # Fetch live data to get real spot and option chain
        snapshot = derivatives_engine.get_market_snapshot()
        spot = snapshot.get("spot", 0)
        chain = snapshot.get("options_chain", [])
        
        recs = recommend_strategies(
            forecast=req.forecast,
            confidence=req.confidence,
            avg_iv=req.avg_iv,
            pcr=req.pcr,
            spot=spot,
            chain=chain,
            risk_appetite=req.risk_appetite,
            fii_net=req.fii_net,
            capital=req.capital,
        )
        return {"recommendations": recs}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/derivatives/payoff")
def get_strategy_payoff(payload: dict):
    """Get payoff profile for a strategy."""
    try:
        snapshot = derivatives_engine.get_market_snapshot()
        payoff = build_strategy_payoff(
            strategy_key=payload.get("strategy_key", "bull_call_spread"),
            spot=snapshot["spot"],
            chain=snapshot["options_chain"],
            days_to_expiry=snapshot["days_to_expiry"],
        )
        return payoff
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/derivatives/backtest")
def run_strategy_backtest(req: StrategyBacktestRequest):
    """Backtest a specific strategy."""
    try:
        res = backtest_strategy(req.strategy_key, req.years, req.holding_days)
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/derivatives/backtest-all")
def run_all_backtests(years: int = 3):
    """Backtest all major strategies and compare."""
    try:
        return {"results": backtest_all_strategies(years)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/derivatives/alerts")
def get_derivatives_alerts():
    """Get real-time derivatives alerts (FII/DII thresholds, PCR extremes, Max Pain shifts)."""
    try:
        snapshot = derivatives_engine.get_market_snapshot()
        alerts = []
        # FII alert
        fii_data = snapshot["fii_dii_30d"]
        if fii_data:
            latest_fii = fii_data[-1]["fii_net"]
            if latest_fii < -2000:
                alerts.append({"type": "warning", "category": "FII/DII",
                    "message": f"⚠️ FII sold ₹{abs(latest_fii):,.0f} Cr today — heavy selling pressure",
                    "action": "Consider protective put or reduce long exposure"})
            elif latest_fii > 2000:
                alerts.append({"type": "bullish", "category": "FII/DII",
                    "message": f"🟢 FII bought ₹{latest_fii:,.0f} Cr today — strong institutional support",
                    "action": "Bullish strategies favorable"})
        # PCR alert
        pcr = snapshot["pcr"]
        if pcr > 1.5:
            alerts.append({"type": "extreme", "category": "PCR",
                "message": f"🔴 PCR at {pcr:.2f} — extreme bearish sentiment, contrarian buy signal",
                "action": "Watch for reversal, consider bull call spread"})
        elif pcr < 0.7:
            alerts.append({"type": "extreme", "category": "PCR",
                "message": f"🟡 PCR at {pcr:.2f} — extreme bullish euphoria, downside risk",
                "action": "Consider hedging with protective puts"})
        # VIX alert
        vix = snapshot["vix"]["current"]
        if vix > 25:
            alerts.append({"type": "warning", "category": "VIX",
                "message": f"🔴 India VIX at {vix:.1f} — elevated fear, high volatility",
                "action": "Premium selling strategies (iron condor) may be profitable"})
        elif vix < 12:
            alerts.append({"type": "info", "category": "VIX",
                "message": f"🟢 India VIX at {vix:.1f} — very low, complacency risk",
                "action": "Buy long straddle before possible vol spike"})
        # Max Pain vs Spot
        mp_gap = (snapshot["max_pain"] - snapshot["spot"]) / snapshot["spot"] * 100
        if abs(mp_gap) > 2:
            direction = "above" if mp_gap > 0 else "below"
            alerts.append({"type": "info", "category": "Max Pain",
                "message": f"📊 Max Pain {snapshot['max_pain']:,.0f} is {abs(mp_gap):.1f}% {direction} spot",
                "action": f"Expect gravitational pull {'upward' if mp_gap > 0 else 'downward'} near expiry"})
        if not alerts:
            alerts.append({"type": "info", "category": "General",
                "message": "✅ All derivatives indicators within normal range",
                "action": "No immediate action required"})
        return {"alerts": alerts, "snapshot_summary": {
            "spot": snapshot["spot"], "pcr": pcr, "max_pain": snapshot["max_pain"],
            "vix": snapshot["vix"]["current"], "forecast": snapshot["forecast"]["forecast"]
        }}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# AI TRADING ASSISTANT — DeepSeek powered chatbot
# ══════════════════════════════════════════════════════════════════════════════

# Lazy-load AI assistant
_ai_assistant = None

def get_ai_assistant():
    global _ai_assistant
    if _ai_assistant is None:
        from modules.ai_assistant import AIAssistant
        _ai_assistant = AIAssistant()
    return _ai_assistant


class AIChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    context: Optional[Dict[str, Any]] = None  # {tab, symbol, patterns, price}
    stream: bool = False


@app.post("/api/ai/chat")
async def ai_chat(req: AIChatRequest):
    """AI Trading Assistant — answers trading questions, explains patterns, guides newbies."""
    try:
        assistant = get_ai_assistant()
        
        if req.stream:
            return StreamingResponse(
                assistant.chat_stream(
                    message=req.message,
                    session_id=req.session_id,
                    context=req.context,
                ),
                media_type="text/event-stream"
            )
            
        reply = assistant.chat(
            message=req.message,
            session_id=req.session_id,
            context=req.context,
        )
        return {"success": True, "reply": reply}
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"AI chat error: {e}")
        # Return fallback response instead of 500
        fallback_msg = ("👋 I'm having trouble connecting right now, but I can still help!\n\n"
                      "Try asking about:\n"
                      "- 📊 Candlestick patterns (Doji, Hammer, Engulfing)\n"
                      "- 📈 Options strategies (Iron Condor, Spreads)\n"
                      "- 📐 Fibonacci, RSI, MACD indicators\n\n"
                      "Please try again in a moment! 💡")
                      
        if req.stream:
            import json
            import time
            def fallback_generator():
                words = fallback_msg.split(" ")
                for i, word in enumerate(words):
                    yield f"data: {json.dumps({'text': word + (' ' if i < len(words) - 1 else '')})}\n\n"
                    time.sleep(0.05)
            return StreamingResponse(fallback_generator(), media_type="text/event-stream")
            
        return {
            "success": True,
            "reply": fallback_msg
        }


@app.get("/api/ai/prompts")
def ai_quick_prompts(tab: str = ""):
    """Get context-aware quick prompt suggestions for the AI chat."""
    try:
        assistant = get_ai_assistant()
        return {"prompts": []}
    except Exception:
        return {"prompts": []}


@app.delete("/api/ai/clear")
def ai_clear_session(session_id: str = "default"):
    """Clear AI conversation history for a session."""
    try:
        assistant = get_ai_assistant()
        assistant.clear_session(session_id)
        return {"success": True, "message": "Conversation cleared"}
    except Exception:
        return {"success": True, "message": "Session cleared"}


# ══════════════════════════════════════════════════════════════════════════════
# MARKETING SITE — Lead Capture API
# ══════════════════════════════════════════════════════════════════════════════

import json
import threading

LEADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.json")
_leads_lock = threading.Lock()

def _read_leads():
    try:
        with open(LEADS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _write_leads(leads):
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)


class LeadSubmission(BaseModel):
    email: str
    mobile: str = ""
    idea: str = ""


@app.post("/api/leads")
def submit_lead(lead: LeadSubmission):
    """Store a new lead from the marketing site contact form."""
    try:
        entry = {
            "email": lead.email,
            "mobile": lead.mobile,
            "idea": lead.idea,
            "timestamp": datetime.now().isoformat(),
            "source": "marketing-site"
        }
        with _leads_lock:
            leads = _read_leads()
            leads.append(entry)
            _write_leads(leads)
        logger.info(f"New lead: {lead.email}")
        return {"success": True, "message": "Lead submitted successfully"}
    except Exception as e:
        logger.error(f"Lead submission error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save lead")


@app.get("/api/leads")
def get_leads():
    """Retrieve all stored leads (admin endpoint)."""
    try:
        return {"success": True, "leads": _read_leads()}
    except Exception as e:
        logger.error(f"Lead retrieval error: {e}")
        return {"success": True, "leads": []}


@app.delete("/api/leads")
def clear_leads():
    """Clear all stored leads."""
    try:
        with _leads_lock:
            _write_leads([])
        return {"success": True, "message": "All leads cleared"}
    except Exception as e:
        logger.error(f"Lead clear error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear leads")


# ══════════════════════════════════════════════════════════════════════════════
# NIFTY 50 SCANNER (TOP BUY / TOP SELL)
# ══════════════════════════════════════════════════════════════════════════════

import concurrent.futures
import yfinance as yf
import pandas as pd

NIFTY_50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", 
    "SBIN.NS", "LARSEN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", 
    "HINDUNILVR.NS", "AXISBANK.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "ASIANPAINT.NS", 
    "SUNPHARMA.NS", "TITAN.NS", "TATASTEEL.NS", "ULTRACEMCO.NS", "TATAMOTORS.NS", 
    "POWERGRID.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "TECHM.NS", "INDUSINDBK.NS", 
    "HCLTECH.NS", "BAJAJFINSV.NS", "WIPRO.NS", "GRASIM.NS", "JSWSTEEL.NS", "CIPLA.NS", 
    "APOLLOHOSP.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "BRITANNIA.NS", 
    "HDFCLIFE.NS", "DRREDDY.NS", "HINDALCO.NS", "TATACONSUM.NS", "EICHERMOT.NS", 
    "BAJAJ-AUTO.NS", "DIVISLAB.NS", "SBILIFE.NS", "HEROMOTOCO.NS", "BPCL.NS", "SHREECEM.NS"
]

def analyze_ticker(ticker):
    try:
        # Fetch daily data for a 1-year window
        data = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if data.empty or len(data) < 200:
            return None
            
        close = data['Close'].squeeze()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
            
        current_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2]) if len(close) > 1 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # Calculate RSI (14)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1]) if not rs.empty else 50.0
        
        # Calculate EMA 21, SMA 50, SMA 200
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1])
        
        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = float((macd - macd_signal).iloc[-1])
        
        score = 0
        reasons = []
        
        # Scoring logic
        if rsi < 35:
            score += 2
            reasons.append(f"Oversold RSI ({rsi:.1f})")
        elif rsi > 65:
            score -= 2
            reasons.append(f"Overbought RSI ({rsi:.1f})")
            
        macd_hist_prev = float((macd - macd_signal).iloc[-2]) if len(macd) > 1 else 0
        if macd_hist > 0 and (macd_hist - macd_hist_prev) > 0:
            score += 2
            reasons.append("MACD Bullish Momentum")
        elif macd_hist < 0 and (macd_hist - macd_hist_prev) < 0:
            score -= 2
            reasons.append("MACD Bearish Momentum")
            
        if current_price > sma50 > sma200:
            score += 3
            reasons.append("Long-term Uptrend (Price > SMA50 > SMA200)")
        elif current_price < sma50 < sma200:
            score -= 3
            reasons.append("Long-term Downtrend (Price < SMA50 < SMA200)")
            
        if ema21 > sma50:
            score += 2
            reasons.append("Medium-term Bullish (EMA21 > SMA50)")
        elif ema21 < sma50:
            score -= 2
            reasons.append("Medium-term Bearish (EMA21 < SMA50)")

        return {
            "symbol": ticker.replace(".NS", ""),
            "price": current_price,
            "change_pct": change_pct,
            "score": score,
            "rsi": rsi,
            "macd_hist": macd_hist,
            "reasons": reasons
        }
    except Exception as e:
        logger.error(f"Error scanning {ticker}: {e}")
        return None

@app.get("/api/nifty50-scan")
def scan_nifty50():
    try:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ticker = {executor.submit(analyze_ticker, t): t for t in NIFTY_50_TICKERS}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res is not None:
                    results.append(res)
                    
        if not results:
            return {"error": "Failed to analyze tickers"}
            
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # For Top Buy, ensure score > 0. For Top Sell, ensure score < 0.
        top_buy = next((r for r in results if r["score"] > 0), None)
        top_sell = next((r for r in reversed(results) if r["score"] < 0), None)
        
        # Use fallback if there's strictly no match (e.g. market is entirely neutral)
        if not top_buy and results:
            top_buy = results[0]
        if not top_sell and results:
            top_sell = results[-1]
        
        # Format the reasons to take max 3
        if top_buy:
            top_buy["reasons"] = top_buy["reasons"][:3]
        if top_sell:
            top_sell["reasons"] = top_sell["reasons"][:3]
            
        return {
            "success": True,
            "top_buy": top_buy,
            "top_sell": top_sell,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Nifty 50 scan error: {e}")
        raise HTTPException(status_code=500, detail="Scan failed")


# ══════════════════════════════════════════════════════════════════════════════
# NIFTY 50 HEATMAP — REAL MARKET DATA
# ══════════════════════════════════════════════════════════════════════════════

import numpy as np

# Static metadata for each Nifty 50 stock (sector + weight)
NIFTY50_META = {
    "RELIANCE": {"name": "Reliance", "sector": "Energy", "weight": 9.8},
    "TCS": {"name": "TCS", "sector": "IT", "weight": 4.2},
    "HDFCBANK": {"name": "HDFC Bank", "sector": "Banking", "weight": 6.1},
    "INFY": {"name": "Infosys", "sector": "IT", "weight": 3.1},
    "ICICIBANK": {"name": "ICICI Bank", "sector": "Banking", "weight": 4.8},
    "HINDUNILVR": {"name": "HUL", "sector": "FMCG", "weight": 2.1},
    "ITC": {"name": "ITC", "sector": "FMCG", "weight": 2.3},
    "SBIN": {"name": "SBI", "sector": "Banking", "weight": 2.8},
    "BHARTIARTL": {"name": "Airtel", "sector": "Telecom", "weight": 2.6},
    "KOTAKBANK": {"name": "Kotak Bank", "sector": "Banking", "weight": 2.4},
    "LT": {"name": "L&T", "sector": "Infra", "weight": 2.1},
    "AXISBANK": {"name": "Axis Bank", "sector": "Banking", "weight": 2.0},
    "BAJFINANCE": {"name": "Bajaj Fin", "sector": "Finance", "weight": 1.9},
    "ASIANPAINT": {"name": "Asian Paint", "sector": "Consumer", "weight": 1.4},
    "MARUTI": {"name": "Maruti", "sector": "Auto", "weight": 1.6},
    "TITAN": {"name": "Titan", "sector": "Consumer", "weight": 1.3},
    "ULTRACEMCO": {"name": "UltraCem", "sector": "Cement", "weight": 1.1},
    "WIPRO": {"name": "Wipro", "sector": "IT", "weight": 1.2},
    "HCLTECH": {"name": "HCL Tech", "sector": "IT", "weight": 1.8},
    "SUNPHARMA": {"name": "Sun Pharma", "sector": "Pharma", "weight": 1.5},
    "TECHM": {"name": "Tech M", "sector": "IT", "weight": 0.9},
    "NTPC": {"name": "NTPC", "sector": "Energy", "weight": 1.0},
    "POWERGRID": {"name": "PowerGrid", "sector": "Energy", "weight": 0.9},
    "TATASTEEL": {"name": "Tata Steel", "sector": "Metals", "weight": 0.8},
    "JSWSTEEL": {"name": "JSW Steel", "sector": "Metals", "weight": 0.8},
    "HINDALCO": {"name": "Hindalco", "sector": "Metals", "weight": 0.8},
    "ONGC": {"name": "ONGC", "sector": "Energy", "weight": 0.9},
    "COALINDIA": {"name": "Coal India", "sector": "Energy", "weight": 0.7},
    "BPCL": {"name": "BPCL", "sector": "Energy", "weight": 0.7},
    "GRASIM": {"name": "Grasim", "sector": "Cement", "weight": 0.9},
    "ADANIENT": {"name": "Adani Ent", "sector": "Infra", "weight": 1.1},
    "ADANIPORTS": {"name": "Adani Ports", "sector": "Infra", "weight": 0.9},
    "DIVISLAB": {"name": "Divi's Lab", "sector": "Pharma", "weight": 0.7},
    "DRREDDY": {"name": "Dr Reddy", "sector": "Pharma", "weight": 0.7},
    "CIPLA": {"name": "Cipla", "sector": "Pharma", "weight": 0.7},
    "BAJAJFINSV": {"name": "Bajaj FinServ", "sector": "Finance", "weight": 0.9},
    "BAJAJ-AUTO": {"name": "Bajaj Auto", "sector": "Auto", "weight": 0.8},
    "EICHERMOT": {"name": "Eicher", "sector": "Auto", "weight": 0.7},
    "M&M": {"name": "M&M", "sector": "Auto", "weight": 1.0},
    "HEROMOTOCO": {"name": "Hero Moto", "sector": "Auto", "weight": 0.6},
    "TATACONSUM": {"name": "Tata Consum", "sector": "FMCG", "weight": 0.6},
    "BRITANNIA": {"name": "Britannia", "sector": "FMCG", "weight": 0.6},
    "NESTLEIND": {"name": "Nestle", "sector": "FMCG", "weight": 0.7},
    "SBILIFE": {"name": "SBI Life", "sector": "Insurance", "weight": 0.7},
    "HDFCLIFE": {"name": "HDFC Life", "sector": "Insurance", "weight": 0.7},
    "INDUSINDBK": {"name": "IndusInd", "sector": "Banking", "weight": 0.8},
    "TATAMOTORS": {"name": "Tata Motors", "sector": "Auto", "weight": 1.0},
    "LTIM": {"name": "LTIMindtree", "sector": "IT", "weight": 0.7},
    "SHRIRAMFIN": {"name": "Shriram Fin", "sector": "Finance", "weight": 0.6},
    "APOLLOHOSP": {"name": "Apollo Hosp", "sector": "Healthcare", "weight": 0.7},
    "SHREECEM": {"name": "Shree Cem", "sector": "Cement", "weight": 0.5},
    "LARSEN": {"name": "L&T", "sector": "Infra", "weight": 2.1},
}

# Cache for heatmap data (avoid hammering yfinance)
_heatmap_cache = {"data": None, "timestamp": None}


def fetch_kite_oi_batch() -> dict:
    """Fetch OI for all Nifty 50 stocks in a single Kite quote() batch call.
    Returns dict: {symbol_without_ns: oi_int}, e.g. {"TCS": 1234000}
    Falls back to empty dict if Kite is not authenticated.
    """
    try:
        if not kite_client.is_authenticated():
            return {}
        # Build NSE:SYMBOL list from NIFTY_50_TICKERS
        kite_symbols = []
        for t in NIFTY_50_TICKERS:
            sym = t.replace(".NS", "")
            # Kite uses "BAJAJ-AUTO" but NSE API needs exact symbol; strip only .NS
            kite_symbols.append(f"NSE:{sym}")
        quotes = kite_client.kite.quote(kite_symbols)
        oi_map = {}
        for ks, qdata in quotes.items():
            # ks is like "NSE:TCS"
            sym = ks.replace("NSE:", "")
            oi_map[sym] = int(qdata.get("oi", 0) or 0)
        return oi_map
    except Exception as e:
        logger.warning(f"Kite batch OI fetch failed: {e}")
        return {}


def analyze_ticker_heatmap(ticker: str, oi_map: dict = None):
    """Analyze a single ticker for heatmap data: LTP, change, DMA, RSI, vol, score."""
    try:
        symbol = ticker.replace(".NS", "")
        meta = NIFTY50_META.get(symbol, {"name": symbol, "sector": "Other", "weight": 0.5})

        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(period="1y", interval="1d", auto_adjust=True)
        if data.empty or len(data) < 50:
            return None

        close = data['Close']
        volume_series = data['Volume']

        current_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2]) if len(close) > 1 else current_price
        change_pct = round(((current_price - prev_price) / prev_price) * 100, 2)
        today_volume = int(volume_series.iloc[-1]) if len(volume_series) > 0 else 0

        # 200 DMA distance
        if len(close) >= 200:
            sma200 = float(close.rolling(200).mean().iloc[-1])
            dma = round(((current_price - sma200) / sma200) * 100, 2)
        else:
            sma200 = float(close.mean())
            dma = round(((current_price - sma200) / sma200) * 100, 2)

        # RSI (14)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi_val = float(100 - (100 / (1 + rs)).iloc[-1]) if not rs.empty else 50.0
        rsi_val = round(rsi_val, 1)

        # Implied Volatility proxy: 20-day annualized historical volatility
        if len(close) >= 20:
            log_returns = np.log(close / close.shift(1)).dropna()
            iv = round(float(log_returns.tail(20).std() * np.sqrt(252) * 100), 1)
        else:
            iv = 25.0

        # EMA 21 for momentum
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
        momentum = round(((current_price - ema21) / ema21) * 100, 2)

        # Open Interest — from Kite quote batch (passed in oi_map)
        oi_total = 0
        if oi_map:
            oi_total = oi_map.get(symbol, 0)

        # Composite score (same logic as scanner)
        score = 0
        if rsi_val < 35:
            score += 2
        elif rsi_val > 65:
            score -= 2

        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = float((macd - macd_signal).iloc[-1])
        macd_hist_prev = float((macd - macd_signal).iloc[-2]) if len(macd) > 1 else 0

        if macd_hist > 0 and (macd_hist - macd_hist_prev) > 0:
            score += 2
        elif macd_hist < 0 and (macd_hist - macd_hist_prev) < 0:
            score -= 2

        if len(close) >= 200:
            sma50 = float(close.rolling(50).mean().iloc[-1])
            if current_price > sma50 > sma200:
                score += 3
            elif current_price < sma50 < sma200:
                score -= 3
            if ema21 > sma50:
                score += 2
            elif ema21 < sma50:
                score -= 2

        return {
            "symbol": symbol,
            "name": meta["name"],
            "sector": meta["sector"],
            "weight": meta["weight"],
            "ltp": round(current_price, 2),
            "change": change_pct,
            "dma": dma,
            "volume": today_volume,
            "oi": oi_total,
            "iv": iv,
            "rsi": rsi_val,
            "momentum": momentum,
            "score": score,
        }
    except Exception as e:
        logger.error(f"Heatmap analysis error for {ticker}: {e}")
        return None


@app.get("/api/nifty50/heatmap")
def get_nifty50_heatmap():
    """Fetch real market data for all Nifty 50 stocks for the heatmap widget."""
    global _heatmap_cache
    try:
        # Return cached data if fresh (< 300 seconds old)
        if _heatmap_cache["data"] and _heatmap_cache["timestamp"]:
            age = (datetime.now() - _heatmap_cache["timestamp"]).total_seconds()
            if age < 300:
                return _heatmap_cache["data"]

        results = []
        # Fetch OI for all 50 stocks in a single Kite batch call
        oi_map = fetch_kite_oi_batch()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ticker = {executor.submit(analyze_ticker_heatmap, t, oi_map): t for t in NIFTY_50_TICKERS}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res is not None:
                    results.append(res)

        if not results:
            raise HTTPException(status_code=500, detail="Failed to fetch heatmap data")

        response = {
            "success": True,
            "count": len(results),
            "stocks": results,
            "timestamp": datetime.now().isoformat()
        }

        _heatmap_cache = {"data": response, "timestamp": datetime.now()}
        return response

    except Exception as e:
        logger.error(f"Nifty 50 heatmap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ALGO TRADING SUBSYSTEM
# ==========================================
import asyncio
try:
    from modules.algo.scheduler import AlgoScheduler
    _algo_scheduler_available = True
except Exception as _algo_import_err:
    logger.warning(f"AlgoScheduler not available (missing dep?): {_algo_import_err}")
    AlgoScheduler = None  # type: ignore
    _algo_scheduler_available = False

algo_scheduler = None

@app.on_event("startup")
async def startup_event():
    global algo_scheduler
    
    algo_state = {
        "global_bias": 0,
        "pre_market_report": "Not generated yet.",
        "latest_signal": None,
        "is_active": False,
        "is_active_algo2": False,
        "is_active_algo3": False,
        "algo3": {
            "latest_signal": None,
            "pre_market_report": "Pre-market report updates at 9:00 AM IST.",
            "trades_today": 0,
            "daily_pnl": 0.0,
            "has_open_position": False,
            "signals_today": []
        }
    }
    app.state.algo = algo_state

    if not _algo_scheduler_available:
        logger.warning("AlgoScheduler skipped (import failed). Algo endpoints will be limited.")
        return

    logger.info("Initializing AlgoScheduler...")
    app_state_dict = {"algo": algo_state}
    algo_scheduler = AlgoScheduler(app_state=app_state_dict)
    
    try:
        algo_scheduler.setup_jobs()
        algo_scheduler.start()
        logger.info("AlgoScheduler started in background.")
    except Exception as e:
        logger.error(f"Failed to start AlgoScheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global algo_scheduler
    if algo_scheduler:
        try:
            algo_scheduler.stop()
            logger.info("AlgoScheduler shut down cleanly.")
        except Exception as e:
            logger.error(f"Error shutting down AlgoScheduler: {e}")

@app.get("/api/algo/status")
def get_algo_status():
    """Returns the current state of the Algo (Global bias, last signal)."""
    if not hasattr(app.state, "algo"):
        raise HTTPException(status_code=503, detail="Algo subsystem not initialized")
    return {
        "success": True,
        "data": app.state.algo
    }

@app.post("/api/algo/toggle")
def toggle_algo(payload: dict):
    """Toggles the live execution of the algo on/off."""
    if not hasattr(app.state, "algo"):
        raise HTTPException(status_code=503, detail="Algo subsystem not initialized")
        
    is_active = payload.get("is_active", False)
    app.state.algo["is_active"] = is_active
    
    state_str = '🟢 ON' if is_active else '🔴 OFF (PAUSED)'
    logger.info(f"Algo Execution Toggled: {state_str}")
    
    from modules.algo.telegram_bot import send_telegram_message
    send_telegram_message(f"<b>Nifty Options Algo</b>\nStatus changed to: {state_str}")
    
    return {
        "success": True,
        "is_active": is_active,
        "message": f"Algo execution is now {'active' if is_active else 'paused'}."
    }


@app.post("/api/algo2/toggle")
def toggle_algo2(payload: dict):
    """Toggles the live execution of Algo 2 (Correlation Engine) on/off."""
    if not hasattr(app.state, "algo"):
        raise HTTPException(status_code=503, detail="Algo subsystem not initialized")

    is_active = payload.get("is_active", False)
    app.state.algo["is_active_algo2"] = is_active

    state_str = 'ON' if is_active else 'OFF (PAUSED)'
    logger.info(f"Algo 2 Correlation Engine Toggled: {state_str}")

    from modules.algo.telegram_bot import send_telegram_message
    send_telegram_message(f"<b>Algo 2 Correlation Engine</b>\nStatus changed to: {state_str}")

    return {
        "success": True,
        "is_active": is_active,
        "message": f"Algo 2 execution is now {'active' if is_active else 'paused'}."
    }


# ─── ALGO 3 ── NIFTY OPTIONS ENGINE ──────────────────────────────────────────

@app.post("/api/algo3/toggle")
def toggle_algo3(payload: dict):
    """Toggles Algo 3 (Nifty Options Engine) on/off."""
    if not hasattr(app.state, "algo"):
        raise HTTPException(status_code=503, detail="Algo subsystem not initialized")

    is_active = payload.get("is_active", False)
    app.state.algo["is_active_algo3"] = is_active

    state_str = "ON" if is_active else "OFF (PAUSED)"
    logger.info(f"Algo 3 Options Engine Toggled: {state_str}")

    try:
        from modules.algo.telegram_bot import send_telegram_message
        send_telegram_message(f"<b>Algo 3 Nifty Options Engine</b>\nStatus changed to: {state_str}")
    except Exception as e:
        logger.warning(f"Algo3 toggle telegram error: {e}")

    return {
        "success": True,
        "is_active": is_active,
        "message": f"Algo 3 execution is now {'active' if is_active else 'paused'}."
    }


@app.get("/api/algo3/live-signal")
def get_algo3_live_signal():
    """
    Algo 3 — Nifty Options 4-Step Engine (110 pts max + 30-pt global bias).
      Step 1: Trend Alignment   (25 pts) — Supertrend 15m+1h, EMA20>50 on 1h
      Step 2: Momentum+Volume   (25 pts) — RSI(14), MACD(12,26,9), Volume ratio
      Step 3: Options Chain     (25 pts) — PCR, Real MaxPain, ATM OI, IV rank
      Step 4: Levels + Time     (25 pts) — Trade windows + key level proximity
      Global Bonus              (+10 max) — direction aligns with global bias
    Thresholds: 85=STRONG/EXECUTE | 70=GOOD/HALF | 55=WEAK/ALERT | <55=WAIT
    Trade: ATM CE (BUY) or ATM PE (SELL), 1 lot=50, SL=40% drop, T1=2x, T2=3x
    """
    import pandas as pd
    from datetime import time as dtime
    from modules.algo.algo3_engine import (
        Algo3Engine, calculate_iv_rank, calculate_gift_nifty_gap,
        generate_algo3_premarket_report, generate_algo3_eod_report
    )
    from modules.algo.global_scoring import calculate_global_bias

    # Default result shape
    base = {
        "direction": "WAIT",
        "total_score": 0,
        "step1_score": 0,
        "step2_score": 0,
        "step3_score": 0,
        "step4_score": 0,
        "global_bonus": 0,
        "global_bias_score": 0,
        "signal_strength": "NO SIGNAL",
        "action": "WAIT",
        "confidence": "LOW",
        "in_trade_window": False,
        "rsi": 0.0,
        "macd_dir": "Flat",
        "vol_ratio": 0.0,
        "pcr": 1.0,
        "max_pain": 0.0,
        "iv_rank": 50.0,
        "call_wall": 0.0,
        "put_wall": 0.0,
        "atm_strike": 0.0,
        "option_type": "",
        "entry_premium": 0.0,
        "sl_premium": 0.0,
        "t1_premium": 0.0,
        "t2_premium": 0.0,
        "lots": 1,
        "safety_clear": False,
        "safety_checks": [],
        "pre_market_report": "",
        "gift_nifty_gap": "",
        "timestamp": datetime.now().isoformat(),
    }

    try:
        # Pull global bias from cached state or recalculate
        global_bias_score = 0
        global_bias_data  = {}
        if hasattr(app.state, "algo"):
            global_bias_score = int(app.state.algo.get("global_bias", 0))

        # Gift Nifty gap
        try:
            gap_info = calculate_gift_nifty_gap()
            base["gift_nifty_gap"] = gap_info.get("gap_label", "")
        except Exception:
            base["gift_nifty_gap"] = "Unavailable"

        # Pre-market report (use cached if available)
        if hasattr(app.state, "algo"):
            pm = app.state.algo.get("algo3", {}).get("pre_market_report", "")
            base["pre_market_report"] = pm or app.state.algo.get("pre_market_report", "")

        base["global_bias_score"] = global_bias_score

        # Get Kite client
        kite_instance = None
        try:
            from modules.kite_client import KiteDataClient
            kdc = KiteDataClient()
            if kdc.is_authenticated():
                kite_instance = kdc.kite
        except Exception as e:
            logger.warning(f"Algo3 kite init: {e}")

        if kite_instance is None:
            base["signal_strength"] = "Kite not authenticated"
            return {"success": True, "data": base}

        engine = Algo3Engine(kite=kite_instance, global_bias_score=global_bias_score)

        # Spot price
        spot = engine.get_nifty_spot()
        if spot <= 0:
            base["signal_strength"] = "Could not fetch Nifty spot price"
            return {"success": True, "data": base}

        # Fetch NIFTY 50 instrument token for historical candles
        # token for ^NSEI equivalent in Kite: NSE:NIFTY 50 → need NFO futures or cash token
        # Use yfinance fallback for OHLCV candles (Kite requires instrument token)
        import yfinance as yf

        def _yf_candles(period: str, interval: str) -> pd.DataFrame:
            df = yf.download("^NSEI", period=period, interval=interval,
                             progress=False, auto_adjust=True)
            if df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            df.rename(columns={"datetime": "dt", "index": "dt"}, inplace=True)
            # yfinance MultiIndex fix
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(filter(None, c)) for c in df.columns]
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df.dropna(subset=['close'])

        df_15m = _yf_candles("5d",  "15m")
        df_1h  = _yf_candles("60d", "60m")

        # IV rank
        iv_rank = 50.0
        try:
            iv_rank = calculate_iv_rank("^NSEI")
        except Exception:
            pass

        # Account state (balance + positions from Kite)
        account_state: dict = {}
        try:
            from modules.algo.algo3_engine import get_account_state
            account_state = get_account_state(kite_instance)
        except Exception as e:
            logger.warning(f"Algo3 account state: {e}")

        # Smart options chain (expiry intelligence + Greeks)
        ce_data  = pd.DataFrame()
        pe_data  = pd.DataFrame()
        expiry_str    = ""
        dte           = 7
        expiry_reason = ""
        try:
            ce_data, pe_data, expiry_str, dte, expiry_reason = engine.get_options_chain_smart(spot, iv_rank)
        except Exception as e:
            logger.warning(f"Algo3 options chain smart: {e}")
            # Legacy fallback
            ce_data, pe_data = engine.get_options_chain(spot)

        # Key levels (use previous day high/low/close from 1h candle data)
        key_levels: dict = {}
        if not df_1h.empty and len(df_1h) >= 2:
            key_levels["prev_close"] = float(df_1h['close'].iloc[-2])
            key_levels["vwap"] = float(
                (df_1h['close'] * df_1h.get('volume', pd.Series([1]*len(df_1h)))).sum() /
                max(df_1h.get('volume', pd.Series([1]*len(df_1h))).sum(), 1)
            )

        current_time = datetime.now().time()
        app_state_dict = {"algo": app.state.algo} if hasattr(app.state, "algo") else {}

        result = engine.evaluate(
            df_15m=df_15m,
            df_1h=df_1h,
            ce_data=ce_data,
            pe_data=pe_data,
            spot=spot,
            key_levels=key_levels,
            current_time=current_time,
            iv_rank=iv_rank,
            dte=dte,
            expiry_str=expiry_str,
            expiry_reason=expiry_reason,
            account=account_state,
            app_state=app_state_dict
        )

        base.update(result)

        # Cache latest signal in app state
        if hasattr(app.state, "algo"):
            app.state.algo["algo3"]["latest_signal"] = base.copy()

    except Exception as e:
        logger.error(f"Algo 3 live-signal error: {e}", exc_info=True)
        base["signal_strength"] = f"Error: {str(e)[:120]}"

    return {"success": True, "data": base}


@app.get("/api/algo3/premarket-report")
def get_algo3_premarket_report():
    """Returns the latest pre-market report for Algo 3."""
    from modules.algo.algo3_engine import generate_algo3_premarket_report
    from modules.algo.global_scoring import calculate_global_bias
    try:
        bias = calculate_global_bias()
        report = generate_algo3_premarket_report(bias)
        if hasattr(app.state, "algo"):
            app.state.algo["algo3"]["pre_market_report"] = report
        return {"success": True, "report": report}
    except Exception as e:
        return {"success": False, "report": f"Error: {e}"}


@app.get("/api/algo3/account")
def get_algo3_account():
    """
    Live account summary from Kite:
      available_cash, used_margin, daily_pnl, open_positions,
      has_open_nifty_option, margin_error
    """
    from modules.algo.algo3_engine import get_account_state
    try:
        from modules.kite_client import KiteDataClient
        kdc = KiteDataClient()
        if not kdc.is_authenticated():
            return {"success": False, "data": {"margin_error": "Kite not authenticated"}}
        state = get_account_state(kdc.kite)
        return {"success": True, "data": state}
    except Exception as e:
        logger.error(f"Algo3 account endpoint: {e}")
        return {"success": False, "data": {"margin_error": str(e)[:120]}}


# ══════════════════════════════════════════════════════════════════════════════
# BALANCE-AWARE INSTRUMENT RECOMMENDATION  (shared by Algo 1 and Algo 2)
# ══════════════════════════════════════════════════════════════════════════════

def _recommend_instrument(
    kite,
    direction: str,
    spot: float,
    atr: float,
    available_cash: float
) -> dict:
    """
    Given a directional signal and live account balance, choose the best
    Nifty instrument to trade:

      Tier 1 — cash >= ₹80,000  → Nifty Futures (MIS, 1 lot = 75 units)
               Strong leverage; suitable for score >= 75 signals
      Tier 2 — cash >= ₹15,000  → ATM CE (BUY) or ATM PE (SELL) weekly option
               Defined max-loss; suitable for any actionable signal
      Tier 3 — cash < ₹15,000   → Cannot trade (insufficient capital)

    Returns a dict with:
      instrument, instrument_type, strike, option_type, premium,
      lots, quantity, estimated_cost, estimated_margin,
      max_loss, target_profit, viable, reason
    """
    LOT_SIZE       = 75
    FUTURES_MARGIN = 80_000   # ₹80k minimum for Nifty MIS futures (1 lot)
    OPTIONS_MIN    = 15_000   # ₹15k minimum for 1 lot ATM option

    rec: dict = {
        "instrument":       "NONE",
        "instrument_type":  "",
        "strike":           0.0,
        "option_type":      "",
        "premium":          0.0,
        "lots":             0,
        "lot_size":         LOT_SIZE,
        "quantity":         0,
        "estimated_cost":   0.0,
        "estimated_margin": 0.0,
        "max_loss":         0.0,
        "target_profit":    0.0,
        "available_cash":   round(available_cash, 0),
        "viable":           False,
        "reason":           "",
    }

    if direction in ("WAIT", "NEUTRAL", ""):
        rec["reason"] = "No directional signal — waiting for setup"
        return rec

    atm = round(spot / 50) * 50 if spot > 0 else 0.0
    opt_type = "CE" if direction == "BUY" else "PE"

    # ── Determine tier ────────────────────────────────────────────────────────
    if available_cash <= 0:
        tier = "unknown"
    elif available_cash >= FUTURES_MARGIN:
        tier = "futures"
    elif available_cash >= OPTIONS_MIN:
        tier = "options"
    else:
        tier = "insufficient"

    # Unknown balance (Kite not connected) → default to options estimate
    if tier == "unknown":
        tier = "options"

    # ── Tier 1: Futures ───────────────────────────────────────────────────────
    if tier == "futures":
        lots = min(2, max(1, int(available_cash // FUTURES_MARGIN)))
        qty  = lots * LOT_SIZE
        sl_pts  = round(atr * 0.8, 1) if atr > 0 else 25.0
        tgt_pts = round(atr * 1.6, 1) if atr > 0 else 50.0
        rec.update({
            "instrument":       "NIFTY FUT (MIS)",
            "instrument_type":  "FUTURES",
            "lots":             lots,
            "quantity":         qty,
            "estimated_margin": round(FUTURES_MARGIN * lots, 0),
            "max_loss":         round(sl_pts  * qty, 0),
            "target_profit":    round(tgt_pts * qty, 0),
            "viable":           True,
            "reason": (
                f"Balance ₹{available_cash:.0f} supports futures. "
                f"{lots} lot × ₹{FUTURES_MARGIN:.0f} margin = ₹{FUTURES_MARGIN*lots:.0f}. "
                f"Risk ₹{round(sl_pts*qty,0):.0f} | Target ₹{round(tgt_pts*qty,0):.0f}"
            ),
        })
        return rec

    # ── Tier 2: Options ───────────────────────────────────────────────────────
    if tier in ("options", "unknown"):
        premium = 0.0
        try:
            if kite is not None:
                from modules.kite_client import KiteDataClient
                kdc = KiteDataClient()
                instruments = kdc.get_instruments("NFO") or []
                nifty_opts = [
                    i for i in instruments
                    if i.get("name", "").upper() == "NIFTY"
                    and i.get("segment") == "NFO-OPT"
                ]
                expiries = sorted(set(
                    str(i.get("expiry", ""))[:10]
                    for i in nifty_opts if i.get("expiry")
                ))
                if expiries:
                    expiry = expiries[0]
                    for inst in nifty_opts:
                        s = float(inst.get("strike", 0))
                        if (abs(s - atm) < 1
                                and str(inst.get("expiry", ""))[:10] == expiry
                                and inst.get("instrument_type") == opt_type):
                            sym = inst.get("tradingsymbol", "")
                            q   = kite.quote([f"NFO:{sym}"])
                            ltp = float(q.get(f"NFO:{sym}", {}).get("last_price", 0))
                            if ltp > 0:
                                premium = ltp
                            break
        except Exception as _e:
            logger.debug(f"Instrument rec options fetch: {_e}")

        if premium <= 0:
            premium = 120.0   # fallback estimate

        cost_per_lot = premium * LOT_SIZE * 1.10
        if available_cash > 0:
            lots = max(1, min(2, int((available_cash * 0.10) // cost_per_lot)))
            if cost_per_lot > available_cash * 0.10:
                lots = 1
        else:
            lots = 1

        qty  = lots * LOT_SIZE
        cost = round(premium * qty, 0)
        rec.update({
            "instrument":      f"NIFTY {atm:.0f} {opt_type} (WEEKLY)",
            "instrument_type": "OPTIONS",
            "strike":          float(atm),
            "option_type":     opt_type,
            "premium":         round(premium, 2),
            "lots":            lots,
            "quantity":        qty,
            "estimated_cost":  cost,
            "max_loss":        cost,        # defined risk = full premium paid
            "target_profit":   round(premium * 2.0 * qty, 0),
            "viable":          (available_cash <= 0 or available_cash >= OPTIONS_MIN),
            "reason": (
                f"Balance ₹{available_cash:.0f}: buy {lots} lot {atm:.0f}{opt_type} "
                f"@ ₹{premium:.0f} = ₹{cost:.0f}. Max loss capped at premium paid."
                if available_cash > 0 else
                f"Balance unknown — estimate: {lots} lot {atm:.0f}{opt_type} "
                f"@ ~₹{premium:.0f} ≈ ₹{cost:.0f}"
            ),
        })
        return rec

    # ── Tier 3: Insufficient ──────────────────────────────────────────────────
    rec["reason"] = (
        f"Insufficient balance ₹{available_cash:.0f}. "
        f"Need ₹{OPTIONS_MIN:.0f}+ for options or ₹{FUTURES_MARGIN:.0f}+ for futures."
    )
    return rec


@app.get("/api/algo/live-signal")
def get_algo_live_signal():
    """
    Improved Algo Engine — 4-Component scoring system.
      Component 1: Correlation Signal  (max 30 pts) — Nasdaq, SP500, USD/INR, Oil, Gold
      Component 2: Global Bias Align   (max 25 pts) — pre-market global markets (cached)
      Component 3: Technical           (max 25 pts) — RSI(14), MACD(12,26,9), VWAP
      Component 4: Price Level + Time  (max 20 pts) — ATR momentum, round level, time window
    Total 100 pts  |  >=75 STRONG  |  55-74 MODERATE  |  <55 WEAK/WAIT
    SL  = Entry ± 0.8 × ATR(14 on 5m)
    TGT = Entry ± 1.6 × ATR(14 on 5m)   →  1:2 R/R
    """
    import pandas as pd
    import numpy as np
    import yfinance as yf
    from datetime import time as dtime

    result = {
        "direction": "WAIT",
        "total_score": 0,
        "comp1_correlation": 0,
        "comp2_global_bias": 0,
        "comp3_technical": 0,
        "comp4_price_level": 0,
        "entry_price": 0.0,
        "target_price": 0.0,
        "stop_loss": 0.0,
        "atr": 25.0,
        "rr_ratio": 2.0,
        "confidence": "LOW",
        "signal_strength": "WAIT",
        "action": "WAIT",
        "rsi": 0.0,
        "macd_direction": "—",
        "global_bias_score": 0,
        "corr_score_raw": 0.0,
        "timestamp": datetime.now().isoformat(),
        "valid_until": (datetime.now() + pd.Timedelta(minutes=15)).isoformat()
    }

    try:
        _mkt = globals()['market']
        start_dt = (datetime.now() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")

        # ─── COMPONENT 1: CORRELATION SIGNAL (max 30 pts) ───────────────────────────
        predictors = {"Nasdaq": "NQ=F", "SP500": "ES=F", "USD_INR": "INR=X", "Oil": "CL=F", "Gold": "GC=F"}
        target_symbol = "^NSEI"
        target_data = _mkt.fetch_stock_data(target_symbol, start_date=start_dt, market="NSE")
        preds_data = {}
        for name, sym in predictors.items():
            df_p = _mkt.fetch_stock_data(sym, start_date=start_dt, market="Global")
            if not df_p.empty:
                df_p = df_p.set_index('date')
                preds_data[name] = df_p['daily_return']

        corr_score_raw = 0.0
        corr_direction = "WAIT"
        comp1 = 0

        if not target_data.empty and preds_data:
            target_ret = target_data.set_index('date')['daily_return']
            combined = pd.DataFrame({target_symbol: target_ret})
            for name, series in preds_data.items():
                combined[name] = series
            combined = combined.dropna()
            if len(combined) >= 10:
                correlations = {}
                for name in preds_data:
                    if name in combined.columns:
                        c = combined[target_symbol].corr(combined[name])
                        correlations[name] = c if not pd.isna(c) else 0.0
                latest = combined.iloc[-1]
                corr_score_raw = sum(float(latest.get(n, 0)) * c for n, c in correlations.items())
                abs_csr = abs(corr_score_raw)
                if abs_csr > 0.5: comp1 = 30
                elif abs_csr > 0.3: comp1 = 20
                elif abs_csr > 0.1: comp1 = 10
                corr_direction = "BUY" if corr_score_raw > 0.1 else "SELL" if corr_score_raw < -0.1 else "WAIT"

        result["comp1_correlation"] = comp1
        result["corr_score_raw"] = round(corr_score_raw, 3)

        # ─── COMPONENT 2: GLOBAL BIAS ALIGNMENT (max 25 pts) ────────────────────────
        comp2 = 0
        global_score = 0
        try:
            if hasattr(app.state, "algo"):
                global_score = int(app.state.algo.get("global_bias", 0))
        except Exception:
            global_score = 0

        if corr_direction != "WAIT":
            direction_aligns = (
                (corr_direction == "BUY" and global_score >= 0) or
                (corr_direction == "SELL" and global_score <= 0)
            )
            abs_gs = abs(global_score)
            if direction_aligns:
                if abs_gs >= 15: comp2 = 25
                elif abs_gs >= 5: comp2 = 15
                elif abs_gs > 0: comp2 = 5
            else:
                comp2 = 0  # conflicting global bias — no credit

        result["comp2_global_bias"] = comp2
        result["global_bias_score"] = global_score

        # ─── COMPONENT 3: TECHNICAL INDICATORS (max 25 pts) ─────────────────────────
        comp3 = 0
        rsi_val = 50.0
        macd_dir = "—"
        price_now = 0.0

        try:
            df15 = yf.Ticker("^NSEI").history(period="5d", interval="15m")
            if not df15.empty and len(df15) >= 30:
                close = df15['Close']

                # RSI(14)
                delta = close.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss.replace(0, 1e-9)
                rsi_series = 100 - (100 / (1 + rs))
                rsi_val = round(float(rsi_series.iloc[-1]), 1)

                # MACD(12,26,9) — histogram direction
                ema12 = close.ewm(span=12, adjust=False).mean()
                ema26 = close.ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                hist = macd_line - macd_line.ewm(span=9, adjust=False).mean()
                macd_dir = "UP" if float(hist.iloc[-1]) > float(hist.iloc[-2]) else "DOWN"

                # VWAP (today's candles only)
                today_df = df15[df15.index.date == df15.index[-1].date()]
                if not today_df.empty and today_df['Volume'].sum() > 0:
                    tp = (today_df['High'] + today_df['Low'] + today_df['Close']) / 3
                    vwap = float((tp * today_df['Volume']).cumsum().iloc[-1] / today_df['Volume'].cumsum().iloc[-1])
                else:
                    vwap = float(close.iloc[-1])

                price_now = float(close.iloc[-1])

                if corr_direction == "BUY":
                    if 40 <= rsi_val <= 65: comp3 += 10
                    elif rsi_val < 35: comp3 += 8        # oversold bounce
                    if macd_dir == "UP": comp3 += 8
                    if price_now > vwap: comp3 += 7
                elif corr_direction == "SELL":
                    if 35 <= rsi_val <= 60: comp3 += 10
                    elif rsi_val > 65: comp3 += 8         # overbought rejection
                    if macd_dir == "DOWN": comp3 += 8
                    if price_now < vwap: comp3 += 7

        except Exception as te:
            logger.warning(f"Technical score error: {te}")

        result["comp3_technical"] = min(comp3, 25)
        result["rsi"] = rsi_val
        result["macd_direction"] = macd_dir

        # ─── COMPONENT 4: PRICE LEVEL + TIME WINDOW (max 20 pts) ───────────────────
        comp4 = 0
        atr_val = 25.0
        entry_price = price_now  # already set from 15m close

        try:
            df5 = yf.Ticker("^NSEI").history(period="2d", interval="5m")
            if not df5.empty and len(df5) >= 15:
                high5 = df5['High']
                low5 = df5['Low']
                pc5 = df5['Close'].shift(1)
                tr5 = pd.concat([(high5 - low5), (high5 - pc5).abs(), (low5 - pc5).abs()], axis=1).max(axis=1)
                atr_val = round(float(tr5.rolling(14).mean().iloc[-1]), 2)

                if entry_price == 0.0:
                    entry_price = float(df5['Close'].iloc[-1])

                candle_range = float(df5['High'].iloc[-1] - df5['Low'].iloc[-1])
                if candle_range > 1.2 * atr_val: comp4 += 10
                elif candle_range > 0.7 * atr_val: comp4 += 5

                # Proximity to nearest 50-point round level (±0.25%)
                closest_50 = round(entry_price / 50) * 50
                if abs(entry_price - closest_50) / entry_price * 100 <= 0.25:
                    comp4 += 5

                # Valid trading window (IST)
                ct = dtime(datetime.now().hour, datetime.now().minute)
                in_window = (
                    dtime(9, 15) <= ct <= dtime(9, 50) or
                    dtime(13, 0) <= ct <= dtime(13, 30) or
                    dtime(14, 30) <= ct <= dtime(15, 15)
                )
                if in_window:
                    comp4 += 5

        except Exception as pe:
            logger.warning(f"Price level score error: {pe}")

        result["comp4_price_level"] = min(comp4, 20)
        result["atr"] = atr_val

        # ─── TOTAL & SIGNAL CLASSIFICATION ──────────────────────────────────────────
        total = result["comp1_correlation"] + result["comp2_global_bias"] + result["comp3_technical"] + result["comp4_price_level"]
        result["total_score"] = total

        if corr_direction == "WAIT" or total < 40:
            result.update({"direction": "WAIT", "signal_strength": "INSUFFICIENT", "action": "WAIT", "confidence": "LOW"})
        elif total >= 75:
            result.update({"direction": corr_direction, "signal_strength": "STRONG", "action": "EXECUTE", "confidence": "HIGH"})
        elif total >= 55:
            result.update({"direction": corr_direction, "signal_strength": "MODERATE", "action": "ALERT", "confidence": "MEDIUM"})
        else:
            result.update({"direction": corr_direction, "signal_strength": "WEAK", "action": "WATCH", "confidence": "LOW"})

        # ─── ENTRY / SL / TARGET (ATR-based, 1:2 R/R) ───────────────────────────────
        try:
            if entry_price == 0.0:
                ldf = yf.Ticker("^NSEI").history(period="1d", interval="1m")
                entry_price = float(ldf['Close'].iloc[-1]) if not ldf.empty else 0.0

            if entry_price > 0 and result["direction"] != "WAIT":
                sl_dist  = round(atr_val * 0.8, 1)
                tgt_dist = round(atr_val * 1.6, 1)
                result["entry_price"] = round(entry_price, 1)
                if result["direction"] == "BUY":
                    result["stop_loss"]   = round(entry_price - sl_dist, 1)
                    result["target_price"] = round(entry_price + tgt_dist, 1)
                else:
                    result["stop_loss"]   = round(entry_price + sl_dist, 1)
                    result["target_price"] = round(entry_price - tgt_dist, 1)
                result["rr_ratio"] = round(tgt_dist / sl_dist, 1) if sl_dist > 0 else 2.0

        except Exception as ee:
            logger.warning(f"Entry/SL calc error: {ee}")

        # ─── BALANCE-AWARE INSTRUMENT RECOMMENDATION ─────────────────────────
        try:
            _kite_a1 = None
            _cash_a1 = 0.0
            try:
                from modules.kite_client import KiteDataClient as _KDC_A1
                _kdc_a1 = _KDC_A1()
                if _kdc_a1.is_authenticated():
                    _kite_a1 = _kdc_a1.kite
                    _margins = _kite_a1.margins()
                    _cash_a1 = float(
                        _margins.get("equity", {})
                        .get("available", {})
                        .get("live_balance", 0) or 0
                    )
            except Exception:
                pass

            if result["direction"] != "WAIT" and result.get("entry_price", 0) > 0:
                result["instrument_rec"] = _recommend_instrument(
                    kite=_kite_a1,
                    direction=result["direction"],
                    spot=result["entry_price"],
                    atr=result.get("atr", 25.0),
                    available_cash=_cash_a1,
                )
            else:
                result["instrument_rec"] = {
                    "instrument": "NONE",
                    "instrument_type": "",
                    "viable": False,
                    "reason": "No actionable signal — waiting for setup",
                    "available_cash": _cash_a1,
                }
        except Exception as _ie:
            result["instrument_rec"] = {
                "instrument": "NONE",
                "instrument_type": "",
                "viable": False,
                "reason": str(_ie)[:100],
            }

    except Exception as e:
        logger.error(f"Algo live signal error: {e}")
        result["signal_strength"] = "ERROR"

    return {"success": True, "data": result}
