"""
Planetary Yoga Detection Engine for Market Forecasting.

Detects special planetary combinations (Yogas) that historically
correlate with severe or significant market movements.

Uses Swiss Ephemeris via the existing moon_calculator infrastructure.
"""

import swisseph as swe
from datetime import datetime, timedelta
from functools import lru_cache
from typing import List, Dict
import pytz

IST = pytz.timezone('Asia/Kolkata')

# Ayanamsa (Lahiri)
AYANAMSA_TYPE = swe.SIDM_LAHIRI
swe.set_sid_mode(AYANAMSA_TYPE)

# ── Planet IDs ───────────────────────────────────────────────────────────────
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


@lru_cache(maxsize=2048)
def _get_all_longitudes(year: int, month: int, day: int, hour: int, minute: int) -> tuple:
    """Return sidereal longitudes for all major planets. Cached."""
    jd = swe.julday(year, month, day, hour + minute / 60.0)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    result = {}
    for name, pid in PLANETS.items():
        data = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
        trop = data[0][0]
        if name == "Rahu":
            sid = (trop - ayanamsa) % 360.0
        else:
            sid = (trop - ayanamsa) % 360.0
        result[name] = sid

    # Ketu is always 180° from Rahu
    result["Ketu"] = (result["Rahu"] + 180.0) % 360.0

    return tuple(sorted(result.items()))


def _get_longitudes(dt: datetime) -> Dict[str, float]:
    """Get sidereal longitudes for a datetime."""
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    utc = dt.astimezone(pytz.UTC)
    raw = _get_all_longitudes(utc.year, utc.month, utc.day, utc.hour, utc.minute)
    return dict(raw)


def _angular_distance(lon1: float, lon2: float) -> float:
    """Shortest angular distance between two longitudes."""
    diff = abs(lon1 - lon2) % 360
    return min(diff, 360 - diff)


def _same_rashi(lon1: float, lon2: float) -> bool:
    """Check if two longitudes are in the same Rashi (30° sign)."""
    return int(lon1 / 30) == int(lon2 / 30)


def _rashi_number(lon: float) -> int:
    """Get 1-indexed Rashi number."""
    return int(lon / 30) + 1


def _kendra_from(base_rashi: int, target_rashi: int) -> bool:
    """Check if target is in Kendra (1,4,7,10) from base."""
    diff = ((target_rashi - base_rashi) % 12)
    return diff in [0, 3, 6, 9]


# ══════════════════════════════════════════════════════════════════════════════
# YOGA DETECTORS
# Each returns a dict with: name, active (bool), severity, market_impact, desc
# ══════════════════════════════════════════════════════════════════════════════

def detect_angarak_yoga(longs: Dict[str, float]) -> Dict:
    """
    Angarak Yoga: Mars conjunct Rahu (within 15°).
    Effect: Extreme volatility, sudden crashes, panic selling.
    Historical: Very bearish, especially in fire signs (Aries, Leo, Sagittarius).
    """
    dist = _angular_distance(longs["Mars"], longs["Rahu"])
    active = dist < 15.0
    tight = dist < 8.0
    mars_rashi = _rashi_number(longs["Mars"])
    fire_sign = mars_rashi in [1, 5, 9]  # Aries, Leo, Sagittarius

    severity = 0
    if active:
        severity = 9 if (tight and fire_sign) else 8 if tight else 6

    return {
        "name": "Angarak Yoga",
        "sanskrit": "अंगारक योग",
        "active": active,
        "severity": severity,
        "market_impact": "bearish",
        "distance": round(dist, 1),
        "desc": f"Mars-Rahu conjunction ({dist:.1f}°) — extreme volatility, panic selloffs" if active else "Mars-Rahu not conjunct",
        "icon": "🔥",
    }


