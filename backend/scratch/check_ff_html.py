import httpx
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

with httpx.Client(headers=headers, verify=False, timeout=15.0) as client:
    r = client.get("https://www.forexfactory.com/calendar")
    print("Status:", r.status_code)
    print("Length:", len(r.text))
    
    # Check if calendar table is present
    if "calendar__table" in r.text or "calendar_row" in r.text or "calendar__row" in r.text:
        print("Calendar table found in HTML!")
        
        # Let's inspect some rows
        rows = re.findall(r'<tr[^>]*data-event-id="(\d+)"[^>]*>(.*?)</tr>', r.text, re.DOTALL)
        print(f"Found {len(rows)} event rows by data-event-id!")
        
        # Let's search for actual values
        # ForexFactory class for actual is often 'calendar__actual'
        actuals = re.findall(r'class="[^"]*calendar__actual[^"]*"[^>]*>(.*?)</td>', r.text, re.DOTALL)
        print(f"Found {len(actuals)} actual cells")
        clean_acts = [re.sub(r'<[^>]+>', '', a).strip() for a in actuals if re.sub(r'<[^>]+>', '', a).strip()]
        print(f"Non-empty actuals count: {len(clean_acts)}")
        print("Sample actuals:", clean_acts[:10])
    else:
        print("Page preview:", r.text[:500])
