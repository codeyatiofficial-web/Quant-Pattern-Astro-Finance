import json
import urllib.request
req = urllib.request.Request("http://localhost:8000/api/analyze", json.dumps({"symbol": "^NSEI", "start_date": "2000-01-01"}).encode('utf-8'))
req.add_header('Content-Type', 'application/json')
response = urllib.request.urlopen(req)
data = json.loads(response.read().decode('utf-8'))
for label, summary in [("Total", data.get("summary", [])), ("Inside H", data.get("summary_market_rise", [])), ("Outside H", data.get("summary_outside_rise", []))]:
    krittika = [n for n in summary if n["nakshatra_name"] == "Krittika"]
    print(f"{label}: len = {len(summary)} elements. Krittika exists: {bool(krittika)}")
