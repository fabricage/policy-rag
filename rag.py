"""
Retrieval-Augmented Generation helpers for Meridian Software policy Q&A.

Runnable as: python rag.py "question here"
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from ingest import CHROMA_DIR, COLLECTION_NAME, get_or_create_collection

# Load environment variables from .env at project root
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# Cosine similarity guardrail: refuse when the best retrieved chunk is
# less similar than this threshold (~0.25). Chroma cosine distance is
# defined as (1 - cosine_similarity), so we convert distance → similarity.
SIMILARITY_THRESHOLD = 0.25
TOP_K = 4
GROQ_MODEL = "llama-3.1-8b-instant"
REFUSAL_MESSAGE = (
    "I can only answer questions about Meridian Software company policies."
)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about Meridian Software Inc. company policies.

Rules:
1. Answer ONLY using the provided context chunks.
2. Cite sources using the exact labels shown in the context, for example [Source: pto-policy.md | Section: Accrual Rates].
3. If the context does not contain the answer, say that the provided policy context does not contain that information.
4. Keep answers under 150 words.
5. Do not invent policies, numbers, or procedures that are not in the context.
"""


def _require_groq_api_key() -> str:
    """Return the Groq API key or raise a clear setup error.

    Why: failing early with instructions is better than a vague client error
    when GROQ_API_KEY is missing from the environment / .env file.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Create a .env file in the project root "
            "with: GROQ_API_KEY=your_key_here"
        )
    return api_key


def retrieve_chunks(question: str, k: int = TOP_K) -> list[dict[str, Any]]:
    """Embed the question and retrieve the top-k policy chunks from Chroma.

    Why: this is the retrieval half of RAG. Each result includes document
    text, metadata, cosine distance, and derived cosine similarity.
    """
    if not CHROMA_DIR.exists():
        raise RuntimeError(
            f"Vector store not found at {CHROMA_DIR}. Run: python ingest.py"
        )

    collection = get_or_create_collection()
    if collection.count() == 0:
        raise RuntimeError(
            "The policies collection is empty. Run: python ingest.py"
        )

    results = collection.query(
        query_texts=[question],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[dict[str, Any]] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, distance in zip(documents, metadatas, distances):
        similarity = 1.0 - float(distance)
        chunks.append(
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", "unknown"),
                "chunk_index": meta.get("chunk_index", -1),
                "distance": float(distance),
                "similarity": similarity,
            }
        )
    return chunks


def build_context_block(chunks: list[dict[str, Any]]) -> str:
    """Format retrieved chunks with explicit source labels for the LLM.

    Why: labeled chunks make citations traceable and teach the model which
    filename/section to mention in the answer.
    """
    blocks: list[str] = []
    for chunk in chunks:
        label = f"[Source: {chunk['source']} | Section: {chunk['section']}]"
        blocks.append(f"{label}\n{chunk['text']}")
    return "\n\n---\n\n".join(blocks)


def call_groq(question: str, context_block: str) -> str:
    """Call Groq with the system prompt, context, and user question.

    Why: generation is intentionally separate from retrieval so either step
    can be tested or swapped without rewriting the whole pipeline.
    """
    api_key = _require_groq_api_key()
    client = Groq(api_key=api_key)

    user_content = (
        "Context:\n"
        f"{context_block}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Answer using only the context above and cite sources with the exact labels."
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        max_tokens=400,
    )
    return (response.choices[0].message.content or "").strip()


def extract_citations(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build a de-duplicated citation list from retrieved chunks.

    Why: the API response should expose which source documents/sections
    informed the answer, even when multiple chunks share a file.
    """
    seen: set[tuple[str, str]] = set()
    citations: list[dict[str, str]] = []
    for chunk in chunks:
        key = (chunk["source"], chunk["section"])
        if key in seen:
            continue
        seen.add(key)
        citations.append({"source": chunk["source"], "section": chunk["section"]})
    return citations


def answer_question(question: str) -> dict[str, Any]:
    """Answer a policy question with retrieval, guardrails, and citations.

    Why: this is the single entry point used by the Flask app, CLI, and
    evaluation script. Returns answer text, citations, snippets, and latency.
    """
    start = time.perf_counter()
    question = (question or "").strip()
    if not question:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return {
            "answer": "Please provide a question about Meridian Software policies.",
            "citations": [],
            "snippets": [],
            "latency_ms": round(latency_ms, 2),
        }

    chunks = retrieve_chunks(question, k=TOP_K)
    best_similarity = chunks[0]["similarity"] if chunks else 0.0

    # Guardrail: refuse out-of-corpus / low-relevance questions
    if not chunks or best_similarity < SIMILARITY_THRESHOLD:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return {
            "answer": REFUSAL_MESSAGE,
            "citations": [],
            "snippets": [],
            "latency_ms": round(latency_ms, 2),
        }

    context_block = build_context_block(chunks)
    answer = call_groq(question, context_block)
    citations = extract_citations(chunks)
    snippets = [chunk["text"] for chunk in chunks]

    latency_ms = (time.perf_counter() - start) * 1000.0
    return {
        "answer": answer,
        "citations": citations,
        "snippets": snippets,
        "latency_ms": round(latency_ms, 2),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for quick manual testing of answer_question()."""
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print('Usage: python rag.py "your question here"')
        return 1

    question = " ".join(argv)
    try:
        result = answer_question(question)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(result["answer"])
    print()
    print(f"Latency: {result['latency_ms']} ms")
    if result["citations"]:
        print("Citations:")
        for citation in result["citations"]:
            print(f"  - {citation['source']} | {citation['section']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
