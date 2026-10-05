"""Optional LLM enrichment. Uses OPENAI_API_KEY or GEMINI_API_KEY if set."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from app.models import MatchResult


PROMPT = """You are a hiring technical screener.
Given a RESUME and JOB, return ONLY JSON with keys:
match_percent (0-100 number), strengths (list of short strings),
gaps (list of short strings), explanation (1-2 sentences).
Be strict about required skills. Do not invent experience.
RESUME:
{resume}

JOB:
{job}
"""


def _call_openai(prompt: str) -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("no OPENAI_API_KEY")
    body = json.dumps(
        {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def _call_gemini(prompt: str) -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get(
        "GOOGLE_API_KEY", ""
    ).strip()
    if not key:
        raise RuntimeError("no GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    body = json.dumps(
        {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0}}
    ).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode())
    return data["candidates"][0]["content"]["parts"][0]["text"]


def llm_available() -> bool:
    return bool(
        os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )


def enrich_with_llm(resume: str, job: str, base: MatchResult) -> MatchResult:
    """Blend keyword score with LLM judgment when an API key is present."""
    if not llm_available():
        return base

    prompt = PROMPT.format(resume=resume[:8000], job=job[:8000])
    try:
        if os.environ.get("OPENAI_API_KEY", "").strip():
            raw = _call_openai(prompt)
        else:
            raw = _call_gemini(prompt)
    except (urllib.error.URLError, TimeoutError, KeyError, RuntimeError, json.JSONDecodeError):
        return base

    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return base

    llm_pct = float(parsed.get("match_percent", base.match_percent))
    llm_pct = max(0.0, min(100.0, llm_pct))
    blended = round((base.match_percent + llm_pct) / 2.0, 1)
    strengths = [str(s) for s in parsed.get("strengths", [])][:8]
    gaps = [str(g) for g in parsed.get("gaps", [])][:8]
    explanation = str(parsed.get("explanation") or base.explanation)
    if strengths:
        explanation += " Strengths: " + "; ".join(strengths) + "."
    missing = gaps if gaps else base.missing_skills

    return MatchResult(
        match_percent=blended,
        matched_skills=base.matched_skills or strengths,
        missing_skills=missing,
        job_skills_found=base.job_skills_found,
        explanation=explanation,
    )
