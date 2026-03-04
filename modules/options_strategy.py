"""
Options Strategy Recommender Engine for NSE India
Recommends optimal strategies based on market conditions, forecast, IV, and risk appetite.
Offers strategies for all outlooks (Bullish, Bearish, Neutral) and computes real premiums.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy Definitions
# ---------------------------------------------------------------------------

STRATEGIES = {
    # ── Bullish ──
    "long_call": {
        "name": "Long Call",
        "category": "BULLISH",
        "legs": 1,
        "description": "Buy a call option to profit from upward price movement.",
        "best_when": "Strong bullish view, limited downside risk desired.",
        "iv_preference": "Low IV (cheaper premium)",
        "risk_profile": "Limited risk (premium paid), unlimited profit potential",
        "complexity": "Simple",
    },
    "bull_call_spread": {
        "name": "Bull Call Spread",
        "category": "BULLISH",
        "legs": 2,
        "description": "Buy lower strike call, sell higher strike call. Reduces cost vs naked call.",
        "best_when": "Moderately bullish, want to reduce premium outlay.",
        "iv_preference": "Low to Moderate IV",
        "risk_profile": "Limited risk & limited profit",
        "complexity": "Moderate",
    },
    "bull_put_spread": {
        "name": "Bull Put Spread",
        "category": "BULLISH",
        "legs": 2,
        "description": "Sell higher strike put, buy lower strike put. Credit strategy.",
        "best_when": "Mildly bullish, want to collect premium (theta decay).",
        "iv_preference": "High IV (more premium collected)",
        "risk_profile": "Limited risk & limited profit (credit received)",
        "complexity": "Moderate",
    },
    # ── Bearish ──
    "long_put": {
        "name": "Long Put",
        "category": "BEARISH",
        "legs": 1,
        "description": "Buy a put option to profit from downward movement.",
        "best_when": "Strong bearish view.",
        "iv_preference": "Low IV (cheaper premium)",
        "risk_profile": "Limited risk (premium), large profit potential",
        "complexity": "Simple",
    },
    "bear_put_spread": {
        "name": "Bear Put Spread",
        "category": "BEARISH",
        "legs": 2,
        "description": "Buy higher strike put, sell lower strike put.",
        "best_when": "Moderately bearish, reduce cost.",
        "iv_preference": "Low to Moderate IV",
        "risk_profile": "Limited risk & limited profit",
        "complexity": "Moderate",
    },
    "bear_call_spread": {
        "name": "Bear Call Spread",
        "category": "BEARISH",
        "legs": 2,
        "description": "Sell lower strike call, buy higher strike call. Credit strategy.",
        "best_when": "Mildly bearish, collect premium (theta/IV crush).",
        "iv_preference": "High IV (more premium)",
        "risk_profile": "Limited risk & limited profit (credit received)",
        "complexity": "Moderate",
    },
    # ── Neutral ──
    "iron_condor": {
        "name": "Iron Condor",
        "category": "NEUTRAL",
        "legs": 4,
        "description": "Sell OTM put/call spreads. Profit from rangebound market.",
        "best_when": "Expect sideways/range-bound, high IV for premium collection.",
        "iv_preference": "High IV (max premium, IV crush profit)",
        "risk_profile": "Limited risk & limited profit",
        "complexity": "Advanced",
    },
    "short_strangle": {
        "name": "Short Strangle",
        "category": "NEUTRAL",
        "legs": 2,
        "description": "Sell OTM call + OTM put. Wider profit zone vs straddle.",
        "best_when": "Expect rangebound, high IV.",
        "iv_preference": "High IV",
        "risk_profile": "Unlimited risk, limited profit",
        "complexity": "Advanced",
    },
    "long_straddle": {
        "name": "Long Straddle",
        "category": "NEUTRAL",
        "legs": 2,
        "description": "Buy ATM call + ATM put. Profit from big move in either direction.",
        "best_when": "Expect big move but unsure of direction.",
        "iv_preference": "Low IV (cheap entry before expected IV expansion)",
        "risk_profile": "Limited risk (premium), unlimited profit",
        "complexity": "Simple",
    },
}

# ---------------------------------------------------------------------------
# Options Leg Builder (35-year expert sizing)
# ---------------------------------------------------------------------------

def _build_actual_trade_legs(strategy_key: str, spot: float, chain: List[Dict]) -> Dict:
    """Builds the exact trade legs, max profit/loss based on the live chain."""
    if not chain:
        return {"legs": [], "max_profit": 0, "max_loss": 0, "trade_description": "Chain data missing.", "expert_insight": "Cannot build trade without live option chain."}

    # Find ATM
    atm_strike = min(chain, key=lambda r: abs(r["strike"] - spot))["strike"]
    atm_idx = next((i for i, r in enumerate(chain) if r["strike"] == atm_strike), len(chain)//2)
    
    legs = []
    trade_desc = ""
    insight = ""
    net_debit = 0
    net_credit = 0

    if strategy_key == "long_call":
        prem = chain[atm_idx]["CE"]["price"]
        legs = [{"action": "BUY", "type": "CE", "strike": atm_strike, "premium": prem}]
        max_loss = prem * 50
        max_profit = "Unlimited"
        trade_desc = f"Buy ATM {atm_strike} CE at ₹{prem:.1f}"
        insight = f"Taking a naked directional bet. ATM strikes offer >0.50 delta, giving immediate response to underlying movement. Ensure tight 30% stop-loss."
        
    elif strategy_key == "bull_call_spread":
        buy_idx = atm_idx
        # 3 strikes out for selling
        sell_idx = min(atm_idx + 3, len(chain) - 1)
        buy_prem = chain[buy_idx]["CE"]["price"]
        sell_prem = chain[sell_idx]["CE"]["price"]
        net_debit = buy_prem - sell_prem
        width = chain[sell_idx]["strike"] - chain[buy_idx]["strike"]
        legs = [
            {"action": "BUY", "type": "CE", "strike": chain[buy_idx]["strike"], "premium": buy_prem},
            {"action": "SELL", "type": "CE", "strike": chain[sell_idx]["strike"], "premium": sell_prem},
        ]
        max_loss = net_debit * 50
        max_profit = (width - net_debit) * 50
        trade_desc = f"Buy {chain[buy_idx]['strike']} CE at ₹{buy_prem:.1f} | Sell {chain[sell_idx]['strike']} CE at ₹{sell_prem:.1f} (Net Debit: ₹{net_debit:.1f})"
        insight = f"A classic low-risk play. Selling the {chain[sell_idx]['strike']} CE offsets theta decay and reduces capital requirement by ₹{sell_prem * 50:.0f} per lot via IV exposure offset."

    elif strategy_key == "bull_put_spread":
        # Sell ATM put, buy OTM put (credit)
        sell_idx = atm_idx
        buy_idx = max(atm_idx - 3, 0)
        sell_prem = chain[sell_idx]["PE"]["price"]
        buy_prem = chain[buy_idx]["PE"]["price"]
        net_credit = sell_prem - buy_prem
        width = chain[sell_idx]["strike"] - chain[buy_idx]["strike"]
        legs = [
            {"action": "SELL", "type": "PE", "strike": chain[sell_idx]["strike"], "premium": sell_prem},
            {"action": "BUY", "type": "PE", "strike": chain[buy_idx]["strike"], "premium": buy_prem},
        ]
        max_profit = net_credit * 50
        max_loss = (width - net_credit) * 50
        trade_desc = f"Sell {chain[sell_idx]['strike']} PE at ₹{sell_prem:.1f} | Buy {chain[buy_idx]['strike']} PE at ₹{buy_prem:.1f} (Net Credit: ₹{net_credit:.1f})"
        insight = f"High probability institutional trade. You simply need the underlying to stay above {chain[sell_idx]['strike'] - net_credit:.0f}. Theta decay works purely in your favor."

    elif strategy_key == "long_put":
        prem = chain[atm_idx]["PE"]["price"]
        legs = [{"action": "BUY", "type": "PE", "strike": atm_strike, "premium": prem}]
        max_loss = prem * 50
        max_profit = "Unlimited"
        trade_desc = f"Buy ATM {atm_strike} PE at ₹{prem:.1f}"
        insight = f"Pure downside velocity play. Puts generally price IV expansion into drops. Exit quickly if structural support holds."

    elif strategy_key == "bear_put_spread":
        buy_idx = atm_idx
        sell_idx = max(atm_idx - 3, 0)
        buy_prem = chain[buy_idx]["PE"]["price"]
        sell_prem = chain[sell_idx]["PE"]["price"]
        net_debit = buy_prem - sell_prem
        width = chain[buy_idx]["strike"] - chain[sell_idx]["strike"]
        legs = [
            {"action": "BUY", "type": "PE", "strike": chain[buy_idx]["strike"], "premium": buy_prem},
            {"action": "SELL", "type": "PE", "strike": chain[sell_idx]["strike"], "premium": sell_prem},
        ]
        max_loss = net_debit * 50
        max_profit = (width - net_debit) * 50
        trade_desc = f"Buy {chain[buy_idx]['strike']} PE at ₹{buy_prem:.1f} | Sell {chain[sell_idx]['strike']} PE at ₹{sell_prem:.1f} (Net Debit: ₹{net_debit:.1f})"
        insight = f"Safer than a naked put. The sold {chain[sell_idx]['strike']} leg insulates against an IV collapse that typically happens during minor pullbacks."

    elif strategy_key == "bear_call_spread":
        sell_idx = atm_idx
        buy_idx = min(atm_idx + 3, len(chain) - 1)
        sell_prem = chain[sell_idx]["CE"]["price"]
        buy_prem = chain[buy_idx]["CE"]["price"]
        net_credit = sell_prem - buy_prem
        width = chain[buy_idx]["strike"] - chain[sell_idx]["strike"]
        legs = [
            {"action": "SELL", "type": "CE", "strike": chain[sell_idx]["strike"], "premium": sell_prem},
            {"action": "BUY", "type": "CE", "strike": chain[buy_idx]["strike"], "premium": buy_prem},
        ]
        max_profit = net_credit * 50
        max_loss = (width - net_credit) * 50
        trade_desc = f"Sell {chain[sell_idx]['strike']} CE at ₹{sell_prem:.1f} | Buy {chain[buy_idx]['strike']} CE at ₹{buy_prem:.1f} (Net Credit: ₹{net_credit:.1f})"
        insight = f"Excellent way to short the market without exposure to IV spikes. Max reward achieved simply if the price stays below {chain[sell_idx]['strike'] + net_credit:.0f}."
        
    elif strategy_key == "iron_condor":
        sell_put = max(atm_idx - 3, 0)
        buy_put = max(atm_idx - 5, 0)
        sell_call = min(atm_idx + 3, len(chain) - 1)
        buy_call = min(atm_idx + 5, len(chain) - 1)
        sp = chain[sell_put]["PE"]["price"]
        bp = chain[buy_put]["PE"]["price"]
        sc = chain[sell_call]["CE"]["price"]
        bc = chain[buy_call]["CE"]["price"]
        net_credit = (sp - bp) + (sc - bc)
        wing_risk = (chain[buy_call]["strike"] - chain[sell_call]["strike"])
        legs = [
            {"action": "SELL", "type": "PE", "strike": chain[sell_put]["strike"], "premium": sp},
            {"action": "BUY", "type": "PE", "strike": chain[buy_put]["strike"], "premium": bp},
            {"action": "SELL", "type": "CE", "strike": chain[sell_call]["strike"], "premium": sc},
            {"action": "BUY", "type": "CE", "strike": chain[buy_call]["strike"], "premium": bc},
        ]
        max_profit = net_credit * 50
        max_loss = (wing_risk - net_credit) * 50
        trade_desc = f"Sell Iron Condor: {chain[buy_put]['strike']}P/{chain[sell_put]['strike']}P & {chain[sell_call]['strike']}C/{chain[buy_call]['strike']}C (Credit: ₹{net_credit:.1f})"
        insight = f"A strict non-directional theta trade. Ideal execution occurs roughly 35-45 days out. Profit zone requires the price to remain trapped between {chain[sell_put]['strike']} and {chain[sell_call]['strike']}."

    elif strategy_key == "short_strangle":
        sell_put = max(atm_idx - 3, 0)
        sell_call = min(atm_idx + 3, len(chain) - 1)
        sp = chain[sell_put]["PE"]["price"]
        sc = chain[sell_call]["CE"]["price"]
        net_credit = sp + sc
        legs = [
            {"action": "SELL", "type": "PE", "strike": chain[sell_put]["strike"], "premium": sp},
            {"action": "SELL", "type": "CE", "strike": chain[sell_call]["strike"], "premium": sc},
        ]
        max_profit = net_credit * 50
        max_loss = "Unlimited"
        trade_desc = f"Sell {chain[sell_put]['strike']} PE at ₹{sp:.1f} | Sell {chain[sell_call]['strike']} CE at ₹{sc:.1f} (Credit: ₹{net_credit:.1f})"
        insight = f"High probability premium collection but demands strict delta hedging. Only execute if historical volatility confirms current implied levels are vastly overstated."

    elif strategy_key == "long_straddle":
        ce = chain[atm_idx]["CE"]["price"]
        pe = chain[atm_idx]["PE"]["price"]
        debit = ce + pe
        legs = [
            {"action": "BUY", "type": "CE", "strike": atm_strike, "premium": ce},
            {"action": "BUY", "type": "PE", "strike": atm_strike, "premium": pe},
        ]
        max_profit = "Unlimited"
        max_loss = debit * 50
        trade_desc = f"Buy ATM {atm_strike} CE/PE pairing (Total Cost: ₹{debit:.1f})"
        insight = f"A pure volatility expansion play. Requires a massive >{(debit/atm_strike)*100 if atm_strike>0 else 0:.1f}% move merely to break even. Best used right before known binary events (RBI/Earnings)."
    else:
        # Fallback
        trade_desc = f"Custom Execution on {atm_strike} Strike"
        max_profit, max_loss = 0, 0
        insight = "Standard options spread."

    return {
        "legs": legs,
        "max_profit": max_profit if isinstance(max_profit, str) else round(max_profit, 2),
        "max_loss": max_loss if isinstance(max_loss, str) else round(max_loss, 2),
        "trade_description": trade_desc,
        "expert_insight": insight,
    }


def _classify_iv(avg_iv: float) -> str:
    if avg_iv < 14: return "LOW"
    elif avg_iv < 20: return "MODERATE"
    else: return "HIGH"

def _classify_risk(risk_appetite: str) -> int:
    mapping = {"conservative": 1, "moderate": 2, "aggressive": 3}
    return mapping.get(risk_appetite.lower(), 2)


def recommend_strategies(
    forecast: str,
    confidence: float,
    avg_iv: float,
    pcr: float,
    spot: float = 0.0,
    chain: List[Dict] = None,
    risk_appetite: str = "moderate",
    fii_net: float = 0,
    capital: float = 100000,
) -> Dict[str, List[Dict]]:
    """
    Recommend strategies categorized by market view (BULLISH, BEARISH, NEUTRAL).
    Builds exact trades with live strikes/premiums via the options chain.
    """
    iv_class = _classify_iv(avg_iv)
    risk_level = _classify_risk(risk_appetite)
    
    # We will return a categorized dictionary
    categorized_recs = {
        "BULLISH": [],
        "BEARISH": [],
        "NEUTRAL": [],
    }

    if not chain or spot <= 0:
        return categorized_recs

    for key, strat in STRATEGIES.items():
        score = 0
        reasons = []

        cat = strat["category"]

        # ── Forecast Context ──
        if cat == forecast:
            score += 20
            reasons.append(f"Top choice: Matches your overall {forecast.lower()} market forecast")
        else:
            reasons.append(f"Alternative outlook: A 35-yr expert play for a {cat.lower()} market perspective")

        # ── IV preference matching ──
        iv_pref = strat["iv_preference"]
        if iv_class == "HIGH":
            if "High" in iv_pref:
                score += 20
                reasons.append(f"IV is {avg_iv:.1f}% (High) — ideal for theta/vega decay setups")
            elif "Low" in iv_pref:
                score -= 10
                reasons.append(f"High IV makes premium buying expensive; tighter stops needed")
        elif iv_class == "LOW":
            if "Low" in iv_pref:
                score += 20
                reasons.append(f"IV is {avg_iv:.1f}% (Low) — excellent cheap premium buying setup")
            elif "High" in iv_pref:
                score -= 10
                reasons.append("Premium selling is risky here; low IV means insufficient credit received")

        # ── Risk profile ──
        complexity = strat["complexity"]
        if complexity == "Simple":
            score += 10
        elif complexity == "Moderate" and risk_level >= 2:
            score += 10
        elif complexity == "Advanced":
            if risk_level >= 3:
                score += 10
                reasons.append("Leverages your aggressive risk profile")
            else:
                score -= 15

        # Base threshold to show the strategy
        if score > -10:
            trade_details = _build_actual_trade_legs(key, spot, chain)
            if not trade_details["legs"]:
                continue
                
            strat_info = {
                **strat,
                "key": key,
                "score": score,
                "reasons": reasons,
                "trade_description": trade_details["trade_description"],
                "expert_insight": trade_details["expert_insight"],
                "legs": trade_details["legs"],
                "max_profit": trade_details["max_profit"],
                "max_loss": trade_details["max_loss"],
            }
            categorized_recs[cat].append(strat_info)

    # Sort each category descending by score
    for cat in categorized_recs:
        categorized_recs[cat].sort(key=lambda x: x["score"], reverse=True)
        # Keep top 3 for each category
        categorized_recs[cat] = categorized_recs[cat][:3]

    return categorized_recs


def build_strategy_payoff(strategy_key: str, spot: float, chain: List[Dict], days_to_expiry: int) -> Dict:
    """Payoff builder using actual trade legs for exact math."""
    trade = _build_actual_trade_legs(strategy_key, spot, chain)
    legs = trade["legs"]
    payoff_points = []
    
    if not legs:
        return {"payoff_curve": [], "breakeven": spot, "max_profit": 0, "max_loss": 0, "legs": []}
        
    strike_range = [r["strike"] for r in chain]
    low, high = min(strike_range), max(strike_range)
    
    breakeven = spot
    if "call" in strategy_key and len(legs) > 0: 
        breakeven = legs[0]["strike"]
    elif "put" in strategy_key and len(legs) > 0:
        breakeven = legs[0]["strike"]

    for price in range(int(low), int(high) + 1, 50):
        pnl = 0
        for leg in legs:
            mult = 50 if leg["action"] == "BUY" else -50
            if leg["type"] == "CE":
                intrinsic = max(0, price - leg["strike"])
            else:
                intrinsic = max(0, leg["strike"] - price)
            pnl += mult * (intrinsic - leg["premium"])
        payoff_points.append({"price": price, "pnl": round(pnl, 2)})

    return {
        "strategy_key": strategy_key,
        "legs": legs,
        "max_profit": trade["max_profit"],
        "max_loss": trade["max_loss"],
        "breakeven": round(breakeven, 2),
        "payoff_curve": payoff_points,
    }
