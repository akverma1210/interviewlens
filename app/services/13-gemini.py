"""Optional Gemini enhancement. Local analysis remains the explicit fallback."""

import json
import os
import re

import httpx

from app.schemas import ScoreSet

PROMPT = """You are an interview coach reviewing a candidate's written practice answer.
Evaluate only the answer against the question. Return one JSON object and no markdown.
Use this exact shape:
{
  "overall_score": 0,
  "scores": {"relevance": 0, "structure": 0, "communication": 0, "technical_depth": 0},
  "strengths": ["specific observation"],
  "improvements": ["specific actionable change"],
  "summary": "two sentences at most"
}
Every score must be an integer from 0 to 100. Give 2 or 3 strengths and 2 or 3 improvements.
Do not invent experience or claim that the candidate actually achieved anything. Coach, do not rewrite
the answer as if it were the candidate's own experience.

Target role: {role}
Interview question: {question}
Candidate answer: {answer}
"""


def _clean_json(text: str) -> str:
    text = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    return fenced.group(1) if fenced else text


def analyze_with_gemini(answer: str, question: str, role: str) -> dict | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": PROMPT.format(role=role, question=question, answer=answer)}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
    }
    try:
        response = httpx.post(url, headers={"x-goog-api-key": api_key}, json=payload, timeout=35)
        response.raise_for_status()
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(_clean_json(text))
        scores = ScoreSet(**result["scores"]).model_dump()
        overall = max(0, min(100, int(result["overall_score"])))
        strengths = [str(item)[:500] for item in result["strengths"][:3]]
        improvements = [str(item)[:500] for item in result["improvements"][:3]]
        summary = str(result["summary"])[:1000]
        if not strengths or not improvements or not summary:
            return None
        return {
            "overall_score": overall,
            "scores": scores,
            "strengths": strengths,
            "improvements": improvements,
            "summary": summary,
        }
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None
