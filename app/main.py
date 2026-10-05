from fastapi import FastAPI

from app.models import MatchRequest, MatchResult
from app.scorer import score_resume

app = FastAPI(
    title="Job-Match AI",
    description="Score a resume against a job description by skill overlap.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/match", response_model=MatchResult)
def match(req: MatchRequest) -> MatchResult:
    return score_resume(req.resume, req.job)
