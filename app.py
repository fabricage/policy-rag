"""
Flask web application for Meridian Software policy RAG chat.

Runnable as: python app.py
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from rag import answer_question

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
)


@app.get("/")
def index():
    """Serve the modern chat page.

    Why: templates + static assets keep semantic HTML, CSS, and ES-module
    JavaScript readable and cacheable instead of one giant inline string.
    """
    return render_template("index.html")


@app.post("/chat")
def chat():
    """Answer a policy question and return RAG JSON.

    Why: the browser posts {question} and receives answer, citations,
    snippets, and latency for display in the chat thread.
    """
    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Request JSON must include a non-empty 'question' string."}), 400

    try:
        result = answer_question(question.strip())
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:  # pragma: no cover - unexpected runtime failures
        return jsonify({"error": f"Unexpected error: {exc}"}), 500

    return jsonify(result)


@app.get("/health")
def health():
    """Liveness endpoint for CI and uptime checks.

    Why: lets tests and operators confirm the Flask app is importable and
    responding without calling the LLM or vector store.
    """
    return jsonify({"status": "ok"})


def main() -> None:
    """Run the development server (local) on PORT or 5000.

    Why: Render injects PORT; locally we default to 5000. Production on
    Render uses gunicorn via render.yaml instead of this entry point.
    """
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("GROQ_API_KEY")):
        print(
            "Warning: No LLM API key is set. Create a .env file with "
            "ANTHROPIC_API_KEY=your_key_here (recommended) or "
            "GROQ_API_KEY=your_key_here before asking questions."
        )
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
