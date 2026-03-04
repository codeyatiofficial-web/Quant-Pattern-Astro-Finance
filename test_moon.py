from datetime import datetime
from modules.moon_calculator import MoonCalculator
import pytz

ist = pytz.timezone('Asia/Kolkata')
mc = MoonCalculator()
d = datetime(2026, 2, 28)
print(mc.get_moon_rise_set(d))
