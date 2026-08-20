# EU Legal RAG

A retrieval-augmented generation (RAG) system that lets you ask natural-language questions about six real EU legal instruments — GDPR, Digital Services Act, Digital Markets Act, Copyright Directive, Law Enforcement Directive, and ePrivacy Directive — and get back cited, grounded answers. Built as a data engineering portfolio project to demonstrate a complete data pipeline from raw source scraping through to a working query interface.

## How it works

The project is structured as a four-stage pipeline feeding into a query API and a React frontend:

**Bronze → Silver → Gold → API → Frontend**

- **Bronze** (`fetch_bronze.py`): Fetches the raw HTML for each legal document from EUR-Lex and saves it as-is. This is the unmodified source of truth.
- **Silver** (`parse_silver.py`): Parses the raw HTML into individual chunks — one chunk per article or recital — using BeautifulSoup. Each chunk gets metadata like its document ID, subdivision type (article/recital), and a human-readable citation label.
- **Gold** (`embed_gold.py` + `load_gold.py`): Embeds every chunk using OpenAI's `text-embedding-3-small` model, then loads the resulting vectors into a Postgres database with the pgvector extension. This is what makes semantic search possible.
- **Query API** (`api.py`): A FastAPI backend. When you ask a question, it embeds your question the same way, finds the closest matching chunks in the database, then asks GPT-4o mini to write an answer using only those chunks as context — with inline citations like "GDPR, Article 20".
- **Frontend** (`frontend/`): A React + TypeScript app (Vite) that calls the API, shows the generated answer, and lists the exact source chunks it was based on with links to the full text on EUR-Lex.

## Interesting technical challenge

One of the six source documents — an older EU directive — was stored on EUR-Lex in a completely different HTML structure from the other five. The modern documents follow a clean, schema-based format that's straightforward to parse with CSS selectors. The older one uses a legacy layout with no consistent structural markers, so a second parsing strategy (regex-based fallback) was needed just for that document. The parser detects which format it's dealing with at runtime and routes accordingly. It's a small thing but it's the kind of real-world messiness that makes scrapers interesting to write.

## How to run it

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for Postgres + pgvector)
- An OpenAI API key

### 1. Clone and set up Python environment

```bash
git clone <your-repo-url>
cd eu-legal-rag

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up environment variables

Copy the example file and fill in your real key:

```bash
cp .env.example .env        # macOS/Linux
copy .env.example .env      # Windows PowerShell
```

Then open `.env` and replace the placeholder:

```
OPENAI_API_KEY=sk-...
PGVECTOR_PASSWORD=postgres
```

### 3. Start Postgres + pgvector

```bash
docker compose up -d
```

### 4. Run the pipeline

Run these scripts in order — each stage produces the input for the next:

```bash
python fetch_bronze.py    # scrape HTML from EUR-Lex → data/bronze/
python parse_silver.py    # parse into chunks → data/silver/chunks.jsonl
python embed_gold.py      # embed chunks → data/gold/embeddings.jsonl
python load_gold.py       # load vectors into Postgres
```

The data files are already committed to this repo, so you can skip straight to step 5 if you just want to run the API against the existing data.

### 5. Start the API

```bash
uvicorn api:app --reload
```

The API will be available at `http://localhost:8000`. You can test it at `http://localhost:8000/docs`.

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Known limitations / future improvements

- **No orchestration**: The pipeline is a set of standalone scripts run manually. A real production version would use something like Airflow or Dagster to schedule re-runs as documents are updated.
- **Legacy parser rough edges**: The regex-based parser for the older document format handles recital splitting imperfectly in a few edge cases — the structure is irregular enough that it's hard to get right without a proper grammar.
- **No retrieval evaluation**: There's no automated way to measure whether the retrieved chunks are actually the right ones for a given question. Adding a small labeled eval set and tracking recall/precision would be the natural next step.
