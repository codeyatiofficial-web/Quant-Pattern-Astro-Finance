"""
Calculate Moon's position in Nakshatra using Swiss Ephemeris.
Provides accurate astronomical calculations for any date/time.
"""

import swisseph as swe
from datetime import datetime, timedelta
import pytz
from typing import Optional, List
import os
import ephem
from functools import lru_cache

from modules.nakshatra_database import get_nakshatra_by_number

# Set ephemeris data path
EPHEMERIS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ephemeris')
if os.path.isdir(EPHEMERIS_PATH):
    swe.set_ephe_path(EPHEMERIS_PATH)

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

# Ayanamsa selection (Lahiri is standard for Indian astrology)
AYANAMSA_TYPE = swe.SIDM_LAHIRI

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

YOGA_NAMES = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]

PLANET_MAP = {
    "Moon": swe.MOON,
    "Sun": swe.SUN,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


# ── Module-level LRU-cached computation helpers ──────────────────────────────
# These are pure functions keyed on hashable primitives so the same date+planet
# never recomputes swisseph or ephem calls within a process lifetime.

@lru_cache(maxsize=4096)
def _calc_nakshatra_cached(year: int, month: int, day: int,
                           hour: int, minute: int, utc_offset_hours: float,
                           planet: str) -> dict:
    """Core ephemeris calculation, cached by date/time/planet."""
    import pytz
    utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)

    jd = swe.julday(year, month, day,
                    hour + minute / 60.0)

    planet_id = PLANET_MAP.get(planet, swe.MOON)
    planet_data = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH)
    planet_longitude_tropical = planet_data[0][0]

    if planet == "Ketu":
        planet_data = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SWIEPH)
        planet_longitude_tropical = (planet_data[0][0] + 180.0) % 360.0

    sun_data = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    sun_longitude_tropical = sun_data[0][0]

    ayanamsa = swe.get_ayanamsa_ut(jd)

    planet_longitude_sidereal = planet_longitude_tropical - ayanamsa
    if planet_longitude_sidereal < 0:
        planet_longitude_sidereal += 360.0

    moon_data_tithi = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    moon_longitude_tropical_tithi = moon_data_tithi[0][0]

    sun_longitude_sidereal = (sun_longitude_tropical - ayanamsa) % 360.0
    moon_longitude_sidereal_tithi = (moon_longitude_tropical_tithi - ayanamsa) % 360.0

    yoga_sum = (moon_longitude_sidereal_tithi + sun_longitude_sidereal) % 360.0
    yoga_number = min(int(yoga_sum / (360.0 / 27.0)) + 1, 27)
    yoga_name = YOGA_NAMES[yoga_number - 1]

    long_diff = moon_longitude_tropical_tithi - sun_longitude_tropical
    if long_diff < 0:
        long_diff += 360.0
    tithi_number = min(int(long_diff / 12.0) + 1, 30)
    tithi_name = TITHI_NAMES[tithi_number - 1]
    paksha = "Shukla Paksha" if tithi_number <= 15 else "Krishna Paksha"

    nakshatra_span = 360.0 / 27.0
    nakshatra_number = min(int(planet_longitude_sidereal / nakshatra_span) + 1, 27)
    position_in_nakshatra = planet_longitude_sidereal % nakshatra_span
    pada = min(int(position_in_nakshatra / (nakshatra_span / 4)) + 1, 4)

    return dict(
        jd=jd,
        nakshatra_number=nakshatra_number,
        pada=pada,
        position_in_nakshatra=position_in_nakshatra,
        planet_longitude_tropical=planet_longitude_tropical,
        planet_longitude_sidereal=planet_longitude_sidereal,
        moon_longitude_tropical=moon_longitude_tropical_tithi,
        sun_longitude_tropical=sun_longitude_tropical,
        ayanamsa=ayanamsa,
        tithi_number=tithi_number,
        tithi_name=tithi_name,
        paksha=paksha,
        yoga_number=yoga_number,
        yoga_name=yoga_name,
    )