def detect_guru_chandal_yoga(longs: Dict[str, float]) -> Dict:
    """
    Guru Chandal Yoga: Jupiter conjunct Rahu (within 15°).
    Effect: False rallies, regulatory shocks, misleading market signals.
    """
    dist = _angular_distance(longs["Jupiter"], longs["Rahu"])
    active = dist < 15.0
    tight = dist < 8.0

    return {
        "name": "Guru Chandal Yoga",
        "sanskrit": "गुरु चांडाल योग",
        "active": active,
        "severity": 8 if tight else 6 if active else 0,
        "market_impact": "bearish",
        "distance": round(dist, 1),
        "desc": f"Jupiter-Rahu conjunction ({dist:.1f}°) — false rallies, regulatory surprises" if active else "Jupiter-Rahu not conjunct",
        "icon": "⚡",
    }


def detect_vish_yoga(longs: Dict[str, float]) -> Dict:
    """
    Vish (Poison) Yoga: Moon conjunct Saturn (within 12°).
    Effect: Market depression, low volume, bearish sentiment.
    """
    dist = _angular_distance(longs["Moon"], longs["Saturn"])
    active = dist < 12.0
    tight = dist < 6.0

    return {
        "name": "Vish Yoga",
        "sanskrit": "विष योग",
        "active": active,
        "severity": 7 if tight else 5 if active else 0,
        "market_impact": "bearish",
        "distance": round(dist, 1),
        "desc": f"Moon-Saturn conjunction ({dist:.1f}°) — depressed sentiment, low volumes" if active else "Moon-Saturn not conjunct",
        "icon": "☠️",
    }


def detect_grahan_yoga(longs: Dict[str, float]) -> Dict:
    """
    Grahan (Eclipse) Yoga: Sun or Moon within 10° of Rahu/Ketu.
    Effect: Major trend reversals, black swan events near actual eclipses.
    """
    sun_rahu = _angular_distance(longs["Sun"], longs["Rahu"])
    sun_ketu = _angular_distance(longs["Sun"], longs["Ketu"])
    moon_rahu = _angular_distance(longs["Moon"], longs["Rahu"])
    moon_ketu = _angular_distance(longs["Moon"], longs["Ketu"])

    closest = min(sun_rahu, sun_ketu, moon_rahu, moon_ketu)
    active = closest < 10.0

    which = "Sun" if min(sun_rahu, sun_ketu) < min(moon_rahu, moon_ketu) else "Moon"
    node = "Rahu" if (sun_rahu < sun_ketu if which == "Sun" else moon_rahu < moon_ketu) else "Ketu"

    return {
        "name": "Grahan Yoga",
        "sanskrit": "ग्रहण योग",
        "active": active,
        "severity": 9 if closest < 5 else 7 if active else 0,
        "market_impact": "reversal",
        "distance": round(closest, 1),
        "desc": f"{which} near {node} ({closest:.1f}°) — major trend reversal risk" if active else "No eclipse alignment",
        "icon": "🌑",
    }


def detect_budh_aditya_yoga(longs: Dict[str, float]) -> Dict:
    """
    Budh-Aditya Yoga: Mercury conjunct Sun (within 14°).
    Effect: Strong market intelligence, bullish IT/tech sector.
    Note: Mercury is always within ~28° of Sun, so this is common.
    """
    dist = _angular_distance(longs["Mercury"], longs["Sun"])
    active = dist < 14.0
    combust = dist < 3.0  # Mercury combust = negative

    return {
        "name": "Budh-Aditya Yoga",
        "sanskrit": "बुध-आदित्य योग",
        "active": active,
        "severity": 5 if combust else 3 if active else 0,
        "market_impact": "bearish" if combust else "bullish",
        "distance": round(dist, 1),
        "desc": f"Mercury combust Sun ({dist:.1f}°) — communication breakdowns, IT weakness" if combust else
                f"Mercury-Sun conjunction ({dist:.1f}°) — strong tech/IT sectors" if active else "Mercury-Sun not aligned",
        "icon": "💡" if not combust else "🔇",
    }


