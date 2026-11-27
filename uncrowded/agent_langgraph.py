"""The same agent in LangGraph. Compare with agent.py: the graph replaces the loop, a checkpointer
replaces the state you passed around by hand, and interrupt() replaces the approval pause."""
from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .agent import State, apply_decision, screen, shortlist


def approval(state: State) -> State:
    # The node restarts from the top on resume, so keep side effects after interrupt().
    urls = interrupt({"shortlist": [j["url"] for j in state["shortlist"]]})
    return apply_decision(state, urls)


def build_graph(checkpointer=None):
    graph = StateGraph(State)
    graph.add_node("screen", screen)
    graph.add_node("shortlist", shortlist)
    graph.add_node("approval", approval)
    graph.add_edge(START, "screen")
    graph.add_edge("screen", "shortlist")
    graph.add_conditional_edges("shortlist", lambda s: "approval" if s["shortlist"] else END, ["approval", END])
    graph.add_edge("approval", END)
    return graph.compile(checkpointer=checkpointer or InMemorySaver())
