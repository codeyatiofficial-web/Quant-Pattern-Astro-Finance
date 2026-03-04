from datetime import datetime
from modules.moon_calculator import MoonCalculator
import pytz

IST = pytz.timezone('Asia/Kolkata')
mc = MoonCalculator()
now = datetime.now()
res = mc.calculate_nakshatra(now)

print("Nakshatra:", res.get("nakshatra_name"))
print("Tithi:", res.get("tithi_name"))
print("Yoga:", res.get("yoga_name"))
print("Yoga Number:", res.get("yoga_number"))
