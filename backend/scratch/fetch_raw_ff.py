import httpx
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.forexfactory.com/",
    "Origin": "https://www.forexfactory.com",
}

with httpx.Client(headers=headers, timeout=10.0) as client:
    r = client.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json")
    print("Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Total events:", len(data))
        has_act = [e for e in data if e.get("actual")]
        print("Events with 'actual' truthy:", len(has_act))
        for e in data[:15]:
            print(f"[{e.get('country')}] {e.get('title')} | Date: {e.get('date')} | act={repr(e.get('actual'))} | fc={repr(e.get('forecast'))}")
        if has_act:
            print("\nSample with actual:")
            for e in has_act[:5]:
                print(f"[{e.get('country')}] {e.get('title')} | act={repr(e.get('actual'))}")
        # Save to file for inspection
        with open("scratch/ff_raw_dump.json", "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2)
        print("Saved raw dump to scratch/ff_raw_dump.json")
    elif r.status_code == 429:
        print("429 Retry-After:", r.headers.get("retry-after"))
    else:
        print("Other:", r.status_code, r.text[:200])
