from modules.analysis_engine import NakshatraAnalyzer
analyzer = NakshatraAnalyzer()

df = analyzer.build_intraday_lagna_dataset("^NSEI")
print("Intraday Lagna Dataset Built rows:", len(df))
if not df.empty:
    print("Start Date:", df['datetime'].min())
