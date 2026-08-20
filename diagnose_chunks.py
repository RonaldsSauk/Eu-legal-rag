
import json
from pathlib import Path

SILVER_PATH = Path("data/silver/chunks.jsonl")

chunks = []
with open(SILVER_PATH, "r", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

# sort by text length, longest first
chunks.sort(key=lambda c: len(c["text"]), reverse=True)

for c in chunks[:5]:
    print(f"{c['celex_id']} / {c['subdivision_id']} ({c['type']}): {len(c['text'])} chars")