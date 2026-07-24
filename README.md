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

## Notes

- Embeddings run fully locally (`all-MiniLM-L6-v2`); only answer generation calls Groq.
- If similarity of the best retrieved chunk is below `0.25`, the app refuses with:  
  `I can only answer questions about Meridian Software company policies.`
- Paths are resolved relative to the project root and work on macOS, Linux, and Windows.
