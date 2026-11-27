"""Deterministic classification and ranking. No model calls, so every score can be explained."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

ROLES: dict[str, str] = {
    "Data Engineer": r"\bdata\s+(platform\s+|warehouse\s+)?engineer|databricks\s+(engineer|developer)|\betl\s+(engineer|developer)",
    "AI Engineer": r"\b(ai|gen\s?ai|generative ai|agentic|llm)\b.{0,40}\b(engineer|developer)\b",
    "SQL Developer": r"\b(pl/)?sql\b.{0,30}\b(developer|engineer)\b",
    "Power BI Developer": r"power\s*bi",
    "Application Engineer": r"\bapplications?\s+(support\s+|software\s+)?engineer",
}

NO_C2C = re.compile(
    r"\bno\s+(c2c|corp[\s-]*(to|2)[\s-]*corp)\b|\bw-?2\s+only\b|\bonly\s+(on\s+)?w-?2\b"
    r"|looking for w-?2 candidates|\bc2c\s+(is\s+)?not\s+(accepted|allowed|available)"
    r"|\bw-?2\s+contract\b|visa:\s*any\s*-\s*w-?2", re.I)
C2C = re.compile(r"\bc2c\b|corp[\s-]*(to|2)[\s-]*corp", re.I)
CONTRACT = re.compile(r"\bcontract(or)?\b(?!\s+(management|law|negotiation))", re.I)
BLOCKERS = {
    "clearance required": r"\b(secret|top secret|ts/sci|security)\s+clearance\b|public trust",
    "citizens or green card only": r"\b(us|u\.s\.)\s+citizens?(hip)?\s+(only|required)|\brequired\s*:\s*usc\b|\bgc\s*/\s*usc?\s+only|\busc?\s*(/|and|or)\s*gc\s+only",
    "no sponsorship": r"\b(no|not\s+able\s+to|unable\s+to|will\s+not|cannot)\s+(provide\s+|offer\s+)?(visa\s+)?sponsor",
}
NON_US = re.compile(r"\b(india|canada|united kingdom|uk|london|ireland|dublin|germany|berlin|poland|"
                    r"mexico|brazil|singapore|japan|australia|france|paris|spain|netherlands|israel|emea|apac|"
                    r"toronto|bangalore|bengaluru|hyderabad|costa rica|argentina|colombia|romania|sweden)\b", re.I)


@dataclass
class Job:
    title: str
    company: str
    url: str
    location: str = ""
    description: str = ""
    posted: str = ""          # ISO date, empty when unknown
    employment: str = ""
    source: str = ""
    easy_apply: bool | None = None


@dataclass
class Ranked:
    job: Job
    role: str
    engagement: str
    remote: bool
    tier: int
    score: int
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


NOT_ENGINEERING = r"\b(manager|director|head of|vp|recruiter|sales|account executive|intern|internship)\b"


def role_of(title: str) -> str | None:
    if re.search(NOT_ENGINEERING, title, re.I):
        return None
    for name, pattern in ROLES.items():
        if re.search(pattern, title, re.I):
            return name
    return None


def engagement_of(job: Job) -> str:
    """C2C stated, C2C refused, contract with C2C unstated, or not a contract."""
    text = f"{job.title}\n{job.employment}\n{job.description}"
    if NO_C2C.search(text):
        return "w2-only"
    if C2C.search(text):
        return "c2c"
    # A full description often mentions "contract" in passing, so trust title and type only.
    if CONTRACT.search(f"{job.title} {job.employment}") or "third party" in job.employment.lower():
        return "contract-unstated"
    return "not-contract"


def blockers_of(job: Job) -> list[str]:
    text = f"{job.title}\n{job.description}"
    return [name for name, pattern in BLOCKERS.items() if re.search(pattern, text, re.I)]


def is_remote(job: Job) -> bool:
    return bool(re.search(r"\bremote\b", f"{job.location} {job.title}", re.I))


def is_foreign(job: Job) -> bool:
    return bool(NON_US.search(job.location)) and not re.search(r"\b(us|usa|united states)\b", job.location, re.I)


TIERS = {1: "Remote C2C", 2: "Remote contract, ask about C2C", 3: "C2C or contract, not remote",
         4: "Remote, not C2C", 5: "Other"}


def tier_of(engagement: str, remote: bool) -> int:
    if remote and engagement == "c2c":
        return 1
    if remote and engagement == "contract-unstated":
        return 2
    if engagement in ("c2c", "contract-unstated"):
        return 3
    return 4 if remote else 5


def rank(job: Job, employers: dict[str, int], today: date) -> Ranked | None:
    """Return None for jobs outside the target roles or clearly outside the US."""
    role = role_of(job.title)
    if role is None or is_foreign(job):
        return None
    engagement, remote = engagement_of(job), is_remote(job)
    score, reasons = 50, []
    if job.posted:
        age = (today - date.fromisoformat(job.posted[:10])).days
        if age <= 2:
            score += 20
            reasons.append(f"posted {age}d ago: early applicant window (+20)")
        elif age <= 7:
            score += 10
            reasons.append(f"posted {age}d ago (+10)")
        elif age > 45:
            score -= 10
            reasons.append(f"open {age}d: may be stale or evergreen (-10)")
    if job.easy_apply is True:
        score -= 10
        reasons.append("one-click apply usually draws more applicants (-10)")
    elif job.easy_apply is False:
        score += 5
        reasons.append("longer apply flow (+5)")
    transfers = employers.get(employer_key(job.company), 0)
    if transfers:
        bonus = min(20, 5 + transfers // 5)
        score += bonus
        reasons.append(f"{transfers} certified change-of-employer H-1B filings in the data window (+{bonus})")
    return Ranked(job, role, engagement, remote, tier_of(engagement, remote), score, reasons, blockers_of(job))


def employer_key(name: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    s = re.sub(r"\b(inc|llc|llp|ltd|corp|corporation|co|company|incorporated|the|usa|us|pbc|technologies)\b", " ", s)
    return " ".join(s.split())
