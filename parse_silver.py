# parse_silver.py
import json
import re
import warnings
from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")
SILVER_DIR.mkdir(parents=True, exist_ok=True)

CELEX_IDS = [
    "32016R0679",
    "32019L0790",
    "32022R2065",
    "32022R1925",
    "32016L0680",
    "32002L0058",
]

ARTICLE_RE = re.compile(r"^Article\s+(\d+)$")
RECITAL_RE = re.compile(r"^\((\d+)\)\s+(.*)")

def classify_subdivision(div_id: str) -> str:
    if div_id.startswith("art_"):
        return "article"
    elif div_id.startswith("rct_"):
        return "recital"
    elif div_id.startswith("cit_"):
        return "citation"
    elif div_id.startswith("pbl_"):
        return "preamble"
    else:
        return "other"

def parse_document_eli(celex_id: str):
    """Parser for newer EUR-Lex documents using eli-subdivision divs."""
    html_path = BRONZE_DIR / f"{celex_id}.html"
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    chunks = []
    for div in soup.find_all("div", class_="eli-subdivision"):
        div_id = div.get("id")
        if not div_id:
            continue
        if div.find("div", class_="eli-subdivision") is not None:
            continue

        paragraphs = div.find_all("p", class_="oj-normal")
        text = " ".join(p.get_text(strip=True) for p in paragraphs)
        if not text:
            continue

        chunks.append({
            "celex_id": celex_id,
            "subdivision_id": div_id,
            "type": classify_subdivision(div_id),
            "text": text,
        })

    return chunks

def parse_document_legacy(celex_id: str):
    """Fallback parser for older documents with flat, unstructured <p> tags."""
    html_path = BRONZE_DIR / f"{celex_id}.html"
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    container = soup.find("div", id="TexteOnly")
    if container is None:
        return []

    paragraphs = [p.get_text(strip=True) for p in container.find_all("p")]
    paragraphs = [p for p in paragraphs if p]

    chunks = []
    current_type = "preamble"
    current_id = "pbl_1"
    current_texts = []

    def flush():
        if current_texts:
            chunks.append({
                "celex_id": celex_id,
                "subdivision_id": current_id,
                "type": current_type,
                "text": " ".join(current_texts),
            })

    for para in paragraphs:
        art_match = ARTICLE_RE.match(para)
        rec_match = RECITAL_RE.match(para)

        if art_match:
            flush()
            current_type = "article"
            current_id = f"art_{art_match.group(1)}"
            current_texts = []
            continue

        if rec_match and current_type != "article":
            flush()
            current_type = "recital"
            current_id = f"rct_{rec_match.group(1)}"
            current_texts = [para]
            continue

        current_texts.append(para)

    flush()
    return chunks

def parse_document(celex_id: str):
    """Try the ELI parser first; fall back to legacy parsing if it finds nothing."""
    chunks = parse_document_eli(celex_id)
    if chunks:
        return chunks
    print(f"  {celex_id}: no eli-subdivision found, using legacy parser")
    return parse_document_legacy(celex_id)

if __name__ == "__main__":
    output_path = SILVER_DIR / "chunks.jsonl"
    total_chunks = 0

    with open(output_path, "w", encoding="utf-8") as out_file:
        for celex_id in CELEX_IDS:
            chunks = parse_document(celex_id)
            print(f"{celex_id}: extracted {len(chunks)} chunks")
            total_chunks += len(chunks)

            for chunk in chunks:
                out_file.write(json.dumps(chunk) + "\n")

    print(f"\ntotal: {total_chunks} chunks written to {output_path}")

    # spot-check the legacy parser output
    legacy_chunks = parse_document_legacy("32002L0058")
    for chunk in legacy_chunks:
        if chunk["subdivision_id"] == "art_5":
            print("\nlegacy sample (Article 5):")
            print(json.dumps(chunk, indent=2))
            break