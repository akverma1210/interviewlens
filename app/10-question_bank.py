"""Original interview prompts and lightweight role-signal extraction."""

import re

TECHNICAL_PROMPTS = [
    (
        "Design a small but production-ready API for a {role}. Walk through the data model, "
        "the most important endpoints, and how you would handle failures.",
        ["api", "data", "endpoint", "error", "validation", "test"],
    ),
    (
        "A feature you own is slow in production but works well locally. How would you investigate "
        "it, and what evidence would guide your fix?",
        ["measure", "log", "profile", "query", "cache", "test"],
    ),
    (
        "Explain how you would model and query the core data for a {role} project. Which constraints, "
        "indexes, and trade-offs would matter?",
        ["database", "schema", "index", "query", "constraint", "trade"],
    ),
    (
        "Describe your testing strategy for a new {role} feature. What would you unit test, integrate, "
        "and check manually before release?",
        ["unit", "integration", "edge", "mock", "regression", "deploy"],
    ),
    (
        "Tell me about a technical trade-off you would make when building a {role} project under a "
        "tight deadline. What would you postpone, and why?",
        ["trade", "scope", "risk", "priority", "maintain", "deadline"],
    ),
    (
        "How would you make a {role} application secure and observable from its first release?",
        ["security", "authentication", "authorization", "log", "metric", "secret"],
    ),
    (
        "A third-party service your {role} project depends on starts timing out. How would you protect "
        "the user experience and diagnose whether your own system is contributing to the problem?",
        ["timeout", "retry", "fallback", "log", "latency", "monitor"],
    ),
    (
        "Walk me through a safe deployment and rollback plan for a {role} service with a database "
        "change. How would you keep the old and new versions compatible?",
        ["deploy", "migration", "rollback", "backup", "version", "test"],
    ),
]

BEHAVIORAL_PROMPTS = [
    (
        "Tell me about a time you had to learn an unfamiliar tool or concept quickly to finish a "
        "{role} assignment. What was your approach and what changed because of your work?",
        ["learn", "action", "result", "feedback", "improve", "because"],
    ),
    (
        "Describe a disagreement with a teammate about implementation or priorities. How did you "
        "work through it, and what did you take away from the experience?",
        ["listen", "communicate", "decide", "trade", "result", "learn"],
    ),
    (
        "Walk me through a mistake you made in a project. When did you notice it, how did you recover, "
        "and what did you change afterward?",
        ["mistake", "responsibility", "fix", "communicate", "prevent", "learn"],
    ),
    (
        "Tell me about a time you balanced several deadlines. How did you choose what to do first, "
        "and how did you keep others informed?",
        ["priority", "deadline", "plan", "communicate", "risk", "result"],
    ),
    (
        "Describe a project where requirements changed midway. What did you do, and how did you "
        "decide whether the new direction was working?",
        ["requirement", "adapt", "scope", "communicate", "measure", "result"],
    ),
    (
        "Tell me about a contribution you made that improved a team project beyond your assigned "
        "tasks. Why did you step in, and what was the outcome?",
        ["initiative", "team", "impact", "help", "result", "learn"],
    ),
    (
        "Describe a time you received difficult feedback on your work. What did you do with it, and "
        "how did your later work change?",
        ["feedback", "listen", "action", "change", "result", "learn"],
    ),
    (
        "Tell me about a time you had to make progress on a {role} task with incomplete information. "
        "What assumptions did you test, and when did you ask for help?",
        ["ambiguous", "assumption", "question", "test", "communicate", "decide"],
    ),
]

STOP_WORDS = {
    "about", "after", "also", "and", "are", "but", "can", "for", "from", "have", "into",
    "our", "that", "the", "their", "this", "using", "will", "with", "you", "your", "must",
    "should", "work", "working", "experience", "years", "ability", "strong", "plus", "who",
}


def extract_job_signals(job_description: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{1,}", job_description.lower())
    seen: set[str] = set()
    signals: list[str] = []
    for word in words:
        cleaned = word.strip(".#-+")
        if len(cleaned) < 3 or cleaned in STOP_WORDS or cleaned in seen:
            continue
        seen.add(cleaned)
        signals.append(cleaned)
        if len(signals) == limit:
            break
    return signals


def generate_questions(role: str, interview_type: str, count: int, job_description: str) -> list[dict]:
    if interview_type == "technical":
        selected = [(text, focus, "technical") for text, focus in TECHNICAL_PROMPTS[:count]]
    elif interview_type == "behavioral":
        selected = [(text, focus, "behavioral") for text, focus in BEHAVIORAL_PROMPTS[:count]]
    else:
        technical_count = (count + 1) // 2
        behavioral_count = count - technical_count
        selected = [
            (text, focus, "technical") for text, focus in TECHNICAL_PROMPTS[:technical_count]
        ] + [
            (text, focus, "behavioral") for text, focus in BEHAVIORAL_PROMPTS[:behavioral_count]
        ]
        # Interleave categories so a practice run does not feel like two separate quizzes.
        reordered = []
        technical = [item for item in selected if item[2] == "technical"]
        behavioral = [item for item in selected if item[2] == "behavioral"]
        while technical or behavioral:
            if technical:
                reordered.append(technical.pop(0))
            if behavioral:
                reordered.append(behavioral.pop(0))
        selected = reordered

    signals = extract_job_signals(job_description)
    questions = []
    for index, (template, focus, category) in enumerate(selected):
        focus_terms = list(dict.fromkeys(focus + signals[:3]))
        suffix = ""
        if signals and index == 0:
            suffix = " Where useful, connect your answer to " + ", ".join(signals[:3]) + "."
        questions.append({
            "position": index,
            "text": template.format(role=role) + suffix,
            "category": category,
            "focus": focus_terms,
        })
    return questions
