# AI Tooling Summary — Meridian Software Policy RAG

## Tools Used
- **Claude (Anthropic)** — project planning, rubric analysis, and phase-by-phase
  build guidance
- **Cursor (AI IDE)** — code generation and in-editor refactoring
- **Anthropic Claude Haiku (via API)** — the LLM inside the application itself
  (answer generation and the LLM-as-judge groundedness check); listed here for
  completeness, not as a development tool

## How They Were Used
I started by loading the project requirements and rubric into Claude and using
it to break the assignment into ten build phases with acceptance criteria for
each: repo setup, corpus, ingestion, the RAG pipeline, guardrails, the Flask
app, evaluation, CI/CD, documentation, and the demo. From that plan, I wrote a
detailed specification prompt for Cursor covering the tech stack, folder
structure, every file to generate, the chunking strategy, the source-labeled
prompt format, the similarity guardrail, the three evaluation metrics, and the
CI workflow. The spec deliberately left the evaluation results and this file
as TODOs so the numbers and the reflection would come from actually running
the system.

Cursor generated the code from that spec: the synthetic Meridian Software
policy corpus first, then `ingest.py`, `rag.py`, the Flask app, the evaluation
harness, the smoke tests, and the GitHub Actions workflow. After each stage I
verified the output manually: running `python ingest.py` and checking the
chunk counts, asking questions from the CLI with `python rag.py`, confirming
that off-topic questions were refused, hitting `/health` and `/chat`, and
running `pytest -q` locally before pushing.

## What Worked Well
- Writing the spec first meant the generated code matched the planned
  architecture on the first pass: one file per responsibility (ingest,
  retrieve/generate, web app, evaluation) with no framework sprawl, since the
  spec ruled out LangChain.
- Generating eight internally consistent policy documents (about 18,000 words)
  with specific, testable facts (accrual rates, per-diems, password rules) was
  far faster than writing them by hand, and the specific numbers made the
  evaluation questions easy to write and score.
- Specifying the `[Source: file | Section: heading]` label format in the
  prompt produced citations that trace back to an exact file and section.
- Designing the smoke tests to need no API key or vector store meant CI went
  green without exposing any secrets to GitHub Actions.

## What Didn't Work / Required Manual Fixes
- I wanted the app live on Render, even though deployment was optional, and
  the first deploy hit Render's free-tier memory limit (about 512MB) because
  `sentence-transformers` pulls in PyTorch. I switched the default embedding
  backend to Chroma's ONNX build of the same `all-MiniLM-L6-v2` model and
  added a slim `requirements-render.txt` without PyTorch. Same embeddings, a
  fraction of the memory. The original PyTorch path is still available
  locally through `EMBEDDING_BACKEND=sentence_transformers`.
- The original plan used Groq as the LLM. I moved the default to Anthropic
  Claude Haiku for the deployed demo and kept Groq as an optional fallback
  through `LLM_PROVIDER`, which meant restructuring `rag.py` and
  `evaluate.py` so provider selection lives in one place.


## Reflection
AI tooling handled the mechanical code generation, but the architecture, the
chunking and retrieval choices, verification at each phase, the deployment
memory fix, and interpreting the evaluation results remained my
responsibility. The biggest lesson was that the RAG pipeline itself is short.
The work that matters is measuring it: building the question set, checking
that citations point to the right document, and making sure the guardrail
refuses what it should without blocking real policy questions.