from fastapi import FastAPI

from app.llm_scorer import enrich_with_llm, llm_available
from app.models import MatchRequest, MatchResult
from app.scorer import score_resume

app = FastAPI(
    title="Job-Match AI",
    description="Score a resume against a job description by skill overlap (+ optional LLM).",
    version="0.2.0",
)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "llm_available": llm_available()}


@app.post("/match", response_model=MatchResult)
def match(req: MatchRequest) -> MatchResult:
    base = score_resume(req.resume, req.job)
    if not req.use_llm:
        return base.model_copy(update={"scoring_mode": "keywords"})
    enriched = enrich_with_llm(req.resume, req.job, base)
    mode = "keywords"
    if llm_available() and req.use_llm:
        mode = (
            "keywords+llm"
            if (
                enriched.match_percent != base.match_percent
                or enriched.explanation != base.explanation
            )
            else "keywords"
        )
    return enriched.model_copy(update={"scoring_mode": mode})
