# api.py
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "eu_legal_rag",
    "user": "postgres",
    "password": os.getenv("PGVECTOR_PASSWORD", "postgres"),
}

app = FastAPI()

CELEX_NAMES = {
    "32016R0679": "GDPR",
    "32002L0058": "ePrivacy Directive",
    "32022R2065": "Digital Services Act",
    "32022R1925": "Digital Markets Act",
    "32019L0790": "Copyright Directive",
    "32016L0680": "Law Enforcement Directive",
}

def format_citation(celex_id: str, subdivision_id: str) -> str:
    doc_name = CELEX_NAMES.get(celex_id, celex_id)

    if subdivision_id.startswith("art_"):
        number = subdivision_id.replace("art_", "").split("_part")[0]
        label = f"Article {number}"
    elif subdivision_id.startswith("rct_"):
        number = subdivision_id.replace("rct_", "").split("_part")[0]
        label = f"Recital {number}"
    elif subdivision_id.startswith("cit_"):
        label = "Citation"
    elif subdivision_id.startswith("pbl_"):
        label = "Preamble"
    else:
        label = subdivision_id

    return f"{doc_name}, {label}"

# allow_origins=["*"] is fine for local dev.
# Before any public hosting, restrict this to your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

def embed_question(text: str):
    response = client.embeddings.create(model="text-embedding-3-small", input=[text])
    return response.data[0].embedding

def retrieve_chunks(question: str, top_k: int = 5):
    query_vector = embed_question(question)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT celex_id, subdivision_id, type, text, embedding <=> %s::vector AS distance
        FROM chunks
        ORDER BY distance
        LIMIT %s
    """, (query_vector, top_k))
    results = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "celex_id": r[0],
            "subdivision_id": r[1],
            "type": r[2],
            "text": r[3],
            "distance": r[4],
            "citation": format_citation(r[0], r[1]),
        }
        for r in results
    ]

def generate_answer(question: str, chunks: list) -> tuple[str, list[str]]:
    context = "\n\n".join(
        f"[{c['citation']}]: {c['text']}"
        for c in chunks
    )

    prompt = f"""Answer the question using ONLY the context below. Cite the source (e.g. "GDPR, Article 15") for each claim you make. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Respond with a JSON object with exactly two keys:
- "answer": your full answer text with inline citations
- "related_questions": an array of 2-3 natural follow-up questions a user might ask next, grounded in the same topic and documents"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    import json
    data = json.loads(response.choices[0].message.content)
    answer = data.get("answer", "")
    related_questions = data.get("related_questions", [])
    if not isinstance(related_questions, list):
        related_questions = []

    return answer, related_questions

@app.post("/query")
def query(request: QueryRequest):
    chunks = retrieve_chunks(request.question)
    answer, related_questions = generate_answer(request.question, chunks)

    return {
        "question": request.question,
        "answer": answer,
        "sources": chunks,
        "related_questions": related_questions,
    }

@app.get("/health")
def health():
    return {"status": "ok"}