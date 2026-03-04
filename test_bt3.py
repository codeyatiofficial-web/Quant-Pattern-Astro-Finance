import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.technical_analysis import TechnicalAnalyzer
import json

scanner = TechnicalAnalyzer()
res = scanner._analyze_timeframe("^NSEI", "5m", "5d", "5m", "NSE", "10y")
print("Response:", json.dumps(res, indent=2))
