from datetime import datetime, date
import holidays
from dateutil.relativedelta import relativedelta

class HolidaysEngine:
    def __init__(self):
        # We initialize both Indian (NSE) and US (NASDAQ) holidays.
        try:
            self.in_holidays = holidays.IND()
            self.us_holidays = holidays.US(subdiv="NY") # NYSE/NASDAQ generally follow US/NY bank holidays
        except Exception:
            # Fallback for older versions of holidays library
            self.in_holidays = holidays.India()
            self.us_holidays = holidays.UnitedStates()

    def get_next_business_day(self, target_date: date, market: str = "NSE") -> date:
        """
        Given a date, rolls it forward to the next valid business day, skipping weekends and market holidays.
        """
        holiday_calendar = self.us_holidays if market.upper() == "NASDAQ" else self.in_holidays
        
        current_date = target_date
        while True:
            # Check if weekend (5 = Saturday, 6 = Sunday)
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
                
            # Check if official holiday
            if current_date in holiday_calendar:
                current_date += timedelta(days=1)
                continue
                
            # Valid business day found!
            break
            
        return current_date

    def calculate_1_month_target(self, anchor_date: date, market: str = "NSE") -> date:
        """
        Calculates the exact date 1 month from the anchor_date.
        If that 1-month mark falls on a weekend or holiday, it returns the next available business day.
        """
        raw_target = anchor_date + relativedelta(months=1)
        return self.get_next_business_day(raw_target, market)

# Singleton instance to be used by the app
holidays_engine = HolidaysEngine()
