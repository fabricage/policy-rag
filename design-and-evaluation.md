# Design and Evaluation

## Design decisions

### Embedding model: `all-MiniLM-L6-v2` (sentence-transformers)

Chosen because it is free, runs locally, and produces reproducible vectors without a paid embedding API. Local embeddings keep ingest cost at zero and avoid sending the full policy corpus to a third-party embedding service. The model is small enough for a student laptop while still providing solid semantic retrieval for short policy questions.

### Chunking strategy and sizes

Documents are split on `##` headings so each chunk maps to a coherent policy topic (accrual, MFA, per-diems, etc.). If a section exceeds ~350 tokens (approximated as whitespace-separated words), it is split into overlapping windows of ~300 tokens with 50-token overlap. Heading-aware chunks improve citation quality; overlap reduces the chance that a fact near a window boundary is missed. A fixed random seed (`42`) is set during ingest for reproducibility.

### Top-k = 4

Retrieving four chunks balances context coverage against prompt size and noise. For this 8-document corpus, k=4 usually surfaces the primary section plus nearby supporting sections without overwhelming the 8B model.

### Prompt format with labeled sources

Each retrieved chunk is labeled as `[Source: <filename> | Section: <heading>]`. The system prompt requires answers only from provided context, citations using those exact labels, honesty when context is insufficient, and answers under 150 words. Explicit labels make citations traceable back to files and sections instead of anonymous paragraph numbers.

### Chroma persistent store (`./chroma_db`)

Chroma provides zero-infrastructure local persistence: ingest once, query many times, no Docker or managed vector DB. The collection is named `policies` and stores metadata `{source, section, chunk_index}` per chunk for citation rendering.

### LLM: Anthropic Claude Haiku (primary), optional Groq

Generation uses Anthropic `claude-haiku-4-5` by default via `ANTHROPIC_API_KEY` (good fit for a Render presentation demo). Groq `llama-3.1-8b-instant` remains an optional fallback when `GROQ_API_KEY` is set (`LLM_PROVIDER=groq`). The model is called only after retrieval (and only when the similarity guardrail passes), so most of the pipeline remains local and inspectable. API keys are loaded from `.env` / Render env vars and are never hardcoded.

### Similarity guardrail threshold = 0.25

After retrieval, cosine similarity is derived from Chroma's cosine distance as `similarity = 1 - distance`. If the best chunk scores below `SIMILARITY_THRESHOLD = 0.25`, the system refuses:

> I can only answer questions about Meridian Software company policies.

The threshold (~0.25) was chosen as a conservative floor: in-corpus policy questions typically retrieve well above it, while unrelated trivia falls below and triggers refusal without calling the LLM.

## Evaluation approach

`evaluate.py` runs all 20 lines in `eval/questions.jsonl` through `answer_question()` and reports three metrics:

1. **Citation accuracy** — percentage of questions where `expected_source` appears in returned citations. For `expected_source: "NONE"`, success means the refusal message was returned (empty citations).
2. **Groundedness (LLM-as-judge)** — for answered (non-refusal) questions, the configured LLM is asked for a strict YES/NO: whether every claim in the answer is fully supported by the retrieved snippets. Report percentage YES.
3. **Latency** — wall-clock `latency_ms` from the full RAG pipeline; report p50 and p95 across all queries.

Results are written to `eval/results.md` as a summary table plus a per-question breakdown.

## Results

TODO: fill after running `evaluate.py`

| Metric | Value |
| --- | --- |
| Citation accuracy | TODO |
| Groundedness (YES %) | TODO |
| Latency p50 (ms) | TODO |
| Latency p95 (ms) | TODO |
