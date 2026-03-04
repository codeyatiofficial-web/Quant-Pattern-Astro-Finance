"""
Enhanced Technical Analysis Engine
Harmonic Patterns (Gartley, Bat, Butterfly, Crab, Cypher, ABCD, 3-Drive)
Full Fibonacci Suite + Pivots, 25+ Japanese Candlestick Patterns,
Volume Confirmation (OBV, VWAP, Volume Ratio), RSI/MACD/Bollinger/ATR,
Kite-first multi-timeframe data, 1-Week Prediction Band, Dynamic Backtesting
"""

import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz

from modules.market_data import MarketDataFetcher
from modules.moon_calculator import MoonCalculator

IST = pytz.timezone('Asia/Kolkata')


# ─── Fibonacci Ratios ────────────────────────────────────────────────────────
FIB_RATIOS = {
    "0.236": 0.236, "0.382": 0.382, "0.500": 0.500, "0.618": 0.618,
    "0.786": 0.786, "0.886": 0.886, "1.000": 1.000,
    "1.272": 1.272, "1.414": 1.414, "1.618": 1.618,
    "2.000": 2.000, "2.618": 2.618, "3.618": 3.618, "4.236": 4.236,
}

# ─── Harmonic Pattern Definitions (B and D ratios of XA) ─────────────────────
# Format: {name: {B_low, B_high, D_low, D_high, D_ext_used}}
HARMONIC_DEFS = {
    "Gartley":  {"b": (0.618, 0.618), "d": (0.786, 0.786)},
    "Bat":      {"b": (0.382, 0.500), "d": (0.886, 0.886)},
    "Butterfly":{"b": (0.786, 0.786), "d": (1.272, 1.618)},
    "Crab":     {"b": (0.382, 0.618), "d": (1.618, 1.618)},
    "Cypher":   {"b": (0.382, 0.618), "d": (0.786, 0.786)},   # vs XC
    "ABCD":     {"b": (None, None),   "d": (1.272, 1.618)},   # pure equal leg
    "3Drive":   {"b": (0.618, 0.618), "d": (1.272, 1.618)},
}


