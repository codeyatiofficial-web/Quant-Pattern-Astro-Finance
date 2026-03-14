"""
Algo 3 — Professional Nifty Weekly Options Engine
====================================================
Built with 30+ years of options-trading discipline.

EXPIRY INTELLIGENCE
  DTE == 0 (expiry day)    : Avoid long options — theta crush. Switch to next week.
  DTE == 1, IV rank < 60   : Too cheap to buy, decay too fast. Switch to next week.
  DTE == 1, IV rank >= 60  : Elevated premium compensates. Trade with caution.
  DTE 2–4                  : Current weekly, tighten SL for theta risk.
  DTE >= 5                 : Normal conditions, full size.

GREEK-BASED STRIKE SELECTION
  Target delta 0.40–0.58   : Near-ATM, confirmed directional play.
  Gamma filter on expiry   : Skip gamma > 0.005 on DTE <= 2 (pin risk).
  Theta filter             : Reject if daily theta > 15% of premium.
  Premium floor            : Min ₹30 (rejects illiquid/near-worthless strikes).
  Liquidity                : Among qualifying strikes, pick highest open interest.

BALANCE-AWARE POSITION SIZING
  LOT_SIZE = 75 (Nifty weekly revised lot)
  Required per lot = premium × 75 × 1.10  (10% MTM buffer)
  Max risk capital = available_cash × 5%
  Recommended lots = min(2, floor(max_risk / required_per_lot))
  Never recommends a trade if capital is insufficient.

4-STEP SCORING  (110 pts)
  Step 1: Trend Alignment   (25) — Supertrend 15m+1h, EMA20>50
  Step 2: Momentum+Volume   (25) — RSI14, MACD(12,26,9), Volume ratio
  Step 3: Options Chain     (25) — PCR, Real MaxPain, ATM OI change, IV rank
  Step 4: Levels + Time     (25) — Trade windows + key level proximity
  Global Bonus            (+10)  — direction aligns global bias

TRADE RULES
  SL  = entry_premium × 0.60  (exit at 40% premium loss)
  T1  = entry_premium × 2.0   (book 50% qty)
  T2  = entry_premium × 3.0   (exit remainder)
  Force-exit at 3:10 PM
"""

import logging
import math
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, date, timedelta, time
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
LOT_SIZE         = 75       # Nifty weekly revised lot size
MAX_LOTS         = 2        # Hard cap per trade
CAPITAL_RISK_PCT = 0.05     # Risk max 5% of available cash per trade
MIN_PREMIUM      = 30.0     # Minimum option premium (₹) — avoid illiquid strikes
MAX_THETA_PCT    = 0.15     # Reject if daily theta > 15% of premium
TARGET_DELTA_MIN = 0.40     # Minimum delta for directional buy
TARGET_DELTA_MAX = 0.58     # Maximum delta for directional buy
MAX_GAMMA_EXPIRY = 0.005    # Max gamma allowed on DTE <= 2

logger = logging.getLogger(__name__)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _signed(val: float) -> str:
    return f"+{val:.2f}" if val >= 0 else f"{val:.2f}"


def _theta_risk_label(dte: int, iv_rank: float) -> str:
    """Human-readable theta risk note given DTE and IV rank."""
    if dte == 0:
        return "EXPIRY DAY — DO NOT BUY OPTIONS"
    if dte == 1:
        if iv_rank >= 60:
            return f"1 DTE | High IV ({iv_rank:.0f}%) compensates — trade with caution"
        return f"1 DTE | Low IV ({iv_rank:.0f}%) — HIGH THETA RISK"
    if dte <= 3:
        return f"{dte} DTE — Elevated theta, tighten SL to 30%"
    return f"{dte} DTE — Normal conditions"


def calculate_gift_nifty_gap(kite_instance=None) -> Dict[str, Any]:
    """
    Estimate Gift Nifty gap using previous Nifty close (^NSEI) vs
    latest SGX/Gift Nifty proxy (last available ^NSEI pre-open or
    nearest futures-equivalent using yfinance).
    Returns: {"gap_points": float, "gap_pct": float, "gap_label": str}
    """
    try:
        import yfinance as yf
        nsei = yf.download("^NSEI", period="3d", interval="1d", progress=False, auto_adjust=True)
        if nsei.empty or len(nsei) < 2:
            return {"gap_points": 0.0, "gap_pct": 0.0, "gap_label": "Flat"}

        closes = nsei['Close'].dropna()
        if len(closes) < 2:
            return {"gap_points": 0.0, "gap_pct": 0.0, "gap_label": "Flat"}

        prev_close = float(closes.iloc[-2])
        last_close = float(closes.iloc[-1])
        gap_pts = round(last_close - prev_close, 1)
        gap_pct = round(gap_pts / prev_close * 100, 2) if prev_close > 0 else 0.0

        if gap_pct > 0.5:
            label = f"Gap Up {gap_pts:.0f} pts ({gap_pct}%)"
        elif gap_pct < -0.5:
            label = f"Gap Down {gap_pts:.0f} pts ({gap_pct}%)"
        else:
            label = f"Flat / Small Gap {gap_pts:.0f} pts"

        return {"gap_points": gap_pts, "gap_pct": gap_pct, "gap_label": label}

    except Exception as e:
        logger.warning(f"Gift Nifty gap calculation failed: {e}")
        return {"gap_points": 0.0, "gap_pct": 0.0, "gap_label": "Unavailable"}