def detect_gajakesari_yoga(longs: Dict[str, float]) -> Dict:
    """
    Gajakesari Yoga: Jupiter in Kendra (1,4,7,10) from Moon.
    Effect: Strong market support, institutional buying, bullish overall.
    """
    moon_rashi = _rashi_number(longs["Moon"])
    jup_rashi = _rashi_number(longs["Jupiter"])
    active = _kendra_from(moon_rashi, jup_rashi)

    return {
        "name": "Gajakesari Yoga",
        "sanskrit": "गजकेसरी योग",
        "active": active,
        "severity": 6 if active else 0,
        "market_impact": "bullish",
        "distance": 0,
        "desc": "Jupiter in Kendra from Moon — strong institutional support, bullish momentum" if active else "Jupiter not in Kendra from Moon",
        "icon": "🐘",
    }


def detect_shakata_yoga(longs: Dict[str, float]) -> Dict:
    """
    Shakata Yoga: Jupiter in 6th or 8th from Moon.
    Effect: Sudden reversals, unstable gains, whipsaw markets.
    """
    moon_rashi = _rashi_number(longs["Moon"])
    jup_rashi = _rashi_number(longs["Jupiter"])
    diff = ((jup_rashi - moon_rashi) % 12)
    active = diff in [5, 7]  # 6th or 8th house

    return {
        "name": "Shakata Yoga",
        "sanskrit": "शकट योग",
        "active": active,
        "severity": 5 if active else 0,
        "market_impact": "bearish",
        "distance": 0,
        "desc": "Jupiter in 6/8 from Moon — unstable markets, whipsaw price action" if active else "Shakata Yoga not active",
        "icon": "🎢",
    }


def detect_shubh_kartari(longs: Dict[str, float]) -> Dict:
    """
    Shubh Kartari Yoga: Benefics (Venus, Jupiter, Mercury) flanking Moon.
    Effect: Protected market, unlikely crash, steady bullish.
    """
    moon = longs["Moon"]
    benefics = [longs["Venus"], longs["Jupiter"], longs["Mercury"]]

    before = [b for b in benefics if ((moon - b) % 360) < 30 and ((moon - b) % 360) > 0]
    after = [b for b in benefics if ((b - moon) % 360) < 30 and ((b - moon) % 360) > 0]
    active = len(before) > 0 and len(after) > 0

    return {
        "name": "Shubh Kartari Yoga",
        "sanskrit": "शुभ कर्तरी योग",
        "active": active,
        "severity": 5 if active else 0,
        "market_impact": "bullish",
        "distance": 0,
        "desc": "Benefics flanking Moon — protected market, steady gains" if active else "Shubh Kartari not active",
        "icon": "🛡️",
    }


def detect_paap_kartari(longs: Dict[str, float]) -> Dict:
    """
    Paap Kartari Yoga: Malefics (Mars, Saturn, Rahu, Ketu) flanking Moon.
    Effect: Trapped market, high stress, potential sell-off.
    """
    moon = longs["Moon"]
    malefics = [longs["Mars"], longs["Saturn"], longs["Rahu"], longs["Ketu"]]

    before = [m for m in malefics if ((moon - m) % 360) < 30 and ((moon - m) % 360) > 0]
    after = [m for m in malefics if ((m - moon) % 360) < 30 and ((m - moon) % 360) > 0]
    active = len(before) > 0 and len(after) > 0

    return {
        "name": "Paap Kartari Yoga",
        "sanskrit": "पाप कर्तरी योग",
        "active": active,
        "severity": 7 if active else 0,
        "market_impact": "bearish",
        "distance": 0,
        "desc": "Malefics flanking Moon — trapped market, high selling pressure" if active else "Paap Kartari not active",
        "icon": "⛓️",
    }


def detect_kemdrum_yoga(longs: Dict[str, float]) -> Dict:
    """
    Kemdrum Yoga: No planet within 30° on either side of Moon (except Sun).
    Effect: Low liquidity, directionless market, elevated uncertainty.
    """
    moon = longs["Moon"]
    others = {k: v for k, v in longs.items() if k not in ("Moon", "Sun")}

    nearby = [v for v in others.values() if _angular_distance(moon, v) < 30]
    active = len(nearby) == 0

    return {
        "name": "Kemdrum Yoga",
        "sanskrit": "केमद्रुम योग",
        "active": active,
        "severity": 6 if active else 0,
        "market_impact": "bearish",
        "distance": 0,
        "desc": "Moon isolated — low liquidity, directionless, elevated uncertainty" if active else "Kemdrum not active",
        "icon": "🌫️",
    }


