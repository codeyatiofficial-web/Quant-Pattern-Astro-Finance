from datetime import datetime
from modules.moon_calculator import MoonCalculator
mc = MoonCalculator()
now = datetime.now()
res = mc.get_yoga_bounds(now)
print(res)
