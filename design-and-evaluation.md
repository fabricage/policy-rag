# Meridian Software Policy RAG — Design & Evaluation Document

Repository: (https://github.com/fabricage/policy-rag/)
Deployed app (optional): (https://meridian-policy-rag.onrender.com)
Author: Ellis Painter

---

## 1. What the system does, and for whom

The Meridian Software Policy RAG is a Flask web application that answers
employee questions about the policies of Meridian Software Inc., a fictional
company. It uses Retrieval-Augmented Generation (RAG): instead of answering
from the LLM's general knowledge, it finds the relevant passages in a fixed
set of policy documents and answers **only** from those passages, citing the
source file and section for every answer.

The intended users are **employees** who need a quick, trustworthy answer
("How many PTO days carry over?", "What is the domestic per-diem?") without
reading eight policy documents. Because every answer shows its citation and the
supporting snippet, the employee can verify the answer instead of trusting the
model blindly.

**Corpus.** Eight synthetic policy documents in Markdown (about 18,000 words,
roughly 40 pages), written for this project so they can be included legally:
PTO, security, expenses, remote work, holiday schedule, code of conduct,
onboarding, and data privacy. Each document is organized by `##` headings and
contains specific, testable facts (day counts, dollar limits, named roles) so
the answers can be checked objectively.

## 2. Architecture and design decisions

### 2.1 Overall architecture

```
 corpus/*.md ──► ingest.py ──► chroma_db/ ("policies" collection)
                 (chunk + embed)            │
                                            ▼
 user question ──► rag.py: embed ──► retrieve top-4 ──► similarity guardrail
                                                            │ pass   │ fail
                                                            ▼        ▼
                                  labeled-source prompt + LLM     refusal
                                                            │
                                                            ▼
                               answer + citations + snippets + latency
                                                            │
                         app.py (Flask): /  ·  POST /chat  ·  /health
```

The system is split into one module per responsibility:

| Module | Responsibility |
|---|---|
| `ingest.py` | Load corpus, chunk by headings, embed, store in Chroma (offline indexing step) |
| `rag.py` | Retrieve top-k, apply guardrail, build prompt, call LLM, return answer + citations (single entry point: `answer_question()`) |
| `app.py` | Flask layer: chat UI at `/`, JSON API at `/chat`, liveness at `/health` |
| `evaluate.py` | Run the question set and compute citation accuracy, groundedness, and latency |
| `tests/test_smoke.py` | CI smoke tests that need no API key or vector store |

**Why this shape:** the Flask app, the CLI (`python rag.py "..."`), and the
evaluation script all call the **same** `answer_question()` function. The
evaluation therefore measures exactly the code path users hit, not a separate
test harness.

### 2.2 Design decisions and reasons

| Decision | Choice | Reason |
|---|---|---|
| Orchestration | Plain Python, no LangChain | The pipeline is a few short functions; writing them directly keeps every step visible, easy to explain, and free of framework version churn |
| Embedding model | `all-MiniLM-L6-v2`, run locally (ONNX by default) | Free, no embedding API key, reproducible vectors, and the corpus is never sent to a third-party embedding service |
| Chunking | Split on `##` headings; sections over ~350 tokens split into ~300-token windows with 50-token overlap | Policy documents are already organized by topic headings, so each chunk is one coherent topic (and the heading becomes the citation's section). Overlap keeps a fact near a window edge from being cut in half |
| Reproducibility | Fixed seed `42`; collection rebuilt on every ingest | The same corpus always produces the same index |
| Retrieval | Top-k = 4, cosine similarity | Enough context to answer questions that span two documents without flooding the prompt with noise |
| Prompt format | Each chunk labeled `[Source: <file> \| Section: <heading>]`; model instructed to answer only from context, cite those exact labels, say when the context lacks the answer, and stay under 150 words | Labels make citations traceable to a specific file and section instead of an anonymous passage |
| Vector store | Chroma, persistent in `./chroma_db` | Zero infrastructure (no server, account, or Docker). Ingest once, query many times |
| LLM | Anthropic Claude Haiku (`claude-haiku-4-5`) by default; Groq `llama-3.1-8b-instant` optional via `LLM_PROVIDER` | Fast, low-cost generation for a live demo; provider choice is kept in one function so switching is a config change, not a code change |
| Secrets | API keys loaded from `.env` / Render env vars; `.env` is git-ignored | No key is ever committed or hardcoded |

### 2.3 Guardrails

1. **Out-of-scope refusal.** Chroma returns cosine distance; the system
   converts it to similarity (`1 − distance`). If the best retrieved chunk
   scores below `SIMILARITY_THRESHOLD = 0.25`, the app returns *"I can only
   answer questions about Meridian Software company policies."* and **never
   calls the LLM**. Off-topic questions cost nothing and cannot produce a
   hallucinated answer.
2. **Answer-only-from-context.** The system prompt forbids inventing policies,
   numbers, or procedures and requires the model to say when the context does
   not contain the answer.
3. **Length limit.** Answers are capped at 150 words in the prompt and
   `max_tokens=400` at the API.
4. **Always cite.** Every non-refusal response returns a de-duplicated list of
   source/section citations plus the raw snippets used.

### 2.4 Tradeoffs I accepted

- **Local embeddings:** I accepted a small general-purpose embedding model
  instead of a larger paid one, because for a 40-page, heading-structured
  corpus it retrieves well, costs nothing, and runs anywhere, including CI.
- **Fixed threshold guardrail:** I accepted that one global threshold (0.25) is
  a blunt tool. A borderline question could be refused or let through. In
  exchange, the guardrail is simple, explainable, and runs before any LLM
  cost is incurred.
- **Retrieval-based citations:** citations are taken from the retrieved chunks
  rather than parsed out of the model's text. This guarantees every citation
  points at a real file and section, but it can list a retrieved section the
  final answer did not actually rely on.

## 3. Evaluation

### 3.1 Evaluation set

`eval/questions.jsonl` contains **20 questions**, each with an
`expected_source` and a short `gold_answer`:

| Topic | Questions |
|---|---|
| PTO | 3 |
| Expenses | 3 |
| Security, remote work, holidays, code of conduct, onboarding, data privacy | 2 each (12) |
| Out-of-corpus (expected refusal, `expected_source: NONE`) | 2 |

Every policy document is covered, and the two out-of-corpus questions test the
refusal guardrail.

### 3.2 Metrics and method

`python evaluate.py` runs every question through `answer_question()` (the same
path the app uses) and writes `eval/results.md`.

1. **Citation accuracy:** the percentage of questions where the expected
   source file appears in the returned citations. For the two `NONE`
   questions, success means the refusal message was returned.
2. **Groundedness (LLM-as-judge):** for every answered (non-refusal) question,
   the LLM receives the question, the answer, and the retrieved snippets and
   must reply strictly **YES** or **NO** to *"Is every claim in this answer
   fully supported by the provided context?"* (temperature 0). Groundedness is
   the share of YES responses. Refusals are excluded rather than counted as
   failures.
3. **Latency:** wall-clock time for the full pipeline (embed → retrieve →
   guardrail → LLM → response), reported as p50 and p95 (nearest-rank) across
   all 20 queries.

### 3.3 Results

*Source: `eval/results.md`, run on [DATE] with LLM provider [anthropic/groq].*

| Metric | Result |
|---|---|
| Citation accuracy | [XX.X]% ([N]/20) |
| Groundedness | [XX.X]% ([N]/[N] judged) |
| Latency p50 | [XXXX] ms |
| Latency p95 | [XXXX] ms |



### 3.4 Limitations

- **Self-judging.** The groundedness judge is the same LLM that generated the
  answers, so it may be lenient toward its own output. I spot-checked
  [N] judgments by hand against the snippets to confirm they were reasonable.
- **Citation accuracy is retrieval-driven.** Because citations come from the
  top-4 retrieved chunks, this metric mainly measures retrieval quality. It
  confirms the right document was retrieved and shown, not that the model's
  wording relied on it (groundedness covers that side).
- **Small, synthetic set.** Twenty questions over a synthetic corpus show the
  approach works; they are not a statistically strong benchmark for a real
  company's policies.

## 4. Testing and CI/CD

### 4.1 Automated tests

`tests/test_smoke.py` (pytest) runs **without an API key or a vector store**,
so CI never needs secrets:

| Test | What it proves |
|---|---|
| `test_app_imports_successfully` | The Flask app and its imports load (catches syntax and import errors) |
| `test_health_endpoint_returns_ok` | `GET /health` returns 200 and `{"status": "ok"}` |
| `test_index_serves_modern_chat_shell` | `GET /` renders the chat page, so template and static paths are wired correctly |
| `test_chunk_markdown_by_headings_splits_sample` | Heading-aware chunking splits sections correctly and keeps each fact in the right section |

### 4.2 CI pipeline

`.github/workflows/ci.yml` runs on **every push and pull request**: check out
the code, set up Python 3.11, `pip install -r requirements.txt`, then
`pytest -q`. A broken dependency or a broken import fails the build before
anything is deployed. On Render, `autoDeployTrigger: commit` redeploys from
`main`.

### 4.3 Manual test pass (before recording the demo)

- In-corpus question → correct answer with a matching citation and snippet
- Question spanning two documents → both sources cited
- Off-corpus question → refusal message, no LLM call
- `GET /health` → `{"status": "ok"}`; `POST /chat` → JSON with `answer`,
  `citations`, `snippets`, `latency_ms`
- `POST /chat` with an empty question → HTTP 400 with a clear error
- Missing API key → clear setup message instead of a stack trace