"""
Astro-Finance API Backend
FastAPI server serving Next.js frontend
"""
import sys
import os
import logging
from fastapi import FastAPI, HTTPException
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

logger = logging.getLogger(__name__)

app = FastAPI(title="Astro-Finance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
                  : window.location.origin;
              setTimeout(function() {{ window.location.href = frontendUrl; }}, 2000);
            </script>
            </head>
            <body>
              <div class='card'>
                <h2>✅ Kite API Connected!</h2>
                <p>Your session is now active. Live market data is enabled.</p>
                <p class='hint'>Redirecting to dashboard in 2 seconds…</p>
                <p><a id='dashLink' href='http://localhost:3000'>← Back to Dashboard</a></p>
                <script>
                  document.getElementById('dashLink').href = window.location.hostname === 'localhost'
                      ? 'http://localhost:3000' : '/';
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

    # ── 2. MACRO EVENTS SIGNAL (weight: 2) ───────────────────────────────────
    try:
        from modules.economic_events import EconomicEventsAnalyzer
        events_engine = EconomicEventsAnalyzer()
        events = events_engine.get_upcoming_events(days_ahead=30) if not is_historical else []
        
        if not is_historical:
            bullish_events = sum(1 for e in events if e.get("expected_bias") == "Bullish")
            bearish_events = sum(1 for e in events if e.get("expected_bias") == "Bearish")
            
            if bullish_events > bearish_events:
                score += 2.0
                signals.append({"category": "Events", "icon": "🗓️", "direction": "bullish", "text": f"{bullish_events} positive macro events upcoming"})
            elif bearish_events > bullish_events:
                score -= 2.0
                signals.append({"category": "Events", "icon": "🗓️", "direction": "bearish", "text": f"{bearish_events} negative macro events upcoming"})
            elif len(events) > 0:
                signals.append({"category": "Events", "icon": "🗓️", "direction": "neutral", "text": f"{len(events)} mixed macro events scheduled"})
            else:
                signals.append({"category": "Events", "icon": "🗓️", "direction": "neutral", "text": "Quiet macroeconomic calendar for the next month"})
        else:
            signals.append({"category": "Events", "icon": "🗓️", "direction": "historical", "text": "Historical macro events N/A"})
    except Exception as e:
        logger.warning(f"Forecast: events signal failed: {e}")

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
# 7-DAY COMPREHENSIVE FORECAST
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/forecast/weekly")
def get_weekly_forecast(market: str = "NSE"):
    """
    Comprehensive 7-day forecast combining:
    - Per-day astro (Nakshatra, Tithi, Yoga, Weekday)
    - Planetary Yogas (Angarak, Guru Chandal, Vish, Grahan, etc.)
    - Upcoming economic events
    - Option chain snapshot (PCR, VIX)
    - FII/DII institutional flows
    - Technical bias (50/200 DMA, RSI)
    - Nakshatra historical win rates
    - Weekday seasonality
    """
    from modules.planetary_yogas import detect_active_yogas, get_yoga_market_score
    from modules.institutional_data import fetch_fii_dii_data
    import yfinance as yf
    import pandas as pd
    from datetime import timedelta

    today = datetime.now()
    days = []

    # ── GLOBAL SIGNALS (computed once) ────────────────────────────────────────

    # 1. Options Chain snapshot
    options_signal = {"pcr": None, "vix": None, "direction": "neutral", "text": "N/A"}
    try:
        snap = derivatives_engine.get_market_snapshot("NIFTY" if market == "NSE" else "SPY")
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
        logger.warning(f"Weekly forecast: Options snapshot failed: {e}")

    # 2. FII/DII flows
    fii_signal = {"direction": "neutral", "text": "N/A", "fii_net": None, "dii_net": None}
    try:
        fii_data = fetch_fii_dii_data()
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

    # 3. Technical snapshot
    tech_signal = {"direction": "neutral", "text": "N/A", "rsi": None, "trend": None}
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

    # 4. Upcoming economic events
    upcoming_events = []
    try:
        events_list = events_engine.get_upcoming_events(days_ahead=10)
        for ev in events_list[:8]:
            upcoming_events.append({
                "date": ev.get("date", ""),
                "name": ev.get("event", ev.get("name", "")),
                "impact": ev.get("impact", "medium"),
                "market_impact": ev.get("historical_market_reaction", ""),
            })
    except Exception as e:
        logger.warning(f"Weekly forecast: Events failed: {e}")

    # 5. Weekday performance map (backtested averages for Indian market)
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

    # ── PER-DAY FORECAST ──────────────────────────────────────────────────────
    for i in range(7):
        target_dt = today + timedelta(days=i)
        # Skip weekends
        if target_dt.weekday() >= 5:
            continue

        # Astro data
        astro = {}
        try:
            calc_dt = target_dt.replace(hour=9, minute=15, second=0, microsecond=0)
            astro = moon_calc.calculate_nakshatra(calc_dt)
        except Exception as e:
            logger.warning(f"Weekly forecast day {i}: astro failed: {e}")

        # Planetary yogas for this day
        yoga_data = {}
        active_yogas = []
        try:
            calc_dt = target_dt.replace(hour=9, minute=15, second=0, microsecond=0)
            yoga_data = get_yoga_market_score(calc_dt)
            active_yogas = yoga_data.get("active_yogas", [])
        except Exception as e:
            logger.warning(f"Weekly forecast day {i}: yogas failed: {e}")

        # Historical tendency from nakshatra
        tendency = astro.get("historical_market_tendency", "Neutral")

        # Weekday bias
        wday = target_dt.weekday()
        wday_info = weekday_map.get(wday, {"day": "", "bias": "neutral", "note": ""})

        # Events on this day
        day_str = target_dt.strftime("%Y-%m-%d")
        day_events = [ev for ev in upcoming_events if ev.get("date", "").startswith(day_str)]

        # ── Compute per-day composite score ───────────────────────────────────
        day_score = 0

        # Astro tendency
        if tendency == "Bullish":
            day_score += 2
        elif tendency == "Bearish":
            day_score -= 2

        # Yoga score (-10 to +10, scale down)
        yoga_score = yoga_data.get("score", 0)
        day_score += yoga_score * 0.3

        # Weekday bias
        if wday_info["bias"] == "bullish":
            day_score += 0.5
        elif wday_info["bias"] == "bearish":
            day_score -= 0.5

        # Events impact
        for ev in day_events:
            impact = ev.get("impact", "medium")
            if impact == "high":
                day_score -= 0.5  # High-impact events add uncertainty

        # Global signals (applied with decay for future days)
        decay = max(0.3, 1.0 - i * 0.1)  # Less weight for further days

        if options_signal["direction"] == "bullish":
            day_score += 1.0 * decay
        elif options_signal["direction"] == "bearish":
            day_score -= 1.0 * decay

        if fii_signal["direction"] == "bullish":
            day_score += 0.8 * decay
        elif fii_signal["direction"] == "bearish":
            day_score -= 0.8 * decay

        if tech_signal["direction"] == "bullish":
            day_score += 1.0 * decay
        elif tech_signal["direction"] == "bearish":
            day_score -= 1.0 * decay

        # Determine verdict
        if day_score >= 2.5:
            verdict = "Strong Buy"
            color = "#4ade80"
        elif day_score >= 1.0:
            verdict = "Bullish"
            color = "#86efac"
        elif day_score <= -2.5:
            verdict = "Strong Sell"
            color = "#f87171"
        elif day_score <= -1.0:
            verdict = "Bearish"
            color = "#fca5a5"
        else:
            verdict = "Neutral"
            color = "#fbbf24"

        # Build day object
        days.append({
            "date": day_str,
            "weekday": target_dt.strftime("%A"),
            "verdict": verdict,
            "verdict_color": color,
            "score": round(day_score, 2),
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
                "icon": y["icon"],
                "severity": y["severity"],
                "impact": y["market_impact"],
                "desc": y["desc"],
            } for y in active_yogas],
            "weekday_bias": wday_info,
            "events": day_events,
        })

    return {
        "market": market,
        "generated_at": datetime.now().isoformat(),
        "days": days,
        "global_signals": {
            "options": options_signal,
            "institutional": fii_signal,
            "technical": tech_signal,
        },
        "upcoming_events": upcoming_events,
    }


@app.get("/api/nakshatras")
def get_nakshatras():
    """Get all 27 Nakshatras."""
    return {"nakshatras": get_all_nakshatras()}


# ══════════════════════════════════════════════════════════════════════════════
# LIVE CHART DATA
# ══════════════════════════════════════════════════════════════════════════════

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
        '1m': 'minute', '5m': '5minute', '15m': '15minute',
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
        INTRADAY_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}
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

        # New engine returns a structured dict with scans, fib, prediction, astro
        result = scanner.run_multi_timeframe_scan(
            symbol=req.symbol,
            market=req.market,
            historical_period=req.historical_period
        )

        return {
            "success": True,
            "symbol": req.symbol,
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
        return res
    except Exception as e:
        import traceback
        traceback.print_exc()
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

