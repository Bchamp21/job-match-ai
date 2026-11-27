"""The apply-queue agent as a hand-written state machine: screen -> shortlist -> await approval -> done.

The nodes are plain functions so the LangGraph version can reuse them unchanged.
The agent has no tool that submits anything. Approval marks an item ready for a person to send.
"""
from __future__ import annotations

from typing import TypedDict

from .guardrails import ApprovalGate, scan_injection


class State(TypedDict, total=False):
    candidates: list[dict]
    shortlist: list[dict]
    rejected: list[dict]
    approved: list[str]
    status: str


def screen(state: State) -> State:
    kept, rejected = [], []
    for job in state["candidates"]:
        reasons = list(job.get("blockers", []))
        if job.get("engagement") == "w2-only":
            reasons.append("W2 only")
        reasons += [f"suspicious text: {f}" for f in scan_injection(job.get("description", ""))]
        (rejected if reasons else kept).append({**job, "why": reasons})
    return {"candidates": kept, "rejected": rejected}


def shortlist(state: State, limit: int = 10) -> State:
    ordered = sorted(state["candidates"], key=lambda j: (j.get("tier", 5), -j.get("score", 0)))
    picks = ordered[:limit]
    return {"shortlist": picks, "status": "awaiting_approval" if picks else "done"}


def apply_decision(state: State, approved_urls: list[str]) -> State:
    offered = {j["url"] for j in state["shortlist"]}
    return {"approved": [u for u in approved_urls if u in offered], "status": "done"}


class Agent:
    def __init__(self, gate: ApprovalGate) -> None:
        self.gate = gate

    def start(self, candidates: list[dict]) -> State:
        state: State = {"candidates": candidates, "approved": []}
        for node in (screen, shortlist):
            state.update(node(state))
        return state

    @staticmethod
    def payload(state: State, urls: list[str]) -> str:
        return "\n".join(sorted(urls)) + "\0" + "\n".join(j["url"] for j in state["shortlist"])

    def resume(self, state: State, urls: list[str], token: str) -> State:
        if state.get("status") != "awaiting_approval":
            raise ValueError("nothing is waiting for approval")
        if not self.gate.consume(token, "approve", self.payload(state, urls)):
            raise PermissionError("approval token does not match this selection")
        state.update(apply_decision(state, urls))
        return state
