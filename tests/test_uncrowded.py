from datetime import date

import pytest

from uncrowded.__main__ import build
from uncrowded.industries import industry_table
from uncrowded.rules import Job, blockers_of, employer_key, engagement_of, rank, role_of
from uncrowded.site import embed
from uncrowded.sources import parse_ashby, parse_greenhouse, parse_lever

TODAY = date(2026, 11, 27)


def job(**kw):
    base = dict(title="Senior Data Engineer", company="Example Corp", url="https://example.com/1", location="Remote, US")
    return Job(**{**base, **kw})


@pytest.mark.parametrize("title,role", [
    ("Senior Data Engineer", "Data Engineer"), ("Lead Agentic AI Engineer", "AI Engineer"),
    ("PL/SQL Developer", "SQL Developer"), ("Power BI Developer", "Power BI Developer"),
    ("Application Support Engineer", "Application Engineer"), ("Account Executive", None),
    ("Maintenance Engineer", None),
    ("Senior Manager, Software Engineering - AI Developer Productivity", None)])
def test_role_of(title, role):
    assert role_of(title) == role


@pytest.mark.parametrize("text,expected", [
    ("Job Type: C2C (Contract)", "c2c"), ("Corp-to-Corp welcome", "c2c"),
    ("Looking for W2 candidates. No C2C", "w2-only"), ("W2 ONLY  No C2C assistance", "w2-only"),
    ("12 month W2 contract", "w2-only"), ("We build data pipelines", "not-contract")])
def test_engagement(text, expected):
    assert engagement_of(job(description=text)) == expected


def test_refusal_wins_over_a_c2c_mention():
    assert engagement_of(job(description="C2C is not accepted")) == "w2-only"


def test_contract_comes_from_type_or_title_not_body_text():
    assert engagement_of(job(employment="Contract, Third Party")) == "contract-unstated"
    assert engagement_of(job(description="You will review each vendor contract")) == "not-contract"


def test_blockers():
    assert "clearance required" in blockers_of(job(description="Active Secret clearance needed"))
    assert "citizens or green card only" in blockers_of(job(description="US Citizens only"))
    assert "no sponsorship" in blockers_of(job(description="We are unable to provide visa sponsorship"))
    assert blockers_of(job(description="Work authorization: H-1B welcome")) == []


def test_remote_c2c_ranks_first_and_blocked_sinks():
    rows = build([
        job(url="https://e.com/a", employment="Full-time"),
        job(url="https://e.com/b", description="C2C", posted="2026-11-20"),
        job(url="https://e.com/c", description="C2C. US citizens only"),
        job(url="https://e.com/d", employment="Contract"),
        job(url="javascript:alert(1)"), job(url="https://e.com/b")], {"employer_transfers": {}}, TODAY)
    assert [r["url"][-1] for r in rows] == ["b", "d", "a", "c"]
    assert "description" not in rows[0]


def test_non_us_and_off_target_dropped():
    assert rank(job(location="Bengaluru, India"), {}, TODAY) is None
    assert rank(job(title="Recruiter"), {}, TODAY) is None


def test_score_has_reasons():
    plain = rank(job(), {}, TODAY)
    boosted = rank(job(company="Example, Inc.", posted="2026-11-26"), {employer_key("Example Corp"): 30}, TODAY)
    assert boosted.score > plain.score and len(boosted.reasons) == 2


def test_industry_table_sorted_and_sane():
    rows = industry_table()
    assert len(rows) == 18
    assert [r["openings_per_hire"] for r in rows] == sorted((r["openings_per_hire"] for r in rows), reverse=True)


def test_embedded_json_cannot_close_the_script_tag():
    assert "</script>" not in embed({"title": "</script><img src=x onerror=alert(1)>"})


def test_parsers():
    gh = parse_greenhouse({"jobs": [{"title": "T", "absolute_url": "https://x", "location": {"name": "Remote"},
                                     "content": "&lt;p&gt;Hi&lt;/p&gt;", "first_published": "2026-11-01T00:00:00Z"}]}, "X")
    assert (gh[0].description, gh[0].posted) == ("Hi", "2026-11-01")
    lv = parse_lever([{"text": "T", "hostedUrl": "https://x", "categories": {"location": "Denver"},
                       "workplaceType": "remote", "country": "US", "createdAt": 1795737600000}], "X")
    assert lv[0].location.startswith("Remote")
    ab = parse_ashby({"jobs": [{"title": "T", "jobUrl": "https://x", "location": "NYC", "isRemote": True,
                                "workplaceType": "Hybrid"}]}, "X")
    assert "Remote" not in ab[0].location
