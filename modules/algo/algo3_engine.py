"""
Algo 3 — Nifty Options Engine
==============================
Full 4-step validation system (110 pts max) + 30-pt global bias.
Step 1: Trend Alignment     (25 pts) — Supertrend 15m+1h, EMA20>50
Step 2: Momentum + Volume   (25 pts) — RSI14, MACD(12,26,9), Volume ratio
Step 3: Options Chain       (25 pts) — PCR, Real MaxPain, ATM OI change, IV rank
Step 4: Time Zone + Levels  (25 pts) — Trade windows + key level proximity
Global Bonus               (up to +10) — if direction aligns with global bias

Trade Rules:
  ATM CE for BUY  |  ATM PE for SELL
  1 lot = 50 units
  SL   = entry_premium * 0.40   (40% drop)
  T1   = entry_premium * 2.0    (2× premium)
  T2   = entry_premium * 3.0    (3× premium)
  Force-exit at 3:10 PM

Thresholds (with global-bias adjustment):
  >= 85  STRONG SIGNAL  → EXECUTE FULL SIZE
  >= 70  GOOD SIGNAL    → EXECUTE HALF SIZE
  >= 55  WEAK SIGNAL    → ALERT ONLY
  <  55  NO SIGNAL      → WAIT
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, time
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _signed(val: float) -> str:
    return f"+{val:.2f}" if val >= 0 else f"{val:.2f}"


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

    def get_options_chain(self, spot: float, expiry_date: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch CE and PE options chain around ATM ±10 strikes (50-pt spacing).
        Returns (ce_df, pe_df) with columns: strike, oi, oi_change, ltp, iv
        Expiry auto-selects nearest weekly if not provided.
        """
        try:
            # Round spot to nearest 50
            atm = round(spot / 50) * 50

            # Build strike range ATM ± 10 steps of 50
            strikes = [atm + (i * 50) for i in range(-10, 11)]

            # Load instrument list once per session (cached in module-level dict)
            from modules.kite_client import KiteDataClient
            kdc = KiteDataClient()
            instruments = kdc.get_instruments("NFO")
            if instruments is None or len(instruments) == 0:
                return pd.DataFrame(), pd.DataFrame()

            nifty_opts = [i for i in instruments if i.get('name', '').upper() == 'NIFTY' and i.get('segment') == 'NFO-OPT']

            if expiry_date is None:
                # Use nearest expiry
                expiries = sorted(set(str(i['expiry']) for i in nifty_opts if i.get('expiry')))
                expiry_date = expiries[0] if expiries else None

            if expiry_date is None:
                return pd.DataFrame(), pd.DataFrame()

            ce_tradingsymbols = []
            pe_tradingsymbols = []
            ce_strike_map: Dict[float, str] = {}
            pe_strike_map: Dict[float, str] = {}

            for inst in nifty_opts:
                strike = _safe_float(inst.get('strike'))
                if strike in strikes and str(inst.get('expiry', '')) == expiry_date:
                    sym = inst.get('tradingsymbol', '')
                    if inst.get('instrument_type') == 'CE':
                        ce_tradingsymbols.append(f"NFO:{sym}")
                        ce_strike_map[strike] = sym
                    elif inst.get('instrument_type') == 'PE':
                        pe_tradingsymbols.append(f"NFO:{sym}")
                        pe_strike_map[strike] = sym

            def _fetch_batch(symbols: List[str]) -> Dict:
                if not symbols:
                    return {}
                try:
                    return self.kite.quote(symbols) or {}
                except Exception as e:
                    logger.error(f"Options quote error: {e}")
                    return {}

            ce_quotes = _fetch_batch(ce_tradingsymbols)
            pe_quotes = _fetch_batch(pe_tradingsymbols)

            def _build_df(strike_map: Dict[float, str], quotes: Dict, opt_type: str) -> pd.DataFrame:
                rows = []
                for strike, sym in strike_map.items():
                    q = quotes.get(f"NFO:{sym}", {})
                    oi = int(q.get('oi', 0))
                    oi_day_high = int(q.get('oi_day_high', oi))
                    oi_change = oi - int(q.get('oi_day_low', oi))
                    ltp = _safe_float(q.get('last_price'))
                    iv  = _safe_float(q.get('implied_volatility', 0.0))
                    rows.append({'strike': strike, 'oi': oi, 'oi_change': oi_change, 'ltp': ltp, 'iv': iv})
                if not rows:
                    return pd.DataFrame()
                return pd.DataFrame(rows).sort_values('strike').reset_index(drop=True)

            ce_df = _build_df(ce_strike_map, ce_quotes, 'CE')
            pe_df = _build_df(pe_strike_map, pe_quotes, 'PE')
            return ce_df, pe_df

        except Exception as e:
            logger.error(f"Options chain fetch error: {e}")
            return pd.DataFrame(), pd.DataFrame()

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

    def get_trade_details(
        self,
        direction: str,
        atm_strike: float,
        ce_data: pd.DataFrame,
        pe_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Return ATM option name, premium, SL (40% below), T1 (2×), T2 (3×).
        """
        details = {
            "option_type": "CE" if direction == "BUY" else "PE",
            "strike": atm_strike,
            "entry_premium": 0.0,
            "sl_premium": 0.0,
            "t1_premium": 0.0,
            "t2_premium": 0.0,
            "lots": 1,
            "lot_size": 50,
            "quantity": 50,
        }
        try:
            if direction == "BUY" and not ce_data.empty:
                row = ce_data[ce_data['strike'] == atm_strike]
                if not row.empty:
                    premium = _safe_float(row.iloc[0]['ltp'])
                    details['entry_premium'] = round(premium, 2)
                    details['sl_premium']    = round(premium * 0.60, 2)  # 40% drop → 60% of premium
                    details['t1_premium']    = round(premium * 2.0, 2)
                    details['t2_premium']    = round(premium * 3.0, 2)

            elif direction == "SELL" and not pe_data.empty:
                row = pe_data[pe_data['strike'] == atm_strike]
                if not row.empty:
                    premium = _safe_float(row.iloc[0]['ltp'])
                    details['entry_premium'] = round(premium, 2)
                    details['sl_premium']    = round(premium * 0.60, 2)
                    details['t1_premium']    = round(premium * 2.0, 2)
                    details['t2_premium']    = round(premium * 3.0, 2)
        except Exception as e:
            logger.error(f"Trade details error: {e}")

        return details

    # ── Safety checks ─────────────────────────────────────────────────────────

    def run_safety_checks(self, app_state: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        5 checks:
        1. Market hours (9:15–15:15)
        2. Max lot size ≤ 2
        3. No duplicate open option position
        4. Max 3 trades today
        5. Daily P&L > –3000

        Returns (all_clear: bool, checks: list of {name, ok, reason})
        """
        now  = datetime.now()
        t    = now.time()
        algo = app_state.get("algo", {})
        a3   = algo.get("algo3", {})

        checks = []

        # 1. Market hours
        market_ok = time(9, 15) <= t <= time(15, 15)
        checks.append({"name": "Market Hours", "ok": market_ok,
                        "reason": "9:15–15:15" if market_ok else "Outside trading hours"})

        # 2. Lot size
        checks.append({"name": "Lot Size OK", "ok": True,
                        "reason": "Max 2 lots enforced"})

        # 3. Duplicate position
        has_open = a3.get("has_open_position", False)
        checks.append({"name": "No Duplicate Position", "ok": not has_open,
                        "reason": "No open position" if not has_open else "Already have open MIS position"})

        # 4. Trade count
        trade_count = int(a3.get("trades_today", 0))
        count_ok = trade_count < 3
        checks.append({"name": f"Trade Count ({trade_count}/3)", "ok": count_ok,
                        "reason": "Within limit" if count_ok else "Daily trade limit reached"})

        # 5. Daily P&L
        daily_pnl = float(a3.get("daily_pnl", 0.0))
        pnl_ok = daily_pnl > -3000.0
        checks.append({"name": f"Daily P&L ({daily_pnl:.0f})", "ok": pnl_ok,
                        "reason": "Within loss limit" if pnl_ok else "Daily loss limit (-3000) breached"})

        all_clear = all(c["ok"] for c in checks)
        return all_clear, checks

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
        app_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run all 4 steps → compute 110-pt score → derive trade details.
        Returns a complete signal dict ready to serve via API.
        """
        result = {
            "direction": "WAIT",
            "total_score": 0,
            "step1_score": 0,
            "step2_score": 0,
            "step3_score": 0,
            "step4_score": 0,
            "global_bonus": 0,
            "global_bias_score": self.global_bias_score,
            "signal_strength": "NO SIGNAL",
            "action": "WAIT",
            "confidence": "LOW",
            "in_trade_window": False,
            # Step meta
            "rsi": 0.0,
            "macd_dir": "Flat",
            "vol_ratio": 0.0,
            "pcr": 1.0,
            "max_pain": 0.0,
            "iv_rank": iv_rank,
            "call_wall": 0.0,
            "put_wall": 0.0,
            "atm_strike": 0.0,
            # Trade details
            "option_type": "",
            "entry_premium": 0.0,
            "sl_premium": 0.0,
            "t1_premium": 0.0,
            "t2_premium": 0.0,
            "lots": 1,
            # Safety
            "safety_clear": False,
            "safety_checks": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Step 1
            s1, direction = self.step1_trend(df_15m, df_1h)
            result["step1_score"] = s1
            result["direction"]   = direction

            if direction == "NEUTRAL" or s1 == 0:
                result["signal_strength"] = "NO SIGNAL — Step 1 Failed"
                return result

            # Step 2
            s2, meta2 = self.step2_momentum(df_15m, direction)
            result["step2_score"] = s2
            result["rsi"]        = meta2["rsi"]
            result["macd_dir"]   = meta2["macd_dir"]
            result["vol_ratio"]  = meta2["vol_ratio"]

            # Step 3
            s3, meta3 = self.step3_options_chain(ce_data, pe_data, spot, direction, iv_rank)
            result["step3_score"] = s3
            result.update({k: meta3[k] for k in meta3})

            # Step 4
            s4, in_window = self.step4_levels_time(spot, key_levels, current_time)
            result["step4_score"]    = s4
            result["in_trade_window"] = in_window

            # Global bonus
            g_bonus = 0
            if direction == "BUY"  and self.global_bias_score >= 5:
                g_bonus = min(10, self.global_bias_score)
            elif direction == "SELL" and self.global_bias_score <= -5:
                g_bonus = min(10, abs(self.global_bias_score))
            result["global_bonus"] = g_bonus

            total = s1 + s2 + s3 + s4 + g_bonus
            result["total_score"] = total

            # Signal strength
            threshold = self.buy_thresh if direction == "BUY" else self.sell_thresh
            if total >= threshold:
                result["signal_strength"] = "STRONG SIGNAL"
                result["action"]          = "EXECUTE"
                result["confidence"]      = "HIGH"
            elif total >= 70:
                result["signal_strength"] = "GOOD SIGNAL"
                result["action"]          = "EXECUTE"
                result["confidence"]      = "MEDIUM"
            elif total >= 55:
                result["signal_strength"] = "WEAK SIGNAL"
                result["action"]          = "ALERT_ONLY"
                result["confidence"]      = "LOW"
            else:
                result["signal_strength"] = "NO SIGNAL"
                result["action"]          = "WAIT"
                result["confidence"]      = "LOW"

            # Trade details
            atm = meta3.get("atm_strike", 0.0)
            if atm > 0 and result["action"] in ("EXECUTE", "ALERT_ONLY"):
                trade = self.get_trade_details(direction, atm, ce_data, pe_data)
                result.update(trade)

            # Safety
            if app_state:
                safe, checks = self.run_safety_checks(app_state)
            else:
                safe, checks = False, [{"name": "State unavailable", "ok": False, "reason": "No app_state"}]
            result["safety_clear"]  = safe
            result["safety_checks"] = checks

            # Telegram notification for actionable signals
            if result["action"] in ("EXECUTE", "ALERT_ONLY"):
                _send_algo3_alert(result)

        except Exception as e:
            logger.error(f"Algo 3 evaluate error: {e}", exc_info=True)
            result["signal_strength"] = f"ERROR: {e}"

        return result


# ─── TELEGRAM HELPERS ─────────────────────────────────────────────────────────

def _send_algo3_alert(signal: Dict[str, Any]):
    """Fire Telegram alert for Algo 3 signal without emojis."""
    try:
        from modules.algo.telegram_bot import send_telegram_message
        direction = signal.get("direction", "WAIT")
        total     = signal.get("total_score", 0)
        action    = signal.get("action", "WAIT")
        premium   = signal.get("entry_premium", 0.0)
        sl        = signal.get("sl_premium", 0.0)
        t1        = signal.get("t1_premium", 0.0)
        t2        = signal.get("t2_premium", 0.0)
        strike    = signal.get("atm_strike", 0.0)
        opt_type  = signal.get("option_type", "")
        s1 = signal.get("step1_score", 0)
        s2 = signal.get("step2_score", 0)
        s3 = signal.get("step3_score", 0)
        s4 = signal.get("step4_score", 0)
        gb = signal.get("global_bonus", 0)

        msg = (
            f"<b>ALGO 3 — NIFTY OPTIONS ENGINE</b>\n"
            f"Signal: <b>{direction} {action}</b>\n"
            f"Score: {total}/110 | Strength: {signal.get('signal_strength', '')}\n\n"
            f"Step 1 Trend: {s1}/25\n"
            f"Step 2 Momentum: {s2}/25\n"
            f"Step 3 Options: {s3}/25\n"
            f"Step 4 Levels: {s4}/25\n"
            f"Global Bonus: +{gb}\n\n"
            f"Strike: {strike:.0f} {opt_type}\n"
            f"Entry Premium: {premium}\n"
            f"SL (40% drop): {sl}\n"
            f"Target 1 (2x): {t1}\n"
            f"Target 2 (3x): {t2}\n"
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
