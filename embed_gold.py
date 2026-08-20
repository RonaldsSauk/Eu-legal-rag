import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SILVER_PATH = Path("data/silver/chunks.jsonl")
GOLD_DIR = Path("data/gold")
GOLD_DIR.mkdir(parents=True, exist_ok=True)
GOLD_PATH = GOLD_DIR / "embeddings.jsonl"

MODEL = "text-embedding-3-small"
BATCH_SIZE = 100

def split_long_text(text, max_chars=20000):
    """Split text into pieces under a safe character budget (rough proxy
    for OpenAI's 8192-token limit — ~4 chars/token, so 20000 chars is a
    conservative margin)."""
    if len(text) <= max_chars:
        return [text]

    words = text.split()
    parts = []
    current = []
    current_len = 0

    for word in words:
        current_len += len(word) + 1
        if current_len > max_chars:
            parts.append(" ".join(current))
            current = [word]
            current_len = len(word) + 1
        else:
            current.append(word)

    if current:
        parts.append(" ".join(current))

    return parts

def load_chunks():
    chunks = []
    with open(SILVER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            chunk = json.loads(line)
            pieces = split_long_text(chunk["text"])

            if len(pieces) == 1:
                chunks.append(chunk)
            else:
                for i, piece in enumerate(pieces):
                    new_chunk = dict(chunk)
                    new_chunk["text"] = piece
                    new_chunk["subdivision_id"] = f"{chunk['subdivision_id']}_part{i+1}"
                    chunks.append(new_chunk)
    return chunks

def embed_batch(texts):
    response = client.embeddings.create(model=MODEL, input=texts)
    return [item.embedding for item in response.data]



def main():
    chunks = load_chunks()
    print(f"loaded {len(chunks)} chunks from silver")

    with open(GOLD_PATH, "w", encoding="utf-8") as out_file:
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            texts = [c["text"] for c in batch]

            embeddings = embed_batch(texts)

            for chunk, embedding in zip(batch, embeddings):
                chunk["embedding"] = embedding
                out_file.write(json.dumps(chunk) + "\n")

            print(f"embedded {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")

if __name__ == "__main__":
    main()