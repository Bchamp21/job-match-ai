"""uvicorn uncrowded.api:app --reload

Local, single-user API. It has no authentication, so do not deploy it publicly as it stands.
Approval is deliberately not an endpoint: anything that can call the API could then approve.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .__main__ import DATA
from .guardrails import ApprovalGate
from .agent import Agent
from .industries import industry_table
from .rag import index_documents, retrieve


class JobIn(BaseModel):
    url: str = Field(pattern=r"^https?://", max_length=2000)
    title: str = Field(min_length=2, max_length=300)
    description: str = Field(default="", max_length=50_000)


class Corpus(BaseModel):
    jobs: list[JobIn] = Field(min_length=1, max_length=500)


class SearchRequest(Corpus):
    question: str = Field(min_length=3, max_length=500)


def create_app() -> FastAPI:
    app = FastAPI(title="Uncrowded", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "h1b_data": (DATA / "h1b_summary.json").exists()}

    @app.get("/industries")
    def industries(limit: int = Query(5, ge=1, le=50), offset: int = Query(0, ge=0)) -> dict:
        rows = industry_table()
        return {"total": len(rows), "items": rows[offset:offset + limit]}

    @app.post("/search")
    def search(request: SearchRequest) -> dict:
        store = index_documents({j.url: f"{j.title}. {j.description}" for j in request.jobs})
        return {"passages": retrieve(store, request.question)}

    @app.post("/shortlist")
    def make_shortlist(request: Corpus) -> dict:
        from datetime import date

        from .rules import Job, rank

        ranked = []
        for item in request.jobs:
            result = rank(Job(item.title, "unknown", item.url, "", item.description), {}, date.today())
            if result:
                ranked.append({"url": item.url, "title": item.title, "description": item.description,
                               "tier": result.tier, "score": result.score, "engagement": result.engagement,
                               "blockers": result.blockers})
        if not ranked:
            raise HTTPException(422, "no job matched a target role")
        state = Agent(ApprovalGate()).start(ranked)
        return {"status": state["status"],
                "shortlist": [{k: j[k] for k in ("url", "title", "tier", "score")} for j in state["shortlist"]],
                "rejected": [{"url": j["url"], "why": j["why"]} for j in state["rejected"]]}

    return app


app = create_app()
