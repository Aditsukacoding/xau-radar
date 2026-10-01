import json

with open("scratch/ff_thisweek_raw.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total events in thisweek: {len(data)}")
keys = set()
for item in data:
    keys.update(item.keys())
print("All keys across all events:", keys)

# Check actual field
has_actual = []
for ev in data:
    act = ev.get("actual")
    if act is not None and act != "" and act != "-":
        has_actual.append(ev)

print(f"Events with non-empty actual: {len(has_actual)}")
for ev in has_actual[:10]:
    print(f"[{ev.get('country')}] {ev.get('title')} | Date: {ev.get('date')} | Act: {ev.get('actual')} | Fc: {ev.get('forecast')} | Prev: {ev.get('previous')}")

# Check what the actual field contains for all events
actual_values = set()
for ev in data:
    act = ev.get("actual")
    if act:
        actual_values.add(act)
print("Unique actual values found:", list(actual_values)[:20])

# Check past events from Monday / Tuesday
print("\n--- Sample past events ---")
for ev in data[:15]:
    print(f"[{ev.get('country')}] {ev.get('title')} | Date: {ev.get('date')} | Act: {repr(ev.get('actual'))} | Fc: {repr(ev.get('forecast'))}")
