import httpx
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

for week in ["thisweek", "nextweek"]:
    url = f"https://nfs.faireconomy.media/ff_calendar_{week}.json"
    try:
        r = httpx.get(url, headers=headers, timeout=10.0)
        print(f"{week} status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"{week} total events: {len(data)}")
            # Check fields
            if data:
                print("First event keys:", list(data[0].keys()))
                print("Sample event:", data[0])
            with_act = [e for e in data if e.get("actual") or "actual" in e and e["actual"] != ""]
            print(f"{week} with non-empty actual: {len(with_act)}")
            for e in with_act[:5]:
                print("  ACTUAL:", e.get("country"), e.get("title"), e.get("date"), "act:", e.get("actual"), "fc:", e.get("forecast"), "prev:", e.get("previous"))
            # Also let's check past events
            for e in data[:10]:
                print("  RAW:", e.get("country"), e.get("title"), e.get("date"), "act:", repr(e.get("actual")), "fc:", repr(e.get("forecast")), "prev:", repr(e.get("previous")))
        else:
            print("Response:", r.text[:200])
    except Exception as exc:
        print(f"Error fetching {week}: {exc}")
