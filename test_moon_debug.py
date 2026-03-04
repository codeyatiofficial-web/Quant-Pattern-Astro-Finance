from datetime import datetime
from modules.moon_calculator import MoonCalculator
import pytz
import ephem

ist = pytz.timezone('Asia/Kolkata')
mc = MoonCalculator()

def test_date(date):
    print(f"\n--- Testing for {date.date()} ---")
    mumbai = ephem.Observer()
    mumbai.lat = '19.0760'
    mumbai.lon = '72.8777'

    # Localize our target start time (Midnight IST)
    target_start = ist.localize(date.replace(hour=0, minute=0, second=0))
    utc_start = target_start.astimezone(pytz.UTC)
    
    # We want to know the Moon's behavior for the daytime of `date`
    # Sunrise of `date` typically happens around 6:30 AM
    # If the moon sets BEFORE this sunrise, it belongs to the previous night's cycle.
    # To get the moon set for THIS night, we should calculate from this evening
    
    # Let's set the observer to Noon IST of the target date to find the *evening's* set time
    noon_ist = target_start.replace(hour=12)
    mumbai.date = noon_ist.astimezone(pytz.UTC)

    moon = ephem.Moon()
    moon.compute(mumbai)

    try:
        next_setting = mumbai.next_setting(moon).datetime().replace(tzinfo=pytz.UTC).astimezone(ist)
        set_time = next_setting.strftime("%I:%M %p")
        
        # When anchored at Noon, any setting that falls on the following calendar date is "Next Day"
        is_next_day = next_setting.date() > target_start.date()
        
        print(f"Anchored at (IST): {noon_ist}")
        print(f"Next Setting (IST): {next_setting}")
        print(f"Formatted Time str: {set_time}")
        print(f"Is Next Day logic: {is_next_day}")
    except Exception as e:
        print(e)
        
test_date(datetime(2026, 2, 28))
