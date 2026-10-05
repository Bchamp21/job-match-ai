from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

try:  # load .env locally; on Render, env vars come from the dashboard
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from app.llm_scorer import enrich_with_llm, llm_available
from app.models import MatchRequest, MatchResult
from app.scorer import score_resume

app = FastAPI(
    title="Job-Match AI",
    description="Score a resume against a job description by skill overlap (+ optional LLM).",
    version="0.2.0",
)


BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR.parent / "samples"


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/samples")
def samples() -> dict[str, str]:
    read = lambda n: (SAMPLES_DIR / n).read_text(encoding="utf-8") if (SAMPLES_DIR / n).exists() else ""
    return {"resume": read("resume.txt"), "job": read("job.txt")}


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "llm_available": llm_available()}


@app.post("/match", response_model=MatchResult)
def match(req: MatchRequest) -> MatchResult:
    base = score_resume(req.resume, req.job)
    if not req.use_llm:
        return base.model_copy(update={"scoring_mode": "keywords"})
    enriched = enrich_with_llm(req.resume, req.job, base)
    mode = "keywords+llm" if llm_available() and enriched is not base else "keywords"
    # enrich returns same object when skipped; still annotate mode
    if llm_available() and req.use_llm:
        # Detect whether LLM path likely ran by explanation growth or percent change
        mode = (
            "keywords+llm"
            if (
                enriched.match_percent != base.match_percent
                or enriched.explanation != base.explanation
            )
            else "keywords"
        )
    return enriched.model_copy(update={"scoring_mode": mode})
