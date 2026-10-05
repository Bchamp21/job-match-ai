import re

from app.models import MatchResult
from app.skills import SKILLS


def _find_skills(text: str) -> list[str]:
    """Return curated skills that appear in text (case-insensitive)."""
    found: list[str] = []
    lower = text.lower()
    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"
        if re.search(pattern, lower):
            found.append(skill)
    return found


def score_resume(resume: str, job: str) -> MatchResult:
    """Score resume against job by overlapping curated skill keywords."""
    job_skills = _find_skills(job)
    resume_skills = set(_find_skills(resume))

    if not job_skills:
        return MatchResult(
            match_percent=0.0,
            matched_skills=[],
            missing_skills=[],
            job_skills_found=[],
            explanation=(
                "No known skills found in the job description. "
                "Add clearer tech keywords or expand the skill list."
            ),
        )

    matched = [s for s in job_skills if s in resume_skills]
    missing = [s for s in job_skills if s not in resume_skills]
    percent = round(100.0 * len(matched) / len(job_skills), 1)

    if percent >= 80:
        tone = "Strong match."
    elif percent >= 50:
        tone = "Partial match."
    else:
        tone = "Weak match."

    explanation = (
        f"{tone} Resume covers {len(matched)} of {len(job_skills)} "
        f"skills required by the job"
        + (f"; missing: {', '.join(missing[:5])}." if missing else ".")
    )

    return MatchResult(
        match_percent=percent,
        matched_skills=matched,
        missing_skills=missing,
        job_skills_found=job_skills,
        explanation=explanation,
    )
