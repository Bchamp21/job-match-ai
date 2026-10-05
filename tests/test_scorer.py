from app.scorer import score_resume


def test_perfect_match():
    resume = "Expert in Python, SQL, FastAPI, Docker, and RAG systems."
    job = "Need Python, SQL, FastAPI, Docker, RAG."
    result = score_resume(resume, job)
    assert result.match_percent == 100.0
    assert result.missing_skills == []
    assert set(result.matched_skills) == {"Python", "SQL", "FastAPI", "Docker", "RAG"}


def test_partial_match():
    resume = "Python and SQL engineer with Pandas."
    job = "Looking for Python, SQL, Spark, Databricks."
    result = score_resume(resume, job)
    assert result.match_percent == 50.0
    assert "Python" in result.matched_skills
    assert "SQL" in result.matched_skills
    assert "Spark" in result.missing_skills
    assert "Databricks" in result.missing_skills


def test_empty_resume_skills():
    resume = "I like hiking and coffee."
    job = "Must know Python and FastAPI."
    result = score_resume(resume, job)
    assert result.match_percent == 0.0
    assert result.matched_skills == []
    assert set(result.missing_skills) == {"Python", "FastAPI"}


def test_case_insensitive():
    resume = "python sql fastapi"
    job = "PYTHON, Sql, FastAPI required"
    result = score_resume(resume, job)
    assert result.match_percent == 100.0


def test_no_job_skills():
    result = score_resume("Python expert", "Friendly team player needed")
    assert result.match_percent == 0.0
    assert result.job_skills_found == []
    assert "No known skills" in result.explanation
