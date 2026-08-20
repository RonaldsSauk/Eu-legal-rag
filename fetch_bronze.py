from textwrap import indent

import requests
import json
import time
from pathlib import Path
from datetime import datetime,timezone

BRONZE_DIR = Path("data/bronze")
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

CELEX_IDS = [
    "32016R0679",  # GDPR
    "32019L0790",  # Copyright DSM Directive
    "32022R2065",  # Digital Services Act
    "32022R1925",  # Digital Markets Act
    "32016L0680",  # Data Protection Law Enforcement Directive
    "32002L0058",  # ePrivacy Directive
]

def fetch_document(celex_id: str):
    url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex_id}"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},timeout=30)
    resp.raise_for_status()

    raw_path = BRONZE_DIR / f"{celex_id}.html"
    raw_path.write_text(resp.text, encoding="utf-8")

    metadata = {
        "celex_id": celex_id,
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "content_length": len(resp.text),
    }
    meta_path = BRONZE_DIR / f"{celex_id}.meta.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved {celex_id}: {len(resp.text)} bytes")

if __name__ == "__main__":
    for celex_id in CELEX_IDS:
        fetch_document(celex_id)
        time.sleep(1) # to make sure the server don't get overwhelmed