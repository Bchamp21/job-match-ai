from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    resume: str = Field(..., min_length=1, description="Plain-text resume")
    job: str = Field(..., min_length=1, description="Plain-text job description")
    use_llm: bool = Field(
        default=True,
        description="If true and an API key is set, blend LLM scoring with keywords",
    )


class MatchResult(BaseModel):
    match_percent: float = Field(..., ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    job_skills_found: list[str]
    explanation: str
    scoring_mode: str = Field(default="keywords", description="keywords | keywords+llm")
