from modules.analysis_engine import NakshatraAnalyzer
import traceback
import pytz
import pandas as pd

a = NakshatraAnalyzer()
df = a.build_merged_dataset('2000-01-01')
print("original merged length:", len(df), df['date'].min())
