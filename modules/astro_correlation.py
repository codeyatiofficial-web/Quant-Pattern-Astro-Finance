"""
Astro-Correlation Engine for quantitative statistical analysis of planetary events versus market performance.
Calculates p-values, t-tests, and correlation matrices using scipy.
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
import pytz
import swisseph as swe
import os

from modules.market_data import MarketDataFetcher

# Set ephemeris data path
EPHEMERIS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ephemeris')
if os.path.isdir(EPHEMERIS_PATH):
    swe.set_ephe_path(EPHEMERIS_PATH)

IST = pytz.timezone('Asia/Kolkata')

PLANET_MAP = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Ketu": swe.MEAN_NODE,
}

# 1-Aries, 2-Taurus, 3-Gemini, 4-Cancer, 5-Leo, 6-Virgo
# 7-Libra, 8-Scorpio, 9-Sagittarius, 10-Capricorn, 11-Aquarius, 12-Pisces
EXALTATION_MAP = {
    "Sun": 1,        # Aries
    "Moon": 2,       # Taurus
    "Jupiter": 4,    # Cancer
    "Mercury": 6,    # Virgo
    "Saturn": 7,     # Libra
    "Ketu": 8,       # Scorpio (Secondary) / Sagittarius
    "Mars": 10,      # Capricorn
    "Venus": 12,     # Pisces
    "Rahu": 2,       # Taurus (Secondary) / Gemini
}

DEBILITATION_MAP = {
    "Sun": 7,        # Libra
    "Moon": 8,       # Scorpio
    "Jupiter": 10,   # Capricorn
    "Mercury": 12,   # Pisces
    "Saturn": 1,     # Aries
    "Ketu": 2,       # Taurus (Secondary) / Gemini
    "Mars": 4,       # Cancer
    "Venus": 6,      # Virgo
    "Rahu": 8,       # Scorpio (Secondary) / Sagittarius
}

OWN_HOUSE_MAP = {
    "Sun": [5],            # Leo
    "Moon": [4],           # Cancer
    "Jupiter": [9, 12],    # Sagittarius, Pisces
    "Mercury": [3, 6],     # Gemini, Virgo
    "Saturn": [10, 11],    # Capricorn, Aquarius
    "Ketu": [8],           # Scorpio (Co-lord)
    "Mars": [1, 8],        # Aries, Scorpio
    "Venus": [2, 7],       # Taurus, Libra
    "Rahu": [11],          # Aquarius (Co-lord)
}

class AstroCorrelationEngine:
    def __init__(self):
        self.market = MarketDataFetcher()
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def _get_planet_metrics(self, dt: datetime, planet_id: int) -> dict:
        """Returns the planet's sidereal longitude (Lahiri) and speed for a specific datetime."""
        if dt.tzinfo is None:
            dt = IST.localize(dt)
            
        utc_dt = dt.astimezone(pytz.UTC)
        jd = swe.julday(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        )
        
        # Calculate with Speed flag
        data = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
        tropical_longitude = data[0][0]
        speed = data[0][3]
        
        if planet_id == swe.MEAN_NODE: # Rahu/Ketu Exception
            # Rahu generally goes backwards
            pass
            
        # Get Ayanamsa (precession correction)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        
        sidereal_longitude = tropical_longitude - ayanamsa
        if sidereal_longitude < 0:
            sidereal_longitude += 360.0
            
        return {
            "longitude": sidereal_longitude,
            "speed": speed # degrees per day. Negative means retrograde.
        }

    def _get_rashi_from_longitude(self, longitude: float) -> int:
        """Returns the Zodiac sign (Rashi) 1-12 from the sidereal longitude (0-360)."""
        rashi_span = 360.0 / 12.0
        rashi = int(longitude / rashi_span) + 1
        return rashi if rashi <= 12 else 12

    def _angular_distance(self, long1: float, long2: float) -> float:
        """Returns the minimum angular distance (0-180) between two ecliptic longitudes."""
        diff = abs(long1 - long2) % 360.0
        return diff if diff <= 180.0 else 360.0 - diff

    def _detect_yogas(self, metrics_cache: dict) -> dict:
        """
        Comprehensive Vedic yoga detector for all 9 planets.
        metrics_cache format: {"Mars": {"longitude": 120.5, "speed": 1.1}, ...}
        Returns a flat dict of yoga_name -> True/False.
        """
        yogas = {
            # ── Conjunction Yogas (same Rashi) ──────────────────────────────
            "Angarak_Yoga": False,          # Mars + Rahu
            "Guru_Chandal_Yoga": False,     # Jupiter + Rahu
            "Budh_Aditya_Yoga": False,      # Mercury + Sun
            "Gajakesari_Yoga": False,       # Jupiter + Moon (same rashi)
            "Gajakesari_Kendra": False,     # Jupiter opposite or square Moon
            "Vish_Yoga": False,             # Moon + Saturn
            "Yama_Yoga": False,             # Mars + Saturn
            "Bhrigu_Mangal_Yoga": False,    # Venus + Mars
            "Clash_Of_Gurus": False,        # Jupiter + Venus
            "Chandra_Mangal_Yoga": False,   # Moon + Mars
            "Shukra_Guru_Yoga": False,      # Venus + Jupiter (benefic confluence)
            "Surya_Mangal_Yoga": False,     # Sun + Mars
            "Surya_Shani_Yoga": False,      # Sun + Saturn
            "Chandra_Shani_Yoga": False,    # Moon + Saturn (also Vish)
            "Guru_Mangal_Yoga": False,      # Jupiter + Mars
            "Budh_Shani_Yoga": False,       # Mercury + Saturn
            "Rahu_Ketu_Axis_Sun": False,    # Sun exactly on Rahu-Ketu axis (<10°)
            "Rahu_Ketu_Axis_Moon": False,   # Moon exactly on Rahu-Ketu axis (<10°)
            "Rahu_Ketu_Axis_Mars": False,   # Mars exactly on Rahu-Ketu axis (<10°)
            "Chandal_Venus": False,         # Venus + Rahu
            "Mangal_Rahu": False,           # Mars + Rahu (alias Angarak, included separately)
            "Shani_Rahu": False,            # Saturn + Rahu (Shrapit Dosh)
            "Shani_Ketu": False,            # Saturn + Ketu
            "Guru_Ketu": False,             # Jupiter + Ketu
            # ── Sign-Based / Positional Yogas ───────────────────────────────
            "Shasha_Yoga": False,           # Saturn in Libra/Capricorn/Aquarius (Kendra)
            "Malavya_Yoga": False,          # Venus in Taurus/Libra/Pisces
            "Ruchaka_Yoga": False,          # Mars in Aries/Scorpio/Capricorn
            "Hamsa_Yoga": False,            # Jupiter exalted or own sign Kendra
            "Bhadra_Yoga": False,           # Mercury in Gemini/Virgo
            "Neech_Bhang_Raj_Yoga": False,  # Debilitated planet saved by mutual aspect
            # ── Moon-Phase Yogas ─────────────────────────────────────────────
            "Amavasya_Defect": False,       # New Moon (Sun+Moon < 12°)
            "Purnima_Yoga": False,          # Full Moon (Sun-Moon ~180°)
            "Paksha_Sandi": False,          # Moon crossing Krishna/Shukla boundary
            # ── Eclipse & Node Yogas ─────────────────────────────────────────
            "Solar_Eclipse": False,         # New Moon near Rahu/Ketu (<18°)
            "Lunar_Eclipse": False,         # Full Moon near Rahu/Ketu (<18°)
            "Grahan_Yoga": False,           # Any planet within 9° of Rahu or Ketu
            "Sarp_Dosh": False,             # Multiple malefics (Mars/Saturn/Rahu/Ketu) in 1 sign
            "Kaal_Sarp_Dosh": False,        # All 7 planets hemmed between Rahu-Ketu
            "Paap_Kartari_Moon": False,     # Moon hemmed by malefics on both sides
            # ── Retrograde Yogas ─────────────────────────────────────────────
            "Multiple_Retrograde": False,   # 3+ inner planets retrograde simultaneously
            "Mercury_Combust": False,       # Mercury within 14° of Sun
            "Venus_Combust": False,         # Venus within 10° of Sun
            "Mars_Combust": False,          # Mars within 17° of Sun
            "Jupiter_Combust": False,       # Jupiter within 11° of Sun
            "Saturn_Combust": False,        # Saturn within 15° of Sun
        }

        rashis = {}
        for p, m in metrics_cache.items():
            rashis[p] = self._get_rashi_from_longitude(m["longitude"])

        # ── Helper closures ─────────────────────────────────────────────────
        def same_rashi(p1, p2):
            return p1 in rashis and p2 in rashis and rashis[p1] == rashis[p2]

        def near_node(p_long, orb=10.0):
            """Returns True if planet is within `orb` degrees of Rahu or Ketu."""
            for node in ["Rahu", "Ketu"]:
                if node in metrics_cache:
                    if self._angular_distance(p_long, metrics_cache[node]["longitude"]) < orb:
                        return True
            return False

        # ── Same-Rashi Conjunction Yogas ────────────────────────────────────
        yogas["Angarak_Yoga"]        = same_rashi("Mars", "Rahu")          # Mars + Rahu
        yogas["Mangal_Rahu"]          = yogas["Angarak_Yoga"]               # alias
        yogas["Guru_Chandal_Yoga"]    = same_rashi("Jupiter", "Rahu")       # Jupiter + Rahu
        yogas["Budh_Aditya_Yoga"]     = same_rashi("Sun", "Mercury")        # Sun + Mercury
        yogas["Gajakesari_Yoga"]      = same_rashi("Moon", "Jupiter")       # Moon + Jupiter (same rashi)
        yogas["Vish_Yoga"]            = same_rashi("Moon", "Saturn")        # Moon + Saturn
        yogas["Chandra_Shani_Yoga"]   = yogas["Vish_Yoga"]                  # alias
        yogas["Yama_Yoga"]            = same_rashi("Mars", "Saturn")        # Mars + Saturn
        yogas["Bhrigu_Mangal_Yoga"]   = same_rashi("Venus", "Mars")         # Venus + Mars
        yogas["Clash_Of_Gurus"]       = same_rashi("Jupiter", "Venus")      # Jupiter + Venus
        yogas["Chandra_Mangal_Yoga"]  = same_rashi("Moon", "Mars")          # Moon + Mars
        yogas["Shukra_Guru_Yoga"]     = same_rashi("Venus", "Jupiter")      # Venus + Jupiter (same as Clash_Of_Gurus)
        yogas["Surya_Mangal_Yoga"]    = same_rashi("Sun", "Mars")           # Sun + Mars
        yogas["Surya_Shani_Yoga"]     = same_rashi("Sun", "Saturn")         # Sun + Saturn
        yogas["Guru_Mangal_Yoga"]     = same_rashi("Jupiter", "Mars")       # Jupiter + Mars
        yogas["Budh_Shani_Yoga"]      = same_rashi("Mercury", "Saturn")     # Mercury + Saturn
        yogas["Chandal_Venus"]        = same_rashi("Venus", "Rahu")         # Venus + Rahu
        yogas["Shani_Rahu"]          = same_rashi("Saturn", "Rahu")        # Saturn + Rahu (Shrapit Dosh)
        yogas["Shani_Ketu"]          = same_rashi("Saturn", "Ketu")        # Saturn + Ketu
        yogas["Guru_Ketu"]           = same_rashi("Jupiter", "Ketu")       # Jupiter + Ketu

        # ── Gajakesari by Kendra (1/4/7/10 houses = mutual sq/opposition) ──
        if "Moon" in metrics_cache and "Jupiter" in metrics_cache:
            moon_r = rashis.get("Moon", 0)
            jupi_r = rashis.get("Jupiter", 0)
            diff_r = abs(moon_r - jupi_r)
            # Kendra = 1st (same), 4th (+/-3), 7th (+/-6), 10th (+/-9) from each other
            if diff_r in [0, 3, 6, 9]:
                yogas["Gajakesari_Kendra"] = True

        # ── Sign-Based Pancha Mahapurusha Yogas ─────────────────────────────
        if "Saturn" in rashis and rashis["Saturn"] in [7, 10, 11]:        # Libra, Cap, Aqua
            yogas["Shasha_Yoga"] = True
        if "Venus" in rashis and rashis["Venus"] in [2, 7, 12]:           # Taurus, Libra, Pisces
            yogas["Malavya_Yoga"] = True
        if "Mars" in rashis and rashis["Mars"] in [1, 8, 10]:             # Aries, Scorpio, Capricorn
            yogas["Ruchaka_Yoga"] = True
        if "Jupiter" in rashis and rashis["Jupiter"] in [4, 9, 12]:       # Cancer, Sagit, Pisces
            yogas["Hamsa_Yoga"] = True
        if "Mercury" in rashis and rashis["Mercury"] in [3, 6]:           # Gemini, Virgo
            yogas["Bhadra_Yoga"] = True

        # ── Neech Bhang Raj Yoga: Debilitated planet in same sign as its dispositor ──
        # Simplified: debilitated planet occupies the same Rashi as the planet that exalts there
        # E.g., Moon debilitated in Scorpio (8) — Mars exalts in Capricorn (10), not same — skip
        # Common pairing: Moon debilitated (Scorpio=8) + Jupiter in Scorpio OR Mars debilitated (Cancer=4) + Jupiter/Moon
        if "Moon" in rashis and rashis["Moon"] == 8:  # Moon debilitated in Scorpio
            if "Mars" in rashis and rashis["Mars"] == 8:  # Mars owns Scorpio -> saves Moon
                yogas["Neech_Bhang_Raj_Yoga"] = True
        if "Mars" in rashis and rashis["Mars"] == 4:  # Mars debilitated in Cancer
            if "Moon" in rashis and rashis["Moon"] == 4:  # Moon owns Cancer -> saves Mars
                yogas["Neech_Bhang_Raj_Yoga"] = True
        if "Jupiter" in rashis and rashis["Jupiter"] == 10:  # Jupiter debilitated in Capricorn
            if "Saturn" in rashis and rashis["Saturn"] == 10:  # Saturn owns Capricorn -> saves Jupiter
                yogas["Neech_Bhang_Raj_Yoga"] = True

        # ── Moon-Phase Yogas ─────────────────────────────────────────────────
        if "Sun" in metrics_cache and "Moon" in metrics_cache:
            sun_l = metrics_cache["Sun"]["longitude"]
            moon_l = metrics_cache["Moon"]["longitude"]
            sm_ang = self._angular_distance(sun_l, moon_l)
            sm_diff_raw = (moon_l - sun_l) % 360.0  # 0-360

            if sm_ang < 12.0:
                yogas["Amavasya_Defect"] = True   # New Moon
            if 168.0 < sm_ang < 192.0:
                yogas["Purnima_Yoga"] = True        # Full Moon
            # Paksha Sandi: Moon crossing the 180° midpoint (waxing/waning boundary)
            if 176.0 < sm_ang < 184.0:
                yogas["Paksha_Sandi"] = True

        # ── Eclipse Yogas ────────────────────────────────────────────────────
        if all(p in metrics_cache for p in ["Sun", "Moon", "Rahu", "Ketu"]):
            sun_l = metrics_cache["Sun"]["longitude"]
            moon_l = metrics_cache["Moon"]["longitude"]
            rahu_l = metrics_cache["Rahu"]["longitude"]
            ketu_l = metrics_cache["Ketu"]["longitude"]
            sm_ang = self._angular_distance(sun_l, moon_l)
            is_new = sm_ang < 15.0
            is_full = (165.0 < sm_ang < 195.0)
            sun_near_node = (self._angular_distance(sun_l, rahu_l) < 18.0 or
                            self._angular_distance(sun_l, ketu_l) < 18.0)
            moon_near_node = (self._angular_distance(moon_l, rahu_l) < 18.0 or
                             self._angular_distance(moon_l, ketu_l) < 18.0)
            if is_new and sun_near_node:
                yogas["Solar_Eclipse"] = True
            if is_full and (sun_near_node or moon_near_node):
                yogas["Lunar_Eclipse"] = True

        # ── Grahan Yoga (any planet within 9° of Rahu or Ketu) ───────────────
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            if p in metrics_cache:
                if near_node(metrics_cache[p]["longitude"], orb=9.0):
                    yogas["Grahan_Yoga"] = True
                    break

        # ── Rahu-Ketu Axis Transits (planet within 10° of nodes) ────────────
        for planet, key in [("Sun", "Rahu_Ketu_Axis_Sun"), ("Moon", "Rahu_Ketu_Axis_Moon"), ("Mars", "Rahu_Ketu_Axis_Mars")]:
            if planet in metrics_cache:
                if near_node(metrics_cache[planet]["longitude"], orb=10.0):
                    yogas[key] = True

        # ── Combustion Yogas (planet within orb of Sun) ───────────────────────
        if "Sun" in metrics_cache:
            sun_l = metrics_cache["Sun"]["longitude"]
            COMBUST_ORB = {"Mercury": 14.0, "Venus": 10.0, "Mars": 17.0, "Jupiter": 11.0, "Saturn": 15.0}
            keys = {"Mercury": "Mercury_Combust", "Venus": "Venus_Combust",
                    "Mars": "Mars_Combust", "Jupiter": "Jupiter_Combust", "Saturn": "Saturn_Combust"}
            for p, orb in COMBUST_ORB.items():
                if p in metrics_cache:
                    if self._angular_distance(sun_l, metrics_cache[p]["longitude"]) < orb:
                        yogas[keys[p]] = True

        # ── Multiple Retrograde (3+ planets in retrograde simultaneously) ────
        retro_planets = [p for p in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
                         if p in metrics_cache and metrics_cache[p]["speed"] < 0]
        if len(retro_planets) >= 3:
            yogas["Multiple_Retrograde"] = True

        # ── Sarp Dosh: 2+ malefics (Mars/Saturn/Rahu/Ketu) in same Rashi ─────
        malefics = [p for p in ["Mars", "Saturn", "Rahu", "Ketu"] if p in rashis]
        for i in range(len(malefics)):
            for j in range(i + 1, len(malefics)):
                if rashis[malefics[i]] == rashis[malefics[j]]:
                    yogas["Sarp_Dosh"] = True
                    break

        # ── Paap Kartari Moon: Moon hemmed by malefics (Mars/Saturn/Sun/Rahu/Ketu) ──
        if "Moon" in rashis:
            moon_r = rashis["Moon"]
            prev_r = (moon_r - 2) % 12 + 1   # Rashi before
            next_r = (moon_r % 12) + 1         # Rashi after
            malefic_rashis = {rashis[p] for p in ["Mars", "Saturn", "Rahu", "Ketu", "Sun"] if p in rashis}
            if prev_r in malefic_rashis and next_r in malefic_rashis:
                yogas["Paap_Kartari_Moon"] = True

        # ── Kaal Sarp Dosh: All 7 planets hemmed between Rahu and Ketu ───────
        if "Rahu" in metrics_cache:
            rahu_l = metrics_cache["Rahu"]["longitude"]
            all_primary = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
            if all(p in metrics_cache for p in all_primary):
                angles = [(metrics_cache[p]["longitude"] - rahu_l) % 360 for p in all_primary]
                if all(a < 180 for a in angles) or all(a > 180 for a in angles):
                    yogas["Kaal_Sarp_Dosh"] = True

        return yogas

    def attach_planetary_states(self, df: pd.DataFrame, planets: list, calculate_yogas: bool = False) -> pd.DataFrame:
        """
        Calculates and appends daily planetary data (Longitude, Velocity, Is_Retrograde) 
        to a market DataFrame for correlation. If calculate_yogas=True, runs the combinations engine.
        """
        if df.empty or 'date' not in df.columns:
            return df

            
        enriched_df = df.copy()
        
        # Determine if we need to track all planets for Yogas, or just target planets
        planets_to_track = planets if not calculate_yogas else list(PLANET_MAP.keys())
        
        planet_data_cache = {p: {"longitudes": [], "speeds": [], "retrogrades": [], "rashis": []} for p in planets_to_track}
        # Complete list of all yoga keys (mirrored from _detect_yogas)
        _ALL_YOGAS = [
            "Angarak_Yoga", "Guru_Chandal_Yoga", "Shasha_Yoga", "Amavasya_Defect",
            "Kaal_Sarp_Dosh", "Solar_Eclipse", "Lunar_Eclipse", "Budh_Aditya_Yoga",
            "Gajakesari_Yoga", "Gajakesari_Kendra", "Vish_Yoga", "Yama_Yoga",
            "Bhrigu_Mangal_Yoga", "Clash_Of_Gurus", "Chandra_Mangal_Yoga",
            "Shukra_Guru_Yoga", "Surya_Mangal_Yoga", "Surya_Shani_Yoga",
            "Chandra_Shani_Yoga", "Guru_Mangal_Yoga", "Budh_Shani_Yoga",
            "Rahu_Ketu_Axis_Sun", "Rahu_Ketu_Axis_Moon", "Rahu_Ketu_Axis_Mars",
            "Chandal_Venus", "Mangal_Rahu", "Shani_Rahu", "Shani_Ketu", "Guru_Ketu",
            "Malavya_Yoga", "Ruchaka_Yoga", "Hamsa_Yoga", "Bhadra_Yoga",
            "Neech_Bhang_Raj_Yoga", "Purnima_Yoga", "Paksha_Sandi",
            "Grahan_Yoga", "Sarp_Dosh", "Paap_Kartari_Moon", "Multiple_Retrograde",
            "Mercury_Combust", "Venus_Combust", "Mars_Combust",
            "Jupiter_Combust", "Saturn_Combust",
        ]
        yoga_results = {y: [] for y in _ALL_YOGAS}
        
        for d in enriched_df['date']:
            # Sample at market open
            dt = pd.to_datetime(d).replace(hour=9, minute=15)
            
            daily_metrics = {}
            for planet in planets_to_track:
                p_id = PLANET_MAP.get(planet)
                if p_id is None:
                    continue
                    
                metrics = self._get_planet_metrics(dt, p_id)
                
                # KETU FIX: Ketu is exactly 180 degrees mathematically opposite Rahu
                if planet == "Ketu":
                    metrics["longitude"] = (metrics["longitude"] + 180.0) % 360.0
                    
                daily_metrics[planet] = metrics
                
                planet_data_cache[planet]["longitudes"].append(metrics['longitude'])
                planet_data_cache[planet]["speeds"].append(metrics['speed'])
                planet_data_cache[planet]["rashis"].append(self._get_rashi_from_longitude(metrics['longitude']))
                
                # Sun and Moon cannot be retrograde
                is_retro = True if metrics['speed'] < 0 and planet not in ['Sun', 'Moon', 'Rahu', 'Ketu'] else False
                planet_data_cache[planet]["retrogrades"].append(is_retro)
                
            # If Yoga calculations are requested, calculate based on today's snapshot
            if calculate_yogas:
                daily_yogas = self._detect_yogas(daily_metrics)
                for y, val in daily_yogas.items():
                    yoga_results[y].append(val)
                    
        # Stitch back into dataframe (only the explicitly requested planets, plus any generated yogas)
        for planet in planets:
            if planet in planet_data_cache:
                enriched_df[f'{planet}_Longitude'] = planet_data_cache[planet]["longitudes"]
                enriched_df[f'{planet}_Speed'] = planet_data_cache[planet]["speeds"]
                enriched_df[f'{planet}_Retrograde'] = planet_data_cache[planet]["retrogrades"]
                enriched_df[f'{planet}_Rashi'] = planet_data_cache[planet]["rashis"]
                
        if calculate_yogas:
            for y_name, items in yoga_results.items():
                enriched_df[y_name] = items
            
        return enriched_df

    def calculate_significance(self, event_mask: pd.Series, df: pd.DataFrame, test_col: str = 'daily_return') -> dict:
        """
        Performs an Independent T-Test between days matching the event_mask vs those that do not.
        Returns the p-value and statistical interpretation.
        """
        event_data = df[event_mask][test_col].dropna()
        normal_data = df[~event_mask][test_col].dropna()
        
        if len(event_data) < 1 or len(normal_data) < 1:
             return {"error": "No market events found matching these criteria."}
             
        # T-Test (requires at least 2 samples for variance)
        if len(event_data) >= 2 and len(normal_data) >= 2:
            t_stat, p_val = stats.ttest_ind(event_data, normal_data, equal_var=False)
            is_significant = bool(p_val < 0.05)
            p_val_num = float(p_val)
            t_stat_num = float(t_stat)
            interpretation = f"The difference in performance is {'statistically significant (p < 0.05)' if is_significant else 'NOT statistically significant (p >= 0.05)'}. Event average return: {event_data.mean() * 100:.2f}% vs Normal average: {normal_data.mean() * 100:.2f}%."
        else:
            p_val_num = 1.0
            t_stat_num = 0.0
            is_significant = False
            interpretation = f"Insufficient sample size for p-value calculation (requires >1). Raw data shows Event average return: {event_data.mean() * 100:.2f}% vs Normal average: {normal_data.mean() * 100:.2f}%."
        
        # Win Rates
        event_win_rate = (event_data > 0).mean() * 100
        normal_win_rate = (normal_data > 0).mean() * 100
        
        return {
            "p_value": p_val_num,
            "t_statistic": t_stat_num,
            "is_significant": is_significant,
            "event_mean_return": float(event_data.mean()),
            "normal_mean_return": float(normal_data.mean()),
            "event_win_rate": float(event_win_rate),
            "normal_win_rate": float(normal_win_rate),
            "event_days": len(event_data),
            "normal_days": len(normal_data),
            "interpretation": f"The difference in performance is {'statistically significant (p < 0.05)' if is_significant else 'NOT statistically significant (p >= 0.05)'}. "
                              f"Event average return: {event_data.mean():.2f}% vs Normal average: {normal_data.mean():.2f}%."
        }

    def backtest_event(self, symbol: str, planet: str, event_type: str, market: str = "NSE", years: int = 10, forward_days: int = 0) -> dict:
        """
        Executes a targeted astro-financial backtest for a specific symbol.
        years=99 is treated as 'Max Available Data' (~30 years).
        """
        effective_years = 30 if years >= 99 else years  # 99 = Max Available Data
        start_date = (datetime.now() - pd.DateOffset(years=effective_years)).strftime('%Y-%m-%d')
        df = self.market.fetch_stock_data(symbol, start_date=start_date, market=market)
        
        if df.empty:
            return {"error": "Could not fetch market data."}
            
        # Optional Forward-return shifting 
        test_col = 'daily_return'
        if forward_days > 0 and 'close' in df.columns:
            # e.g., Cumulative return over next N days
            df[f'forward_{forward_days}d_return'] = df['close'].shift(-forward_days) / df['close'] - 1.0
            test_col = f'forward_{forward_days}d_return'
            
        # Check if a Yoga was requested based on event_type name
        _YOGA_EVENTS = [
            "Angarak_Yoga", "Guru_Chandal_Yoga", "Shasha_Yoga", "Amavasya_Defect",
            "Kaal_Sarp_Dosh", "Solar_Eclipse", "Lunar_Eclipse", "Budh_Aditya_Yoga",
            "Gajakesari_Yoga", "Gajakesari_Kendra", "Vish_Yoga", "Yama_Yoga",
            "Bhrigu_Mangal_Yoga", "Clash_Of_Gurus", "Chandra_Mangal_Yoga",
            "Shukra_Guru_Yoga", "Surya_Mangal_Yoga", "Surya_Shani_Yoga",
            "Chandra_Shani_Yoga", "Guru_Mangal_Yoga", "Budh_Shani_Yoga",
            "Rahu_Ketu_Axis_Sun", "Rahu_Ketu_Axis_Moon", "Rahu_Ketu_Axis_Mars",
            "Chandal_Venus", "Mangal_Rahu", "Shani_Rahu", "Shani_Ketu", "Guru_Ketu",
            "Malavya_Yoga", "Ruchaka_Yoga", "Hamsa_Yoga", "Bhadra_Yoga",
            "Neech_Bhang_Raj_Yoga", "Purnima_Yoga", "Paksha_Sandi",
            "Grahan_Yoga", "Sarp_Dosh", "Paap_Kartari_Moon", "Multiple_Retrograde",
            "Mercury_Combust", "Venus_Combust", "Mars_Combust",
            "Jupiter_Combust", "Saturn_Combust",
        ]
        is_yoga_event = event_type in _YOGA_EVENTS
        
        df = self.attach_planetary_states(df, list(PLANET_MAP.keys()) if is_yoga_event else [planet], calculate_yogas=is_yoga_event)
        
        # Build boolean filter mask
        if is_yoga_event:
            if event_type not in df.columns:
                 return {"error": f"Failed to compute {event_type}."}
            mask = df[event_type] == True
            planet = "Multiple" # Yogas typically involve multiple planets
        else:
            if f'{planet}_Speed' not in df.columns:
                return {"error": f"Could not calculate ephemeris for {planet}."}
                
            if event_type.lower() == "retrograde":
                mask = df[f'{planet}_Retrograde'] == True
                if planet in ["Sun", "Moon", "Rahu", "Ketu"]:
                     return {"error": f"{planet} does not go retrograde."}
            elif event_type.lower() == "direct":
                mask = df[f'{planet}_Retrograde'] == False
            elif event_type.lower() == "high speed":
                 # E.g., top 20% of orbital velocity
                 threshold = df[f'{planet}_Speed'].quantile(0.8)
                 mask = df[f'{planet}_Speed'] > threshold
            elif event_type.lower() == "exalted":
                 exalted_rashi = EXALTATION_MAP.get(planet)
                 if exalted_rashi is None:
                     return {"error": f"Exaltation mapping missing for {planet}."}
                 mask = df[f'{planet}_Rashi'] == exalted_rashi
            elif event_type.lower() == "debilitated":
                 debilitated_rashi = DEBILITATION_MAP.get(planet)
                 if debilitated_rashi is None:
                     return {"error": f"Debilitation mapping missing for {planet}."}
                 mask = df[f'{planet}_Rashi'] == debilitated_rashi
            elif event_type.lower() == "own house":
                 own_rashis = OWN_HOUSE_MAP.get(planet)
                 if own_rashis is None:
                     return {"error": f"Own House mapping missing for {planet}."}
                 mask = df[f'{planet}_Rashi'].isin(own_rashis)
            else:
                 return {"error": "Unsupported event type."}
                 
        stats_result = self.calculate_significance(mask, df, test_col=test_col)
        
        if "error" in stats_result:
            return stats_result
            
        return {
            "symbol": symbol,
            "planet": planet,
            "event": event_type,
            "period": f"Last {effective_years} Years" + (" (Max Available)" if years >= 99 else ""),
            "stats": stats_result
        }

    def generate_correlation_heatmap(self, symbols: list, planets: list, market: str = "NSE", years: int = 5) -> dict:
        """
        Creates a Pearson correlation matrix mapping planetary velocities against the returns of multiple symbols.
        Useful for Sector-to-Planet alignment.
        """
        # 1. Fetch data for all symbols
        start_date = (datetime.now() - pd.DateOffset(years=years)).strftime('%Y-%m-%d')
        combined_df = pd.DataFrame()
        
        for sym in symbols:
            df = self.market.fetch_stock_data(sym, start_date=start_date, market=market)
            if not df.empty:
                # Set index to date for easy joining
                df['date'] = pd.to_datetime(df['date']).dt.normalize()
                df = df.set_index('date')
                combined_df[sym] = df['daily_return']
                
        if combined_df.empty:
            return {"error": "Could not fetch structural data."}
            
        # 2. Add Planet Speeds
        # We only need to calculate planets for one date range
        ephem_df = pd.DataFrame({'date': combined_df.index})
        ephem_df = self.attach_planetary_states(ephem_df, planets)
        ephem_df = ephem_df.set_index('date')
        
        for planet in planets:
            combined_df[f'{planet}_Velocity'] = ephem_df[f'{planet}_Speed']
            
        # Drop NaNs to align matrices
        combined_df = combined_df.dropna()
        
        if combined_df.empty:
             return {"error": "Not enough overlapping data points."}
             
        # 3. Calculate Pearson Correlation
        corr_matrix = combined_df.corr(method='pearson')
        
        # We only care about Symbol vs Planet cross-correlation
        cross_corr = {}
        for sym in symbols:
            if sym in corr_matrix.index:
                cross_corr[sym] = {}
                for planet in planets:
                    planet_col = f'{planet}_Velocity'
                    if planet_col in corr_matrix.columns:
                        val = corr_matrix.loc[sym, planet_col]
                        cross_corr[sym][planet] = round(float(val), 4)
                        
        return {
            "period": f"Last {years} Years",
            "matrix": cross_corr
        }

    def backtest_vix_event(self, planet: str, event_type: str, years: int = 15, forward_days: int = 0) -> dict:
        """
        Runs the same T-Test backtest engine but against India VIX daily changes
        instead of market price returns. Tests if astro-events correlate with fear spikes.
        """
        effective_years = 30 if years >= 99 else years  # 99 = Max Available Data
        start_date = (datetime.now() - pd.DateOffset(years=effective_years)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        # Fetch India VIX using MarketDataFetcher
        try:
            vix_hist = self.market.fetch_stock_data("^INDIAVIX", start_date=start_date, end_date=end_date)
            if vix_hist.empty:
                return {"error": "No India VIX data available for this period."}

            # Build DataFrame
            df = pd.DataFrame()
            df['date'] = vix_hist['date'].dt.tz_localize(None)
            df['vix_close'] = vix_hist['close'].values
            df['vix_daily_change'] = vix_hist['daily_return'].values
            df = df.dropna().reset_index(drop=True)

            if df.empty:
                return {"error": "Insufficient VIX data after processing."}
        except Exception as e:
            return {"error": f"Failed to fetch India VIX data: {e}"}

        # Forward return on VIX
        test_col = 'vix_daily_change'
        if forward_days > 0:
            df[f'vix_forward_{forward_days}d'] = df['vix_close'].shift(-forward_days) / df['vix_close'] - 1.0
            test_col = f'vix_forward_{forward_days}d'

        # Check if a Yoga was requested
        _YOGA_EVENTS_VIX = [
            "Angarak_Yoga", "Guru_Chandal_Yoga", "Shasha_Yoga", "Amavasya_Defect",
            "Kaal_Sarp_Dosh", "Solar_Eclipse", "Lunar_Eclipse", "Budh_Aditya_Yoga",
            "Gajakesari_Yoga", "Gajakesari_Kendra", "Vish_Yoga", "Yama_Yoga",
            "Bhrigu_Mangal_Yoga", "Clash_Of_Gurus", "Chandra_Mangal_Yoga",
            "Shukra_Guru_Yoga", "Surya_Mangal_Yoga", "Surya_Shani_Yoga",
            "Chandra_Shani_Yoga", "Guru_Mangal_Yoga", "Budh_Shani_Yoga",
            "Rahu_Ketu_Axis_Sun", "Rahu_Ketu_Axis_Moon", "Rahu_Ketu_Axis_Mars",
            "Chandal_Venus", "Mangal_Rahu", "Shani_Rahu", "Shani_Ketu", "Guru_Ketu",
            "Malavya_Yoga", "Ruchaka_Yoga", "Hamsa_Yoga", "Bhadra_Yoga",
            "Neech_Bhang_Raj_Yoga", "Purnima_Yoga", "Paksha_Sandi",
            "Grahan_Yoga", "Sarp_Dosh", "Paap_Kartari_Moon", "Multiple_Retrograde",
            "Mercury_Combust", "Venus_Combust", "Mars_Combust",
            "Jupiter_Combust", "Saturn_Combust",
        ]
        is_yoga_event = event_type in _YOGA_EVENTS_VIX

        df = self.attach_planetary_states(df, list(PLANET_MAP.keys()) if is_yoga_event else [planet], calculate_yogas=is_yoga_event)

        # Build boolean filter mask
        if is_yoga_event:
            if event_type not in df.columns:
                return {"error": f"Failed to compute {event_type}."}
            mask = df[event_type] == True
            planet = "Multiple"
        else:
            if f'{planet}_Speed' not in df.columns:
                return {"error": f"Could not calculate ephemeris for {planet}."}

            if event_type.lower() == "retrograde":
                mask = df[f'{planet}_Retrograde'] == True
                if planet in ["Sun", "Moon", "Rahu", "Ketu"]:
                    return {"error": f"{planet} does not go retrograde."}
            elif event_type.lower() == "direct":
                mask = df[f'{planet}_Retrograde'] == False
            elif event_type.lower() == "high speed":
                threshold = df[f'{planet}_Speed'].quantile(0.8)
                mask = df[f'{planet}_Speed'] > threshold
            elif event_type.lower() == "exalted":
                exalted_rashi = EXALTATION_MAP.get(planet)
                if exalted_rashi is None:
                    return {"error": f"Exaltation mapping missing for {planet}."}
                mask = df[f'{planet}_Rashi'] == exalted_rashi
            elif event_type.lower() == "debilitated":
                debilitated_rashi = DEBILITATION_MAP.get(planet)
                if debilitated_rashi is None:
                    return {"error": f"Debilitation mapping missing for {planet}."}
                mask = df[f'{planet}_Rashi'] == debilitated_rashi
            elif event_type.lower() == "own house":
                own_rashis = OWN_HOUSE_MAP.get(planet)
                if own_rashis is None:
                    return {"error": f"Own House mapping missing for {planet}."}
                mask = df[f'{planet}_Rashi'].isin(own_rashis)
            else:
                return {"error": "Unsupported event type."}

        # Use calculate_significance with VIX column
        stats_result = self.calculate_significance(mask, df, test_col=test_col)

        if "error" in stats_result:
            return stats_result

        return {
            "symbol": "India VIX",
            "planet": planet,
            "event": event_type,
            "period": f"Last {effective_years} Years" + (" (Max Available)" if years >= 99 else ""),
            "stats": stats_result
        }
