"""
Flask web application for Meridian Software policy RAG chat.

Runnable as: python app.py
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from rag import answer_question

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

app = Flask(__name__)

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Meridian Policy Assistant</title>
  <style>
    :root {
      --bg: #f3f6f4;
      --panel: #ffffff;
      --ink: #1f2a24;
      --muted: #5c6b62;
      --accent: #1f6f5b;
      --accent-dark: #155445;
      --border: #d5ddd8;
      --refuse: #7a3e3e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #dcece6 0%, transparent 40%),
        linear-gradient(180deg, #eef4f1 0%, var(--bg) 100%);
      min-height: 100vh;
    }
    main {
      max-width: 760px;
      margin: 0 auto;
      padding: 2rem 1.25rem 3rem;
    }
    h1 {
      margin: 0 0 0.35rem;
      font-size: 1.75rem;
    }
    .subtitle {
      margin: 0 0 1.5rem;
      color: var(--muted);
    }
    form {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }
    input[type="text"] {
      flex: 1;
      padding: 0.8rem 0.9rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 1rem;
      background: var(--panel);
    }
    button {
      padding: 0.8rem 1.1rem;
      border: none;
      border-radius: 8px;
      background: var(--accent);
      color: white;
      font-size: 1rem;
      cursor: pointer;
    }
    button:hover { background: var(--accent-dark); }
    button:disabled {
      opacity: 0.65;
      cursor: wait;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.1rem;
      margin-bottom: 1rem;
    }
    .label {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
      margin-bottom: 0.4rem;
    }
    #answer { white-space: pre-wrap; line-height: 1.45; }
    #meta { color: var(--muted); font-size: 0.9rem; }
    ul { margin: 0.25rem 0 0; padding-left: 1.2rem; }
    .snippet {
      margin-top: 0.75rem;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.92rem;
      white-space: pre-wrap;
    }
    .error { color: var(--refuse); }
    .hidden { display: none; }
  </style>
</head>
<body>
  <main>
    <h1>Meridian Policy Assistant</h1>
    <p class="subtitle">Ask questions about Meridian Software Inc. company policies.</p>

    <form id="chat-form">
      <input
        id="question"
        type="text"
        placeholder="e.g. How many PTO days do employees accrue in year one?"
        autocomplete="off"
        required
      />
      <button type="submit" id="ask-btn">Ask</button>
    </form>

    <div id="status" class="panel hidden"></div>

    <div id="result" class="hidden">
      <div class="panel">
        <div class="label">Answer</div>
        <div id="answer"></div>
        <div id="meta"></div>
      </div>

      <div class="panel">
        <div class="label">Citations</div>
        <ul id="citations"></ul>
      </div>

      <div class="panel">
        <div class="label">Retrieved snippets</div>
        <div id="snippets"></div>
      </div>
    </div>
  </main>

  <script>
    const form = document.getElementById("chat-form");
    const questionInput = document.getElementById("question");
    const askBtn = document.getElementById("ask-btn");
    const statusEl = document.getElementById("status");
    const resultEl = document.getElementById("result");
    const answerEl = document.getElementById("answer");
    const metaEl = document.getElementById("meta");
    const citationsEl = document.getElementById("citations");
    const snippetsEl = document.getElementById("snippets");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = questionInput.value.trim();
      if (!question) return;

      askBtn.disabled = true;
      resultEl.classList.add("hidden");
      statusEl.classList.remove("hidden", "error");
      statusEl.textContent = "Thinking...";

      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Request failed");
        }

        statusEl.classList.add("hidden");
        resultEl.classList.remove("hidden");
        answerEl.textContent = data.answer || "";
        metaEl.textContent = `Latency: ${data.latency_ms} ms`;

        citationsEl.innerHTML = "";
        if (!data.citations || data.citations.length === 0) {
          const li = document.createElement("li");
          li.textContent = "None";
          citationsEl.appendChild(li);
        } else {
          data.citations.forEach((citation) => {
            const li = document.createElement("li");
            li.textContent = `${citation.source} — ${citation.section}`;
            citationsEl.appendChild(li);
          });
        }

        snippetsEl.innerHTML = "";
        (data.snippets || []).forEach((snippet, index) => {
          const div = document.createElement("div");
          div.className = "snippet";
          div.textContent = `[${index + 1}] ${snippet}`;
          snippetsEl.appendChild(div);
        });
        if (!data.snippets || data.snippets.length === 0) {
          snippetsEl.textContent = "None";
        }
      } catch (error) {
        statusEl.classList.add("error");
        statusEl.textContent = error.message || "Something went wrong.";
      } finally {
        askBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    """Serve the minimal chat page.

    Why: a single inline template keeps the demo self-contained without a
    templates/ directory or frontend build step.
    """
    return INDEX_HTML


@app.post("/chat")
def chat():
    """Answer a policy question and return RAG JSON.

    Why: the browser posts {question} and receives answer, citations,
    snippets, and latency for display on the chat page.
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
    # Fail fast with a clear message if the key is missing when starting chat use
    if not os.getenv("GROQ_API_KEY"):
        print(
            "Warning: GROQ_API_KEY is not set. Create a .env file with "
            "GROQ_API_KEY=your_key_here before asking questions."
        )
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
