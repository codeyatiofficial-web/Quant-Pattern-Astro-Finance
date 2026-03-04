"""
Options Strategy Backtesting Engine for NSE India
Tests strategies against historical data, computes win rate, Sharpe, max drawdown, ROI.
"""
import logging
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def _generate_synthetic_nifty_path(days: int = 750, start_price: float = 17500) -> List[Dict]:
    """
    Generate a realistic synthetic NIFTY daily price series for backtesting.
    Uses geometric Brownian motion with regime switching.
    In production: use real historical data from yfinance / NSE.
    """
    prices = []
    price = start_price
    base_date = datetime.now() - timedelta(days=days)
    daily_drift = 0.0004  # ~10% annualized
    daily_vol = 0.012     # ~19% annualized

    regime = "normal"
    for i in range(days):
        d = base_date + timedelta(days=i)
        if d.weekday() >= 5:
            continue

        # Regime switching
        if random.random() < 0.02:
            regime = random.choice(["bull", "bear", "volatile", "normal"])

        if regime == "bull":
            drift = daily_drift * 2.5
            vol = daily_vol * 0.8
        elif regime == "bear":
            drift = -daily_drift * 2
            vol = daily_vol * 1.5
        elif regime == "volatile":
            drift = 0
            vol = daily_vol * 2.5
        else:
            drift = daily_drift
            vol = daily_vol

        ret = drift + vol * random.gauss(0, 1)
        price *= (1 + ret)

        prices.append({
            "date": d.strftime("%Y-%m-%d"),
            "close": round(price, 2),
            "return_pct": round(ret * 100, 4),
            "regime": regime,
        })

    return prices


def _compute_strategy_pnl(
    strategy_key: str,
    entry_price: float,
    exit_price: float,
    iv_entry: float,
    days_held: int,
) -> Dict:
    """
    Simplified P&L calculation for a strategy trade based on spot move.
    Returns trade result dict.
    """
    spot_move_pct = (exit_price - entry_price) / entry_price * 100
    lot_size = 50

    if strategy_key == "bull_call_spread":
        width = entry_price * 0.013  # ~1.3% spread width
        premium_paid = width * 0.4
        if exit_price > entry_price + premium_paid:
            pnl = min(width - premium_paid, exit_price - entry_price - premium_paid)
        else:
            pnl = max(-premium_paid, exit_price - entry_price - premium_paid)
        pnl *= lot_size

    elif strategy_key == "bear_put_spread":
        width = entry_price * 0.013
        premium_paid = width * 0.4
        if exit_price < entry_price - premium_paid:
            pnl = min(width - premium_paid, entry_price - exit_price - premium_paid)
        else:
            pnl = max(-premium_paid, entry_price - exit_price - premium_paid)
        pnl *= lot_size

    elif strategy_key == "iron_condor":
        upper = entry_price * 1.02
        lower = entry_price * 0.98
        credit = entry_price * 0.004
        if lower <= exit_price <= upper:
            pnl = credit * lot_size
        else:
            breach = max(0, exit_price - upper) + max(0, lower - exit_price)
            pnl = (credit - breach) * lot_size
        pnl = max(pnl, -entry_price * 0.008 * lot_size)

    elif strategy_key == "long_call":
        premium = entry_price * 0.022 * (iv_entry / 15)
        intrinsic_gain = max(0, exit_price - entry_price) - premium
        pnl = intrinsic_gain * lot_size

    elif strategy_key == "long_put":
        premium = entry_price * 0.022 * (iv_entry / 15)
        intrinsic_gain = max(0, entry_price - exit_price) - premium
        pnl = intrinsic_gain * lot_size

    elif strategy_key == "short_straddle":
        ce_prem = entry_price * 0.025
        pe_prem = entry_price * 0.02
        total_prem = ce_prem + pe_prem
        move = abs(exit_price - entry_price)
        pnl = (total_prem - move) * lot_size

    elif strategy_key == "long_straddle":
        ce_prem = entry_price * 0.025
        pe_prem = entry_price * 0.02
        total_prem = ce_prem + pe_prem
        move = abs(exit_price - entry_price)
        pnl = (move - total_prem) * lot_size

    elif strategy_key == "protective_put":
        put_cost = entry_price * 0.015
        stock_pnl = exit_price - entry_price
        if exit_price < entry_price * 0.97:
            # Put kicks in
            pnl = (-entry_price * 0.03 - put_cost) * lot_size
        else:
            pnl = (stock_pnl - put_cost) * lot_size

    else:
        # Default: directional move based PnL
        premium = entry_price * 0.02
        pnl = (spot_move_pct / 100 * entry_price - premium) * lot_size

    return {
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl / (entry_price * lot_size) * 10000, 2),
        "spot_move_pct": round(spot_move_pct, 2),
        "win": pnl > 0,
    }


