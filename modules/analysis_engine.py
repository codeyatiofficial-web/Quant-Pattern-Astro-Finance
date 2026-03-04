"""
Statistical analysis engine for Nakshatra-market correlation.
Merges astronomical and market data, performs ANOVA, chi-square tests,
and generates correlation metrics.
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import pytz
from typing import Optional, Tuple

from modules.moon_calculator import MoonCalculator
from modules.market_data import MarketDataFetcher
from modules.nakshatra_database import get_all_nakshatras

IST = pytz.timezone('Asia/Kolkata')
EST = pytz.timezone('America/New_York')

MARKET_LOCATIONS = {
    'NSE': {'lat': 18.9220, 'lon': 72.8277, 'tz': IST, 'open_hour': 9, 'open_minute': 15},
    'NASDAQ': {'lat': 40.7128, 'lon': -74.0060, 'tz': EST, 'open_hour': 9, 'open_minute': 30}
}


class NakshatraAnalyzer:
    """Analyze correlation between Nakshatras and market performance."""

    def __init__(self):
        self.moon_calc = MoonCalculator()
        self.market = MarketDataFetcher()

    def build_merged_dataset(self, start_date: str = "2005-01-01",
                              end_date: Optional[str] = None,
                              symbol: str = "^NSEI",
                              planet: str = "Moon",
                              market: str = "NSE") -> pd.DataFrame:
        """
        Build merged dataset of Nakshatra positions and market data.

        Args:
            start_date: Start date YYYY-MM-DD
            end_date: End date (default: today)
            symbol: Market symbol (default: NIFTY 50)
            planet: Planet to analyze (default: Moon)
            market: Market region (NSE|NASDAQ)

        Returns:
            DataFrame with both Nakshatra and market data per trading day
        """
        if end_date is None:
            end_date = datetime.now(IST).strftime("%Y-%m-%d")
            
        settings = MARKET_LOCATIONS.get(market.upper(), MARKET_LOCATIONS['NSE'])
        tz = settings['tz']
        lat, lon = settings['lat'], settings['lon']
        op_h, op_m = settings['open_hour'], settings['open_minute']

        # Fetch market data
        if symbol == "^NSEI":
            market_df = self.market.fetch_nifty_data(start_date, end_date)
        else:
            market_df = self.market.fetch_stock_data(symbol, start_date, end_date, market=market)

        if market_df.empty:
            return pd.DataFrame()

        # Calculate Nakshatra for each trading day (at market local open)
        nakshatra_records = []
        for _, row in market_df.iterrows():
            trade_date = row['date']
            if isinstance(trade_date, str):
                trade_date = pd.to_datetime(trade_date)

            dt = trade_date.replace(hour=op_h, minute=op_m, second=0)
            try:
                nak_data = self.moon_calc.calculate_nakshatra(dt, tz, planet=planet)
                market_hours_rise = self.moon_calc.is_planet_rising_during_market_hours(
                    trade_date, tz, planet_name=planet, lat=str(lat), lon=str(lon)
                )
                
                nakshatra_records.append({
                    'date': trade_date,
                    'planet': planet,
                    'nakshatra_number': nak_data['nakshatra_number'],
                    'nakshatra_name': nak_data['nakshatra_name'],
                    'nakshatra_sanskrit': nak_data['nakshatra_sanskrit'],
                    'pada': nak_data['pada'],
                    'planet_longitude_sidereal': nak_data.get('planet_longitude_sidereal', nak_data.get('moon_longitude_sidereal')),
                    'tithi_number': nak_data['tithi_number'],
                    'tithi_name': nak_data['tithi_name'],
                    'paksha': nak_data['paksha'],
                    'ruling_planet': nak_data['ruling_planet'],
                    'element': nak_data['element'],
                    'gana': nak_data['gana'],
                    'historical_market_tendency': nak_data['historical_market_tendency'],
                    'planet_rise_market_hours': market_hours_rise,
                })
            except Exception as e:
                print(f"Error calculating nakshatra for {trade_date}: {e}")
                continue

        nak_df = pd.DataFrame(nakshatra_records)

        if nak_df.empty:
            return pd.DataFrame()

        # Normalize dates for merge
        market_df['date'] = pd.to_datetime(market_df['date']).dt.normalize()
        nak_df['date'] = pd.to_datetime(nak_df['date']).dt.normalize()

        # Merge datasets
        merged = pd.merge(market_df, nak_df, on='date', how='inner')

        # Add day of week
        merged['day_of_week'] = merged['date'].dt.day_name()

        # Add month
        merged['month'] = merged['date'].dt.month
        merged['year'] = merged['date'].dt.year

        return merged

    def nakshatra_performance_summary(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate performance summary for each Nakshatra.
        """
        if merged_df.empty:
            return pd.DataFrame()

        summary = []

        for nak_num in range(1, 28):
            nak = merged_df[merged_df['nakshatra_number'] == nak_num]

            if len(nak) == 0:
                continue

            nak_info = get_all_nakshatras()[nak_num - 1]
            returns = nak['daily_return'].dropna()

            bullish = (returns > 0).sum()
            bearish = (returns < 0).sum()
            flat = (returns == 0).sum()
            total = len(returns)

            recent_trades = []
            if not nak.empty:
                recent = nak.sort_values('date', ascending=False).head(50)
                for _, row in recent.iterrows():
                    ret_val = row['daily_return']
                    recent_trades.append({
                        "date": row['date'].strftime('%Y-%m-%d'),
                        "return": round(ret_val, 4) if pd.notna(ret_val) else 0
                    })

            summary.append({
                'nakshatra_number': nak_num,
                'nakshatra_name': nak_info['name_english'],
                'nakshatra_sanskrit': nak_info['name_sanskrit'],
                'ruling_planet': nak_info['ruling_planet'],
                'element': nak_info['element'],
                'trading_days': total,
                'mean_return': round(returns.mean(), 4) if total > 0 else 0,
                'median_return': round(returns.median(), 4) if total > 0 else 0,
                'std_dev': round(returns.std(), 4) if total > 0 else 0,
                'min_return': round(returns.min(), 4) if total > 0 else 0,
                'max_return': round(returns.max(), 4) if total > 0 else 0,
                'bullish_days': bullish,
                'bearish_days': bearish,
                'flat_days': flat,
                'win_rate': round(bullish / total * 100, 2) if total > 0 else 0,
                'avg_gain': round(returns[returns > 0].mean(), 4) if bullish > 0 else 0,
                'avg_loss': round(returns[returns < 0].mean(), 4) if bearish > 0 else 0,
                'gain_loss_ratio': round(
                    abs(returns[returns > 0].mean() / returns[returns < 0].mean()), 4
                ) if bearish > 0 and bullish > 0 else 0,
                'cumulative_return': round(returns.sum(), 4),
                'sharpe_like_ratio': round(
                    returns.mean() / returns.std(), 4
                ) if returns.std() > 0 else 0,
                'previous_trading_date': nak['date'].max().strftime('%Y-%m-%d') if not nak.empty else None,
                'recent_trades': recent_trades,
            })

        summary_df = pd.DataFrame(summary)
        summary_df = summary_df.sort_values('mean_return', ascending=False)
        return summary_df

    def tithi_performance_summary(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate performance summary for each Lunar Tithi.
        """
        if merged_df.empty:
            return pd.DataFrame()

        summary = []
        tithis = merged_df['tithi_name'].unique()

        for tithi_name in tithis:
            tithi_data = merged_df[merged_df['tithi_name'] == tithi_name]

            if len(tithi_data) == 0:
                continue

            returns = tithi_data['daily_return'].dropna()

            bullish = (returns > 0).sum()
            bearish = (returns < 0).sum()
            flat = (returns == 0).sum()
            total = len(returns)

            recent_trades = []
            recent = tithi_data.sort_values('date', ascending=False).head(50)
            for _, row in recent.iterrows():
                ret_val = row['daily_return']
                recent_trades.append({
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "return": round(ret_val, 4) if pd.notna(ret_val) else 0
                })

            summary.append({
                'tithi_name': tithi_name,
                'trading_days': total,
                'mean_return': round(returns.mean(), 4) if total > 0 else 0,
                'median_return': round(returns.median(), 4) if total > 0 else 0,
                'std_dev': round(returns.std(), 4) if total > 0 else 0,
                'bullish_days': bullish,
                'bearish_days': bearish,
                'flat_days': flat,
                'win_rate': round(bullish / total * 100, 2) if total > 0 else 0,
                'previous_trading_date': tithi_data['date'].max().strftime('%Y-%m-%d') if not tithi_data.empty else None,
                'recent_trades': recent_trades,
            })

        summary_df = pd.DataFrame(summary)
        summary_df = summary_df.sort_values('mean_return', ascending=False)
        return summary_df

    def run_anova_test(self, merged_df: pd.DataFrame) -> dict:
        """
        Run one-way ANOVA test: Are mean returns significantly different across Nakshatras?

        H0: Mean returns are equal across all Nakshatras
        H1: At least one Nakshatra has a different mean return
        """
        groups = []
        group_names = []

        for nak_num in range(1, 28):
            nak_returns = merged_df[merged_df['nakshatra_number'] == nak_num]['daily_return'].dropna()
            if len(nak_returns) > 1:
                groups.append(nak_returns.values)
                nak_info = get_all_nakshatras()[nak_num - 1]
                group_names.append(nak_info['name_english'])

        if len(groups) < 2:
            return {"error": "Not enough data for ANOVA"}

        f_stat, p_value = stats.f_oneway(*groups)

        significance = "Significant" if p_value < 0.05 else "Not Significant"

        return {
            "test": "One-Way ANOVA",
            "hypothesis": "H0: Mean returns are equal across Nakshatras",
            "f_statistic": round(f_stat, 6),
            "p_value": round(p_value, 6),
            "significance_level": 0.05,
            "result": significance,
            "interpretation": (
                f"F({len(groups)-1}, {sum(len(g) for g in groups)-len(groups)}) = {f_stat:.4f}, "
                f"p = {p_value:.6f}. "
                f"{'Reject H0: Nakshatra position has a statistically significant effect on returns.' if p_value < 0.05 else 'Fail to reject H0: No significant difference in returns across Nakshatras.'}"
            ),
            "num_groups": len(groups),
            "total_observations": sum(len(g) for g in groups),
        }

    def run_chi_square_test(self, merged_df: pd.DataFrame) -> dict:
        """
        Run Chi-Square test: Is market direction (Bullish/Bearish) independent of Nakshatra?

        H0: Market direction is independent of Nakshatra
        H1: Market direction depends on Nakshatra
        """
        # Create contingency table
        contingency = pd.crosstab(
            merged_df['nakshatra_name'],
            merged_df['direction']
        )

        if contingency.empty or contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return {"error": "Not enough data for Chi-Square test"}

        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        significance = "Significant" if p_value < 0.05 else "Not Significant"

        return {
            "test": "Chi-Square Test of Independence",
            "hypothesis": "H0: Market direction is independent of Nakshatra",
            "chi_square_statistic": round(chi2, 6),
            "p_value": round(p_value, 6),
            "degrees_of_freedom": dof,
            "significance_level": 0.05,
            "result": significance,
            "interpretation": (
                f"χ²({dof}) = {chi2:.4f}, p = {p_value:.6f}. "
                f"{'Reject H0: Market direction is associated with Nakshatra position.' if p_value < 0.05 else 'Fail to reject H0: Market direction appears independent of Nakshatra.'}"
            ),
            "contingency_table": contingency.to_dict(),
        }

    def ruling_planet_analysis(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze market performance by ruling planet."""
        if merged_df.empty:
            return pd.DataFrame()

        planet_stats = merged_df.groupby('ruling_planet').agg(
            trading_days=('daily_return', 'count'),
            mean_return=('daily_return', 'mean'),
            median_return=('daily_return', 'median'),
            std_dev=('daily_return', 'std'),
            total_return=('daily_return', 'sum'),
        ).reset_index()

        # Win rate per planet
        for planet in planet_stats['ruling_planet'].unique():
            planet_data = merged_df[merged_df['ruling_planet'] == planet]['daily_return']
            win_rate = (planet_data > 0).sum() / len(planet_data) * 100
            planet_stats.loc[planet_stats['ruling_planet'] == planet, 'win_rate'] = round(win_rate, 2)

        planet_stats = planet_stats.round(4)
        planet_stats = planet_stats.sort_values('mean_return', ascending=False)
        return planet_stats

    def element_analysis(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze market performance by element (Fire, Earth, Air, Water, Ether)."""
        if merged_df.empty:
            return pd.DataFrame()

        element_stats = merged_df.groupby('element').agg(
            trading_days=('daily_return', 'count'),
            mean_return=('daily_return', 'mean'),
            median_return=('daily_return', 'median'),
            std_dev=('daily_return', 'std'),
            total_return=('daily_return', 'sum'),
        ).reset_index()

        for element in element_stats['element'].unique():
            el_data = merged_df[merged_df['element'] == element]['daily_return']
            win_rate = (el_data > 0).sum() / len(el_data) * 100
            element_stats.loc[element_stats['element'] == element, 'win_rate'] = round(win_rate, 2)

        element_stats = element_stats.round(4)
        element_stats = element_stats.sort_values('mean_return', ascending=False)
        return element_stats

    def gana_analysis(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze market performance by Gana (Deva, Manushya, Rakshasa)."""
        if merged_df.empty:
            return pd.DataFrame()

        gana_stats = merged_df.groupby('gana').agg(
            trading_days=('daily_return', 'count'),
            mean_return=('daily_return', 'mean'),
            median_return=('daily_return', 'median'),
            std_dev=('daily_return', 'std'),
            total_return=('daily_return', 'sum'),
        ).reset_index()

        for gana in gana_stats['gana'].unique():
            gana_data = merged_df[merged_df['gana'] == gana]['daily_return']
            win_rate = (gana_data > 0).sum() / len(gana_data) * 100
            gana_stats.loc[gana_stats['gana'] == gana, 'win_rate'] = round(win_rate, 2)

        gana_stats = gana_stats.round(4)
        gana_stats = gana_stats.sort_values('mean_return', ascending=False)
        return gana_stats

    def pada_analysis(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze market performance by Pada (quarter within Nakshatra)."""
        if merged_df.empty:
            return pd.DataFrame()

        pada_stats = merged_df.groupby(['nakshatra_name', 'pada']).agg(
            trading_days=('daily_return', 'count'),
            mean_return=('daily_return', 'mean'),
            std_dev=('daily_return', 'std'),
        ).reset_index()

        pada_stats = pada_stats.round(4)
        return pada_stats

    def get_top_bottom_nakshatras(self, summary_df: pd.DataFrame,
                                   n: int = 5) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get top N bullish and bearish Nakshatras."""
        top = summary_df.nlargest(n, 'mean_return')
        bottom = summary_df.nsmallest(n, 'mean_return')
        return top, bottom

    def generate_insight_for_date(self, target_date: datetime, planet: str = "Moon", market: str = "NSE") -> dict:
        """Generate trading insight for a specific date based on Nakshatra."""
        settings = MARKET_LOCATIONS.get(market.upper(), MARKET_LOCATIONS['NSE'])
        tz, lat, lon = settings['tz'], settings['lat'], settings['lon']
        op_h, op_m = settings['open_hour'], settings['open_minute']
        
        dt = target_date.replace(hour=op_h, minute=op_m, second=0, microsecond=0)
        current = self.moon_calc.calculate_nakshatra(dt, tz, planet=planet)

        # Get transition info
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        transition = self.moon_calc.get_transition_time(start_of_day, tz, planet=planet)
        
        # Get moon rise and set
        rise_set = self.moon_calc.get_planet_rise_set(target_date, tz, planet_name=planet, lat=str(lat), lon=str(lon))
        
        # Get yoga boundaries
        yoga_bounds = self.moon_calc.get_yoga_bounds(dt, tz)

        insight = {
            "date": target_date.strftime("%Y-%m-%d"),
            "time": dt.strftime(f"%H:%M:%S {tz.tzname(datetime.now())}"),
            "current_nakshatra": current["nakshatra_name"],
            "nakshatra_number": current["nakshatra_number"],
            "nakshatra_sanskrit": current["nakshatra_sanskrit"],
            "pada": current["pada"],
            "tithi_number": current.get("tithi_number"),
            "tithi_name": current.get("tithi_name"),
            "paksha": current.get("paksha"),
            "yoga_name": current.get("yoga_name"),
            "yoga_start": yoga_bounds.get("start_time"),
            "yoga_end": yoga_bounds.get("end_time"),
            "ruling_planet": current["ruling_planet"],
            "planet": planet,
            "planet_longitude": current.get("planet_longitude_tropical", current.get("moon_longitude_tropical")),
            "financial_traits": current["financial_traits"],
            "favorable_for": current["favorable_for"],
            "unfavorable_for": current["unfavorable_for"],
            "historical_tendency": current.get("historical_market_tendency", "Neutral"),
            "lucky_colors": current["lucky_colors"],
            "lucky_numbers": current["lucky_numbers"],
            "transition": transition,
            "planet_rise": rise_set.get("planet_rise"),
            "planet_set": rise_set.get("planet_set")
        }

        return insight

    def generate_today_insight(self) -> dict:
        """Generate trading insight for today based on current Nakshatra."""
        return self.generate_insight_for_date(datetime.now(IST), market="NSE")

    def predict_upcoming_market(self, start_date: Optional[datetime] = None, days: int = 7, planet: str = "Moon", market: str = "NSE") -> list:
        """Predict upcoming market moves based on Nakshatras."""
        if start_date is None:
            tz = MARKET_LOCATIONS.get(market.upper(), MARKET_LOCATIONS['NSE'])['tz']
            start_date = datetime.now(tz)
            
        predictions = []
        current = start_date
        added = 0
        
        while added < days:
            if current.weekday() < 5:  # Skip weekends
                insight = self.generate_insight_for_date(current, planet=planet, market=market)
                predictions.append(insight)
                added += 1
            current += timedelta(days=1)
            
        return predictions

    def build_intraday_lagna_dataset(self, symbol: str, period: str = "5000d", market: str = "NSE") -> pd.DataFrame:
        """
        Builds a dataset mapping 1-hour intraday market returns to the
        active Ascendant (Lagna/Rashi) over a dynamic horizon window.
        """
        # We instantiate a fresh fetcher here since it was not stored on self
        from modules.market_data import MarketDataFetcher
        market_fetcher = MarketDataFetcher()
        intraday_df = market_fetcher.fetch_intraday_data(symbol, period=period, interval="1h", market=market)
        
        if intraday_df.empty:
            return pd.DataFrame()
            
        settings = MARKET_LOCATIONS.get(market.upper(), MARKET_LOCATIONS['NSE'])
        tz, lat, lon = settings['tz'], settings['lat'], settings['lon']
            
        lagna_records = []
        for _, row in intraday_df.iterrows():
            candle_time = row['date']
            # Compute which Ascendant was rising during this exact UTC->Market Time window
            asc_data = self.moon_calc.calculate_ascendant(candle_time, tz, lat=lat, lon=lon)
            
            lagna_records.append({
                'datetime': candle_time,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row.get('volume', 0),
                'return': row.get('return', 0.0),
                'rashi_number': asc_data['rashi_number'],
                'rashi_name': asc_data['rashi_name'],
                'ascendant_sidereal': asc_data['ascendant_sidereal']
            })
            
        return pd.DataFrame(lagna_records)
        
    def lagna_performance_summary(self, df: pd.DataFrame) -> list:
        """Calculate aggregate performance metrics by Lagna Rashi."""
        if df.empty or 'rashi_name' not in df.columns:
            return []
            
        summary = []
        # Exclude NaN return items and group by the 12 active houses
        valid_df = df.dropna(subset=['return'])
        grouped = valid_df.groupby('rashi_name')
        
        for name, group in grouped:
            trades = len(group)
            if trades == 0:
                continue
                
            wins = len(group[group['return'] > 0])
            mean_ret = group['return'].mean()
            win_rate = (wins / trades) * 100
            
            # Extract last 10 exact timestamp returns for the UI to digest and print.
            sorted_group = group.sort_values(by='datetime', ascending=False)
            recent = sorted_group.head(10)[['datetime', 'return']].to_dict('records')
            
            summary.append({
                'rashi_name': name,
                'mean_return': float(mean_ret),
                'win_rate': float(win_rate),
                'total_candles': int(trades),
                'recent_trades': [{'datetime': r['datetime'].strftime('%Y-%m-%d %H:%M'), 'return': float(r['return'])} for r in recent]
            })
            
        # Return cleanly sorted descending default
        return sorted(summary, key=lambda x: x['mean_return'], reverse=True)

    def build_intraday_yoga_dataset(self, symbol: str, period: str = "5000d", market: str = "NSE") -> pd.DataFrame:
        """
        Builds a dataset mapping 1-hour intraday market returns to the
        active Nitya Yoga over a dynamic horizon.
        """
        from modules.market_data import MarketDataFetcher
        market_fetcher = MarketDataFetcher()
        intraday_df = market_fetcher.fetch_intraday_data(symbol, period=period, interval="1h", market=market)
        
        if intraday_df.empty:
            return pd.DataFrame()
            
        settings = MARKET_LOCATIONS.get(market.upper(), MARKET_LOCATIONS['NSE'])
        tz = settings['tz']
        
        yoga_records = []
        for _, row in intraday_df.iterrows():
            candle_time = row['date']
            # Get the exact Yoga at this specific timestamp
            yoga_data = self.moon_calc.calculate_nakshatra(candle_time, tz)
            
            yoga_records.append({
                'datetime': candle_time,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row.get('volume', 0),
                'return': row.get('return', 0.0),
                'yoga_number': yoga_data['yoga_number'],
                'yoga_name': yoga_data['yoga_name']
            })
            
        return pd.DataFrame(yoga_records)
        
    def yoga_performance_summary(self, df: pd.DataFrame) -> list:
        """Calculate aggregate performance metrics by Nitya Yoga."""
        if df.empty or 'yoga_name' not in df.columns:
            return []
            
        summary = []
        valid_df = df.dropna(subset=['return'])
        grouped = valid_df.groupby('yoga_name')
        
        for name, group in grouped:
            trades = len(group)
            if trades == 0:
                continue
                
            wins = len(group[group['return'] > 0])
            mean_ret = group['return'].mean()
            win_rate = (wins / trades) * 100
            
            sorted_group = group.sort_values(by='datetime', ascending=False)
            recent = sorted_group.head(10)[['datetime', 'return']].to_dict('records')
            
            summary.append({
                'yoga_name': name,
                'mean_return': float(mean_ret),
                'win_rate': float(win_rate),
                'total_candles': int(trades),
                'recent_trades': [{'datetime': r['datetime'].strftime('%Y-%m-%d %H:%M'), 'return': float(r['return'])} for r in recent]
            })
            
        return sorted(summary, key=lambda x: x['mean_return'], reverse=True)

    def build_intraday_nakshatra_dataset(self, symbol: str, period: str = "5000d", market: str = "NSE") -> pd.DataFrame:
        """
        Builds a dataset mapping 1-hour intraday market returns to the
        active Nakshatra over a dynamic horizon.
        """
        from modules.market_data import MarketDataFetcher
        market_fetcher = MarketDataFetcher()
        intraday_df = market_fetcher.fetch_intraday_data(symbol, period=period, interval="1h", market=market)
        
        if intraday_df.empty:
            return pd.DataFrame()
            
        settings = MARKET_LOCATIONS.get(market.upper(), MARKET_LOCATIONS['NSE'])
        tz = settings['tz']
        
        nak_records = []
        for _, row in intraday_df.iterrows():
            candle_time = row['date']
            nak_data = self.moon_calc.calculate_nakshatra(candle_time, tz)
            
            nak_records.append({
                'datetime': candle_time,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row.get('volume', 0),
                'return': row.get('return', 0.0),
                'nakshatra_number': nak_data['nakshatra_number'],
                'nakshatra_name': nak_data['nakshatra_name'],
                'pada': nak_data.get('pada')
            })
            
        return pd.DataFrame(nak_records)
        
    def nakshatra_intraday_performance_summary(self, df: pd.DataFrame) -> list:
        """Calculate aggregate performance metrics by Intraday Nakshatra hourly cycles."""
        if df.empty or 'nakshatra_name' not in df.columns:
            return []
            
        summary = []
        valid_df = df.dropna(subset=['return'])
        grouped = valid_df.groupby('nakshatra_name')
        
        for name, group in grouped:
            trades = len(group)
            if trades == 0:
                continue
                
            wins = len(group[group['return'] > 0])
            mean_ret = group['return'].mean()
            win_rate = (wins / trades) * 100
            
            sorted_group = group.sort_values(by='datetime', ascending=False)
            recent = sorted_group.head(10)[['datetime', 'return']].to_dict('records')
            
            summary.append({
                'nakshatra_name': name,
                'mean_return': float(mean_ret),
                'win_rate': float(win_rate),
                'total_candles': int(trades),
                'recent_trades': [{'datetime': r['datetime'].strftime('%Y-%m-%d %H:%M'), 'return': float(r['return'])} for r in recent]
            })
            
        return sorted(summary, key=lambda x: x['mean_return'], reverse=True)

    def build_volatility_dataset(self, symbol: str, period: str = "5000d", threshold: float = 1.0, market: str = "NSE") -> tuple[pd.DataFrame, int]:
        """
        Builds a dataset extracting daily candles where absolute return exceeded `threshold`.
        Calculates all Astrological metrics precisely at 09:15 AM (Market Open) for those volatile days.
        """
        from modules.market_data import MarketDataFetcher
        from datetime import datetime, timedelta
        
        market_fetcher = MarketDataFetcher()
        
        # Parse approximate period to historical date
        days_back = int(period.replace('d', '')) if 'd' in period else 3650 
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Fetch daily data natively
        daily_df = market_fetcher.fetch_stock_data(symbol, start_date=start_date, market=market)
        
        if daily_df.empty:
            return pd.DataFrame(), 0
            
        settings = MARKET_LOCATIONS.get(market.upper(), MARKET_LOCATIONS['NSE'])
        tz = settings['tz']
        
        # Filter for volatile conditions
        volatile_df = daily_df[abs(daily_df['daily_return']) >= threshold].copy()
        
        vol_records = []
        for _, row in volatile_df.iterrows():
            # Force target calculation strictly to market opening minute of this calendar day
            open_dt = row['date'].replace(hour=settings['open_hour'], minute=settings['open_minute'], second=0, microsecond=0)
            
            # Fetch Astrometrics 
            metrics = self.moon_calc.calculate_nakshatra(open_dt, tz)
            
            # Additional metric formatting
            weekday_name = open_dt.strftime('%A')
            
            vol_records.append({
                'datetime': row['date'],
                'market_open': open_dt,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row.get('volume', 0),
                'return': row.get('daily_return', 0.0),
                'weekday': weekday_name,
                'tithi_name': metrics['tithi_name'],
                'nakshatra_name': metrics['nakshatra_name'],
                'yoga_name': metrics['yoga_name'],
                'rashi_name': metrics['rashi_name'] # Lagna mapping
            })
            
        return pd.DataFrame(vol_records), len(daily_df) # Pass back total days scoped
        
    def volatility_performance_summary(self, df: pd.DataFrame, total_scoped_days: int) -> dict:
        """Calculate ranked distributions and total probabilities of violent setups."""
        if df.empty:
            return {"weekday": [], "nakshatra": [], "tithi": [], "yoga": [], "lagna": []}
            
        vol_count = len(df)
        
        def _rank_category(column_name: str):
            grouped = df.groupby(column_name)
            cat_list = []
            for name, group in grouped:
                occurrences = len(group)
                avg_move = abs(group['return']).mean()
                win_pct = len(group[group['return'] > 0]) / occurrences * 100
                loss_pct = len(group[group['return'] < 0]) / occurrences * 100
                
                cat_list.append({
                    'name': name,
                    'count': occurrences,
                    'probability': (occurrences / total_scoped_days) * 100,
                    'share_of_volatile': (occurrences / vol_count) * 100,
                    'avg_absolute_move': float(avg_move),
                    'bull_bias': float(win_pct),
                    'bear_bias': float(loss_pct),
                    'recent_trades': group.sort_values(by='datetime', ascending=False).head(5)[['datetime', 'return']].to_dict('records')
                })
            return sorted(cat_list, key=lambda x: x['count'], reverse=True)
            
        return {
            "weekday": _rank_category('weekday'),
            "nakshatra": _rank_category('nakshatra_name'),
            "tithi": _rank_category('tithi_name'),
            "yoga": _rank_category('yoga_name'),
            "lagna": _rank_category('rashi_name')
        }
