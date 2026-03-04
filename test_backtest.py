import asyncio
from modules.technical_analysis import TechnicalAnalyzer

async def main():
    scanner = TechnicalAnalyzer()
    res = scanner.run_multi_timeframe_scan("^NSEI", "NSE", "10y")
    import json
    print(json.dumps(res, indent=2))

asyncio.run(main())