@lru_cache(maxsize=4096)
def _is_rising_cached(date_iso: str, tz_key: str, planet_name: str,
                      lat: str, lon: str) -> bool:
    """Cached ephem rise check, keyed by date string."""
    import ephem, pytz
    tz = pytz.timezone(tz_key)
    date = datetime.fromisoformat(date_iso)
    ephem_map = {
        "Moon": ephem.Moon, "Sun": ephem.Sun, "Mercury": ephem.Mercury,
        "Venus": ephem.Venus, "Mars": ephem.Mars,
        "Jupiter": ephem.Jupiter, "Saturn": ephem.Saturn,
    }
    if planet_name not in ephem_map:
        return False
    observer = ephem.Observer()
    observer.lat = lat
    observer.lon = lon
    observer.elevation = 14
    utc_start = tz.localize(date.replace(hour=0, minute=0, second=0,
                                         microsecond=0)).astimezone(pytz.UTC)
    observer.date = utc_start.strftime("%Y/%m/%d %H:%M:%S")
    planet_obj = ephem_map[planet_name]()
    planet_obj.compute(observer)
    try:
        next_rising = (observer.next_rising(planet_obj).datetime()
                       .replace(tzinfo=pytz.UTC).astimezone(tz))
        if next_rising.date() != date.date():
            return False
        market_open = next_rising.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = next_rising.replace(hour=15, minute=30, second=0, microsecond=0)
        return market_open <= next_rising <= market_close
    except Exception:
        return False


