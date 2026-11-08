"""Transparent, deterministic answer analysis used with or without an AI key."""

import re
from dataclasses import asdict, dataclass

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'+#.-]*")
FILLERS = {"um", "uh", "basically", "literally", "actually", "stuff", "things"}
TECHNICAL_SIGNALS = {
    "api", "database", "sql", "query", "index", "cache", "test", "tests", "testing",
    "unit", "integration", "deploy", "deployment", "security", "authentication", "authorization",
    "performance", "latency", "scale", "scaling", "error", "errors", "logging", "metrics",
    "python", "fastapi", "javascript", "react", "node", "transaction", "validation", "async",
    "mongodb", "postgresql", "sqlite", "docker", "http", "endpoint", "schema", "regression",
}
ACTION_WORDS = {
    "built", "created", "implemented", "designed", "tested", "improved", "reduced", "fixed",
    "led", "decided", "measured", "deployed", "refactored", "learned", "communicated", "prioritized",
}


@dataclass
class LocalAnalysis:
    overall_score: int
    scores: dict[str, int]
    strengths: list[str]
    improvements: list[str]
    summary: str

    def as_dict(self) -> dict:
        return asdict(self)


def clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def analyze_locally(response: str, question: str, role: str, focus: list[str]) -> LocalAnalysis:
    words = [word.lower() for word in WORD_RE.findall(response)]
    word_count = len(words)
    unique_words = set(words)
    sentences = [part for part in re.split(r"[.!?]+", response) if part.strip()]

    matched_focus = [term for term in focus if term.lower() in response.lower()]
    focus_ratio = len(matched_focus) / max(1, min(len(focus), 6))
    role_tokens = [token for token in WORD_RE.findall(role.lower()) if len(token) > 2]
    role_mentioned = any(token in unique_words for token in role_tokens)
    relevance = clamp(40 + focus_ratio * 48 + (7 if role_mentioned else 0) + min(word_count, 100) * 0.05)

    structure_signals = {
        "context": {"when", "while", "during", "situation", "background"},
        "goal": {"needed", "goal", "task", "responsible", "requirements"},
        "action": ACTION_WORDS,
        "outcome": {"result", "outcome", "improved", "reduced", "increased", "learned", "because"},
    }
    structure_hits = sum(bool(unique_words & signals) for signals in structure_signals.values())
    structure = clamp(28 + structure_hits * 14 + (6 if len(sentences) >= 3 else 0))

    filler_count = sum(word in FILLERS for word in words)
    if word_count < 35:
        length_score = 35 + word_count
    elif word_count <= 260:
        length_score = 94
    elif word_count <= 450:
        length_score = 88
    else:
        length_score = max(55, 88 - (word_count - 450) // 8)
    communication = clamp(length_score - filler_count * 5 + min(len(sentences), 6))

    technical_matches = unique_words & TECHNICAL_SIGNALS
    has_metric = bool(re.search(r"\b\d+(?:\.\d+)?%?\b", response))
    reasoning_terms = {"because", "trade", "tradeoff", "however", "instead", "risk", "measure"}
    technical_depth = clamp(
        30 + min(len(technical_matches), 9) * 6 + (8 if has_metric else 0)
        + min(len(unique_words & reasoning_terms), 3) * 5
    )

    scores = {
        "relevance": relevance,
        "structure": structure,
        "communication": communication,
        "technical_depth": technical_depth,
    }
    overall = clamp(
        relevance * 0.30 + structure * 0.25 + communication * 0.20 + technical_depth * 0.25
    )

    strengths: list[str] = []
    if matched_focus:
        strengths.append("You addressed useful cues from the question: " + ", ".join(matched_focus[:4]) + ".")
    if structure_hits >= 3:
        strengths.append("Your answer has a clear context-action-outcome arc, which makes it easy to follow.")
    if has_metric:
        strengths.append("You included a concrete number, giving the interviewer evidence of scale or impact.")
    if len(technical_matches) >= 4:
        strengths.append("You used specific engineering vocabulary instead of staying at a high level.")
    if word_count >= 70 and filler_count <= 1:
        strengths.append("The response is substantial and stays concise, with few filler words.")
    if not strengths:
        strengths.append("You started answering directly. Keep that direct opening as you add more detail.")

    improvements: list[str] = []
    if len(matched_focus) < 2:
        improvements.append("Tie each part of the answer back to the exact question and name your key decisions explicitly.")
    if structure_hits < 3:
        improvements.append("Use a simple arc: brief context, your goal, the actions you personally took, and the result.")
    if word_count < 70:
        improvements.append("Add a specific example and explain one important decision rather than stopping at a general approach.")
    elif word_count > 350:
        improvements.append("Tighten the answer to two or three minutes by removing repeated background and keeping the strongest example.")
    if not has_metric:
        improvements.append("Add one concrete measure such as latency, test coverage, users, time saved, or a before-and-after comparison.")
    if filler_count > 2:
        improvements.append("Replace filler words with a short pause; it will make the delivery sound more deliberate.")
    if len(technical_matches) < 3:
        improvements.append("Name the tools, failure modes, tests, or trade-offs that shaped your approach.")
    if not improvements:
        improvements.append("Finish with what you would improve next time to show reflection and ownership.")

    if overall >= 85:
        summary = "A strong, specific response. Keep the same evidence and structure while tightening the delivery."
    elif overall >= 70:
        summary = "A solid foundation. More measurable impact and sharper decision-making would make it memorable."
    elif overall >= 50:
        summary = "The core idea is there. Add a concrete example, your personal actions, and a clearer outcome."
    else:
        summary = "Start with one specific example, then explain your actions and result in more detail."

    return LocalAnalysis(overall, scores, strengths[:3], improvements[:3], summary)
