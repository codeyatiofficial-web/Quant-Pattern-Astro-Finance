import asyncio
from modules.technical_analysis import TechnicalAnalyzer

async def main():
    ta = TechnicalAnalyzer()
    res = ta.run_multi_timeframe_scan("^NSEI", "NSE", "1y")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