class MoonCalculator:
    """Calculate Moon's Nakshatra position using Swiss Ephemeris."""

    def __init__(self):
        """Initialize calculator with Lahiri ayanamsa."""
        swe.set_sid_mode(AYANAMSA_TYPE)

    def calculate_nakshatra(self, date_time: datetime, timezone=IST, planet: str = "Moon") -> dict:
        """
        Calculate Nakshatra for given date/time. Results are LRU-cached.
        """
        if date_time.tzinfo is None:
            date_time = timezone.localize(date_time)

        utc_time = date_time.astimezone(pytz.UTC)

        raw = _calc_nakshatra_cached(
            utc_time.year, utc_time.month, utc_time.day,
            utc_time.hour, utc_time.minute,
            utc_time.utcoffset().total_seconds() / 3600.0,
            planet,
        )

        nakshatra_info = get_nakshatra_by_number(raw['nakshatra_number'])

        return {
            "date_time": date_time.isoformat(),
            "date_time_utc": utc_time.isoformat(),
            "julian_day": raw['jd'],
            "nakshatra_number": raw['nakshatra_number'],
            "nakshatra_name": nakshatra_info["name_english"],
            "nakshatra_sanskrit": nakshatra_info["name_sanskrit"],
            "pada": raw['pada'],
            "planet": planet,
            "planet_longitude_tropical": round(raw['planet_longitude_tropical'], 6),
            "planet_longitude_sidereal": round(raw['planet_longitude_sidereal'], 6),
            "moon_longitude_tropical": round(raw['moon_longitude_tropical'], 6),
            "sun_longitude_tropical": round(raw['sun_longitude_tropical'], 6),
            "position_in_nakshatra_degrees": round(raw['position_in_nakshatra'], 6),
            "ayanamsa": round(raw['ayanamsa'], 6),
            "tithi_number": raw['tithi_number'],
            "tithi_name": raw['tithi_name'],
            "paksha": raw['paksha'],
            "yoga_number": raw['yoga_number'],
            "yoga_name": raw['yoga_name'],
            "ruling_planet": nakshatra_info["ruling_planet"],
            "ruling_deity": nakshatra_info["ruling_deity"],
            "element": nakshatra_info["element"],
            "gana": nakshatra_info["gana"],
            "rashi_name": nakshatra_info["constellation"],
            "western_star": nakshatra_info["star_name_western"],
            "financial_traits": nakshatra_info["financial_traits"],
            "favorable_for": nakshatra_info["favorable_for"],
            "unfavorable_for": nakshatra_info["unfavorable_for"],
            "historical_market_tendency": nakshatra_info["historical_market_tendency"],
            "lucky_colors": nakshatra_info["lucky_colors"],
            "lucky_numbers": nakshatra_info["lucky_numbers"],
        }

    def calculate_range(self, start_date: datetime, end_date: datetime,
                        time_of_day: str = "09:15", timezone=IST) -> list:
        """
        Calculate Nakshatra for date range.

        Args:
            start_date: Start date
            end_date: End date
            time_of_day: Time in HH:MM format (default: market open 9:15 AM)
            timezone: Timezone (default: IST)

        Returns:
            List of dicts with date and Nakshatra info
        """
        results = []
        current_date = start_date

        # Parse time
        hour, minute = map(int, time_of_day.split(':'))

        while current_date <= end_date:
            dt = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            nakshatra_data = self.calculate_nakshatra(dt, timezone)
            results.append(nakshatra_data)
            current_date += timedelta(days=1)

        return results

    def get_transition_time(self, date: datetime, timezone=IST, planet: str = "Moon") -> Optional[dict]:
        """
        Find when the selected Planet transitions from one Nakshatra to another on given date.

        Returns:
            dict with transition details or None if no transition on that day
        """
        transitions = []

        for hour in range(24):
            check_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            nak1 = self.calculate_nakshatra(check_time, timezone, planet=planet)

            next_hour = check_time + timedelta(hours=1)
            nak2 = self.calculate_nakshatra(next_hour, timezone, planet=planet)

            if nak1["nakshatra_number"] != nak2["nakshatra_number"]:
                # Binary search for exact minute
                for minute in range(60):
                    exact_time = check_time + timedelta(minutes=minute)
                    nak_exact = self.calculate_nakshatra(exact_time, timezone, planet=planet)

                    if nak_exact["nakshatra_number"] != nak1["nakshatra_number"]:
                        transitions.append({
                            "from_nakshatra": nak1["nakshatra_name"],
                            "from_number": nak1["nakshatra_number"],
                            "to_nakshatra": nak2["nakshatra_name"],
                            "to_number": nak2["nakshatra_number"],
                            "transition_time": exact_time.isoformat(),
                            "during_market_hours": 9 <= exact_time.hour < 16,
                            "significance": f"{planet} enters {nak2['nakshatra_name']}"
                        })
                        break

        return transitions[0] if transitions else None

    def get_all_transitions(self, start_date: datetime, end_date: datetime,
                            timezone=IST) -> List[dict]:
        """Get all Nakshatra transitions in a date range."""
        transitions = []
        current = start_date

        while current <= end_date:
            t = self.get_transition_time(current, timezone)
            if t:
                transitions.append(t)
            current += timedelta(days=1)

        return transitions

    def calculate_ascendant(self, date_time: datetime, timezone=IST, lat: float = 18.9220, lon: float = 72.8277) -> dict:
        """
        Calculate the Ascendant (Lagna) at a specific time and location.
        
        Args:
            date_time: datetime object
            timezone: timezone object (default IST)
            lat: Latitude (default Mumbai)
            lon: Longitude (default Mumbai)
        
        Returns:
            dict containing rashi number, sidereal degree, and rashi name
        """
        # Convert to UTC
        if not date_time.tzinfo:
            date_time = timezone.localize(date_time)
        utc_time = date_time.astimezone(pytz.UTC)
        
        # Calculate Julian Day
        hour_dec = utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0
        jd = swe.julday(utc_time.year, utc_time.month, utc_time.day, hour_dec)
        
        # Calculate houses (P = Placidus)
        # ascmc[0] is the Ascendant in Tropical zodiac
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        ascendant_tropical = ascmc[0]
        
        # Apply Ayanamsa for Sidereal zodiac
        ayanamsa = swe.get_ayanamsa_ut(jd)
        ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
        
        # 12 Rashis (Zodiac Signs), 30 degrees each
        rashi_names = [
            'Aries (Mesha)', 'Taurus (Vrishabha)', 'Gemini (Mithuna)', 
            'Cancer (Karka)', 'Leo (Simha)', 'Virgo (Kanya)', 
            'Libra (Tula)', 'Scorpio (Vrishchika)', 'Sagittarius (Dhanu)', 
            'Capricorn (Makara)', 'Aquarius (Kumbha)', 'Pisces (Meena)'
        ]
        
        rashi_num = int(ascendant_sidereal / 30) + 1
        
        return {
            "ascendant_sidereal": ascendant_sidereal,
            "rashi_number": rashi_num,
            "rashi_name": rashi_names[rashi_num - 1]
        }

    def get_planet_rise_set(self, date: datetime, timezone=IST, planet_name: str = "Moon", lat: str = '18.9220', lon: str = '72.8277') -> dict:
        """
        Calculate Planet rise and set time for a specific location.
        
        Args:
            date: date for the calculations
            timezone: timezone for calculations
            planet_name: English name of the planet
            lat: Latitude as string (default Mumbai)
            lon: Longitude as string (default Mumbai)
            
        Returns:
            dict containing rise and set times
        """
        # Create observer at midnight of the target date to find the *first* occurrence
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if not start_of_day.tzinfo:
            start_of_day = timezone.localize(start_of_day)
            
        utc_midnight = start_of_day.astimezone(pytz.UTC)
            
        obs = ephem.Observer()
        obs.lat = lat
        obs.lon = lon
        obs.elevation = 14
        obs.date = utc_midnight.strftime("%Y/%m/%d %H:%M:%S")
        
        ephem_map = {
            "Moon": ephem.Moon,
            "Sun": ephem.Sun,
            "Mercury": ephem.Mercury,
            "Venus": ephem.Venus,
            "Mars": ephem.Mars,
            "Jupiter": ephem.Jupiter,
            "Saturn": ephem.Saturn
        }
        
        if planet_name not in ephem_map:
            return {
                "planet_rise": "N/A (Node)",
                "planet_set": "N/A (Node)"
            }
            
        planet_obj = ephem_map[planet_name]()
        planet_obj.compute(obs)
        
        try:
            next_rising = obs.next_rising(planet_obj).datetime().replace(tzinfo=pytz.UTC).astimezone(timezone)
            rise_time = next_rising.strftime("%I:%M %p")
            if next_rising.date() > date.date():
                rise_time += f" ({next_rising.strftime('%b %d')})"
        except ephem.AlwaysUpError:
            rise_time = "Always Up"
        except ephem.NeverUpError:
            rise_time = "Never Up"
            
        try:
            next_setting = obs.next_setting(planet_obj).datetime().replace(tzinfo=pytz.UTC).astimezone(timezone)
            
            # Check if event is strictly on the requested date
            if next_setting.date() != date.date():
                set_time = None
            else:
                set_time = next_setting.strftime("%I:%M %p")
        except ephem.AlwaysUpError:
            set_time = None
        except ephem.NeverUpError:
            set_time = "Never Up"
            
        return {
            "planet_rise": rise_time,
            "planet_set": set_time
        }

    def is_planet_rising_during_market_hours(self, date: datetime, timezone=IST,
                                              planet_name: str = "Moon",
                                              open_hour=9, open_minute=15,
                                              close_hour=15, close_minute=30,
                                              lat: str = '18.9220',
                                              lon: str = '72.8277') -> bool:
        """
        Check if a given planet rises during market trading hours. LRU-cached.
        """
        tz_key = timezone.zone if hasattr(timezone, 'zone') else str(timezone)
        date_iso = date.strftime("%Y-%m-%d")
        return _is_rising_cached(date_iso, tz_key, planet_name, lat, lon)
    def get_yoga_bounds(self, date_time: datetime, timezone=IST) -> dict:
        """
        Calculate the exact start and end times of the Nitya Yoga active at the given time.
        Uses a binary search algorithm accurate to 1 minute.
        """
        current_res = self.calculate_nakshatra(date_time, timezone)
        current_yoga_num = current_res["yoga_number"]
        
        # Find start time (search backwards)
        search_start = date_time - timedelta(hours=30)
        search_end = date_time
        
        # Binary search for start
        while (search_end - search_start).total_seconds() > 60:
            mid = search_start + (search_end - search_start) / 2
            mid_res = self.calculate_nakshatra(mid, timezone)
            if mid_res["yoga_number"] == current_yoga_num:
                search_end = mid
            else:
                search_start = mid
        start_time = search_end
        
        # Find end time (search forwards)
        search_start = date_time
        search_end = date_time + timedelta(hours=30)
        
        # Binary search for end
        while (search_end - search_start).total_seconds() > 60:
            mid = search_start + (search_end - search_start) / 2
            mid_res = self.calculate_nakshatra(mid, timezone)
            if mid_res["yoga_number"] == current_yoga_num:
                search_start = mid
            else:
                search_end = mid
        end_time = search_start
        
        return {
            "yoga_number": current_yoga_num,
            "yoga_name": current_res["yoga_name"],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    def get_current_nakshatra(self) -> dict:
        """Get Moon's current Nakshatra position."""
        return self.calculate_nakshatra(datetime.now(IST))


# Convenience functions
def get_nakshatra_for_date(date: datetime, time: str = "09:15") -> dict:
    """Quick function to get Nakshatra for a date."""
    calculator = MoonCalculator()
    hour, minute = map(int, time.split(':'))
    dt = date.replace(hour=hour, minute=minute)
    return calculator.calculate_nakshatra(dt)


def get_current_nakshatra() -> dict:
    """Get the current Nakshatra."""
    calculator = MoonCalculator()
    return calculator.get_current_nakshatra()
