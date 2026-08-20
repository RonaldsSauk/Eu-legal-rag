
import os
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "eu_legal_rag",
    "user": "postgres",
    "password": os.getenv("PGVECTOR_PASSWORD", "postgres"),
}

QUESTION = "What are the rules about cookies and consent?"

def embed_question(text):
    response = client.embeddings.create(model="text-embedding-3-small", input=[text])
    return response.data[0].embedding

def main():
    query_vector = embed_question(QUESTION)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT celex_id, subdivision_id, type, text, embedding <=> %s::vector AS distance
        FROM chunks
        ORDER BY distance
        LIMIT 5
    """, (query_vector,))

    results = cur.fetchall()

    print(f"Question: {QUESTION}\n")
    for celex_id, subdivision_id, chunk_type, text, distance in results:
        print(f"[{celex_id} / {subdivision_id} / {chunk_type}] distance={distance:.4f}")
        print(text[:200] + "...\n")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()