class TechnicalAnalyzer:
    """Quantitative pattern detection, live scanning, and forecasting engine."""

    def __init__(self):
        self.market_fetcher = MarketDataFetcher()
        self.moon_calc = MoonCalculator()
        # Kite client lazy-imported to avoid mandatory dependency
        self._kite = None

    def _get_kite(self):
        if self._kite is None:
            try:
                from modules.kite_client import KiteDataClient
                self._kite = KiteDataClient()
            except Exception:
                self._kite = None
        return self._kite

    # ═══════════════════════════════════════════════════════════════════════
    #  DATA FETCHING — Kite first, yfinance fallback
    # ═══════════════════════════════════════════════════════════════════════

    def _fetch_with_kite_or_fallback(self, symbol: str, interval: str,
                                      period_str: str, market: str,
                                      days_back: int = 3000) -> pd.DataFrame:
        """
        Try Kite histogram first (authenticated, high-quality data).
        Falls back to yfinance / MarketDataFetcher automatically.
        """
        KITE_INTERVAL_MAP = {
            "1m": "minute", "3m": "3minute", "5m": "5minute",
            "15m": "15minute", "30m": "30minute", "60m": "60minute",
            "1h": "60minute", "1d": "day", "1wk": "day"
        }
        kite = self._get_kite()
        if kite and kite.is_authenticated():
            try:
                kite_interval = KITE_INTERVAL_MAP.get(interval, "60minute")
                df = kite.fetch_historical_data(symbol, interval=kite_interval, days_back=days_back)
                if not df.empty and len(df) > 50:
                    # Standardise column names
                    df = df.rename(columns={
                        "datetime": "date", "open": "open", "high": "high",
                        "low": "low", "close": "close", "volume": "volume"
                    })
                    return df
            except Exception as e:
                pass  # silent fallback

        # yfinance fallback
        if interval in ["1d", "1wk"]:
            start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            df = self.market_fetcher.fetch_stock_data(symbol, start_date=start, market=market)
        else:
            fetch_days = min(days_back, 730 if interval in ["60m", "1h"] else 60)
            fetch_period = f"{fetch_days}d"
            df = self.market_fetcher.fetch_intraday_data(symbol, period=fetch_period,
                                                          interval=interval, market=market)
        if df is not None:
            df.columns = [c.lower() for c in df.columns]
        return df if df is not None else pd.DataFrame()

    # ═══════════════════════════════════════════════════════════════════════
    #  MAIN SCAN ENTRY POINT
    # ═══════════════════════════════════════════════════════════════════════

    def run_multi_timeframe_scan(self, symbol: str, market: str = "NSE",
                                  historical_period: str = "5y") -> Dict:
        """Run comprehensive scan across 6 timeframes. Returns structured dict."""
        years = int(historical_period.replace("y", "").replace("Max", "20")) if any(
            c.isdigit() for c in historical_period) else 5

        TIMEFRAMES = [
            {"label": "1m",     "interval": "1m",   "days_back": 5},
            {"label": "5m",     "interval": "5m",   "days_back": 30},
            {"label": "15m",    "interval": "15m",  "days_back": 60},
            {"label": "1h",     "interval": "60m",  "days_back": 400},
            {"label": "Daily",  "interval": "1d",   "days_back": max(3650, years * 365)},
            {"label": "Weekly", "interval": "1wk",  "days_back": max(7300, years * 365)},
        ]

        scans = {}
        for tf in TIMEFRAMES:
            try:
                df = self._fetch_with_kite_or_fallback(
                    symbol, tf["interval"], "", market, tf["days_back"])
                if df is None or df.empty or len(df) < 50:
                    scans[tf["label"]] = {"error": "Insufficient data", "patterns": []}
                    continue
                df.columns = [c.lower() for c in df.columns]
                result = self._analyse_df(df, tf["label"], symbol, years)
                scans[tf["label"]] = result
            except Exception as e:
                scans[tf["label"]] = {"error": str(e)[:80], "patterns": []}

        # 1-week prediction band from Daily tf
        prediction = self._predict_week(
            self._fetch_with_kite_or_fallback(symbol, "1d", "", market, max(3650, years * 365)))

        # Fibonacci levels from same daily df
        daily_df = self._fetch_with_kite_or_fallback(symbol, "1d", "", market, 365)
        fib_levels = self._fibonacci_levels(daily_df)

        # Astro triggers
        astro = self.get_upcoming_astro_triggers()

        return {
            "symbol": symbol,
            "scans":  scans,
            "fibonacci": fib_levels,
            "week_prediction": prediction,
            "astro_confluence": astro,
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  ANALYSE A SINGLE DATAFRAME
    # ═══════════════════════════════════════════════════════════════════════

    def _analyse_df(self, df: pd.DataFrame, label: str, symbol: str, years: int) -> Dict:
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = 0.0

        # ── Indicators ───────────────────────────────────────────────────
        df["rsi"] = self._rsi(df["close"])
        df["macd"], df["macd_sig"] = self._macd(df["close"])
        df["boll_mid"], df["boll_up"], df["boll_dn"] = self._bollinger(df["close"])
        df["atr"] = self._atr(df)
        df["obv"] = self._obv(df)
        df["vwap"] = self._vwap(df)
        df["vol_20ma"] = df["volume"].rolling(20).mean().fillna(0)
        df["vol_ratio"] = (df["volume"] / df["vol_20ma"].replace(0, 1)).fillna(1)

        latest = df.iloc[-1]
        current_price = float(latest["close"])

        # ── Volume confirmation ──────────────────────────────────────────
        vol_ratio = float(latest.get("vol_ratio", 1.0))
        rsi_val = float(latest["rsi"]) if pd.notna(latest["rsi"]) else 50.0
        macd_bull = float(latest["macd"]) > float(latest["macd_sig"]) if pd.notna(latest["macd"]) else False
        price_above_vwap = current_price > float(latest["vwap"]) if pd.notna(latest["vwap"]) and latest["vwap"] != 0 else None
        obv_rising = bool(df["obv"].diff().iloc[-3:].mean() > 0)

        vol_confirms = vol_ratio >= 1.3
        vol_label = f"{'✅ Strong' if vol_ratio >= 1.5 else '⚠️ Moderate' if vol_ratio >= 1.3 else '❌ Weak'} ({vol_ratio:.1f}x avg)"

        # ── Pattern Detection ────────────────────────────────────────────
        harmonic = self._detect_harmonics(df, current_price)
        candle   = self._detect_candlestick_patterns(df)
        chart    = self._detect_chart_patterns(df, current_price)

        # Priority: harmonic > chart > candle
        patterns = []

        def _enrich(pat: Dict, source: str) -> Dict:
            bias = "Bullish" if any(k in pat.get("name", "") for k in ["Bull", "Morning", "Hammer", "Soldier", "Piercing", "Bottom", "Inverted", "Tweezer Bot", "Kicker Up"]) else \
                   "Bearish" if any(k in pat.get("name", "") for k in ["Bear", "Evening", "Shooting", "Hanging", "Crow", "Dark Cloud", "Top", "Kicker Dn"]) else "Neutral"
            vol_ok = vol_confirms
            return {**pat, "source": source, "bias": bias, "vol_confirms": vol_ok,
                    "vol_label": vol_label, "rsi": round(rsi_val, 1),
                    "macd_bull": macd_bull, "obv_rising": obv_rising,
                    "price_above_vwap": price_above_vwap}

        if harmonic.get("name") not in ["No Swing", "Consolidation", "Bull Flag", "Bear Flag"]:
            patterns.append(_enrich(harmonic, "Harmonic"))
        if chart.get("name") not in ["Consolidation", "Ranging"]:
            patterns.append(_enrich(chart, "Chart"))
        if candle.get("name") not in ["Consolidation", "No Signal"]:
            patterns.append(_enrich(candle, "Candlestick"))

        # ── Backtest ─────────────────────────────────────────────────────
        bt_results = []
        for pat in patterns[:3]:
            bt = self._backtest_pattern(df, pat.get("name", ""), years)
            pat_run = {**pat, **bt}
            bt_results.append(pat_run)

        # Current indicators summary
        indicators = {
            "rsi": round(rsi_val, 1),
            "rsi_signal": "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral",
            "macd_bull": macd_bull,
            "boll_position": round((current_price - float(latest["boll_dn"])) /
                                   max(float(latest["boll_up"]) - float(latest["boll_dn"]), 0.001) * 100, 1)
                             if pd.notna(latest["boll_up"]) else 50.0,
            "atr": round(float(latest["atr"]), 2) if pd.notna(latest["atr"]) else 0,
            "vol_ratio": round(vol_ratio, 2),
            "obv_rising": obv_rising,
            "price_above_vwap": price_above_vwap,
            "current_price": round(current_price, 2),
        }

        # Data transparency
        date_col = df['date'] if 'date' in df.columns else pd.Series(df.index)
        try:
            date_range = f"{pd.to_datetime(date_col.iloc[0]).strftime('%Y-%m-%d')} → {pd.to_datetime(date_col.iloc[-1]).strftime('%Y-%m-%d')}"
        except Exception:
            date_range = "—"

        return {
            "patterns": bt_results,
            "indicators": indicators,
            "vol_label": vol_label,
            "total_candles": len(df),
            "data_range": date_range,
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  HARMONIC PATTERN DETECTION — X, A, B, C → D PRZ
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_harmonics(self, df: pd.DataFrame, current_price: float) -> Dict:
        prices = df["close"].values
        highs  = df["high"].values
        lows   = df["low"].values

        order = max(3, len(prices) // 30)
        max_idx = argrelextrema(highs,  np.greater_equal, order=order)[0]
        min_idx = argrelextrema(lows,   np.less_equal,    order=order)[0]

        swings = sorted([(i, "H", highs[i]) for i in max_idx] +
                        [(i, "L", lows[i])  for i in min_idx])

        if len(swings) < 5:
            return {"name": "No Swing", "status": "Monitoring"}

        # Take last 5 swing points as X, A, B, C, (current=D candidate)
        pts = swings[-5:]
        X = pts[0][2]; A = pts[1][2]; B = pts[2][2]; C = pts[3][2]
        D = current_price

        XA = A - X
        if abs(XA) < 0.001:
            return {"name": "Consolidation", "status": "Ranging"}

        AB = B - A
        BC = C - B
        # CD is in progress — D = current
        CD = D - C

        ab_xa = abs(AB / XA)
        bc_ab = abs(BC / AB) if abs(AB) > 0.001 else 0
        cd_bc = abs(CD / BC) if abs(BC) > 0.001 else 0
        ad_xa = abs((D - A) / XA) if abs(XA) > 0.001 else 0

        direction = "Bullish" if XA > 0 else "Bearish"

        def _match(name, b_ratio, d_xa_ratio, tol=0.05):
            b_lo, b_hi = b_ratio
            d_lo, d_hi = d_xa_ratio
            b_ok = (b_lo is None) or (b_lo - tol <= ab_xa <= b_hi + tol)
            d_ok = d_lo - tol <= abs(D - X) / abs(XA) <= d_hi + tol if abs(XA) > 0 else False
            return b_ok and d_ok

        matched = None
        for pname, pdef in HARMONIC_DEFS.items():
            b_range = pdef["b"]
            d_range = pdef["d"]
            if b_range[0] is None:  # ABCD — no B condition, check CD/BC equal
                if 1.2 <= cd_bc <= 1.65:
                    matched = pname; break
                continue
            if _match(pname, b_range, d_range):
                matched = pname; break

        if not matched:
            # Fallback to trend flag
            return {
                "name": f"{direction} Trend",
                "status": "Trending",
                "completion_pct": 50.0,
                "prz": f"{C:.2f}",
                "target": f"{A:.2f}",
                "stop": f"{X:.2f}",
            }

        # Compute PRZ (D completion level)
        d_def = HARMONIC_DEFS[matched]["d"]
        d_mid_ratio = (d_def[0] + d_def[1]) / 2
        prz = X + d_mid_ratio * XA

        # Target / Stop
        if direction == "Bullish":
            target = A + 0.382 * abs(XA)
            stop   = prz - 0.1 * abs(XA)
        else:
            target = A - 0.382 * abs(XA)
            stop   = prz + 0.1 * abs(XA)

        comp = min(abs(D - C) / max(abs(prz - C), 0.001) * 100, 100)

        return {
            "name": f"{direction} {matched}",
            "pattern_name": f"{direction} {matched}",
            "status": "Completing" if comp > 75 else "Forming",
            "completion_pct": round(comp, 1),
            "prz": f"{prz:.2f}",
            "target": f"{target:.2f}",
            "stop": f"{stop:.2f}",
            "ratios": {"AB/XA": round(ab_xa, 3), "BC/AB": round(bc_ab, 3), "AD/XA": round(ad_xa, 3)},
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  25+ JAPANESE CANDLESTICK PATTERNS
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        if len(df) < 5:
            return {"name": "No Signal", "status": "Insufficient data"}

        d = df.copy()
        d["body"]  = abs(d["close"] - d["open"])
        d["bull"]  = d["close"] > d["open"]
        d["uwick"] = d["high"] - d[["open", "close"]].max(axis=1)
        d["lwick"] = d[["open", "close"]].min(axis=1) - d["low"]
        d["range"] = (d["high"] - d["low"]).replace(0, 0.0001)
        d["body_ratio"] = d["body"] / d["range"]

        avg_body = d["body"].rolling(10).mean()
        d["rel_body"] = d["body"] / avg_body.replace(0, 0.0001)

        c = [d.iloc[-i - 1] for i in range(5)]  # c[0]=latest, c[1]=prev, ...
        ab = avg_body.iloc[-1]
        ab = ab if pd.notna(ab) and ab > 0 else 1.0

        downtrend = c[2]["close"] > c[0]["close"]
        uptrend   = c[2]["close"] < c[0]["close"]

        def doji(x):   return x["body"] <= x["range"] * 0.25
        def big(x):    return x["body"] >= ab * 0.8
        def long_lw(x): return x["lwick"] >= x["body"] * 1.5 and x["uwick"] <= x["body"] * 0.5
        def long_uw(x): return x["uwick"] >= x["body"] * 1.5 and x["lwick"] <= x["body"] * 0.5
        def gap_up(a, b): return a["open"] > b["close"]
        def gap_dn(a, b): return a["open"] < b["close"]

        detections = []

        # ── 3-Candle ─────────────────────────────────────────────────────
        if (c[2]["bull"] and big(c[2]) and doji(c[1]) and not c[0]["bull"] and
                big(c[0]) and c[0]["close"] < (c[2]["open"] + c[2]["close"]) / 2):
            detections.append(("Bearish Evening Star", False))

        if (not c[2]["bull"] and big(c[2]) and doji(c[1]) and c[0]["bull"] and
                big(c[0]) and c[0]["close"] > (c[2]["open"] + c[2]["close"]) / 2):
            detections.append(("Bullish Morning Star", True))

        if (not c[2]["bull"] and not c[1]["bull"] and not c[0]["bull"] and
                c[0]["close"] < c[1]["close"] < c[2]["close"] and
                big(c[0]) and big(c[1]) and big(c[2])):
            detections.append(("Bearish Three Black Crows", False))

        if (c[2]["bull"] and c[1]["bull"] and c[0]["bull"] and
                c[0]["close"] > c[1]["close"] > c[2]["close"] and
                big(c[0]) and big(c[1]) and big(c[2])):
            detections.append(("Bullish Three White Soldiers", True))

        if (c[2]["bull"] and big(c[2]) and c[1]["bull"] and c[0]["bull"] and
                c[0]["close"] > c[1]["close"] and c[0]["open"] > c[2]["open"] and
                c[0]["close"] > c[2]["close"] * 1.003):
            detections.append(("Bullish Marubozu Continuation", True))

        if (not c[2]["bull"] and big(c[2]) and not c[1]["bull"] and not c[0]["bull"] and
                c[0]["close"] < c[1]["close"] and c[0]["close"] < c[2]["close"] * 0.997):
            detections.append(("Bearish Marubozu Continuation", False))

        # Tri-star doji
        if doji(c[0]) and doji(c[1]) and doji(c[2]):
            if downtrend:
                detections.append(("Bullish Tri-Star Doji", True))
            elif uptrend:
                detections.append(("Bearish Tri-Star Doji", False))

        # ── 2-Candle ─────────────────────────────────────────────────────
        if uptrend and c[1]["bull"] and not c[0]["bull"] and c[0]["open"] > c[1]["close"] and c[0]["close"] < c[1]["open"]:
            detections.append(("Bearish Engulfing", False))

        if downtrend and not c[1]["bull"] and c[0]["bull"] and c[0]["open"] < c[1]["close"] and c[0]["close"] > c[1]["open"]:
            detections.append(("Bullish Engulfing", True))

        if uptrend and c[1]["bull"] and not c[0]["bull"] and c[0]["open"] < c[1]["close"] and c[0]["close"] > c[1]["open"]:
            detections.append(("Bearish Harami", False))

        if downtrend and not c[1]["bull"] and c[0]["bull"] and c[0]["open"] > c[1]["close"] and c[0]["close"] < c[1]["open"]:
            detections.append(("Bullish Harami", True))

        if downtrend and not c[1]["bull"] and c[0]["bull"] and c[0]["open"] < c[1]["low"] and c[0]["close"] > (c[1]["open"] + c[1]["close"]) / 2:
            detections.append(("Bullish Piercing Line", True))

        if uptrend and c[1]["bull"] and not c[0]["bull"] and c[0]["open"] > c[1]["high"] and c[0]["close"] < (c[1]["open"] + c[1]["close"]) / 2:
            detections.append(("Bearish Dark Cloud Cover", False))

        # Tweezer tops / bottoms
        if uptrend and abs(c[0]["high"] - c[1]["high"]) / max(c[0]["range"], 0.001) < 0.03:
            detections.append(("Bearish Tweezer Top", False))

        if downtrend and abs(c[0]["low"] - c[1]["low"]) / max(c[0]["range"], 0.001) < 0.03:
            detections.append(("Bullish Tweezer Bottom", True))

        # Kicker pattern
        if c[1]["bull"] and not c[0]["bull"] and gap_dn(c[0], c[1]) and big(c[0]) and big(c[1]):
            detections.append(("Bearish Kicker", False))
        if not c[1]["bull"] and c[0]["bull"] and gap_up(c[0], c[1]) and big(c[0]) and big(c[1]):
            detections.append(("Bullish Kicker", True))

        # ── 1-Candle ─────────────────────────────────────────────────────
        if long_lw(c[0]) and downtrend:
            detections.append(("Bullish Hammer", True))
        if long_lw(c[0]) and uptrend:
            detections.append(("Bearish Hanging Man", False))
        if long_uw(c[0]) and uptrend:
            detections.append(("Bearish Shooting Star", False))
        if long_uw(c[0]) and downtrend:
            detections.append(("Bullish Inverted Hammer", True))

        if doji(c[0]):
            # Dragonfly / Gravestone Doji
            if c[0]["lwick"] > c[0]["range"] * 0.6 and downtrend:
                detections.append(("Bullish Dragonfly Doji", True))
            elif c[0]["uwick"] > c[0]["range"] * 0.6 and uptrend:
                detections.append(("Bearish Gravestone Doji", False))
            elif uptrend:
                detections.append(("Bearish Top Doji", False))
            elif downtrend:
                detections.append(("Bullish Bottom Doji", True))

        # Spinning top
        if 0.2 < c[0]["body_ratio"] < 0.45 and c[0]["uwick"] > ab * 0.3 and c[0]["lwick"] > ab * 0.3:
            detections.append(("Spinning Top", None))  # Neutral

        # Belt Hold
        if c[0]["bull"] and c[0]["open"] <= min(c[1]["open"], c[1]["close"]) * 1.002 and big(c[0]) and c[0]["lwick"] < ab * 0.15:
            detections.append(("Bullish Belt Hold", True))
        if not c[0]["bull"] and c[0]["open"] >= max(c[1]["open"], c[1]["close"]) * 0.998 and big(c[0]) and c[0]["uwick"] < ab * 0.15:
            detections.append(("Bearish Belt Hold", False))

        if not detections:
            return {"name": "No Signal", "status": "Neutral"}

        name, is_bull = detections[0]
        risk_ref = max(c[0]["range"], c[1]["range"], ab * 0.5)

        if is_bull is True:
            prz  = float(c[0]["close"])
            stop = float(min(c[0]["low"], c[1]["low"])) * 0.998
            tgt  = prz + (prz - stop) * 2.0
        elif is_bull is False:
            prz  = float(c[0]["close"])
            stop = float(max(c[0]["high"], c[1]["high"])) * 1.002
            tgt  = prz - (stop - prz) * 2.0
        else:  # Neutral — spinning top / doji
            prz  = float(c[0]["close"])
            stop = float(c[0]["low"])
            tgt  = float(c[0]["high"])

        return {
            "name": name,
            "pattern_name": name,
            "status": "Triggered",
            "completion_pct": 100.0,
            "prz": f"{prz:.2f}",
            "target": f"{tgt:.2f}",
            "stop": f"{stop:.2f}",
            "all_detected": [d[0] for d in detections],
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  CHART PATTERNS (Structural)
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_chart_patterns(self, df: pd.DataFrame, current_price: float) -> Dict:
        prices = df["close"].values
        highs  = df["high"].values
        lows   = df["low"].values

        if len(prices) < 30:
            return {"name": "Consolidation", "status": "Ranging"}

        order = max(3, len(prices) // 15)
        max_i = argrelextrema(highs, np.greater_equal, order=order)[0]
        min_i = argrelextrema(lows,  np.less_equal,    order=order)[0]

        if len(max_i) < 2 or len(min_i) < 2:
            return {"name": "Consolidation", "status": "Ranging"}

        H = highs[max_i[-min(len(max_i), 3):]]
        L = lows[min_i[-min(len(min_i), 3):]]

        tol = 0.015

        def pct_diff(a, b): return abs(a - b) / max(a, 0.001)

        # Double Top
        if len(H) >= 2 and pct_diff(H[-1], H[-2]) < tol:
            neckline = L[-1] if len(L) >= 1 else current_price * 0.97
            target_dt = neckline - (H[-1] - neckline)
            return {"name": "Double Top", "status": "Forming", "completion_pct": 80.0,
                    "prz": f"{neckline:.2f}", "target": f"{target_dt:.2f}", "stop": f"{H[-1] * 1.005:.2f}"}

        # Double Bottom
        if len(L) >= 2 and pct_diff(L[-1], L[-2]) < tol:
            neckline_db = H[-1] if len(H) >= 1 else current_price * 1.03
            target_db = neckline_db + (neckline_db - L[-1])
            return {"name": "Double Bottom", "status": "Forming", "completion_pct": 80.0,
                    "prz": f"{neckline_db:.2f}", "target": f"{target_db:.2f}", "stop": f"{L[-1] * 0.995:.2f}"}

        # Head & Shoulders
        if len(H) >= 3:
            if H[-2] > H[-1] and H[-2] > H[-3] and pct_diff(H[-1], H[-3]) < tol * 2:
                ns_h = min(L[-2], L[-1]) if len(L) >= 2 else current_price * 0.97
                return {"name": "Head & Shoulders", "status": "Right Shoulder",
                        "completion_pct": 85.0, "prz": f"{ns_h:.2f}",
                        "target": f"{ns_h - (H[-2] - ns_h):.2f}", "stop": f"{H[-2] * 1.002:.2f}"}

        # Inverse H&S
        if len(L) >= 3:
            if L[-2] < L[-1] and L[-2] < L[-3] and pct_diff(L[-1], L[-3]) < tol * 2:
                ns_i = max(H[-2], H[-1]) if len(H) >= 2 else current_price * 1.03
                return {"name": "Inverse Head & Shoulders", "status": "Right Shoulder",
                        "completion_pct": 85.0, "prz": f"{ns_i:.2f}",
                        "target": f"{ns_i + (ns_i - L[-2]):.2f}", "stop": f"{L[-2] * 0.998:.2f}"}

        # Ascending / Descending Triangle
        if len(H) >= 2 and len(L) >= 2:
            slope_h = (H[-1] - H[-2]) / max(H[-2], 0.001)
            slope_l = (L[-1] - L[-2]) / max(L[-2], 0.001)
            if abs(slope_h) < tol and slope_l > 0.005:
                return {"name": "Ascending Triangle", "status": "Approaching Resistance",
                        "completion_pct": 70.0, "prz": f"{H[-1]:.2f}",
                        "target": f"{H[-1] + (H[-1] - L[-1]):.2f}", "stop": f"{L[-1] * 0.997:.2f}"}
            if abs(slope_l) < tol and slope_h < -0.005:
                return {"name": "Descending Triangle", "status": "Approaching Support",
                        "completion_pct": 70.0, "prz": f"{L[-1]:.2f}",
                        "target": f"{L[-1] - (H[-1] - L[-1]):.2f}", "stop": f"{H[-1] * 1.003:.2f}"}

        # Rising / Falling Wedge
        if len(H) >= 2 and len(L) >= 2:
            if slope_h > 0 and slope_l > 0 and slope_l > slope_h:
                return {"name": "Rising Wedge (Bearish)", "status": "Constricting",
                        "completion_pct": 65.0, "prz": f"{current_price:.2f}",
                        "target": f"{L[-1]:.2f}", "stop": f"{H[-1] * 1.003:.2f}"}
            if slope_h < 0 and slope_l < 0 and slope_h < slope_l:
                return {"name": "Falling Wedge (Bullish)", "status": "Constricting",
                        "completion_pct": 65.0, "prz": f"{current_price:.2f}",
                        "target": f"{H[-1]:.2f}", "stop": f"{L[-1] * 0.997:.2f}"}

        return {"name": "Consolidation", "status": "Ranging"}

    # ═══════════════════════════════════════════════════════════════════════
    #  FIBONACCI LEVELS
    # ═══════════════════════════════════════════════════════════════════════

    def _fibonacci_levels(self, df: pd.DataFrame, lookback: int = 252) -> Dict:
        if df is None or df.empty:
            return {}
        df.columns = [c.lower() for c in df.columns]
        recent = df.tail(lookback)
        swing_high = float(recent["high"].max())
        swing_low  = float(recent["low"].min())
        diff = swing_high - swing_low

        levels = {}
        # Retracement from high → low
        for name, ratio in FIB_RATIOS.items():
            if ratio <= 1.0:
                levels[f"Ret_{name}"] = round(swing_high - diff * ratio, 2)
        # Extension from low → high (above swing high)
        for name, ratio in FIB_RATIOS.items():
            if ratio > 1.0:
                levels[f"Ext_{name}"] = round(swing_low + diff * ratio, 2)

        # Pivot levels (standard floor trader pivots)
        last = df.iloc[-1]
        P  = (float(last["high"]) + float(last["low"]) + float(last["close"])) / 3
        R1 = 2 * P - float(last["low"])
        S1 = 2 * P - float(last["high"])
        R2 = P + (float(last["high"]) - float(last["low"]))
        S2 = P - (float(last["high"]) - float(last["low"]))

        return {
            "swing_high": swing_high, "swing_low": swing_low,
            "fib_levels": levels,
            "pivots": {"P": round(P, 2), "R1": round(R1, 2), "R2": round(R2, 2),
                       "S1": round(S1, 2), "S2": round(S2, 2)},
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  1-WEEK PRICE PREDICTION
    # ═══════════════════════════════════════════════════════════════════════

    def _predict_week(self, df: pd.DataFrame) -> Dict:
        """
        Predicts next 5 trading days using:
        - 5-day momentum (linear regression slope)
        - ATR-based volatility band
        - Bollinger Band position
        - RSI momentum weight
        """
        if df is None or df.empty or len(df) < 30:
            return {"error": "Insufficient data for prediction"}

        df.columns = [c.lower() for c in df.columns]
        df["rsi"] = self._rsi(df["close"])
        df["atr"] = self._atr(df)
        df["boll_mid"], df["boll_up"], df["boll_dn"] = self._bollinger(df["close"])

        last_price = float(df["close"].iloc[-1])
        atr_val    = float(df["atr"].iloc[-1]) if pd.notna(df["atr"].iloc[-1]) else last_price * 0.01
        rsi_val    = float(df["rsi"].iloc[-1]) if pd.notna(df["rsi"].iloc[-1]) else 50.0

        # 5-day momentum slope (normalized)
        y = df["close"].values[-10:]
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        slope_pct = slope / last_price * 100  # daily % direction

        # Bias from RSI
        rsi_bias = (rsi_val - 50) / 50 * 0.3  # -0.3 to +0.3

        # Combined daily drift estimate
        daily_drift = slope_pct / 100 * 0.5 + rsi_bias / 100 * 0.5

        days = []
        for i in range(1, 6):
            proj = last_price * (1 + daily_drift * i)
            upper = proj + atr_val * i * 0.7
            lower = proj - atr_val * i * 0.7
            days.append({
                "day": f"Day {i}",
                "projected": round(proj, 2),
                "upper_band": round(upper, 2),
                "lower_band": round(lower, 2),
            })

        bias = "Bullish" if daily_drift > 0.001 else "Bearish" if daily_drift < -0.001 else "Neutral"
        return {
            "current_price": round(last_price, 2),
            "daily_drift_pct": round(daily_drift * 100, 3),
            "atr": round(atr_val, 2),
            "bias": bias,
            "rsi": round(rsi_val, 1),
            "days": days,
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  BACKTESTING
    # ═══════════════════════════════════════════════════════════════════════

    def _backtest_pattern(self, df: pd.DataFrame, pattern_name: str, years: int = 5) -> Dict:
        """Walk-forward backtest of a named pattern across historical data."""
        default = {"wins": 0, "losses": 0, "win_rate": 0.0, "avg_return": 0.0,
                   "last_seen": "—", "last_result": "—", "trades": [],
                   "sharpe_like": 0.0, "max_drawdown": 0.0}
        if not pattern_name or pattern_name in ["No Signal", "Consolidation", "No Swing", "Ranging"]:
            return default

        cutoff = datetime.now() - timedelta(days=years * 365)
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        if "date" in df.columns:
            df.index = pd.to_datetime(df["date"])
        elif not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                return default

        try:
            if df.index.tz is not None:
                cutoff = cutoff.replace(tzinfo=df.index.tz)
        except Exception:
            pass

        df = df[df.index >= cutoff].copy()
        if len(df) < 60:
            return default

        is_bull = any(k in pattern_name for k in ["Bull", "Morning", "Hammer", "Soldier", "Piercing",
                                                    "Bottom", "Inverted", "Ascending", "Inverse"])
        prices = df["close"].values
        dates  = df.index

        trades = []
        wins = losses = 0
        pnl_list = []
        equity = [1.0]

        step = 1
        i = 30
        while i < len(df) - 15:
            window = df.iloc[:i]
            cp = prices[i - 1]
            dt_str = dates[i - 1].strftime("%Y-%m-%d")

            # Match pattern
            pat = {}
            try:
                if "Harmonic" in pattern_name or "Trend" in pattern_name or any(k in pattern_name for k in
                        ["Gartley", "Bat", "Butterfly", "Crab", "Cypher", "ABCD"]):
                    pat = self._detect_harmonics(window, cp)
                elif any(k in pattern_name for k in
                         ["Engulfing", "Hammer", "Doji", "Star", "Crow", "Soldier", "Harami",
                          "Cloud", "Piercing", "Tweezer", "Kicker", "Marubozu"]):
                    pat = self._detect_candlestick_patterns(window)
                else:
                    pat = self._detect_chart_patterns(window, cp)
            except Exception:
                i += step; continue

            if pat.get("name", "") == pattern_name:
                try:
                    prz  = float(pat.get("prz", cp))
                    tgt  = float(pat.get("target", cp))
                    stop = float(pat.get("stop", cp))
                    if prz == 0 or tgt == 0 or stop == 0 or abs(tgt - prz) < 0.001:
                        i += step; continue

                    future = prices[i: min(i + 30, len(prices))]
                    result = exit_p = None
                    for fp in future:
                        if is_bull:
                            if fp >= tgt: result = "Win";  exit_p = fp; break
                            if fp <= stop: result = "Loss"; exit_p = fp; break
                        else:
                            if fp <= tgt: result = "Win";  exit_p = fp; break
                            if fp >= stop: result = "Loss"; exit_p = fp; break

                    if result is None and len(future):
                        exit_p = future[-1]
                        result = "Win" if (is_bull and exit_p > prz) or (not is_bull and exit_p < prz) else "Loss"

                    if result and exit_p:
                        pnl = (exit_p - cp) / cp * 100 * (1 if is_bull else -1)
                        pnl_list.append(pnl)
                        equity.append(equity[-1] * (1 + pnl / 100))
                        if result == "Win": wins += 1
                        else: losses += 1
                        trades.append({"date": dt_str, "result": result,
                                       "return": f"{'+'if pnl>0 else''}{pnl:.2f}%"})
                        i += 20
                        continue
                except Exception:
                    pass
            i += step

        total = wins + losses
        wr = wins / total * 100 if total > 0 else 0.0
        avg_ret = float(np.mean(pnl_list)) if pnl_list else 0.0
        std_ret = float(np.std(pnl_list)) if len(pnl_list) > 1 else 1.0
        sharpe  = avg_ret / std_ret * np.sqrt(252) if std_ret > 0 else 0.0

        # Max drawdown
        eq = np.array(equity)
        peak = np.maximum.accumulate(eq)
        dd   = (eq - peak) / peak
        max_dd = float(dd.min() * 100) if len(dd) > 1 else 0.0

        last_trade = trades[-1] if trades else {}

        return {
            "wins": wins, "losses": losses,
            "win_rate": round(wr, 1),
            "avg_return": round(avg_ret, 3),
            "sharpe_like": round(sharpe, 2),
            "max_drawdown": round(max_dd, 2),
            "last_seen": last_trade.get("date", "—"),
            "last_result": last_trade.get("result", "—"),
            "trades": trades[-15:],
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  TECHNICAL INDICATORS
    # ═══════════════════════════════════════════════════════════════════════

    def _rsi(self, s: pd.Series, n: int = 14) -> pd.Series:
        d = s.diff()
        up = d.clip(lower=0).ewm(com=n - 1, adjust=True, min_periods=n).mean()
        dn = (-d.clip(upper=0)).ewm(com=n - 1, adjust=True, min_periods=n).mean()
        return 100 - 100 / (1 + up / dn.replace(0, 1e-9))

    def _macd(self, s: pd.Series, fast=12, slow=26, sig=9):
        ema_f = s.ewm(span=fast, adjust=False).mean()
        ema_s = s.ewm(span=slow, adjust=False).mean()
        macd  = ema_f - ema_s
        signal = macd.ewm(span=sig, adjust=False).mean()
        return macd, signal

    def _bollinger(self, s: pd.Series, n=20, k=2):
        mid = s.rolling(n).mean()
        std = s.rolling(n).std()
        return mid, mid + k * std, mid - k * std

    def _atr(self, df: pd.DataFrame, n: int = 14) -> pd.Series:
        hl = df["high"] - df["low"]
        hc = (df["high"] - df["close"].shift()).abs()
        lc = (df["low"]  - df["close"].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return tr.ewm(com=n - 1, adjust=False).mean()

    def _obv(self, df: pd.DataFrame) -> pd.Series:
        direction = np.sign(df["close"].diff().fillna(0))
        return (direction * df["volume"]).cumsum()

    def _vwap(self, df: pd.DataFrame) -> pd.Series:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        vol = df["volume"].replace(0, 1)
        return (tp * vol).cumsum() / vol.cumsum()

    # ═══════════════════════════════════════════════════════════════════════
    #  ASTRO TRIGGERS (unchanged from original)
    # ═══════════════════════════════════════════════════════════════════════

    def get_upcoming_astro_triggers(self, days_ahead: int = 7) -> List[Dict]:
        today = datetime.now()
        triggers = []
        for d in range(days_ahead):
            check_date = today + timedelta(days=d)
            dt = check_date.replace(hour=9, minute=15, second=0)
            try:
                metrics = self.moon_calc.calculate_nakshatra(dt, IST)
                tithi = metrics.get("tithi_number", 0)
                nk    = metrics.get("nakshatra", "")
                if tithi in [14, 15]:
                    triggers.append({"date": check_date.strftime("%Y-%m-%d"),
                                     "event": "🌕 Full Moon (Purnima)", "nakshatra": nk,
                                     "bias": "High Volatility", "impact": "Watch for reversal"})
                elif tithi in [29, 30]:
                    triggers.append({"date": check_date.strftime("%Y-%m-%d"),
                                     "event": "🌑 New Moon (Amavasya)", "nakshatra": nk,
                                     "bias": "Neutral", "impact": "Trend change probability"})
            except Exception:
                pass
        return triggers

    # ── Legacy compatibility: old endpoint still calls run_multi_timeframe_scan ──
    def _calculate_historical_success(self, df, pattern_name, historical_period):
        years = int(historical_period.replace("y", "").replace("Max", "20")) if any(
            c.isdigit() for c in historical_period) else 5
        return self._backtest_pattern(df, pattern_name, years)
