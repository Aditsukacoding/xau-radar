import json

path = r"C:\Users\Aditya\.gemini\antigravity-ide\brain\6c164e48-4d66-4007-b2a4-b172f3768b30\.system_generated\logs\transcript_full.jsonl"

with open(path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f):
        if line_num >= 1990 and line_num <= 2015:
            d = json.loads(line)
            content = d.get("content", "")
            if content:
                print(f"--- Line {line_num} ({d.get('type')}) ---")
                safe = content[:400].encode('ascii', errors='replace').decode('ascii')
                print(safe)
