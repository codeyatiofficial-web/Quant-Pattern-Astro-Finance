from modules.technical_analysis import TechnicalAnalyzer

ta = TechnicalAnalyzer()
result = ta.run_multi_timeframe_scan("^NSEI", "NSE", "1y")

chart_pattern_summary = {"bullish_count": 0, "bearish_count": 0, "neutral_count": 0, "patterns": [], "direction": "neutral"}

all_pats = []
for tf_key, tf_data in result.get("scans", {}).items():
    for p in tf_data.get("patterns", []):
        bias = (p.get("bias") or "").lower()
        name = p.get("pattern_name") or p.get("name", "")
        wr = p.get("win_rate")
        all_pats.append({"name": name, "bias": bias, "source": p.get("source", ""), "timeframe": tf_key, "win_rate": wr})
        if "bullish" in bias:
            chart_pattern_summary["bullish_count"] += 1
        elif "bearish" in bias:
            chart_pattern_summary["bearish_count"] += 1
        else:
            chart_pattern_summary["neutral_count"] += 1

chart_pattern_summary["patterns"] = all_pats[:10]
bc = chart_pattern_summary["bullish_count"]
brc = chart_pattern_summary["bearish_count"]
if bc > brc + 1:
    chart_pattern_summary["direction"] = "bullish"
elif brc > bc + 1:
    chart_pattern_summary["direction"] = "bearish"

print("Direction:", chart_pattern_summary["direction"])
print(f"Bull: {bc}, Bear: {brc}, Neutral: {chart_pattern_summary['neutral_count']}")
for p in all_pats:
    print(p)
