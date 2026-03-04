"""
News Sentiment Backtest & Market Forecast Engine for Astro-Finance.
Provides:
  1. Historical sentiment backtesting using price-action sentiment proxy
  2. 1-month (22-trading-day) market forecast combining sentiment, events, seasonality, and astro
  3. News-impact correlation across configurable periods
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from modules.market_data import MarketDataFetcher

logger = logging.getLogger(__name__)

# ============================================================
# PERIOD MAPPING
# ============================================================
PERIOD_MAP = {
    "1y": 365,
    "5y": 365 * 5,
    "10y": 365 * 10,
    "max": 365 * 25,
}

# Seasonality: historical monthly bias for Nifty (approximate)
MONTHLY_SEASONAL_BIAS = {
    1: {"bias": "Bullish", "reason": "Jan effect — fresh FII allocations", "strength": 0.6},
    2: {"bias": "Bearish", "reason": "Pre-budget volatility / profit booking", "strength": 0.5},
    3: {"bias": "Bullish", "reason": "FY-end buying + LTCG harvesting", "strength": 0.55},
    4: {"bias": "Bullish", "reason": "New FY inflows + fresh institutional cycles", "strength": 0.6},
    5: {"bias": "Neutral", "reason": "Consolidation post Q4 results", "strength": 0.4},
    6: {"bias": "Neutral", "reason": "Monsoon watch + global cues", "strength": 0.45},
    7: {"bias": "Bullish", "reason": "Budget rally + monsoon momentum", "strength": 0.55},
    8: {"bias": "Bearish", "reason": "Historically weak — profit booking", "strength": 0.5},
    9: {"bias": "Bullish", "reason": "Festive demand anticipation", "strength": 0.6},
    10: {"bias": "Bullish", "reason": "Diwali rally + festive buying", "strength": 0.65},
    11: {"bias": "Neutral", "reason": "FII outflows + global uncertainty", "strength": 0.45},
    12: {"bias": "Bullish", "reason": "Santa rally + year-end window dressing", "strength": 0.6},
}


class NewsBacktestEngine:
    """Historical news/sentiment backtesting and 2-week market forecasting."""

    def __init__(self):
        self.market_fetcher = MarketDataFetcher()

    def _fetch_market_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch daily OHLCV data via Kite-first pipeline (falls back to yfinance)."""
        end = datetime.now()
        start = end - timedelta(days=days + 30)  # buffer for rolling calcs
        try:
            raw_df = self.market_fetcher.fetch_stock_data(symbol, start_date=start.strftime("%Y-%m-%d"))
            if raw_df is None or raw_df.empty:
                return pd.DataFrame()
            hist = raw_df.copy()
            # Normalize column names to title case for downstream compatibility
            if 'close' in hist.columns and 'Close' not in hist.columns:
                hist = hist.rename(columns={'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
            if 'date' in hist.columns:
                hist.index = pd.to_datetime(hist['date'])
            hist.index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
            hist['daily_return'] = hist['Close'].pct_change() * 100 if 'daily_return' not in hist.columns else hist['daily_return']
            hist['abs_return'] = hist['daily_return'].abs()
            return hist
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            return pd.DataFrame()

    def _compute_sentiment_proxy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build a synthetic sentiment proxy from price action:
        - 5-day EMA of returns (momentum)
        - Volume surge ratio
        - Advance-decline proxy: ratio of up-days in last 5 sessions
        """
        df = df.copy()
        # Momentum: 5-day EMA of daily returns
        df['momentum_5'] = df['daily_return'].ewm(span=5, adjust=False).mean()
        # Longer-term: 20-day EMA
        df['momentum_20'] = df['daily_return'].ewm(span=20, adjust=False).mean()
        # Volume surge: current volume vs 20-day average
        df['vol_sma_20'] = df['Volume'].rolling(20).mean()
        df['vol_surge'] = df['Volume'] / df['vol_sma_20'].replace(0, np.nan)
        # Up-day ratio in rolling 5-day window
        df['up_day'] = (df['daily_return'] > 0).astype(int)
        df['up_ratio_5'] = df['up_day'].rolling(5).mean()

        # Composite sentiment score (-1 to +1 range)
        df['sentiment_score'] = (
            0.5 * np.tanh(df['momentum_5'] / 0.5) +
            0.3 * np.tanh(df['momentum_20'] / 0.3) +
            0.2 * (df['up_ratio_5'] - 0.5) * 2
        ).clip(-1, 1)

        # Labels
        df['sentiment_label'] = 'Neutral'
        df.loc[df['sentiment_score'] > 0.15, 'sentiment_label'] = 'Bullish'
        df.loc[df['sentiment_score'] < -0.15, 'sentiment_label'] = 'Bearish'

        return df.dropna(subset=['sentiment_score'])

    def backtest_sentiment(self, symbol: str = "^NSEI", period: str = "5y",
                           market: str = "NSE") -> Dict:
        """
        Backtest historical sentiment signals against actual market returns.
        Returns win rates, avg returns, monthly patterns, and signal breakdown.
        """
        days = PERIOD_MAP.get(period, 365 * 5)
        df = self._fetch_market_data(symbol, days)
        if df.empty:
            return {"error": "No market data available for this symbol/period."}

        df = self._compute_sentiment_proxy(df)
        if len(df) < 30:
            return {"error": "Insufficient data for backtesting."}

        # Trim to actual requested period
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df.index >= cutoff]

        # Next-day return (what we're predicting)
        df['next_day_return'] = df['daily_return'].shift(-1)
        # Next-week return (5-day forward)
        df['next_week_return'] = df['Close'].pct_change(periods=5).shift(-5) * 100
        df = df.dropna(subset=['next_day_return'])

        # Split by sentiment
        bullish = df[df['sentiment_label'] == 'Bullish']
        bearish = df[df['sentiment_label'] == 'Bearish']
        neutral = df[df['sentiment_label'] == 'Neutral']

        def calc_stats(subset, label):
            if len(subset) == 0:
                return {"label": label, "count": 0, "win_rate": 0, "avg_next_day": 0, "avg_next_week": 0}
            wins = (subset['next_day_return'] > 0).sum()
            return {
                "label": label,
                "count": int(len(subset)),
                "win_rate": round(wins / len(subset) * 100, 1),
                "avg_next_day": round(subset['next_day_return'].mean(), 3),
                "avg_next_week": round(subset['next_week_return'].dropna().mean(), 3) if len(subset['next_week_return'].dropna()) > 0 else 0,
                "max_gain": round(subset['next_day_return'].max(), 3),
                "max_loss": round(subset['next_day_return'].min(), 3),
            }

        stats = {
            "bullish": calc_stats(bullish, "Bullish"),
            "bearish": calc_stats(bearish, "Bearish"),
            "neutral": calc_stats(neutral, "Neutral"),
        }

        # Overall accuracy: did bullish predict up? did bearish predict down?
        bullish_correct = (bullish['next_day_return'] > 0).sum() if len(bullish) > 0 else 0
        bearish_correct = (bearish['next_day_return'] < 0).sum() if len(bearish) > 0 else 0
        total_signals = len(bullish) + len(bearish)
        overall_accuracy = round((bullish_correct + bearish_correct) / total_signals * 100, 1) if total_signals > 0 else 0

        # Monthly seasonality analysis
        df['month'] = df.index.month
        monthly_data = []
        for m in range(1, 13):
            month_df = df[df['month'] == m]
            if len(month_df) == 0:
                continue
            up_days = (month_df['daily_return'] > 0).sum()
            monthly_data.append({
                "month": m,
                "month_name": datetime(2000, m, 1).strftime("%B"),
                "trading_days": int(len(month_df)),
                "win_rate": round(up_days / len(month_df) * 100, 1),
                "avg_return": round(month_df['daily_return'].mean(), 3),
                "avg_sentiment": round(month_df['sentiment_score'].mean(), 3),
                "bullish_days": int((month_df['sentiment_label'] == 'Bullish').sum()),
                "bearish_days": int((month_df['sentiment_label'] == 'Bearish').sum()),
            })

        # Sentiment divergence signals (sentiment flips before price)
        df['prev_sentiment'] = df['sentiment_label'].shift(1)
        divergence_signals = []
        reversals = df[(df['sentiment_label'] != df['prev_sentiment']) & (df['prev_sentiment'].notna())]
        for idx, row in reversals.tail(20).iterrows():
            divergence_signals.append({
                "date": idx.strftime("%Y-%m-%d"),
                "from": row['prev_sentiment'],
                "to": row['sentiment_label'],
                "next_day_return": round(row['next_day_return'], 3) if pd.notna(row['next_day_return']) else None,
                "correct": bool(
                    (row['sentiment_label'] == 'Bullish' and row['next_day_return'] > 0) or
                    (row['sentiment_label'] == 'Bearish' and row['next_day_return'] < 0)
                ) if pd.notna(row['next_day_return']) else None,
            })

        # Current state
        latest = df.iloc[-1] if len(df) > 0 else None
        current_state = None
        if latest is not None:
            current_state = {
                "date": latest.name.strftime("%Y-%m-%d"),
                "sentiment_score": round(float(latest['sentiment_score']), 3),
                "sentiment_label": latest['sentiment_label'],
                "momentum_5": round(float(latest['momentum_5']), 3),
                "momentum_20": round(float(latest['momentum_20']), 3),
                "vol_surge": round(float(latest['vol_surge']), 2) if pd.notna(latest['vol_surge']) else 1.0,
            }

        return {
            "symbol": symbol,
            "period": period,
            "total_trading_days": int(len(df)),
            "overall_accuracy": overall_accuracy,
            "stats": stats,
            "monthly_seasonality": monthly_data,
            "divergence_signals": divergence_signals,
            "current_state": current_state,
        }

    def generate_forecast(self, symbol: str = "^NSEI", market: str = "NSE") -> Dict:
        """
        Generate a 1-month (22 trading-day) forward market forecast.
        Combines: current sentiment, upcoming events, seasonality, momentum, and Nakshatra.
        """
        # Import events engine for integration
        from modules.economic_events import EconomicEventsEngine
        events_engine = EconomicEventsEngine()

        # Try to import nakshatra analyzer for day-level astro data
        try:
            from modules.analysis_engine import NakshatraAnalyzer
            nak_analyzer = NakshatraAnalyzer()
        except Exception:
            nak_analyzer = None

        # Fetch recent data for current state analysis
        df = self._fetch_market_data(symbol, 120)
        if df.empty:
            return {"error": "Could not fetch market data for forecasting."}

        df = self._compute_sentiment_proxy(df)
        if len(df) < 20:
            return {"error": "Insufficient recent data for forecasting."}

        latest = df.iloc[-1]
        current_sentiment = float(latest['sentiment_score'])
        current_momentum_5 = float(latest['momentum_5'])
        current_momentum_20 = float(latest['momentum_20'])
        current_vol_surge = float(latest['vol_surge']) if pd.notna(latest['vol_surge']) else 1.0

        # Trend analysis
        last_5_returns = df['daily_return'].tail(5).tolist()
        last_20_returns = df['daily_return'].tail(20).tolist()
        trend_5d = sum(last_5_returns) / len(last_5_returns) if last_5_returns else 0
        trend_20d = sum(last_20_returns) / len(last_20_returns) if last_20_returns else 0

        # Volatility regime
        recent_vol = df['abs_return'].tail(20).mean()
        hist_vol = df['abs_return'].mean()
        vol_regime = "High" if recent_vol > hist_vol * 1.3 else "Low" if recent_vol < hist_vol * 0.7 else "Normal"

        # Support / Resistance levels
        recent_high = float(df['High'].tail(20).max())
        recent_low = float(df['Low'].tail(20).min())
        current_price = float(latest['Close'])

        # Get upcoming events for the next 35 days (covers 1 month)
        upcoming_events = events_engine.get_upcoming_events(days_ahead=36)
        all_events_in_window = events_engine.get_events_in_window(days_ahead=36)

        # Build date -> events map
        event_date_map = {}
        for ev in all_events_in_window:
            d = ev.get("date", "")
            if d not in event_date_map:
                event_date_map[d] = []
            event_date_map[d].append(ev)

        # Generate day-by-day forecast
        today = datetime.now()
        forecasts = []
        trading_day = 0
        day_offset = 1

        while trading_day < 22:  # ~1 calendar month of trading days
            forecast_date = today + timedelta(days=day_offset)
            # Skip weekends
            if forecast_date.weekday() >= 5:
                day_offset += 1
                continue

            date_str = forecast_date.strftime("%Y-%m-%d")
            month = forecast_date.month
            seasonal = MONTHLY_SEASONAL_BIAS.get(month, {"bias": "Neutral", "reason": "No data", "strength": 0.5})

            # Compute forecast confidence from multiple signals
            signals = []
            scores = []

            # 1. Momentum signal
            if current_momentum_5 > 0.3:
                signals.append("Strong short-term momentum")
                scores.append(0.7)
            elif current_momentum_5 > 0:
                signals.append("Mild positive momentum")
                scores.append(0.55)
            elif current_momentum_5 < -0.3:
                signals.append("Strong negative momentum")
                scores.append(-0.7)
            else:
                signals.append("Mild negative momentum")
                scores.append(-0.5)

            # 2. Sentiment signal
            if current_sentiment > 0.3:
                signals.append("Strong bullish sentiment")
                scores.append(0.65)
            elif current_sentiment > 0:
                signals.append("Mild bullish sentiment")
                scores.append(0.55)
            elif current_sentiment < -0.3:
                signals.append("Strong bearish sentiment")
                scores.append(-0.65)
            else:
                signals.append("Mild bearish sentiment")
                scores.append(-0.55)

            # 3. Seasonal signal
            if seasonal["bias"] == "Bullish":
                signals.append(seasonal["reason"])
                scores.append(seasonal["strength"])
            elif seasonal["bias"] == "Bearish":
                signals.append(seasonal["reason"])
                scores.append(-seasonal["strength"])
            else:
                signals.append(seasonal["reason"])
                scores.append(0)

            # 4. Volume signal
            if current_vol_surge > 1.5:
                signals.append("Volume surge — high conviction move")
                scores.append(0.1 if current_momentum_5 > 0 else -0.1)
            elif current_vol_surge < 0.7:
                signals.append("Low volume — lack of conviction")
                scores.append(0)

            # 5. Mean reversion signal (fade extreme moves)
            if trend_5d > 1.5:
                signals.append("Overextended short-term — mean reversion risk")
                scores.append(-0.3)
            elif trend_5d < -1.5:
                signals.append("Oversold short-term — bounce potential")
                scores.append(0.3)

            # 6. Volatility regime
            if vol_regime == "High":
                signals.append("High volatility regime — wider swings expected")
            elif vol_regime == "Low":
                signals.append("Low volatility — breakout potential")

            # 7. EVENT-DRIVEN SIGNAL — check if any economic event is on this date
            day_events = event_date_map.get(date_str, [])
            event_labels = []
            for ev in day_events:
                is_anni = ev.get("is_anniversary", False)
                if is_anni:
                    event_labels.append(f"📆 {ev['description']}")
                else:
                    bias = ev.get("historical_bias", ev.get("expected_bias", "Volatile"))
                    event_labels.append(f"⚡ {ev['description']}")
                    # Apply event bias to score
                    if "Bullish" in str(bias):
                        signals.append(f"Event: {ev['sub_event']} (historically bullish)")
                        scores.append(0.4)
                    elif "Bearish" in str(bias):
                        signals.append(f"Event: {ev['sub_event']} (historically bearish)")
                        scores.append(-0.4)
                    else:
                        signals.append(f"Event: {ev['sub_event']} (high vol expected)")
                        scores.append(0)

            # Decay confidence for further-out days (gentler slope for 22-day window)
            decay = max(0.35, 1.0 - (trading_day * 0.03))
            avg_score = (sum(scores) / len(scores)) * decay if scores else 0

            # Determine bias
            if avg_score > 0.15:
                bias = "Bullish"
            elif avg_score < -0.15:
                bias = "Bearish"
            else:
                bias = "Neutral"

            confidence = min(85, max(25, int(abs(avg_score) * 100 + 30)))

            # Nakshatra for this date
            nak_name = None
            nak_planet = None
            if nak_analyzer is not None:
                try:
                    nak_info = nak_analyzer.generate_insight_for_date(forecast_date)
                    nak_name = nak_info.get('current_nakshatra')
                    nak_planet = nak_info.get('ruling_planet')
                except Exception:
                    pass

            day_forecast = {
                "date": date_str,
                "day_name": forecast_date.strftime("%A"),
                "day_number": trading_day + 1,
                "bias": bias,
                "confidence": confidence,
                "drivers": signals[:4],  # top 4 drivers
                "score": round(avg_score, 3),
                "week": (trading_day // 5) + 1,
            }
            if nak_name:
                day_forecast["nakshatra"] = nak_name
            if nak_planet:
                day_forecast["ruling_planet"] = nak_planet
            if event_labels:
                day_forecast["events"] = event_labels

            forecasts.append(day_forecast)

            trading_day += 1
            day_offset += 1

        # Overall 1-month outlook
        bullish_days = sum(1 for f in forecasts if f['bias'] == 'Bullish')
        bearish_days = sum(1 for f in forecasts if f['bias'] == 'Bearish')
        neutral_days = sum(1 for f in forecasts if f['bias'] == 'Neutral')
        avg_confidence = sum(f['confidence'] for f in forecasts) / len(forecasts) if forecasts else 0

        if bullish_days > bearish_days + 4:
            overall_bias = "Bullish"
        elif bearish_days > bullish_days + 4:
            overall_bias = "Bearish"
        else:
            overall_bias = "Neutral"

        outlook = {
            "overall_bias": overall_bias,
            "bullish_days": bullish_days,
            "bearish_days": bearish_days,
            "neutral_days": neutral_days,
            "avg_confidence": round(avg_confidence, 1),
            "vol_regime": vol_regime,
            "current_price": round(current_price, 2),
            "support": round(recent_low, 2),
            "resistance": round(recent_high, 2),
        }

        return {
            "symbol": symbol,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "current_state": {
                "sentiment_score": round(current_sentiment, 3),
                "sentiment_label": "Bullish" if current_sentiment > 0.15 else "Bearish" if current_sentiment < -0.15 else "Neutral",
                "momentum_5d": round(current_momentum_5, 3),
                "momentum_20d": round(current_momentum_20, 3),
                "vol_surge": round(current_vol_surge, 2),
                "trend_5d": round(trend_5d, 3),
                "trend_20d": round(trend_20d, 3),
            },
            "outlook": outlook,
            "daily_forecasts": forecasts,
            "upcoming_events": [
                {
                    "date": ev["date"],
                    "category": ev["category"],
                    "sub_event": ev["sub_event"],
                    "description": ev["description"],
                    "days_away": ev["days_away"],
                    "urgency": ev["urgency"],
                    "emoji": ev.get("emoji", "📅"),
                }
                for ev in upcoming_events
            ],
        }

