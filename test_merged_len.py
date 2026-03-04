from modules.analysis_engine import NakshatraAnalyzer
analyzer = NakshatraAnalyzer()

df = analyzer.build_merged_dataset(start_date="1995-01-01", symbol="^NSEI", market="NSE")
print("Merged Dataset Built rows:", len(df))
if not df.empty:
    print("Start Date:", df['date'].min())