def detect_chandra_mangal_yoga(longs: Dict[str, float]) -> Dict:
    """
    Chandra-Mangal Yoga: Moon conjunct Mars (within 12°).
    Effect: Aggressive trading, high volume, sector-specific sharp moves.
    """
    dist = _angular_distance(longs["Moon"], longs["Mars"])
    active = dist < 12.0

    return {
        "name": "Chandra-Mangal Yoga",
        "sanskrit": "चंद्र-मंगल योग",
        "active": active,
        "severity": 5 if active else 0,
        "market_impact": "volatile",
        "distance": round(dist, 1),
        "desc": f"Moon-Mars conjunction ({dist:.1f}°) — aggressive trading, sharp sector moves" if active else "Moon-Mars not conjunct",
        "icon": "⚔️",
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN API
# ══════════════════════════════════════════════════════════════════════════════

ALL_DETECTORS = [
    detect_angarak_yoga,
    detect_guru_chandal_yoga,
    detect_vish_yoga,
    detect_grahan_yoga,
    detect_budh_aditya_yoga,
    detect_gajakesari_yoga,
    detect_shakata_yoga,
    detect_shubh_kartari,
    detect_paap_kartari,
    detect_kemdrum_yoga,
    detect_chandra_mangal_yoga,
]


def detect_all_yogas(dt: datetime) -> List[Dict]:
    """Detect all planetary yogas for a given datetime."""
    longs = _get_longitudes(dt)
    results = []
    for detector in ALL_DETECTORS:
        result = detector(longs)
        results.append(result)
    return results


def detect_active_yogas(dt: datetime) -> List[Dict]:
    """Return only ACTIVE yogas for a given datetime, sorted by severity desc."""
    all_yogas = detect_all_yogas(dt)
    active = [y for y in all_yogas if y["active"]]
    return sorted(active, key=lambda y: y["severity"], reverse=True)


def get_yoga_market_score(dt: datetime) -> Dict:
    """
    Compute a composite yoga score for market forecasting.

    Returns:
        score: float (-10 to +10), negative = bearish yogas dominate
        active_yogas: list of active yoga dicts
        severity_max: highest severity among active yogas
        summary: text summary
    """
    active = detect_active_yogas(dt)
    if not active:
        return {
            "score": 0,
            "active_yogas": [],
            "severity_max": 0,
            "summary": "No significant planetary yogas active — neutral astro conditions."
        }

    score = 0
    for y in active:
        impact = y["market_impact"]
        sev = y["severity"]
        if impact == "bullish":
            score += sev * 0.5
        elif impact == "bearish":
            score -= sev * 0.7
        elif impact == "reversal":
            score -= sev * 0.5  # reversals lean bearish in uncertainty
        elif impact == "volatile":
            score -= sev * 0.3  # volatility = slight negative

    # Clamp
    score = max(-10, min(10, score))

    severity_max = max(y["severity"] for y in active)

    # Build summary
    bearish_yogas = [y for y in active if y["market_impact"] in ("bearish", "reversal")]
    bullish_yogas = [y for y in active if y["market_impact"] == "bullish"]

    parts = []
    if bearish_yogas:
        names = ", ".join(y["name"] for y in bearish_yogas[:3])
        parts.append(f"⚠️ Bearish pressure from {names}")
    if bullish_yogas:
        names = ", ".join(y["name"] for y in bullish_yogas[:2])
        parts.append(f"✅ Support from {names}")

    return {
        "score": round(score, 1),
        "active_yogas": active,
        "severity_max": severity_max,
        "summary": " · ".join(parts) if parts else "Mixed yoga conditions."
    }
