from app.llm_scorer import enrich_with_llm, llm_available
from app.scorer import score_resume


def test_enrich_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert llm_available() is False
    base = score_resume("Python FastAPI", "Need Python FastAPI Docker")
    out = enrich_with_llm("Python FastAPI", "Need Python FastAPI Docker", base)
    assert out.match_percent == base.match_percent
    assert out.explanation == base.explanation


def test_llm_available_with_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert llm_available() is True
