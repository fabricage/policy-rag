"""
Smoke tests that do not require an LLM API key or a populated vector store.
"""

from __future__ import annotations

from ingest import chunk_markdown_by_headings


def test_app_imports_successfully():
    """Verify the Flask app module imports without side-effect failures.

    Why: catches syntax/import errors early in CI without needing API keys.
    """
    import app as app_module

    assert app_module.app is not None


def test_health_endpoint_returns_ok():
    """Verify GET /health returns HTTP 200 and {"status": "ok"}.

    Why: proves the Flask routes are wired and the test client can exercise
    the app without calling an LLM API or Chroma.
    """
    import app as app_module

    client = app_module.app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_chunk_markdown_by_headings_splits_sample():
    """Verify markdown chunking splits on ## headings correctly.

    Why: ingestion quality depends on heading-aware chunking; this unit test
    locks the public chunking behavior without touching the vector store.
    """
    sample = """# Title

Intro paragraph about the company.

## Accrual Rates

Employees accrue 1.25 days per month in years one and two.

## Request Process

Submit requests at least 10 business days in advance for long absences.
"""
    chunks = chunk_markdown_by_headings(sample)

    headings = [heading for heading, _text in chunks]
    assert "Introduction" in headings
    assert "Accrual Rates" in headings
    assert "Request Process" in headings

    accrual = next(text for heading, text in chunks if heading == "Accrual Rates")
    assert "1.25 days" in accrual
    assert "## Accrual Rates" in accrual

    request = next(text for heading, text in chunks if heading == "Request Process")
    assert "10 business days" in request
