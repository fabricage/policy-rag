"""
Evaluate the Meridian policy RAG pipeline on a fixed question set.

Runnable as: python evaluate.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from rag import REFUSAL_MESSAGE, _require_groq_api_key, answer_question

PROJECT_ROOT = Path(__file__).resolve().parent
EVAL_DIR = PROJECT_ROOT / "eval"
QUESTIONS_PATH = EVAL_DIR / "questions.jsonl"
RESULTS_PATH = EVAL_DIR / "results.md"

load_dotenv(PROJECT_ROOT / ".env")

JUDGE_MODEL = "llama-3.1-8b-instant"


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict[str, str]]:
    """Load evaluation questions from a JSONL file.

    Why: JSONL keeps each example self-contained and easy to append without
    editing a large JSON array.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Questions file not found: {path}")

    questions: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
            for key in ("question", "expected_source", "gold_answer"):
                if key not in item:
                    raise ValueError(f"Missing '{key}' on line {line_number} of {path}")
            questions.append(item)
    return questions


def citation_is_correct(expected_source: str, result: dict[str, Any]) -> bool:
    """Score citation accuracy for one evaluation example.

    Why: for in-corpus questions we check whether the expected filename
    appears in returned citations; for NONE questions, success means the
    guardrail refusal was returned.
    """
    if expected_source == "NONE":
        return result.get("answer", "").strip() == REFUSAL_MESSAGE

    cited_sources = {c.get("source") for c in result.get("citations", [])}
    return expected_source in cited_sources


def judge_groundedness(question: str, answer: str, snippets: list[str]) -> str:
    """Ask Groq for a strict YES/NO groundedness judgment.

    Why: LLM-as-judge estimates whether every claim in the answer is
    supported by retrieved context, catching fluent but ungrounded answers.
    Returns 'Y' or 'N'.
    """
    # Refusal / empty-context cases are not judged for groundedness claims
    if answer.strip() == REFUSAL_MESSAGE or not snippets:
        return "N"

    api_key = _require_groq_api_key()
    client = Groq(api_key=api_key)
    context = "\n\n".join(snippets)
    prompt = (
        "You are a strict factuality judge.\n"
        "Question:\n"
        f"{question}\n\n"
        "Answer:\n"
        f"{answer}\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Is every claim in this answer fully supported by the provided context?\n"
        "Reply with ONLY YES or NO."
    )
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=5,
    )
    text = (response.choices[0].message.content or "").strip().upper()
    if text.startswith("YES"):
        return "Y"
    return "N"


def percentile(values: list[float], pct: float) -> float:
    """Compute a percentile using nearest-rank on sorted values.

    Why: p50/p95 latency summaries need a simple, dependency-free method
    that works on small evaluation sets.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(1, int(round((pct / 100.0) * len(ordered))))
    return ordered[min(rank, len(ordered)) - 1]


def run_evaluation() -> dict[str, Any]:
    """Run every eval question through the RAG pipeline and score metrics.

    Why: centralizes citation accuracy, groundedness, and latency so the
    markdown report can be generated from one structured result object.
    """
    questions = load_questions()
    rows: list[dict[str, Any]] = []

    citation_hits = 0
    grounded_yes = 0
    grounded_judged = 0
    latencies: list[float] = []

    for item in questions:
        question = item["question"]
        expected_source = item["expected_source"]
        print(f"Evaluating: {question}")

        result = answer_question(question)
        latencies.append(float(result["latency_ms"]))

        citation_ok = citation_is_correct(expected_source, result)
        if citation_ok:
            citation_hits += 1

        cited = ", ".join(
            sorted({c["source"] for c in result.get("citations", [])})
        ) or "(none)"

        # Groundedness only judged for non-refusal answers with snippets
        if expected_source == "NONE" or result.get("answer", "").strip() == REFUSAL_MESSAGE:
            grounded = "N/A"
        else:
            grounded = judge_groundedness(
                question,
                result.get("answer", ""),
                result.get("snippets", []),
            )
            grounded_judged += 1
            if grounded == "Y":
                grounded_yes += 1

        rows.append(
            {
                "question": question,
                "expected_source": expected_source,
                "cited_source": cited,
                "citation_ok": citation_ok,
                "grounded": grounded,
                "latency_ms": result["latency_ms"],
                "answer": result.get("answer", ""),
            }
        )

    citation_accuracy = (citation_hits / len(questions) * 100.0) if questions else 0.0
    groundedness = (grounded_yes / grounded_judged * 100.0) if grounded_judged else 0.0
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    mean_latency = statistics.mean(latencies) if latencies else 0.0

    return {
        "rows": rows,
        "citation_accuracy": citation_accuracy,
        "groundedness": groundedness,
        "grounded_judged": grounded_judged,
        "grounded_yes": grounded_yes,
        "p50": p50,
        "p95": p95,
        "mean_latency": mean_latency,
        "n": len(questions),
        "citation_hits": citation_hits,
    }


def write_results_markdown(summary: dict[str, Any], path: Path = RESULTS_PATH) -> None:
    """Write aggregate metrics and a per-question breakdown to markdown.

    Why: a checked-in results file documents evaluation outcomes for the
    course write-up without requiring reviewers to re-run the suite.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Evaluation Results")
    lines.append("")
    lines.append("## Summary Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(
        f"| Citation accuracy | {summary['citation_accuracy']:.1f}% "
        f"({summary['citation_hits']}/{summary['n']}) |"
    )
    lines.append(
        f"| Groundedness (YES) | {summary['groundedness']:.1f}% "
        f"({summary['grounded_yes']}/{summary['grounded_judged']} judged) |"
    )
    lines.append(f"| Latency p50 (ms) | {summary['p50']:.2f} |")
    lines.append(f"| Latency p95 (ms) | {summary['p95']:.2f} |")
    lines.append(f"| Latency mean (ms) | {summary['mean_latency']:.2f} |")
    lines.append("")
    lines.append("## Per-Question Breakdown")
    lines.append("")
    lines.append(
        "| Question | Cited source | Expected source | Grounded | Latency (ms) |"
    )
    lines.append("| --- | --- | --- | --- | --- |")

    for row in summary["rows"]:
        question = row["question"].replace("|", "\\|")
        cited = row["cited_source"].replace("|", "\\|")
        expected = row["expected_source"]
        grounded = row["grounded"]
        latency = row["latency_ms"]
        lines.append(
            f"| {question} | {cited} | {expected} | {grounded} | {latency} |"
        )

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """Run evaluation end-to-end and write eval/results.md."""
    try:
        _require_groq_api_key()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        summary = run_evaluation()
        write_results_markdown(summary)
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1

    print()
    print("Evaluation complete.")
    print(
        f"  Citation accuracy: {summary['citation_accuracy']:.1f}% "
        f"({summary['citation_hits']}/{summary['n']})"
    )
    print(
        f"  Groundedness:      {summary['groundedness']:.1f}% "
        f"({summary['grounded_yes']}/{summary['grounded_judged']} judged)"
    )
    print(f"  Latency p50:       {summary['p50']:.2f} ms")
    print(f"  Latency p95:       {summary['p95']:.2f} ms")
    print(f"  Wrote:             {RESULTS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
