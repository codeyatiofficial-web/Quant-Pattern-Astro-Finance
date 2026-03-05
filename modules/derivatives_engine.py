"""
Derivatives Engine for NSE India — Kite API Connected
Handles: Options Chain, Greeks, IV, PCR, Max Pain, FII/DII Flow, VIX
Uses KiteConnect for real-time data with synthetic fallback when not authenticated.
"""
import logging
import math
import random
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Black-Scholes Pricing & Greeks  (pure math, no API dependency)
# ---------------------------------------------------------------------------

def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

def black_scholes_price(S, K, T, r, sigma, option_type="CE"):
    if T <= 0 or sigma <= 0:
        return max(0, S - K) if option_type == "CE" else max(0, K - S)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == "CE":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)

def compute_greeks(S, K, T, r, sigma, option_type="CE"):
    if T <= 0 or sigma <= 0:
        return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0, "price": 0}
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    price = black_scholes_price(S, K, T, r, sigma, option_type)
    gamma = _norm_pdf(d1) / (S * sigma * math.sqrt(T))
    vega = S * _norm_pdf(d1) * math.sqrt(T) / 100
    if option_type == "CE":
        delta = _norm_cdf(d1)
        theta = (-(S * _norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * _norm_cdf(d2)) / 365
        rho = K * T * math.exp(-r * T) * _norm_cdf(d2) / 100
    else:
        delta = _norm_cdf(d1) - 1
        theta = (-(S * _norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * _norm_cdf(-d2)) / 365
        rho = -K * T * math.exp(-r * T) * _norm_cdf(-d2) / 100
    return {"price": round(price, 2), "delta": round(delta, 4), "gamma": round(gamma, 6),
            "theta": round(theta, 2), "vega": round(vega, 2), "rho": round(rho, 4)}

def implied_volatility_newton(market_price, S, K, T, r, option_type="CE", max_iter=100, tol=1e-6):
    if T <= 0 or market_price <= 0:
        return 0.0
    sigma = 0.3
    for _ in range(max_iter):
        price = black_scholes_price(S, K, T, r, sigma, option_type)
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        vega = S * _norm_pdf(d1) * math.sqrt(T)
        if abs(vega) < 1e-10:
            break
        diff = price - market_price
        sigma -= diff / vega
        sigma = max(0.001, min(sigma, 10.0))
        if abs(diff) < tol:
            break
    return round(sigma * 100, 2)

# ---------------------------------------------------------------------------
# PCR & Max Pain  (pure math)
# ---------------------------------------------------------------------------

def calculate_pcr(chain: List[Dict]) -> float:
    total_pe = sum(row["PE"]["oi"] for row in chain)
    total_ce = sum(row["CE"]["oi"] for row in chain)
    return round(total_pe / total_ce, 3) if total_ce else 1.0

def calculate_max_pain(chain: List[Dict]) -> float:
    strikes = [r["strike"] for r in chain]
    oi_map = {r["strike"]: {"ce": r["CE"]["oi"], "pe": r["PE"]["oi"]} for r in chain}
    min_pain, mp_strike = float("inf"), strikes[len(strikes) // 2]
    for exp in strikes:
        pain = sum(max(0, exp - k) * v["ce"] + max(0, k - exp) * v["pe"] for k, v in oi_map.items())
        if pain < min_pain:
            min_pain, mp_strike = pain, exp
    return mp_strike

# ---------------------------------------------------------------------------
# VIX Interpretation
# ---------------------------------------------------------------------------

def _interpret_vix(vix: float) -> str:
    if vix < 13: return "Very Low Volatility — Complacency Risk"
    if vix < 17: return "Low Volatility — Calm Market"
    if vix < 22: return "Moderate Volatility — Normal Range"
    if vix < 28: return "High Volatility — Elevated Fear"
    return "Extreme Volatility — Panic Mode"

# ---------------------------------------------------------------------------
# Synthetic fallback generators  (used when Kite is not connected)
# ---------------------------------------------------------------------------

def _synthetic_options_chain(spot, days_to_expiry, r=0.065):
    T = days_to_expiry / 365.0
    atm = round(spot / 100) * 100
    strikes = [atm + i * 100 for i in range(-15, 16)]
    base_iv = 0.14
    chain = []
    for K in strikes:
        m = abs(K - spot) / spot
        skew = m * 0.4
        iv_ce = base_iv + (skew + random.uniform(-0.01, 0.01) if K > spot else random.uniform(-0.005, 0.005))
        iv_pe = base_iv + (skew * 1.2 + random.uniform(-0.01, 0.01) if K < spot else random.uniform(-0.005, 0.005))
        g_ce = compute_greeks(spot, K, T, r, iv_ce, "CE")
        g_pe = compute_greeks(spot, K, T, r, iv_pe, "PE")
        oi_f = max(0, 1 - m * 8)
        ce_oi = int(oi_f * random.uniform(30000, 150000) + random.uniform(1000, 5000))
        pe_oi = int((oi_f * random.uniform(30000, 150000) + random.uniform(1000, 5000)) * (1 + 0.2 * oi_f))
        chain.append({"strike": K,
            "CE": {"price": g_ce["price"], "iv": round(iv_ce * 100, 2), "oi": ce_oi,
                   "change_oi": int(random.uniform(-5000, 15000)), "volume": int(ce_oi * random.uniform(0.1, 0.3)),
                   "delta": g_ce["delta"], "gamma": g_ce["gamma"], "theta": g_ce["theta"], "vega": g_ce["vega"]},
            "PE": {"price": g_pe["price"], "iv": round(iv_pe * 100, 2), "oi": pe_oi,
                   "change_oi": int(random.uniform(-5000, 20000)), "volume": int(pe_oi * random.uniform(0.1, 0.3)),
                   "delta": g_pe["delta"], "gamma": g_pe["gamma"], "theta": g_pe["theta"], "vega": g_pe["vega"]}})
    return chain

def _synthetic_fii_dii(days=30):
    data = []
    now = datetime.now()
    for i in range(days, 0, -1):
        d = now - timedelta(days=i)
        if d.weekday() >= 5: continue
        fb, fs = random.uniform(2000, 12000), random.uniform(2500, 13000)
        db, ds = random.uniform(1500, 9000), random.uniform(1000, 7000)
        data.append({"date": d.strftime("%Y-%m-%d"),
                      "fii_buy": round(fb, 2), "fii_sell": round(fs, 2), "fii_net": round(fb - fs, 2),
                      "dii_buy": round(db, 2), "dii_sell": round(ds, 2), "dii_net": round(db - ds, 2)})
    return data

def _synthetic_vix():
    c = round(random.uniform(12.5, 22.0), 2)
    p = c + random.uniform(-1.5, 1.5)
    return {"current": c, "previous": round(p, 2), "change": round(c - p, 2),
            "change_pct": round((c - p) / p * 100, 2), "interpretation": _interpret_vix(c)}

# ---------------------------------------------------------------------------
# Trend Forecaster  (works with both real & synthetic data)
# ---------------------------------------------------------------------------

def forecast_market_trend(fii_dii_data, pcr, max_pain, spot, vix):
    score, signals = 0, []
    recent = fii_dii_data[-10:] if len(fii_dii_data) >= 10 else fii_dii_data
    avg_fii = sum(d["fii_net"] for d in recent) / len(recent) if recent else 0
    avg_dii = sum(d["dii_net"] for d in recent) / len(recent) if recent else 0

    if avg_fii > 1500:   score += 2; signals.append({"type": "bullish", "signal": f"FII net buying ₹{avg_fii:,.0f} Cr avg (10d)"})
    elif avg_fii > 0:    score += 1; signals.append({"type": "bullish", "signal": f"FII mild buying ₹{avg_fii:,.0f} Cr avg"})
    elif avg_fii < -2000: score -= 2; signals.append({"type": "bearish", "signal": f"FII heavy selling ₹{abs(avg_fii):,.0f} Cr avg (10d)"})
    else:                score -= 1; signals.append({"type": "bearish", "signal": f"FII mild selling ₹{abs(avg_fii):,.0f} Cr avg"})

    if avg_dii > 1000:   score += 1; signals.append({"type": "bullish", "signal": f"DII supporting ₹{avg_dii:,.0f} Cr avg"})
    elif avg_dii < -500: score -= 1; signals.append({"type": "bearish", "signal": f"DII selling ₹{abs(avg_dii):,.0f} Cr avg"})

    if pcr > 1.3:   score += 1; signals.append({"type": "bullish", "signal": f"PCR {pcr:.2f} > 1.3 — Reversal likely"})
    elif pcr > 1.0:  signals.append({"type": "neutral", "signal": f"PCR {pcr:.2f} — Moderate bearish"})
    elif pcr < 0.75: score -= 1; signals.append({"type": "bearish", "signal": f"PCR {pcr:.2f} < 0.75 — Euphoria risk"})
    else:            signals.append({"type": "neutral", "signal": f"PCR {pcr:.2f} — Balanced"})

    mp_gap = (max_pain - spot) / spot * 100
    if mp_gap > 2:   score += 1; signals.append({"type": "bullish", "signal": f"Max Pain {max_pain:,.0f} {mp_gap:.1f}% above spot"})
    elif mp_gap < -2: score -= 1; signals.append({"type": "bearish", "signal": f"Max Pain {max_pain:,.0f} {abs(mp_gap):.1f}% below spot"})
    else:            signals.append({"type": "neutral", "signal": f"Max Pain {max_pain:,.0f} near spot"})

    vv = vix["current"]
    if vv > 22:  score -= 1; signals.append({"type": "bearish", "signal": f"VIX {vv:.1f} elevated"})
    elif vv < 14: signals.append({"type": "neutral", "signal": f"VIX {vv:.1f} low — complacency"})
    else:        signals.append({"type": "neutral", "signal": f"VIX {vv:.1f} normal"})

    conf = round(min(0.95, 0.45 + abs(score) / 7 * 0.5) * 100, 1)
    fc = "BULLISH" if score >= 2 else ("BEARISH" if score <= -2 else "NEUTRAL")
    fc_c = "green" if fc == "BULLISH" else ("red" if fc == "BEARISH" else "yellow")
    return {"forecast": fc, "forecast_color": fc_c, "confidence": conf, "score": score,
            "signals": signals, "avg_fii_net_10d": round(avg_fii, 2), "avg_dii_net_10d": round(avg_dii, 2)}


# ---------------------------------------------------------------------------
# NSE FII/DII Scraper  (fetches real data from NSE website)
# ---------------------------------------------------------------------------

NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

def _fetch_nse_fii_dii() -> List[Dict]:
    """Try to scrape live FII/DII data from NSE India website."""
    try:
        session = requests.Session()
        # First hit the main page to get cookies
        session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=10)
        resp = session.get(NSE_FII_DII_URL, headers=NSE_HEADERS, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"NSE FII/DII API returned {resp.status_code}")
            return []
        raw = resp.json()
        # NSE returns list of dicts with keys like: category, date, buyValue, sellValue
        result = []
        fii_row = {}
        dii_row = {}
        for entry in raw:
            cat = entry.get("category", "")
            if "FII" in cat or "FPI" in cat:
                fii_row = {
                    "date": entry.get("date", datetime.now().strftime("%d-%b-%Y")),
                    "fii_buy": round(float(entry.get("buyValue", 0)) / 100, 2),    # Convert lakhs to Cr
                    "fii_sell": round(float(entry.get("sellValue", 0)) / 100, 2),
                }
                fii_row["fii_net"] = round(fii_row["fii_buy"] - fii_row["fii_sell"], 2)
            elif "DII" in cat:
                dii_row = {
                    "dii_buy": round(float(entry.get("buyValue", 0)) / 100, 2),
                    "dii_sell": round(float(entry.get("sellValue", 0)) / 100, 2),
                }
                dii_row["dii_net"] = round(dii_row["dii_buy"] - dii_row["dii_sell"], 2)
        if fii_row and dii_row:
            merged = {**fii_row, **dii_row}
            result.append(merged)
        return result
    except Exception as e:
        logger.warning(f"NSE FII/DII scrape failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENGINE CLASS  —  Kite-connected with graceful fallback
# ═══════════════════════════════════════════════════════════════════════════

# Kite instrument key for index quotes (exchange:tradingsymbol format for the quote API)
KITE_INDEX_KEYS = {
    "NIFTY": "NSE:NIFTY 50",
    "BANKNIFTY": "NSE:NIFTY BANK",
    "NIFTYIT": "NSE:NIFTY IT",
    "INDIAVIX": "NSE:INDIA VIX",
}

# Kite instrument token constants for indices (kept for VIX)
KITE_INDEX_TOKENS = {
    "NIFTY": 256265,       # NIFTY 50
    "BANKNIFTY": 260105,   # NIFTY BANK
    "NIFTYIT": 259849,     # NIFTY IT
    "INDIAVIX": 264969,    # INDIA VIX
}

# yfinance symbol map for real-price fallback
YFIN_SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYIT": "^CNXIT",
}

# NFO exchange segment prefix
NFO_EXCHANGE = "NFO"
NSE_EXCHANGE = "NSE"

class DerivativesEngine:
    """
    Orchestrates all derivatives data — uses Kite API when authenticated,
    falls back to synthetic data otherwise.
    """

    def __init__(self):
        self.kite = None
        self.kite_client = None
        self._nfo_instruments = None
        self._init_kite()

    def _init_kite(self):
        """Initialize Kite connection using the shared KiteDataClient."""
        try:
            from modules.kite_client import KiteDataClient
            self.kite_client = KiteDataClient()
            if self.kite_client.kite and self.kite_client.is_authenticated():
                self.kite = self.kite_client.kite
                logger.info("DerivativesEngine: Kite API connected ✓")
            else:
                logger.info("DerivativesEngine: Kite not authenticated, using synthetic data")
        except Exception as e:
            logger.warning(f"DerivativesEngine: Kite init failed ({e}), using synthetic data")

    def _refresh_kite(self):
        """Re-check Kite auth (it may have been authenticated after init)."""
        if self.kite_client and not self.kite:
            try:
                if self.kite_client.is_authenticated():
                    self.kite = self.kite_client.kite
                    logger.info("DerivativesEngine: Kite reconnected ✓")
            except Exception:
                pass

    @property
    def is_kite_live(self) -> bool:
        self._refresh_kite()
        return self.kite is not None

    # ── Kite: Get live spot quote ──────────────────────────────────────────

    def _kite_spot(self, symbol: str = "NIFTY") -> Optional[float]:
        """Fetch live NIFTY/BANKNIFTY spot from Kite quote API."""
        if not self.is_kite_live:
            return None
        try:
            key = KITE_INDEX_KEYS.get(symbol.upper(), "NSE:NIFTY 50")
            quote = self.kite.quote([key])
            if quote:
                q_key = list(quote.keys())[0]
                price = float(quote[q_key].get("last_price", 0))
                if price > 0:
                    return price
        except Exception as e:
            logger.warning(f"Kite spot fetch failed: {e}")
        return None

    def _yfinance_spot(self, symbol: str = "NIFTY") -> Optional[float]:
        """Fetch the ACTUAL current Nifty price from Yahoo Finance as a reliable fallback."""
        try:
            import yfinance as yf
            yf_symbol = YFIN_SYMBOL_MAP.get(symbol.upper(), "^NSEI")
            ticker = yf.Ticker(yf_symbol)
            # fast_info.last_price gives the most recent price reliably
            price = ticker.fast_info.last_price
            if price and price > 0:
                return round(float(price), 2)
            # Fallback: get today's close from 1 day of history
            hist = ticker.history(period="2d")
            if not hist.empty:
                return round(float(hist["Close"].iloc[-1]), 2)
        except Exception as e:
            logger.warning(f"yfinance spot fetch failed: {e}")
        return None

    # ── Kite: Get India VIX ────────────────────────────────────────────────

    def _kite_vix(self) -> Optional[Dict]:
        """Fetch real India VIX from Kite."""
        if not self.is_kite_live:
            return None
        try:
            token = KITE_INDEX_TOKENS["INDIAVIX"]
            quote = self.kite.quote([f"NSE:{token}"])
            if quote:
                key = list(quote.keys())[0]
                q = quote[key]
                current = float(q.get("last_price", 0))
                prev_close = float(q.get("ohlc", {}).get("close", current))
                change = current - prev_close
                return {
                    "current": round(current, 2),
                    "previous": round(prev_close, 2),
                    "change": round(change, 2),
                    "change_pct": round(change / prev_close * 100, 2) if prev_close else 0,
                    "interpretation": _interpret_vix(current),
                    "source": "Kite Live",
                }
        except Exception as e:
            logger.warning(f"Kite VIX fetch failed: {e}")
        return None

    # ── Kite: Load NFO instruments for options chain ───────────────────────

    def _load_nfo_instruments(self):
        """Download NFO instrument list from Kite for options chain data."""
        if self._nfo_instruments is not None:
            return
        if not self.is_kite_live:
            return
        try:
            instruments = self.kite.instruments(NFO_EXCHANGE)
            self._nfo_instruments = pd.DataFrame(instruments)
            logger.info(f"Loaded {len(self._nfo_instruments)} NFO instruments")
        except Exception as e:
            logger.warning(f"NFO instruments load failed: {e}")
            self._nfo_instruments = pd.DataFrame()

    def _get_next_expiry(self, symbol_prefix: str = "NIFTY") -> Optional[datetime]:
        """Find the nearest weekly/monthly expiry for NIFTY options."""
        self._load_nfo_instruments()
        if self._nfo_instruments is None or self._nfo_instruments.empty:
            return None
        try:
            opts = self._nfo_instruments[
                (self._nfo_instruments["name"] == symbol_prefix) &
                (self._nfo_instruments["instrument_type"].isin(["CE", "PE"]))
            ]
            if opts.empty:
                return None
            today = datetime.now().date()
            future_expiries = opts[pd.to_datetime(opts["expiry"]).dt.date >= today]["expiry"].unique()
            if len(future_expiries) == 0:
                return None
            nearest = min(future_expiries, key=lambda x: abs((pd.Timestamp(x).date() - today).days))
            return pd.Timestamp(nearest).to_pydatetime()
        except Exception as e:
            logger.warning(f"Expiry lookup failed: {e}")
            return None

    # ── Kite: Build real options chain from NFO quotes ─────────────────────

    def _kite_options_chain(self, spot: float, symbol_prefix: str = "NIFTY") -> Optional[List[Dict]]:
        """
        Build options chain from Kite NFO instrument data + live quotes.
        Fetches real OI, last price, volume for strikes around spot.
        """
        if not self.is_kite_live:
            return None
        self._load_nfo_instruments()
        if self._nfo_instruments is None or self._nfo_instruments.empty:
            return None

        try:
            expiry = self._get_next_expiry(symbol_prefix)
            if not expiry:
                logger.warning("No expiry found for options chain")
                return None

            expiry_date = expiry.date() if hasattr(expiry, 'date') else expiry
            T = max(1, (expiry_date - datetime.now().date()).days) / 365.0
            r = 0.065

            # Filter instruments for this expiry
            opts = self._nfo_instruments[
                (self._nfo_instruments["name"] == symbol_prefix) &
                (pd.to_datetime(self._nfo_instruments["expiry"]).dt.date == expiry_date)
            ]

            # Pick strikes around ATM (±1500 points for NIFTY)
            atm = round(spot / 100) * 100
            strike_range = range(int(atm - 1500), int(atm + 1600), 100)
            opts = opts[opts["strike"].isin(strike_range)]

            if opts.empty:
                return None

            # Build instrument token list for batch quote
            token_map = {}  # token -> {strike, type}
            for _, row in opts.iterrows():
                token_map[row["instrument_token"]] = {
                    "strike": float(row["strike"]),
                    "type": row["instrument_type"],
                    "tradingsymbol": row["tradingsymbol"],
                }

            # Kite allows max ~200 instruments per quote call
            tokens = list(token_map.keys())
            all_quotes = {}

            for i in range(0, len(tokens), 200):
                batch = tokens[i:i+200]
                symbols = [f"{NFO_EXCHANGE}:{token_map[t]['tradingsymbol']}" for t in batch]
                try:
                    quotes = self.kite.quote(symbols)
                    all_quotes.update(quotes)
                except Exception as qe:
                    logger.warning(f"Quote batch failed: {qe}")

            # Organize into chain
            chain_data = {}  # strike -> {"CE": {...}, "PE": {...}}
            for sym, q in all_quotes.items():
                # Parse token from the symbol
                trading_symbol = sym.split(":")[-1] if ":" in sym else sym
                # Find matching instrument
                match = opts[opts["tradingsymbol"] == trading_symbol]
                if match.empty:
                    continue
                row = match.iloc[0]
                strike = float(row["strike"])
                opt_type = row["instrument_type"]

                if strike not in chain_data:
                    chain_data[strike] = {"CE": None, "PE": None}

                ltp = float(q.get("last_price", 0))
                oi = int(q.get("oi", 0))
                vol = int(q.get("volume", 0))
                oi_day_change = int(q.get("oi_day_high", 0)) - int(q.get("oi_day_low", 0))

                # Compute Greeks from market price
                iv_pct = implied_volatility_newton(ltp, spot, strike, T, r, opt_type) if ltp > 0 else 15.0
                greeks = compute_greeks(spot, strike, T, r, iv_pct / 100.0, opt_type)

                chain_data[strike][opt_type] = {
                    "price": round(ltp, 2),
                    "iv": iv_pct,
                    "oi": oi,
                    "change_oi": oi_day_change,
                    "volume": vol,
                    "delta": greeks["delta"],
                    "gamma": greeks["gamma"],
                    "theta": greeks["theta"],
                    "vega": greeks["vega"],
                }

            # Build sorted chain list
            chain = []
            for strike in sorted(chain_data.keys()):
                cd = chain_data[strike]
                # Fill missing side with zeros
                empty_side = {"price": 0, "iv": 0, "oi": 0, "change_oi": 0, "volume": 0,
                              "delta": 0, "gamma": 0, "theta": 0, "vega": 0}
                chain.append({
                    "strike": strike,
                    "CE": cd["CE"] or empty_side,
                    "PE": cd["PE"] or empty_side,
                })

            if len(chain) >= 5:
                logger.info(f"Kite options chain: {len(chain)} strikes, expiry {expiry_date}")
                return chain

        except Exception as e:
            logger.warning(f"Kite options chain build failed: {e}")
        return None

    # ── FII/DII: Try NSE scrape, then synthetic fallback ──────────────────

    def _get_fii_dii(self, days: int = 30) -> List[Dict]:
        """Fetch FII/DII data — try NSE website first, fallback to synthetic."""
        live = _fetch_nse_fii_dii()
        if live:
            # Pad with synthetic historical data if we only got today's
            synthetic_hist = _synthetic_fii_dii(days - 1)
            return synthetic_hist + live
        return _synthetic_fii_dii(days)

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_market_snapshot(self, symbol: str = "NIFTY") -> Dict:
        """Full derivatives snapshot with Kite live data or synthetic fallback."""
        try:
            data_source = "synthetic"

            # 1. Spot price — try Kite first, then yfinance, never generate random
            spot = self._kite_spot(symbol)
            if spot and spot > 0:
                data_source = "kite"
            else:
                spot = self._yfinance_spot(symbol)
                if spot and spot > 0:
                    data_source = "yfinance"
                else:
                    # Last resort: use a known rough estimate — will be stale but not misleading
                    logger.error("Both Kite and yfinance spot fetch failed — using cached fallback")
                    spot = 22500.0  # static fallback only if all else fails

            # 2. VIX — try Kite
            vix = self._kite_vix()
            if not vix:
                vix = _synthetic_vix()

            # 3. Options chain — try Kite NFO
            chain = self._kite_options_chain(spot, symbol.upper())
            if chain:
                data_source = "kite"
                # Calculate days to expiry from nearest expiry
                expiry = self._get_next_expiry(symbol.upper())
                days_to_expiry = max(1, (expiry.date() - datetime.now().date()).days) if expiry else 15
            else:
                days_to_expiry = random.randint(5, 25)
                chain = _synthetic_options_chain(spot, days_to_expiry)

            # 4. PCR & Max Pain from chain
            pcr = calculate_pcr(chain)
            max_pain = calculate_max_pain(chain)

            # 5. FII/DII
            fii_dii = self._get_fii_dii(30)

            # 6. Forecast
            forecast = forecast_market_trend(fii_dii, pcr, max_pain, spot, vix)

            return {
                "symbol": symbol,
                "spot": spot,
                "days_to_expiry": days_to_expiry,
                "timestamp": datetime.now().isoformat(),
                "data_source": data_source,
                "kite_connected": self.is_kite_live,
                "pcr": pcr,
                "max_pain": max_pain,
                "vix": vix,
                "forecast": forecast,
                "options_chain": chain,
                "fii_dii_30d": fii_dii,
            }
        except Exception as e:
            logger.error(f"Snapshot error: {e}")
            raise

    def get_fii_dii_summary(self, days: int = 30) -> Dict:
        data = self._get_fii_dii(days)
        return {
            "data": data,
            "total_fii_net": round(sum(d["fii_net"] for d in data), 2),
            "total_dii_net": round(sum(d["dii_net"] for d in data), 2),
            "trading_days": len(data),
        }

    def calculate_greeks_for_option(self, S, K, T_days, r, market_price, option_type="CE"):
        T = T_days / 365.0
        iv = implied_volatility_newton(market_price, S, K, T, r, option_type)
        greeks = compute_greeks(S, K, T, r, iv / 100.0, option_type)
        greeks["implied_volatility"] = iv
        return greeks
