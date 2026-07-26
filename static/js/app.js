/**
 * Meridian Policy Assistant — chat UI
 * Vanilla ES module + Motion.dev for presence animations.
 */

import { animate, stagger } from "https://cdn.jsdelivr.net/npm/motion@12.42.2/+esm";

const form = document.querySelector("#chat-form");
const questionInput = document.querySelector("#question");
const askBtn = document.querySelector("#ask-btn");
const statusEl = document.querySelector("#status");
const threadEl = document.querySelector("#thread");
const emptyHint = document.querySelector("#empty-hint");
const brand = document.querySelector("#brand");
const intro = document.querySelector(".intro");

const NEXT_PLACEHOLDER = "What's your next question?";
const FIRST_PLACEHOLDER = "Ask about Meridian policies…";

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Run entrance motion for the brand and intro.
 * Why: establishes a calm, intentional first impression without clutter.
 */
function playIntroMotion() {
  if (reduceMotion) return;

  animate(
    brand,
    { opacity: [0, 1], y: [18, 0] },
    { duration: 0.7, easing: [0.22, 1, 0.36, 1] }
  );
  animate(
    intro,
    { opacity: [0, 1], y: [14, 0] },
    { duration: 0.65, delay: 0.12, easing: [0.22, 1, 0.36, 1] }
  );
  animate(
    form,
    { opacity: [0, 1], y: [20, 0] },
    { duration: 0.6, delay: 0.22, easing: [0.22, 1, 0.36, 1] }
  );
}

/**
 * Animate a newly added conversation turn into view.
 * Why: makes each answer feel present without distracting from content.
 */
function animateTurn(turn) {
  if (reduceMotion) return;
  animate(
    turn,
    { opacity: [0, 1], y: [16, 0] },
    { duration: 0.45, easing: [0.22, 1, 0.36, 1] }
  );

  const details = turn.querySelectorAll(".citations li, .snippet");
  if (details.length) {
    animate(
      details,
      { opacity: [0, 1], y: [8, 0] },
      { delay: stagger(0.04, { start: 0.15 }), duration: 0.35 }
    );
  }
}

/**
 * Build DOM for one user + assistant exchange.
 * Why: keeps markup generation in one place for the chat thread.
 */
function appendTurn(question, data) {
  emptyHint.hidden = true;

  const turn = document.createElement("article");
  turn.className = "turn";
  turn.setAttribute("aria-label", "Question and answer");

  const userBubble = document.createElement("div");
  userBubble.className = "bubble user";
  userBubble.innerHTML = `<p class="role">You</p>`;
  const userText = document.createElement("p");
  userText.textContent = question;
  userBubble.appendChild(userText);

  const assistantBubble = document.createElement("div");
  assistantBubble.className = "bubble assistant";
  assistantBubble.innerHTML = `<p class="role">Meridian</p>`;

  const answer = document.createElement("p");
  answer.textContent = data.answer || "";
  assistantBubble.appendChild(answer);

  const meta = document.createElement("div");
  meta.className = "meta-row";
  meta.textContent = `Latency ${Number(data.latency_ms ?? 0).toFixed(0)} ms`;
  assistantBubble.appendChild(meta);

  const citations = Array.isArray(data.citations) ? data.citations : [];
  const citeBlock = document.createElement("div");
  citeBlock.className = "citations";
  citeBlock.innerHTML = "<h3>Citations</h3>";
  const list = document.createElement("ul");
  if (!citations.length) {
    const li = document.createElement("li");
    li.textContent = "None";
    list.appendChild(li);
  } else {
    citations.forEach((citation) => {
      const li = document.createElement("li");
      li.textContent = `${citation.source} — ${citation.section}`;
      list.appendChild(li);
    });
  }
  citeBlock.appendChild(list);
  assistantBubble.appendChild(citeBlock);

  const snippets = Array.isArray(data.snippets) ? data.snippets : [];
  if (snippets.length) {
    const snipBlock = document.createElement("div");
    snipBlock.className = "snippets";
    snipBlock.innerHTML = "<h3>Retrieved snippets</h3>";
    snippets.forEach((snippet, index) => {
      const p = document.createElement("p");
      p.className = "snippet";
      p.textContent = `[${index + 1}] ${snippet}`;
      snipBlock.appendChild(p);
    });
    assistantBubble.appendChild(snipBlock);
  }

  turn.appendChild(userBubble);
  turn.appendChild(assistantBubble);
  threadEl.appendChild(turn);
  animateTurn(turn);
  turn.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "end" });
}

/**
 * Reset the composer for the next question.
 * Why: after one answer, the field should invite another question immediately.
 */
function readyForNextQuestion() {
  questionInput.value = "";
  questionInput.placeholder = NEXT_PLACEHOLDER;
  questionInput.focus({ preventScroll: true });
}

/**
 * Show or clear the status line under the composer.
 */
function setStatus(message, isError = false) {
  if (!message) {
    statusEl.hidden = true;
    statusEl.textContent = "";
    statusEl.classList.remove("is-error");
    return;
  }
  statusEl.hidden = false;
  statusEl.textContent = message;
  statusEl.classList.toggle("is-error", isError);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  askBtn.disabled = true;
  setStatus("Thinking…");

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

    appendTurn(question, data);
    setStatus("");
    readyForNextQuestion();
  } catch (error) {
    setStatus(error.message || "Something went wrong.", true);
    // Keep the typed question so the user can retry
    questionInput.focus({ preventScroll: true });
  } finally {
    askBtn.disabled = false;
  }
});

// First load: restore first-run placeholder if thread empty
if (!threadEl.children.length) {
  questionInput.placeholder = FIRST_PLACEHOLDER;
}

playIntroMotion();
