import json
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv


load_dotenv()

GOLD_PATH = Path("data/gold/embeddings.jsonl")


DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "eu_legal_rag",
    "user": "postgres",
    "password": os.getenv("PGVECTOR_PASSWORD", "postgres"),
}

def load_records():
    records = []
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records

def main():
    records = load_records()
    print(f"loaded {len(records)} records from gold")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insert_query = """
        INSERT INTO chunks (celex_id, subdivision_id, type, text, embedding)
        VALUES (%s, %s, %s, %s, %s)
    """

    for i, record in enumerate(records):
        cur.execute(insert_query, (
            record["celex_id"],
            record["subdivision_id"],
            record["type"],
            record["text"],
            record["embedding"],
        ))

        if (i + 1) % 100 == 0:
            print(f"inserted {i + 1}/{len(records)}")

    conn.commit()
    print(f"inserted {len(records)}/{len(records)} — done")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()