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

@app.post("/api/kite/callback")
def kite_callback(payload: dict):
    request_token = payload.get("request_token")
    if not request_token:
        raise HTTPException(status_code=400, detail="Request token missing")
    try:
        kite_client.generate_session(request_token)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
