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
    return {"authenticated": kite_client.is_authenticated()}

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
            html = """
            <html>
            <head><title>Kite Connected</title>
            <style>
              body { font-family: sans-serif; display: flex; justify-content: center; 
                     align-items: center; height: 100vh; margin: 0; 
                     background: #0a0f1e; color: white; flex-direction: column; }
              .card { background: #1a2035; padding: 40px; border-radius: 16px; 
                      text-align: center; border: 1px solid #2a3f6f; }
              h2 { color: #4ade80; margin-bottom: 8px; }
              a { color: #60a5fa; }
            </style>
            </head>
            <body>
              <div class='card'>
                <h2>✅ Kite API Connected!</h2>
                <p>Your session is now active. Live market data is enabled.</p>
                <p><a href='/'>← Back to Dashboard</a></p>
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
def get_monthly_forecast():
    """
    Elite-only: Composite 1-Month Market Forecast.
    Combines Astro signals, Technical trends, Options Chain, and News Sentiment
    into a weighted score and directional forecast.
    """
    from datetime import timedelta
    from dateutil.relativedelta import relativedelta
    import math

    signals = []
    score = 0.0  # -12 = very bearish, +12 = very bullish

    # ── 1. ASTRO SIGNAL (weight: 3) ──────────────────────────────────────────
    try:
        # Project 30 days into the future
        upcoming_astro = analyzer.predict_upcoming_market(days=30)
        bull_days = sum(1 for d in upcoming_astro if d.get("historical_tendency") == "Bullish")
        bear_days = sum(1 for d in upcoming_astro if d.get("historical_tendency") == "Bearish")
        
        astro_score = 0
        if bull_days > bear_days + 4:
            astro_score += 3.0
            signals.append({"category": "Astro", "icon": "🔮", "direction": "bullish",
                            "text": f"Next 30 days favors bulls ({bull_days} Bull vs {bear_days} Bear nakshatras)"})
        elif bear_days > bull_days + 4:
            astro_score -= 3.0
            signals.append({"category": "Astro", "icon": "🔮", "direction": "bearish",
                            "text": f"Next 30 days favors bears ({bear_days} Bear vs {bull_days} Bull nakshatras)"})
        else:
            signals.append({"category": "Astro", "icon": "🔮", "direction": "neutral",
                            "text": f"Balanced planetary transit month ({bull_days} Bull vs {bear_days} Bear)"})

        # Today's Yoga bonus
        today_astro = analyzer.generate_today_insight()
        yoga_name = today_astro.get("yoga_name", "")
        bullish_yogas = ["Gajakesari", "Raja", "Amala", "Dhana", "Saraswati"]
        bearish_yogas = ["Shula", "Visha", "Daridra", "Kemadruma"]
        if any(y.lower() in yoga_name.lower() for y in bullish_yogas):
            astro_score += 1.0
            signals.append({"category": "Astro", "icon": "⭐", "direction": "bullish",
                            "text": f"{yoga_name} yoga active today — auspicious trigger"})
        elif any(y.lower() in yoga_name.lower() for y in bearish_yogas):
            astro_score -= 1.0
            signals.append({"category": "Astro", "icon": "⚠️", "direction": "bearish",
                            "text": f"{yoga_name} yoga active today — short-term resistance"})
                            
        score += astro_score
    except Exception as e:
        logger.warning(f"Forecast: astro signal failed: {e}")

    # ── 2. MACRO EVENTS SIGNAL (weight: 2) ───────────────────────────────────
    try:
        from modules.economic_events import EconomicEventsAnalyzer
        events_engine = EconomicEventsAnalyzer()
        events = events_engine.get_upcoming_events(days_ahead=30)
        
        bullish_events = sum(1 for e in events if e.get("expected_bias") == "Bullish")
        bearish_events = sum(1 for e in events if e.get("expected_bias") == "Bearish")
        
        if bullish_events > bearish_events:
            score += 2.0
            signals.append({"category": "Events", "icon": "🗓️", "direction": "bullish",
                            "text": f"{bullish_events} positive macro events upcoming (e.g. rate cuts or earnings)"})
        elif bearish_events > bullish_events:
            score -= 2.0
            signals.append({"category": "Events", "icon": "🗓️", "direction": "bearish",
                            "text": f"{bearish_events} negative macro events upcoming (e.g. rate hikes or inflation)"})
        elif len(events) > 0:
            signals.append({"category": "Events", "icon": "🗓️", "direction": "neutral",
                            "text": f"{len(events)} mixed macro events scheduled in the next 30 days"})
        else:
            signals.append({"category": "Events", "icon": "🗓️", "direction": "neutral",
                            "text": "Quiet macroeconomic calendar for the next month"})
    except Exception as e:
        logger.warning(f"Forecast: events signal failed: {e}")

    # ── 3. TECHNICAL SIGNAL (weight: 3) ──────────────────────────────────────
    try:
        import yfinance as yf
        ticker = yf.Ticker("^NSEI")
        hist = ticker.history(period="1y")
        if not hist.empty and len(hist) >= 200:
            close = hist["Close"]
            current = close.iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]
            
            # RSI
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean().iloc[-1]
            loss = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + gain / loss)) if loss != 0 else 50

            tech_score = 0
            tech_notes = []
            
            if current > ma50: tech_score += 1
            else: tech_score -= 1
            
            if ma50 > ma200: 
                tech_score += 1; tech_notes.append("Golden Cross (50DMA > 200DMA)")
            else: 
                tech_score -= 1; tech_notes.append("Death Cross (50DMA < 200DMA)")
                
            if rsi < 30: 
                tech_score += 1; tech_notes.append("RSI deeply oversold")
            elif rsi > 70: 
                tech_score -= 1; tech_notes.append("RSI heavily overbought")

            score += tech_score
            direction = "bullish" if tech_score > 0 else ("bearish" if tech_score < 0 else "neutral")
            signals.append({"category": "Technical", "icon": "📈", "direction": direction,
                            "text": " · ".join(tech_notes) if tech_notes else "Neutral trend continuation"})
    except Exception as e:
        logger.warning(f"Forecast: technical signal failed: {e}")

    # ── 4. OPTIONS CHAIN SIGNAL (weight: 2) ──────────────────────────────────
    try:
        snap = derivatives_engine.get_market_snapshot("NIFTY")
        pcr = snap.get("pcr", 1.0)
        vix = snap.get("vix", {}).get("current", 15) if isinstance(snap.get("vix"), dict) else snap.get("vix", 15)

        opt_score = 0
        if pcr > 1.3:
            opt_score += 2; signals.append({"category": "Options", "icon": "⛓️", "direction": "bullish",
                                            "text": f"PCR {pcr:.2f} — high put accumulation, strong support"})
        elif pcr < 0.7:
            opt_score -= 2; signals.append({"category": "Options", "icon": "⛓️", "direction": "bearish",
                                            "text": f"PCR {pcr:.2f} — heavy call writing, tight resistance"})
        
        if vix > 22:
            opt_score -= 1
            if opt_score < 0: signals.append({"category": "Options", "icon": "🌡️", "direction": "bearish", "text": f"VIX {vix:.1f} — high volatility panic"})
        elif vix < 14:
            opt_score += 1
            if opt_score > 0 and len(signals) < 5: signals.append({"category": "Options", "icon": "🌡️", "direction": "bullish", "text": f"VIX {vix:.1f} — low volatility complacency"})
            
        if opt_score == 0:
            signals.append({"category": "Options", "icon": "⛓️", "direction": "neutral",
                            "text": f"Options chain balanced (PCR {pcr:.1f}, VIX {vix:.1f})"})
        score += opt_score
    except Exception as e:
        logger.warning(f"Forecast: options signal failed: {e}")

    # ── 5. NEWS SENTIMENT SIGNAL (weight: 2) ─────────────────────────────────
    try:
        sent = sentiment_engine.get_sentiment_forecast("^NSEI", "NSE")
        sentiment_text = sent.get("overall_sentiment", "Neutral")
        if sentiment_text == "Bullish":
            score += 2; signals.append({"category": "Sentiment", "icon": "📰", "direction": "bullish",
                                        "text": "News & macro sentiment broadly positive for Indian markets"})
        elif sentiment_text == "Bearish":
            score -= 2; signals.append({"category": "Sentiment", "icon": "📰", "direction": "bearish",
                                        "text": "News & macro sentiment broadly negative — caution warranted"})
    except Exception as e:
        logger.warning(f"Forecast: sentiment signal failed: {e}")

    # ── COMPOSITE RESULT ─────────────────────────────────────────────────────
    max_possible = 12.0
    normalized = round(max(min(score / max_possible * 100, 100), -100), 1)
    confidence = round(min(abs(normalized), 90), 0)

    if score >= 4:
        verdict, verdict_color, verdict_emoji = "BULLISH", "#4ade80", "📈"
        summary = "Multiple converging signals point to upward momentum over the next month. Look for buying opportunities on dips."
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

    # Exact calendar month projection
    target_date = (datetime.now() + relativedelta(months=1)).strftime("%d %b %Y")

    return {
        "verdict": verdict,
        "verdict_color": verdict_color,
        "verdict_emoji": verdict_emoji,
        "score": round(score, 1),
        "normalized_score": normalized,
        "confidence": int(confidence),
        "summary": summary,
        "target_date": target_date,
        "signals": signals,
        "generated_at": datetime.now().isoformat(),
    }


@app.get("/api/nakshatras")
def get_nakshatras():
    """Get all 27 Nakshatras."""
    return {"nakshatras": get_all_nakshatras()}

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

