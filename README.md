# Meridian Software Policy RAG

A Flask web app that answers questions about Meridian Software Inc. company policies using Retrieval-Augmented Generation (RAG). Policy documents are chunked, embedded locally with sentence-transformers, stored in Chroma, and retrieved at query time so Groq's LLM can answer with source citations. No LangChain — retrieval, prompting, and API calls are implemented directly in plain Python.

## Architecture

```
 corpus/*.md
      |
      v
  ingest.py  ---- embeds chunks (all-MiniLM-L6-v2)
      |
      v
  chroma_db/ ("policies" collection)
      |
      v
  retrieve top-k=4  ---- similarity guardrail (~0.25)
      |
      v
  prompt + Groq (llama-3.1-8b-instant)
      |
      v
  cited answer (source + section + snippets)
```

## Prerequisites

- Python 3.11
- A Groq API key ([console.groq.com](https://console.groq.com/))

## Setup

```bash
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env in the project root (never commit this file)
echo "GROQ_API_KEY=your_key_here" > .env
```

## How to run

**1. Ingest the corpus** (creates `./chroma_db`):

```bash
python ingest.py
```

**2. Start the web app** (http://localhost:5000):

```bash
python app.py
```

**3. Ask a question from the CLI** (optional):

```bash
python rag.py "What is the domestic meal per-diem?"
```

**4. Run the evaluation suite** (writes `eval/results.md`):

```bash
python evaluate.py
```

**5. Run smoke tests** (no API key or vector store required):

```bash
pytest -q
```

## Example questions

1. How many PTO days per month do employees accrue in years 1–2?
2. What is the minimum password length required by the security policy?
3. What is the domestic meal per-diem for business travel?
4. What are Meridian's core collaboration hours for remote work?
5. What is the anonymous Ethics Hotline phone number?

## Project structure

```
.
├── app.py                      # Flask UI + /chat + /health
├── rag.py                      # retrieve → guardrail → Groq → citations
├── ingest.py                   # chunk, embed, store in Chroma
├── evaluate.py                 # citation / groundedness / latency metrics
├── requirements.txt
├── render.yaml                 # Render Blueprint (web service + GROQ_API_KEY)
├── pytest.ini                  # adds project root to PYTHONPATH for tests
├── README.md
├── design-and-evaluation.md
├── ai-tooling.md
├── corpus/                     # 8 Meridian policy markdown docs
├── eval/
│   ├── questions.jsonl         # 20 evaluation questions
│   └── results.md              # produced by evaluate.py
├── tests/
│   └── test_smoke.py
└── .github/workflows/ci.yml
```

## Deploy on Render (presentation)

This repo includes a Render Blueprint at `render.yaml`.

1. Merge this branch to `main` (if it is not already).
2. Open [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Connect the `fabricage/policy-rag` GitHub repo (branch `main`).
4. When prompted, paste your **GROQ_API_KEY** (marked `sync: false` in the blueprint).
5. Apply the Blueprint and wait for the first deploy.
   - Build runs `pip install` then `python ingest.py` (embeds corpus into `chroma_db`).
   - Start runs `gunicorn` on `$PORT` with health checks at `/health`.
6. Open the `*.onrender.com` URL and try an example question below.

If the free instance runs out of memory while loading `sentence-transformers`, edit the service plan in Render from **Free** to **Starter** and redeploy.

## Notes

- Embeddings run fully locally (`all-MiniLM-L6-v2`); only answer generation calls Groq.
- If similarity of the best retrieved chunk is below `0.25`, the app refuses with:  
  `I can only answer questions about Meridian Software company policies.`
- Paths are resolved relative to the project root and work on macOS, Linux, and Windows.
