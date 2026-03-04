import pandas as pd
from datetime import datetime
from modules.astro_correlation import AstroCorrelationEngine, PLANET_MAP

engine = AstroCorrelationEngine()
df = pd.DataFrame({'date': pd.date_range(start='2024-04-07', end='2024-04-09')}) # Known Solar Eclipse April 8, 2024
res = engine.attach_planetary_states(df, ["Sun", "Moon", "Rahu", "Ketu"], calculate_yogas=True)
print(res[['date', 'Solar_Eclipse', 'Lunar_Eclipse']])

df = engine.attach_planetary_states(df, [], calculate_yogas=True) # test empty planets

dt = pd.to_datetime('2024-04-08 14:00:00')
metrics = {}
for p in PLANET_MAP.keys():
    metrics[p] = engine._get_planet_metrics(dt, PLANET_MAP[p])

sun_long = metrics["Sun"]["longitude"]
moon_long = metrics["Moon"]["longitude"]
rahu_long = metrics["Rahu"]["longitude"]
ketu_long = metrics["Ketu"]["longitude"]
sm_diff = abs(sun_long - moon_long)
print(f"Sun: {sun_long}, Moon: {moon_long}, Diff: {sm_diff}")
sun_rahu_diff = min(abs(sun_long - rahu_long), 360 - abs(sun_long - rahu_long))
sun_ketu_diff = min(abs(sun_long - ketu_long), 360 - abs(sun_long - ketu_long))
near_node = sun_rahu_diff < 18.0 or sun_ketu_diff < 18.0
print(f"Node Diffs: Rahu={sun_rahu_diff}, Ketu={sun_ketu_diff}, near_node: {near_node}")