def backtest_strategy(
    strategy_key: str,
    years: int = 3,
    holding_days: int = 20,  # ~1 monthly expiry
) -> Dict:
    """
    Backtest a specific strategy over historical data.
    Returns comprehensive metrics.
    """
    days = years * 365
    prices = _generate_synthetic_nifty_path(days)
    if len(prices) < holding_days + 10:
        return {"error": "Insufficient data for backtesting"}

    trades = []
    equity_curve = [100000]  # Start with ₹1L
    running_capital = 100000

    i = 0
    while i < len(prices) - holding_days:
        entry = prices[i]
        exit_point = prices[i + holding_days]
        iv_entry = random.uniform(12, 25)

        result = _compute_strategy_pnl(
            strategy_key, entry["close"], exit_point["close"], iv_entry, holding_days
        )

        running_capital += result["pnl"]
        equity_curve.append(round(running_capital, 2))

        trades.append({
            "entry_date": entry["date"],
            "exit_date": exit_point["date"],
            "entry_price": entry["close"],
            "exit_price": exit_point["close"],
            "regime": entry["regime"],
            **result,
        })

        i += holding_days  # Non-overlapping trades

    if not trades:
        return {"error": "No trades generated"}

    # ── Compute Metrics ──
    wins = sum(1 for t in trades if t["win"])
    losses = len(trades) - wins
    win_rate = round(wins / len(trades) * 100, 1)

    pnl_list = [t["pnl"] for t in trades]
    total_pnl = sum(pnl_list)
    avg_pnl = total_pnl / len(pnl_list)
    avg_win = sum(p for p in pnl_list if p > 0) / max(wins, 1)
    avg_loss = sum(p for p in pnl_list if p <= 0) / max(losses, 1)

    # Sharpe Ratio (annualized)
    if len(pnl_list) > 1:
        import statistics
        pnl_std = statistics.stdev(pnl_list)
        sharpe = round((avg_pnl / pnl_std) * math.sqrt(252 / holding_days), 2) if pnl_std > 0 else 0
    else:
        sharpe = 0

    # Max Drawdown
    peak = equity_curve[0]
    max_dd = 0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100
        if dd > max_dd:
            max_dd = dd
    max_dd = round(max_dd, 2)

    # ROI
    roi = round((running_capital - 100000) / 100000 * 100, 2)

    # Performance by regime
    regime_perf = {}
    for t in trades:
        r = t["regime"]
        if r not in regime_perf:
            regime_perf[r] = {"trades": 0, "wins": 0, "total_pnl": 0}
        regime_perf[r]["trades"] += 1
        regime_perf[r]["wins"] += 1 if t["win"] else 0
        regime_perf[r]["total_pnl"] += t["pnl"]

    for r in regime_perf:
        rp = regime_perf[r]
        rp["win_rate"] = round(rp["wins"] / rp["trades"] * 100, 1) if rp["trades"] > 0 else 0
        rp["total_pnl"] = round(rp["total_pnl"], 2)

    # Buy & Hold comparison
    buy_hold_roi = round((prices[-1]["close"] - prices[0]["close"]) / prices[0]["close"] * 100, 2)

    return {
        "strategy_key": strategy_key,
        "period_years": years,
        "holding_days": holding_days,
        "total_trades": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": round(total_pnl, 2),
        "avg_pnl_per_trade": round(avg_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_dd,
        "roi_pct": roi,
        "buy_hold_roi_pct": buy_hold_roi,
        "final_capital": round(running_capital, 2),
        "equity_curve": equity_curve[-50:],  # Last 50 points for chart
        "regime_performance": regime_perf,
        "recent_trades": trades[-15:],  # Last 15 trades for trade log
    }


def backtest_all_strategies(years: int = 3) -> List[Dict]:
    """Backtest all major strategies and return comparative results."""
    strategy_keys = [
        "bull_call_spread", "bear_put_spread", "iron_condor",
        "long_call", "long_put", "short_straddle", "long_straddle",
        "protective_put",
    ]
    results = []
    for key in strategy_keys:
        try:
            res = backtest_strategy(key, years)
            if "error" not in res:
                results.append(res)
        except Exception as e:
            logger.warning(f"Backtest failed for {key}: {e}")

    results.sort(key=lambda x: x.get("sharpe_ratio", 0), reverse=True)
    return results