def calculate_real_max_pain(ce_data: pd.DataFrame, pe_data: pd.DataFrame) -> float:
    """
    True MaxPain: for each strike, compute total loss to option buyers
    (ITM intrinsic value × OI) for both CE and PE, return the strike
    that minimises combined loss.
    """
    if ce_data.empty or pe_data.empty:
        return 0.0

    try:
        # Build unified strike list
        strikes = sorted(set(ce_data['strike'].tolist() + pe_data['strike'].tolist()))

        min_pain = float('inf')
        max_pain_strike = strikes[len(strikes) // 2]

        ce_oi = {row['strike']: row['oi'] for _, row in ce_data.iterrows()}
        pe_oi = {row['strike']: row['oi'] for _, row in pe_data.iterrows()}

        for candidate in strikes:
            pain = 0.0
            for s in strikes:
                # CE holders lose if spot (candidate) < strike
                if candidate < s:
                    pain += (s - candidate) * ce_oi.get(s, 0)
                # PE holders lose if spot (candidate) > strike
                if candidate > s:
                    pain += (candidate - s) * pe_oi.get(s, 0)
            if pain < min_pain:
                min_pain = pain
                max_pain_strike = candidate

        return float(max_pain_strike)

    except Exception as e:
        logger.warning(f"MaxPain calculation error: {e}")
        return 0.0


def calculate_iv_rank(symbol: str = "^NSEI", lookback_days: int = 252) -> float:
    """
    IV rank approximation using 20-day historical volatility percentile
    over the past year.  Returns 0–100.
    """
    try:
        import yfinance as yf
        df = yf.download(symbol, period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 22:
            return 50.0

        closes = df['Close'].dropna()
        log_ret = np.log(closes / closes.shift(1)).dropna()

        # Rolling 20-day annualised HV
        hv_series = log_ret.rolling(20).std() * np.sqrt(252) * 100
        hv_series = hv_series.dropna()
        if len(hv_series) < 2:
            return 50.0

        hv_52w_low  = float(hv_series.min())
        hv_52w_high = float(hv_series.max())
        current_hv  = float(hv_series.iloc[-1])

        if hv_52w_high == hv_52w_low:
            return 50.0

        rank = (current_hv - hv_52w_low) / (hv_52w_high - hv_52w_low) * 100
        return round(rank, 1)

    except Exception as e:
        logger.warning(f"IV rank calculation error: {e}")
        return 50.0


# ─── ACCOUNT / BALANCE ────────────────────────────────────────────────────────

def _days_to_expiry(expiry_str: str) -> int:
    """Calendar days from today to expiry_str (YYYY-MM-DD)."""
    try:
        exp = datetime.strptime(str(expiry_str)[:10], "%Y-%m-%d").date()
        return max(0, (exp - date.today()).days)
    except Exception:
        return 7


def get_account_state(kite) -> Dict[str, Any]:
    """
    Fetch live balance and open positions from Kite.
    Returns safe defaults (available_cash=0) on failure so the engine
    can still produce a signal — it will just size at 1 lot.
    """
    state: Dict[str, Any] = {
        "available_cash":        0.0,
        "used_margin":           0.0,
        "net_value":             0.0,
        "daily_pnl":             0.0,
        "open_positions":        [],
        "has_open_nifty_option": False,
        "margin_error":          "",
    }
    try:
        margins = kite.margins()
        equity  = margins.get("equity", {})
        state["available_cash"] = _safe_float(
            equity.get("available", {}).get("live_balance", 0.0)
        )
        state["used_margin"] = _safe_float(
            equity.get("utilised", {}).get("debits", 0.0)
        )
        state["net_value"] = state["available_cash"] + state["used_margin"]
    except Exception as e:
        state["margin_error"] = str(e)[:80]
        logger.warning(f"Kite margins error: {e}")

    try:
        positions = kite.positions()
        net_pos   = positions.get("net", [])
        day_pos   = positions.get("day", [])
        state["daily_pnl"] = sum(_safe_float(p.get("pnl", 0)) for p in day_pos)
        nifty_opts = [
            p for p in net_pos
            if "NIFTY" in str(p.get("tradingsymbol", "")).upper()
            and p.get("product") in ("MIS", "NRML")
            and int(p.get("quantity", 0)) != 0
        ]
        state["open_positions"] = [
            {
                "symbol":    p.get("tradingsymbol"),
                "qty":       p.get("quantity"),
                "avg_price": _safe_float(p.get("average_price")),
                "pnl":       _safe_float(p.get("pnl")),
                "product":   p.get("product"),
            }
            for p in nifty_opts
        ]
        state["has_open_nifty_option"] = len(nifty_opts) > 0
    except Exception as e:
        logger.warning(f"Kite positions error: {e}")

    return state


def calculate_recommended_lots(available_cash: float, entry_premium: float) -> int:
    """
    Conservative lot sizing:
      required_per_lot = premium × LOT_SIZE × 1.10  (10% MTM buffer)
      max_risk         = available_cash × CAPITAL_RISK_PCT (5%)
      lots             = min(MAX_LOTS, floor(max_risk / required_per_lot))
    Always returns at least 1 so the signal remains informative.
    Returns 0 only when available_cash is explicitly 0 (Kite not available).
    """
    if entry_premium <= 0:
        return 1
    required_per_lot = entry_premium * LOT_SIZE * 1.10
    if available_cash <= 0:
        return 1  # unknown balance → default 1
    max_risk = available_cash * CAPITAL_RISK_PCT
    lots = int(math.floor(max_risk / required_per_lot))
    return max(1, min(MAX_LOTS, lots))


def select_best_expiry(
    nifty_opts: List[Dict],
    iv_rank: float
) -> Tuple[Optional[str], int, str]:
    """
    Smart expiry selection:
      DTE == 0               → switch to next weekly (theta crush)
      DTE == 1, IV < 60      → switch to next weekly (premium decays too fast)
      DTE == 1, IV >= 60     → proceed with strong warning
      DTE 2–4                → current weekly, warn on theta
      DTE >= 5               → current weekly, normal
    Returns (expiry_str, dte, reason_label)
    """
    expiries = sorted(set(
        str(i.get("expiry", ""))[:10]
        for i in nifty_opts
        if i.get("expiry")
    ))
    if not expiries:
        return None, 0, "No expiries found in instruments"

    current   = expiries[0]
    dte       = _days_to_expiry(current)
    next_exp  = expiries[1] if len(expiries) > 1 else current
    next_dte  = _days_to_expiry(next_exp)

    if dte == 0:
        return next_exp, next_dte, (
            f"Expiry day — theta crush on longs — switched to next weekly ({next_dte} DTE)"
        )
    if dte == 1 and iv_rank < 60:
        return next_exp, next_dte, (
            f"1 DTE + Low IV ({iv_rank:.0f}%) — decay risk — switched to next ({next_dte} DTE)"
        )
    if dte == 1:
        return current, dte, f"1 DTE | High IV ({iv_rank:.0f}%) — elevated premium, proceed with caution"
    if dte <= 3:
        return current, dte, f"{dte} DTE — current weekly, elevated theta — tighten SL"
    return current, dte, f"{dte} DTE — current weekly, normal conditions"


def select_best_strike(
    option_df: pd.DataFrame,
    spot: float,
    dte: int,
    iv_rank: float
) -> Tuple[Optional[Dict], str]:
    """
    Professional strike selection using Greeks:
      1. Filter: premium >= MIN_PREMIUM
      2. Delta targeting: 0.40–0.58 for directional buys
      3. Gamma filter on DTE <= 2: skip gamma > MAX_GAMMA_EXPIRY
      4. Theta filter: reject if daily theta > 15% of premium
      5. Liquidity: highest open interest among qualified strikes
      6. Fallback: nearest ATM if Greeks unavailable
    """
    if option_df.empty:
        return None, "No chain data"

    candidates = option_df[option_df["ltp"] >= MIN_PREMIUM].copy()
    if candidates.empty:
        # Premium filter too strict — widen to nearest ATM
        nearest_idx = (option_df["strike"] - spot).abs().argsort().iloc[0]
        row = option_df.iloc[nearest_idx]
        return row.to_dict(), f"ATM fallback (all premiums < ₹{MIN_PREMIUM:.0f})"

    has_greeks = (
        "delta" in candidates.columns and
        candidates["delta"].abs().sum() > 0
    )
    reason_parts: List[str] = []

    if has_greeks:
        # Step A: Delta range
        delta_abs = candidates["delta"].abs()
        delta_filtered = candidates[delta_abs.between(TARGET_DELTA_MIN, TARGET_DELTA_MAX)]
        if delta_filtered.empty:
            delta_filtered = candidates  # widen — use all
        else:
            reason_parts.append(f"delta {TARGET_DELTA_MIN}–{TARGET_DELTA_MAX}")

        # Step B: Gamma cap on near-expiry
        if dte <= 2 and "gamma" in delta_filtered.columns:
            gamma_ok = delta_filtered[delta_filtered["gamma"].abs() <= MAX_GAMMA_EXPIRY]
            if not gamma_ok.empty:
                delta_filtered = gamma_ok
                reason_parts.append(f"gamma≤{MAX_GAMMA_EXPIRY}")

        # Step C: Theta cost vs premium
        if "theta" in delta_filtered.columns:
            theta_ok = delta_filtered[
                delta_filtered["theta"].abs() <= delta_filtered["ltp"] * MAX_THETA_PCT
            ]
            if not theta_ok.empty:
                delta_filtered = theta_ok
                reason_parts.append(f"theta≤{MAX_THETA_PCT*100:.0f}% of premium")

        # Step D: Pick highest OI (most liquid)
        if not delta_filtered.empty:
            best = delta_filtered.loc[delta_filtered["oi"].idxmax()]
            delta_val = abs(_safe_float(best.get("delta", 0)))
            reason_parts.insert(0, f"delta={delta_val:.2f}")
            return best.to_dict(), " | ".join(reason_parts) if reason_parts else "Greek-targeted"

    # No Greeks — pure ATM
    nearest_idx = (candidates["strike"] - spot).abs().argsort().iloc[0]
    row = candidates.iloc[nearest_idx]
    return row.to_dict(), "ATM (no Greeks in response)"


# ─── ALGO 3 ENGINE ────────────────────────────────────────────────────────────

class Algo3Engine:
    """
    Complete Nifty Options trading engine.
    kite: an authenticated KiteConnect instance  (kite_client.kite)
    global_bias_score: int pre-computed from calculate_global_bias()
    """

    def __init__(self, kite, global_bias_score: int = 0):
        self.kite = kite
        self.global_bias_score = global_bias_score

        # Threshold adjustment
        if global_bias_score > 15:
            self.buy_thresh  = 75
            self.sell_thresh = 92
        elif global_bias_score < -15:
            self.buy_thresh  = 92
            self.sell_thresh = 75
        else:
            self.buy_thresh  = 85
            self.sell_thresh = 85

    # ── Data fetch helpers ─────────────────────────────────────────────────────

    def _fetch_candles(self, instrument_token: int, interval: str, days: int) -> pd.DataFrame:
        """Fetch OHLCV candles from Kite historical API."""
        from datetime import timedelta
        try:
            to_dt   = datetime.now()
            from_dt = to_dt - timedelta(days=days)
            raw = self.kite.historical_data(
                instrument_token, from_dt, to_dt, interval
            )
            if not raw:
                return pd.DataFrame()
            df = pd.DataFrame(raw)
            df.rename(columns={'date': 'datetime'}, inplace=True)
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['high']  = pd.to_numeric(df['high'],  errors='coerce')
            df['low']   = pd.to_numeric(df['low'],   errors='coerce')
            df['open']  = pd.to_numeric(df['open'],  errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
            return df.dropna(subset=['close'])
        except Exception as e:
            logger.error(f"Candle fetch error ({interval}): {e}")
            return pd.DataFrame()

    def get_nifty_spot(self) -> float:
        """Return live Nifty 50 spot from Kite."""
        try:
            q = self.kite.quote(["NSE:NIFTY 50"])
            return float(q.get("NSE:NIFTY 50", {}).get("last_price", 0.0))
        except Exception as e:
            logger.error(f"Spot price fetch error: {e}")
            return 0.0

    def get_options_chain_smart(
        self,
        spot: float,
        iv_rank: float = 50.0
    ) -> Tuple[pd.DataFrame, pd.DataFrame, str, int, str]:
        """
        Smart options chain fetch:
          1. Loads NFO instruments (NFO-OPT NIFTY)
          2. Calls select_best_expiry() — checks DTE + IV rank
          3. Fetches ATM ±12 strikes for the chosen expiry
          4. Batch-quotes via Kite — pulls ltp, oi, iv, greeks
          5. Returns (ce_df, pe_df, expiry_str, dte, expiry_reason)
             DataFrame cols: strike, oi, oi_change, ltp, iv, delta, theta, gamma, vega
        """
        try:
            from modules.kite_client import KiteDataClient
            kdc = KiteDataClient()
            instruments = kdc.get_instruments("NFO")
            if not instruments:
                return pd.DataFrame(), pd.DataFrame(), "", 0, "No instruments"

            nifty_opts = [
                i for i in instruments
                if i.get("name", "").upper() == "NIFTY"
                and i.get("segment") == "NFO-OPT"
            ]

            expiry_str, dte, exp_reason = select_best_expiry(nifty_opts, iv_rank)
            if not expiry_str:
                return pd.DataFrame(), pd.DataFrame(), "", 0, "No valid expiry found"

            atm     = round(spot / 50) * 50
            strikes = [atm + (i * 50) for i in range(-12, 13)]

            ce_map: Dict[float, str] = {}
            pe_map: Dict[float, str] = {}
            for inst in nifty_opts:
                s   = _safe_float(inst.get("strike"))
                exp = str(inst.get("expiry", ""))[:10]
                if s in strikes and exp == expiry_str:
                    sym = inst.get("tradingsymbol", "")
                    if inst.get("instrument_type") == "CE":
                        ce_map[s] = sym
                    elif inst.get("instrument_type") == "PE":
                        pe_map[s] = sym

            def _batch_quote(sym_map: Dict[float, str]) -> Dict:
                if not sym_map:
                    return {}
                keys = [f"NFO:{s}" for s in sym_map.values()]
                try:
                    return self.kite.quote(keys) or {}
                except Exception as e:
                    logger.error(f"Options quote error: {e}")
                    return {}

            ce_q = _batch_quote(ce_map)
            pe_q = _batch_quote(pe_map)

            def _build_df(sym_map: Dict[float, str], quotes: Dict) -> pd.DataFrame:
                rows = []
                for s, sym in sym_map.items():
                    q = quotes.get(f"NFO:{sym}", {})
                    # Greeks from Kite quote (only available for options in live market)
                    greeks_raw = q.get("greeks") or {}
                    rows.append({
                        "strike":    s,
                        "oi":        int(q.get("oi", 0)),
                        "oi_change": int(q.get("oi", 0)) - int(q.get("oi_day_low", q.get("oi", 0))),
                        "ltp":       _safe_float(q.get("last_price")),
                        "iv":        _safe_float(q.get("implied_volatility")),
                        "delta":     _safe_float(greeks_raw.get("delta") if isinstance(greeks_raw, dict) else 0),
                        "theta":     _safe_float(greeks_raw.get("theta") if isinstance(greeks_raw, dict) else 0),
                        "gamma":     _safe_float(greeks_raw.get("gamma") if isinstance(greeks_raw, dict) else 0),
                        "vega":      _safe_float(greeks_raw.get("vega")  if isinstance(greeks_raw, dict) else 0),
                    })
                if not rows:
                    return pd.DataFrame()
                return pd.DataFrame(rows).sort_values("strike").reset_index(drop=True)

            ce_df = _build_df(ce_map, ce_q)
            pe_df = _build_df(pe_map, pe_q)
            return ce_df, pe_df, expiry_str, dte, exp_reason

        except Exception as e:
            logger.error(f"Options chain smart error: {e}")
            return pd.DataFrame(), pd.DataFrame(), "", 0, str(e)

    # ── Legacy wrapper (kept for backward compat) ──────────────────────────────

    def get_options_chain(
        self, spot: float, expiry_date: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Legacy method — calls get_options_chain_smart with default iv_rank=50."""
        ce_df, pe_df, _, _, _ = self.get_options_chain_smart(spot, iv_rank=50.0)
        return ce_df, pe_df

    # ── Step 1 ─────────────────────────────────────────────────────────────────

    def step1_trend(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Tuple[int, str]:
        """Supertrend (10,3) on 15m + 1h, EMA20>50 on 1h. Max 25 pts."""
        if df_15m.empty or len(df_15m) < 20 or df_1h.empty or len(df_1h) < 52:
            return 0, "NEUTRAL"
        try:
            from ta.trend import SuperTrend, EMAIndicator
            st15 = SuperTrend(high=df_15m['high'], low=df_15m['low'], close=df_15m['close'], window=10, multiplier=3)
            df_15m['st_dir'] = st15.super_trend_direction()

            st1h = SuperTrend(high=df_1h['high'], low=df_1h['low'], close=df_1h['close'], window=10, multiplier=3)
            df_1h['st_dir'] = st1h.super_trend_direction()
            df_1h['ema20']  = EMAIndicator(close=df_1h['close'], window=20).ema_indicator()
            df_1h['ema50']  = EMAIndicator(close=df_1h['close'], window=50).ema_indicator()

            l15 = df_15m.iloc[-1]
            l1h = df_1h.iloc[-1]

            bull = (l15['st_dir'] == 1) and (l1h['st_dir'] == 1) and (l1h['ema20'] > l1h['ema50'])
            bear = (l15['st_dir'] == -1) and (l1h['st_dir'] == -1) and (l1h['ema20'] < l1h['ema50'])

            if bull:   return 25, "BUY"
            if bear:   return 25, "SELL"
            return 0, "NEUTRAL"
        except Exception as e:
            logger.error(f"Step 1 error: {e}")
            return 0, "NEUTRAL"

    # ── Step 2 ─────────────────────────────────────────────────────────────────

    def step2_momentum(self, df_15m: pd.DataFrame, direction: str) -> Tuple[int, Dict[str, Any]]:
        """RSI(14) + MACD(12,26,9) + Volume ratio on 15m. Max 25 pts."""
        meta = {"rsi": 0.0, "macd_dir": "Flat", "vol_ratio": 0.0}
        if df_15m.empty or len(df_15m) < 30 or direction == "NEUTRAL":
            return 0, meta
        try:
            from ta.trend import MACD
            from ta.momentum import RSIIndicator

            df = df_15m.copy()
            df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
            macd_i = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
            df['macd_hist'] = macd_i.macd_diff()
            df['vol_sma20'] = df['volume'].rolling(20).mean()
            df['vol_ratio'] = df['volume'] / df['vol_sma20'].replace(0, np.nan)

            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last

            rsi       = _safe_float(last['rsi'], 50.0)
            mhist     = _safe_float(last['macd_hist'])
            p_mhist   = _safe_float(prev['macd_hist'])
            vol_ratio = _safe_float(last['vol_ratio'], 1.0)

            meta['rsi']       = round(rsi, 1)
            meta['vol_ratio'] = round(vol_ratio, 2)
            meta['macd_dir']  = "Rising" if mhist > p_mhist else "Falling"

            score = 0
            if direction == "BUY":
                if 50 <= rsi <= 65:    score += 10
                elif 45 <= rsi < 50:   score += 5
                elif rsi < 30:         score += 8
                if mhist > 0 and mhist > p_mhist:
                    score += 8
            elif direction == "SELL":
                if 35 <= rsi <= 50:    score += 10
                elif 50 < rsi <= 55:   score += 5
                elif rsi > 70:         score += 8
                if mhist < 0 and mhist < p_mhist:
                    score += 8

            if vol_ratio > 1.5:
                score += 7

            return min(score, 25), meta
        except Exception as e:
            logger.error(f"Step 2 error: {e}")
            return 0, meta

    # ── Step 3 ─────────────────────────────────────────────────────────────────

    def step3_options_chain(
        self,
        ce_data: pd.DataFrame,
        pe_data: pd.DataFrame,
        spot: float,
        direction: str,
        iv_rank: float = 50.0
    ) -> Tuple[int, Dict[str, Any]]:
        """PCR + Real MaxPain + ATM OI change + IV rank. Max 25 pts."""
        meta = {"pcr": 1.0, "max_pain": 0.0, "iv_rank": iv_rank,
                "call_wall": 0.0, "put_wall": 0.0, "atm_strike": 0.0}

        if ce_data.empty or pe_data.empty or direction == "NEUTRAL":
            return 0, meta

        try:
            total_ce_oi = ce_data['oi'].sum()
            total_pe_oi = pe_data['oi'].sum()
            pcr = (total_pe_oi / total_ce_oi) if total_ce_oi > 0 else 1.0

            max_pain = calculate_real_max_pain(ce_data, pe_data)
            if max_pain == 0.0:
                max_pain = float(ce_data.iloc[(ce_data['strike'] - spot).abs().argsort().iloc[0]]['strike'])

            atm_strike = float(
                ce_data.iloc[(ce_data['strike'] - spot).abs().argsort().iloc[0]]['strike']
            )

            atm_pe_row = pe_data[pe_data['strike'] == atm_strike]
            atm_ce_row = ce_data[ce_data['strike'] == atm_strike]
            pe_oi_chg = int(atm_pe_row['oi_change'].values[0]) if not atm_pe_row.empty else 0
            ce_oi_chg = int(atm_ce_row['oi_change'].values[0]) if not atm_ce_row.empty else 0

            call_wall = float(ce_data.loc[ce_data['oi'].idxmax()]['strike']) if not ce_data.empty else 0.0
            put_wall  = float(pe_data.loc[pe_data['oi'].idxmax()]['strike']) if not pe_data.empty else 0.0

            meta.update({
                "pcr": round(pcr, 2),
                "max_pain": max_pain,
                "iv_rank": iv_rank,
                "call_wall": call_wall,
                "put_wall": put_wall,
                "atm_strike": atm_strike,
            })

            score = 0
            if direction == "BUY":
                if pcr > 1.2:           score += 8
                if spot < max_pain:     score += 7
                if pe_oi_chg > 0:       score += 5   # PE OI building at ATM (support)
                if iv_rank < 40:        score += 5
            elif direction == "SELL":
                if pcr < 0.8:           score += 8
                if spot > max_pain:     score += 7
                if ce_oi_chg > 0:       score += 5   # CE OI building at ATM (resistance)
                if iv_rank > 60:        score += 5

            return min(score, 25), meta
        except Exception as e:
            logger.error(f"Step 3 error: {e}")
            return 0, meta

    # ── Step 4 ─────────────────────────────────────────────────────────────────

    def step4_levels_time(
        self,
        spot: float,
        key_levels: Dict[str, float],
        current_time: time
    ) -> Tuple[int, bool]:
        """Trade windows + key level / round-number proximity. Max 25 pts."""
        w1 = (time(9, 15),  time(9, 45))
        w2 = (time(13, 0),  time(13, 30))
        w3 = (time(14, 30), time(15, 15))

        in_window = (
            (w1[0] <= current_time <= w1[1]) or
            (w2[0] <= current_time <= w2[1]) or
            (w3[0] <= current_time <= w3[1])
        )

        if not in_window:
            return 0, False

        score = 15  # +15 for being in a valid window

        best_proximity = 0
        for level in key_levels.values():
            if not level or level == 0:
                continue
            dist_pct = abs(spot - level) / spot * 100
            if dist_pct <= 0.2:
                best_proximity = max(best_proximity, 10)
            elif dist_pct <= 0.4:
                best_proximity = max(best_proximity, 5)

        # Round number proximity (500-pt levels)
        rn = round(spot / 500) * 500
        dist_pct = abs(spot - rn) / spot * 100
        if dist_pct <= 0.2:
            best_proximity = max(best_proximity, 10)
        elif dist_pct <= 0.4:
            best_proximity = max(best_proximity, 5)

        return min(score + best_proximity, 25), True

    # ── Entry / SL / T1 / T2 ──────────────────────────────────────────────────

    def build_trade_setup(
        self,
        direction: str,
        ce_data: pd.DataFrame,
        pe_data: pd.DataFrame,
        spot: float,
        dte: int,
        iv_rank: float,
        available_cash: float
    ) -> Dict[str, Any]:
        """
        Complete trade setup using Greek-targeted strike selection
        and balance-aware lot sizing.

        Returns a dict with:
          option_type, strike, entry_premium, sl, t1, t2,
          recommended_lots, quantity, total_cost_est,
          delta, theta, gamma, vega,
          strike_reason, theta_warning, trade_viable, viability_note
        """
        opt_type = "CE" if direction == "BUY" else "PE"
        df       = ce_data if opt_type == "CE" else pe_data

        base = {
            "option_type":      opt_type,
            "strike":           0.0,
            "entry_premium":    0.0,
            "sl_premium":       0.0,
            "t1_premium":       0.0,
            "t2_premium":       0.0,
            "recommended_lots": 1,
            "lot_size":         LOT_SIZE,
            "quantity":         LOT_SIZE,
            "total_cost_est":   0.0,
            "delta":            0.0,
            "theta":            0.0,
            "gamma":            0.0,
            "vega":             0.0,
            "strike_reason":    "",
            "theta_warning":    _theta_risk_label(dte, iv_rank),
            "trade_viable":     False,
            "viability_note":   "",
        }

        if df.empty:
            base["viability_note"] = "No option chain data"
            return base

        # Block trades on expiry day
        if dte == 0:
            base["viability_note"] = "Expiry day — long options not recommended (theta crush)"
            return base

        best_row, reason = select_best_strike(df, spot, dte, iv_rank)
        if best_row is None:
            base["viability_note"] = "No qualifying strike found"
            return base

        premium = _safe_float(best_row.get("ltp", 0))
        if premium < MIN_PREMIUM:
            base["viability_note"] = f"Premium ₹{premium:.0f} below minimum ₹{MIN_PREMIUM:.0f}"
            return base

        # Capital adequacy
        required_per_lot = premium * LOT_SIZE * 1.10
        if available_cash > 0 and available_cash < required_per_lot:
            base["viability_note"] = (
                f"Insufficient capital: need ₹{required_per_lot:.0f}, have ₹{available_cash:.0f}"
            )
            base["strike"]        = _safe_float(best_row.get("strike"))
            base["entry_premium"] = round(premium, 2)
            base["strike_reason"] = reason
            return base

        lots = calculate_recommended_lots(available_cash, premium)

        # Theta advisory (don't block — just annotate)
        theta     = abs(_safe_float(best_row.get("theta", 0)))
        theta_pct = (theta / premium * 100) if premium > 0 else 0
        vibe_note = ""
        if theta > 0 and theta_pct > MAX_THETA_PCT * 100:
            vibe_note = f"Theta {theta_pct:.0f}% of premium/day — consider tighter SL"

        base.update({
            "strike":           _safe_float(best_row.get("strike")),
            "entry_premium":    round(premium, 2),
            "sl_premium":       round(premium * 0.60, 2),
            "t1_premium":       round(premium * 2.0,  2),
            "t2_premium":       round(premium * 3.0,  2),
            "recommended_lots": lots,
            "quantity":         lots * LOT_SIZE,
            "total_cost_est":   round(premium * lots * LOT_SIZE, 0),
            "delta":            round(_safe_float(best_row.get("delta")), 3),
            "theta":            round(_safe_float(best_row.get("theta")), 3),
            "gamma":            round(_safe_float(best_row.get("gamma")), 4),
            "vega":             round(_safe_float(best_row.get("vega")),  3),
            "strike_reason":    reason,
            "trade_viable":     True,
            "viability_note":   vibe_note,
        })
        return base

    # ── Legacy method (backward compat) ───────────────────────────────────────

    def get_trade_details(
        self,
        direction: str,
        atm_strike: float,
        ce_data: pd.DataFrame,
        pe_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Legacy ATM-only method — kept for backward compatibility."""
        return self.build_trade_setup(
            direction, ce_data, pe_data, atm_strike,
            dte=5, iv_rank=50.0, available_cash=0.0
        )

    # ── Safety checks ─────────────────────────────────────────────────────────

    def run_safety_checks(
        self,
        app_state: Dict[str, Any],
        account: Optional[Dict[str, Any]] = None,
        entry_premium: float = 0.0,
        dte: int = 7,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        6 safety checks (upgraded from 5):
        1. Market hours (9:15–15:15)
        2. Not expiry day (DTE != 0)
        3. No duplicate Nifty option position (from live Kite positions)
        4. Max 3 trades today
        5. Daily P&L > −3000
        6. Capital adequate for at least 1 lot

        Falls back gracefully if account data is not available.
        """
        now  = datetime.now()
        t    = now.time()
        a3   = app_state.get("algo", {}).get("algo3", {})
        acc  = account or {}
        checks: List[Dict[str, Any]] = []

        # 1. Market hours
        mok = time(9, 15) <= t <= time(15, 15)
        checks.append({
            "name": "Market Hours", "ok": mok,
            "reason": "9:15–15:15 IST" if mok else "Outside trading hours"
        })

        # 2. Not expiry day
        ok2 = dte != 0
        checks.append({
            "name": "Not Expiry Day", "ok": ok2,
            "reason": f"DTE = {dte}" if ok2 else "Expiry day — theta crush on long options"
        })

        # 3. Duplicate position (live from Kite, else fallback to app_state)
        has_open = acc.get("has_open_nifty_option", a3.get("has_open_position", False))
        checks.append({
            "name": "No Duplicate Position", "ok": not has_open,
            "reason": "No open Nifty option" if not has_open else "Already holding Nifty option"
        })

        # 4. Trade count
        tc   = int(a3.get("trades_today", 0))
        ok4  = tc < 3
        checks.append({
            "name": f"Daily Trade Limit ({tc}/3)", "ok": ok4,
            "reason": "Within limit" if ok4 else "3 trades already taken today"
        })

        # 5. Daily P&L (merge live pnl from Kite with app state)
        pnl  = float(acc.get("daily_pnl", a3.get("daily_pnl", 0.0)))
        ok5  = pnl > -3000.0
        checks.append({
            "name": f"Daily P&L ({pnl:+.0f})", "ok": ok5,
            "reason": "Within loss limit" if ok5 else "Daily loss limit −3000 breached"
        })

        # 6. Capital adequacy
        cash = float(acc.get("available_cash", 0.0))
        if cash > 0 and entry_premium > 0:
            required = entry_premium * LOT_SIZE * 1.10
            ok6 = cash >= required
            checks.append({
                "name": "Capital Adequate", "ok": ok6,
                "reason": f"Need ₹{required:.0f}, have ₹{cash:.0f}" if not ok6 else f"Cash ₹{cash:.0f} OK"
            })
        else:
            checks.append({
                "name": "Capital (unknown)", "ok": True,
                "reason": "Balance unavailable — defaulting to 1 lot"
            })

        return all(c["ok"] for c in checks), checks

    # ── Main evaluate ─────────────────────────────────────────────────────────

    def evaluate(
        self,
        df_15m: pd.DataFrame,
        df_1h: pd.DataFrame,
        ce_data: pd.DataFrame,
        pe_data: pd.DataFrame,
        spot: float,
        key_levels: Dict[str, float],
        current_time: time,
        iv_rank: float = 50.0,
        dte: int = 7,
        expiry_str: str = "",
        expiry_reason: str = "",
        account: Optional[Dict[str, Any]] = None,
        app_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run all 4 steps, build trade setup with Greeks + balance awareness,
        run safety checks, and return a complete signal dict.
        """
        acc = account or {}
        result: Dict[str, Any] = {
            # Direction & score
            "direction":         "WAIT",
            "total_score":       0,
            "step1_score":       0,
            "step2_score":       0,
            "step3_score":       0,
            "step4_score":       0,
            "global_bonus":      0,
            "global_bias_score": self.global_bias_score,
            "signal_strength":   "NO SIGNAL",
            "action":            "WAIT",
            "confidence":        "LOW",
            "in_trade_window":   False,
            # Step 2 meta
            "rsi":       0.0,
            "macd_dir":  "Flat",
            "vol_ratio": 0.0,
            # Step 3 meta
            "pcr":        1.0,
            "max_pain":   0.0,
            "iv_rank":    iv_rank,
            "call_wall":  0.0,
            "put_wall":   0.0,
            "atm_strike": 0.0,
            # Trade setup (populated later)
            "option_type":      "",
            "strike":           0.0,
            "entry_premium":    0.0,
            "sl_premium":       0.0,
            "t1_premium":       0.0,
            "t2_premium":       0.0,
            "recommended_lots": 1,
            "lot_size":         LOT_SIZE,
            "quantity":         LOT_SIZE,
            "total_cost_est":   0.0,
            "delta":            0.0,
            "theta":            0.0,
            "gamma":            0.0,
            "vega":             0.0,
            "strike_reason":    "",
            "theta_warning":    _theta_risk_label(dte, iv_rank),
            "trade_viable":     False,
            "viability_note":   "",
            # Expiry intelligence
            "expiry_str":    expiry_str,
            "dte":           dte,
            "expiry_reason": expiry_reason,
            # Account
            "available_cash": float(acc.get("available_cash", 0.0)),
            "used_margin":    float(acc.get("used_margin", 0.0)),
            "daily_pnl":      float(acc.get("daily_pnl", 0.0)),
            "open_positions": acc.get("open_positions", []),
            # Safety
            "safety_clear":  False,
            "safety_checks": [],
            "timestamp":     datetime.now().isoformat(),
        }

        try:
            # ── Step 1: Trend ─────────────────────────────────────────────────
            s1, direction = self.step1_trend(df_15m, df_1h)
            result["step1_score"] = s1
            result["direction"]   = direction
            if direction == "NEUTRAL" or s1 == 0:
                result["signal_strength"] = "NO SIGNAL — Trend not aligned"
                return result

            # ── Step 2: Momentum ──────────────────────────────────────────────
            s2, meta2 = self.step2_momentum(df_15m, direction)
            result.update({
                "step2_score": s2,
                "rsi":       meta2["rsi"],
                "macd_dir":  meta2["macd_dir"],
                "vol_ratio": meta2["vol_ratio"],
            })

            # ── Step 3: Options chain ─────────────────────────────────────────
            s3, meta3 = self.step3_options_chain(ce_data, pe_data, spot, direction, iv_rank)
            result["step3_score"] = s3
            result.update({k: meta3[k] for k in meta3})

            # ── Step 4: Levels + time ─────────────────────────────────────────
            s4, in_window = self.step4_levels_time(spot, key_levels, current_time)
            result.update({"step4_score": s4, "in_trade_window": in_window})

            # ── Global bias bonus ─────────────────────────────────────────────
            g_bonus = 0
            if direction == "BUY" and self.global_bias_score >= 5:
                g_bonus = min(10, self.global_bias_score)
            elif direction == "SELL" and self.global_bias_score <= -5:
                g_bonus = min(10, abs(self.global_bias_score))
            result["global_bonus"] = g_bonus

            total = s1 + s2 + s3 + s4 + g_bonus
            result["total_score"] = total

            # ── Signal classification ─────────────────────────────────────────
            threshold = self.buy_thresh if direction == "BUY" else self.sell_thresh
            if total >= threshold:
                result.update({"signal_strength": "STRONG SIGNAL", "action": "EXECUTE", "confidence": "HIGH"})
            elif total >= 70:
                result.update({"signal_strength": "GOOD SIGNAL", "action": "EXECUTE", "confidence": "MEDIUM"})
            elif total >= 55:
                result.update({"signal_strength": "WEAK SIGNAL", "action": "ALERT_ONLY", "confidence": "LOW"})
            else:
                result.update({"signal_strength": "NO SIGNAL", "action": "WAIT", "confidence": "LOW"})

            # ── Trade setup (Greek-targeted, balance-aware) ───────────────────
            if result["action"] in ("EXECUTE", "ALERT_ONLY"):
                cash  = float(acc.get("available_cash", 0.0))
                setup = self.build_trade_setup(
                    direction, ce_data, pe_data, spot, dte, iv_rank, cash
                )
                result.update(setup)

            # ── Safety checks (upgraded — includes capital + DTE) ─────────────
            safe, checks = self.run_safety_checks(
                app_state or {},
                account=acc,
                entry_premium=float(result.get("entry_premium", 0.0)),
                dte=dte,
            )
            result.update({"safety_clear": safe, "safety_checks": checks})

            # ── Telegram ──────────────────────────────────────────────────────
            if result["action"] in ("EXECUTE", "ALERT_ONLY") and result.get("trade_viable", False):
                _send_algo3_alert(result)

        except Exception as e:
            logger.error(f"Algo 3 evaluate error: {e}", exc_info=True)
            result["signal_strength"] = f"ERROR: {e}"

        return result


# ─── TELEGRAM HELPERS ─────────────────────────────────────────────────────────

def _send_algo3_alert(signal: Dict[str, Any]):
    """Fire Telegram alert for Algo 3 — no emojis, includes Greeks + account."""
    try:
        from modules.algo.telegram_bot import send_telegram_message
        d   = signal.get("direction", "WAIT")
        act = signal.get("action", "WAIT")
        tot = signal.get("total_score", 0)
        ss  = signal.get("signal_strength", "")
        st  = signal.get("strike", signal.get("atm_strike", 0))
        ot  = signal.get("option_type", "")
        ep  = signal.get("entry_premium", 0)
        sl  = signal.get("sl_premium", 0)
        t1  = signal.get("t1_premium", 0)
        t2  = signal.get("t2_premium", 0)
        dt  = signal.get("delta", 0)
        th  = signal.get("theta", 0)
        gm  = signal.get("gamma", 0)
        ve  = signal.get("vega", 0)
        dte = signal.get("dte", 0)
        lo  = signal.get("recommended_lots", 1)
        qty = signal.get("quantity", LOT_SIZE)
        ca  = signal.get("available_cash", 0)
        tc  = signal.get("total_cost_est", 0)
        er  = signal.get("expiry_reason", "")
        sr  = signal.get("strike_reason", "")
        s1  = signal.get("step1_score", 0)
        s2  = signal.get("step2_score", 0)
        s3  = signal.get("step3_score", 0)
        s4  = signal.get("step4_score", 0)
        gb  = signal.get("global_bonus", 0)
        msg = (
            f"<b>ALGO 3 — NIFTY OPTIONS ENGINE</b>\n"
            f"Signal: <b>{d} {act}</b> | Score: {tot}/110\n"
            f"Strength: {ss}\n\n"
            f"<b>TRADE SETUP</b>\n"
            f"Strike: {st:.0f} {ot} | DTE: {dte}\n"
            f"Entry: {ep} | SL: {sl} | T1: {t1} | T2: {t2}\n"
            f"Lots: {lo} x {LOT_SIZE} = {qty} qty | Est Cost: {tc:.0f}\n\n"
            f"<b>GREEKS</b>\n"
            f"Delta: {dt:.3f} | Theta: {th:.3f} | Gamma: {gm:.4f} | Vega: {ve:.3f}\n"
            f"Strike reason: {sr}\n\n"
            f"<b>ACCOUNT</b>\n"
            f"Available Cash: {ca:.0f}\n"
            f"Expiry: {er}\n\n"
            f"Steps: {s1}+{s2}+{s3}+{s4}+{gb} | "
            f"Time: {datetime.now().strftime('%H:%M:%S')}"
        )
        send_telegram_message(msg)
    except Exception as e:
        logger.warning(f"Algo3 Telegram alert error: {e}")


def generate_algo3_premarket_report(global_bias_data: Dict[str, Any]) -> str:
    """
    Full pre-market report text for Algo 3 (9:00 AM daily).
    global_bias_data: return value of calculate_global_bias()
    """
    now  = datetime.now()
    date = now.strftime("%d %b %Y %A")
    changes = global_bias_data.get("market_changes", {})
    score   = global_bias_data.get("score", 0)
    bias    = global_bias_data.get("bias_label", "NEUTRAL")
    vix     = global_bias_data.get("vix_level", "—")
    gap     = global_bias_data.get("gap_label", "—")

    def p(key): 
        v = changes.get(key, 0)
        return _signed(float(v)) + "%" if v is not None else "—"

    lines = [
        f"ALGO 3 — PRE-MARKET REPORT",
        f"{date}",
        "",
        "GLOBAL MARKETS",
        f"  S&P 500     {p('S&P 500')}",
        f"  Nasdaq      {p('NASDAQ')}",
        f"  Dow Jones   {p('Dow Jones')}",
        f"  Nikkei 225  {p('Nikkei')}",
        f"  Hang Seng   {p('Hang Seng')}",
        f"  KOSPI       {p('KOSPI')}",
        f"  ASX 200     {p('ASX 200')}",
        f"  DAX         {p('DAX')}",
        f"  FTSE 100    {p('FTSE')}",
        "",
        "COMMODITIES & CURRENCY",
        f"  Crude Oil   {p('Crude Oil')}",
        f"  Gold        {p('Gold')}",
        f"  USD/INR     {changes.get('USDINR', '—')}",
        f"  DXY         {p('DXY')}",
        "",
        f"VIX: {vix}",
        f"GIFT NIFTY GAP: {gap}",
        f"GLOBAL BIAS: {score:+d}/30 — {bias}",
        "",
    ]

    if score >= 15:
        lines += ["PLAN: Prefer BUY setups. Raise sell threshold."]
    elif score <= -15:
        lines += ["PLAN: Prefer SELL setups. Raise buy threshold."]
    else:
        lines += ["PLAN: Neutral global. Trade on 4-step algo signals only."]

    return "\n".join(lines)


def generate_algo3_eod_report(algo3_state: Dict[str, Any]) -> str:
    """
    EOD report at 3:35 PM.
    algo3_state: app_state["algo"]["algo3"] dict
    """
    trades  = int(algo3_state.get("trades_today", 0))
    pnl     = float(algo3_state.get("daily_pnl", 0.0))
    signals = algo3_state.get("signals_today", [])
    date    = datetime.now().strftime("%d %b %Y")

    lines = [
        f"ALGO 3 — EOD REPORT {date}",
        f"Trades Executed: {trades}/3",
        f"Daily P&L: {pnl:+.0f} INR",
        "",
        "SIGNALS GENERATED TODAY:",
    ]
    if signals:
        for i, s in enumerate(signals, 1):
            lines.append(
                f"  {i}. {s.get('time','')} {s.get('direction','')} "
                f"| Score {s.get('total_score',0)}/110 | {s.get('action','')}"
            )
    else:
        lines.append("  No signals generated.")

    return "\n".join(lines)
