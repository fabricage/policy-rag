"""
Ingest Meridian Software policy documents into a persistent Chroma vector store.

Runnable as: python ingest.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# Project paths (relative to this file's directory = project root)
PROJECT_ROOT = Path(__file__).resolve().parent
CORPUS_DIR = PROJECT_ROOT / "corpus"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "policies"

# Chunking constants (approximate tokens as whitespace-separated words)
SECTION_TOKEN_LIMIT = 350
WINDOW_TOKENS = 300
WINDOW_OVERLAP = 50
RANDOM_SEED = 42

# Embedding model used for all chunk vectors
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def approximate_token_count(text: str) -> int:
    """Approximate token count using whitespace-separated words.

    Why: sentence-transformers and LLMs use subword tokens, but a simple
    word count is stable, dependency-free, and good enough for chunk sizing.
    """
    return len(text.split())


def split_into_overlapping_windows(
    text: str,
    window_tokens: int = WINDOW_TOKENS,
    overlap: int = WINDOW_OVERLAP,
) -> list[str]:
    """Split long text into overlapping word windows.

    Why: keeps chunks near a target size while preserving continuity across
    window boundaries via overlap so facts near edges are less likely lost.
    Uses a fixed random seed elsewhere in the pipeline for reproducibility;
    this splitter itself is deterministic.
    """
    words = text.split()
    if not words:
        return []

    if len(words) <= window_tokens:
        return [" ".join(words)]

    step = max(window_tokens - overlap, 1)
    windows: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + window_tokens, len(words))
        windows.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += step
    return windows


def chunk_markdown_by_headings(markdown_text: str) -> list[tuple[str, str]]:
    """Split markdown into (section_heading, section_body) chunks.

    Why: ## headings mark coherent policy topics, which retrieve better than
    arbitrary fixed-size slices. Oversized sections are further windowed.
    Returns a list of (heading, chunk_text) pairs ready for embedding.
    """
    # Split on level-2 headings while keeping the heading line
    parts = re.split(r"(?m)^(## .+)$", markdown_text)
    chunks: list[tuple[str, str]] = []

    # Text before the first ## heading (e.g. title / intro)
    preamble = parts[0].strip() if parts else ""
    if preamble:
        heading = "Introduction"
        for window in _section_to_windows(heading, preamble):
            chunks.append(window)

    # parts alternates: preamble, heading, body, heading, body, ...
    for i in range(1, len(parts), 2):
        heading_line = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        heading = heading_line.lstrip("#").strip()
        section_text = f"{heading_line}\n\n{body}".strip()
        for window in _section_to_windows(heading, section_text):
            chunks.append(window)

    return chunks


def _section_to_windows(heading: str, section_text: str) -> list[tuple[str, str]]:
    """Convert one section into one or more (heading, text) windows.

    Why: sections under the token limit stay whole; longer ones are split
    with overlap so retrieval can still surface mid-section details.
    """
    if approximate_token_count(section_text) <= SECTION_TOKEN_LIMIT:
        return [(heading, section_text)]

    windows = split_into_overlapping_windows(section_text)
    return [(heading, window) for window in windows]


def load_corpus_markdown(corpus_dir: Path = CORPUS_DIR) -> list[tuple[str, str]]:
    """Load every .md file from the corpus directory.

    Why: keeps ingestion file-discovery in one place and ignores non-markdown
    artifacts. Returns (filename, raw_text) pairs sorted by filename.
    """
    if not corpus_dir.is_dir():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    documents: list[tuple[str, str]] = []
    for path in sorted(corpus_dir.glob("*.md")):
        documents.append((path.name, path.read_text(encoding="utf-8")))
    return documents


def get_embedding_function() -> embedding_functions.SentenceTransformerEmbeddingFunction:
    """Create the shared SentenceTransformer embedding function.

    Why: Chroma needs a consistent embedding function at ingest and query
    time so vectors live in the same space.
    """
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )


def get_or_create_collection(
    persist_dir: Path = CHROMA_DIR,
    collection_name: str = COLLECTION_NAME,
):
    """Open the persistent Chroma collection used for policy chunks.

    Why: persistence in ./chroma_db lets ingest once and query many times
    without re-embedding the corpus on every app start.
    """
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    embedding_fn = get_embedding_function()
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_corpus(
    corpus_dir: Path = CORPUS_DIR,
    persist_dir: Path = CHROMA_DIR,
) -> tuple[int, int]:
    """Chunk, embed, and store all corpus markdown files.

    Why: this is the offline indexing step of the RAG pipeline. Returns
    (documents_processed, chunks_stored) for the summary printout.
    """
    # Fixed seed for any randomized chromadb / numpy paths during ingest
    import random

    import numpy as np

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    documents = load_corpus_markdown(corpus_dir)
    if not documents:
        raise RuntimeError(f"No markdown files found in {corpus_dir}")

    # Recreate collection for a clean ingest each run
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        # Collection may not exist on first run
        pass

    collection = get_or_create_collection(persist_dir=persist_dir)

    ids: list[str] = []
    documents_text: list[str] = []
    metadatas: list[dict] = []

    for filename, text in documents:
        section_chunks = chunk_markdown_by_headings(text)
        for chunk_index, (section, chunk_text) in enumerate(section_chunks):
            chunk_id = f"{filename}::{chunk_index}"
            ids.append(chunk_id)
            documents_text.append(chunk_text)
            metadatas.append(
                {
                    "source": filename,
                    "section": section,
                    "chunk_index": chunk_index,
                }
            )

    # Add in batches to avoid oversized single requests
    batch_size = 64
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents_text[start:end],
            metadatas=metadatas[start:end],
        )

    return len(documents), len(ids)


def main() -> int:
    """Run ingestion from the command line and print a short summary."""
    docs_processed, chunks_stored = ingest_corpus()
    print("Ingest complete.")
    print(f"  Documents processed: {docs_processed}")
    print(f"  Chunks stored:       {chunks_stored}")
    print(f"  Collection:          {COLLECTION_NAME}")
    print(f"  Persist directory:   {CHROMA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
