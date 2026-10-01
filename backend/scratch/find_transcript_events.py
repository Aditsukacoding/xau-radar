import json

path = r"C:\Users\Aditya\.gemini\antigravity-ide\brain\6c164e48-4d66-4007-b2a4-b172f3768b30\.system_generated\logs\transcript_full.jsonl"

with open(path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f):
        if "Got " in line and "raw events" in line:
            print(f"Line {line_num}: {line[:300]}")
            data = json.loads(line)
            print("Content:", data.get("content", "")[:500])
