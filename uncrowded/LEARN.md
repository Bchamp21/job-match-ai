# Learn by rebuilding Uncrowded

Each lesson has the same shape: what we built, why, rebuild it, break it, answer it out loud.
To learn from scratch, create a branch, empty the module, and rewrite it until its tests pass.
Run tests with `pytest -q`.

## What job descriptions ask for, and where you learn it
Share of 21 job descriptions read on 2026-11-27 (a small hand sample of AI, agent and FDE roles, plus a few others).

| Skill | Share | Here | Honest status |
|---|---|---|---|
| AI agents | 95% | 6, 7 | State and approval flow. No model chooses tools yet |
| Python | 86% | 0 | Drills |
| Evaluation | 81% | 2, 4 | Retrieval metrics only, tiny test set |
| Guardrails, AI security | 76% | 5 | Basic layers |
| API design | 76% | 8 | Local API, no auth |
| Cloud | 76% | none | Next build: deploy it |
| Observability | 71% | none | Next build: tracing and structured logs |
| RAG | 67% | 4 | Retrieval works. Needs a real model for generation |
| Agent framework | 62% | 7 | LangGraph |
| Prompt and context engineering | 57% | 4 | One prompt only. Next build |
| Vector DB and search | 57% | 3 | Built by hand. Next: pgvector |
| LangGraph | 52% | 7 | Covered |
| MCP | 48% | none | Next build: an MCP server over `/search` |
| Cost, latency, model routing | 48% | none | After a model is added |
| CI/CD | 38% | 9 | Tests and a scheduled job |
| Data pipelines | 38% | 1 | Covered at small scale |
| FastAPI | 29% | 8 | Covered |

Also not covered: AWS and Azure specifics, Docker and Kubernetes for this module, TypeScript, SQL practice.
A skill counts as proven when you rebuild it, pass its tests and explain it without notes.

## How to run each study session (45-60 minutes)
1. Pick the lesson. Read its "Built" and "Why" lines.
2. Predict how the code works, then read it.
3. Delete one function, rewrite it, run its test.
4. Do "Break it" and add a test for what you found.
5. Answer "Say aloud" in under two minutes. Record the miss, and start there next time.

## Lessons

| # | Lesson | Files | Job-description skill |
|---|---|---|---|
| 0 | Python data structures | `practice/` | Python |
| 1 | Data engineering: collect and aggregate | `sources.py`, `build_h1b.py` | Data pipelines, SQL-style thinking |
| 2 | Rules before models | `rules.py` | Evaluation, explainability |
| 3 | Vector store | `vectors.py` | Vector search |
| 4 | RAG and retrieval evals | `rag.py` | RAG, evals |
| 5 | Guardrails | `guardrails.py` | AI security |
| 6 | Agents by hand | `agent.py` | Agentic AI |
| 7 | LangGraph | `agent_langgraph.py` | LangGraph |
| 8 | API design | `api.py` | APIs, FastAPI |
| 9 | CI, publishing, operations | `.github/workflows/` | CI/CD, observability |

## 0. Python data structures
**Built:** seven drills in `practice/ds_exercises.py`, each from a real need in this app.
**Why:** a `set` removes duplicate postings, a heap finds the top results without sorting everything,
and an inverted index (a dict of sets or lists) is the core of the vector store.

| Structure | Use it when | Typical cost |
|---|---|---|
| `list` | ordered items, append at the end | index O(1), search O(n) |
| `dict` / `set` | lookup, counting, de-duplication | O(1) on average |
| `collections.deque` | add and remove at both ends | O(1) at the ends |
| `heapq` | best k of many | push or pop O(log n) |
| graph as `dict[str, list[str]]` | dependencies, workflows | traversal O(nodes + edges) |

**Do:** `pytest uncrowded/practice/check_ds.py -q`. All checks fail until you write the code.
**Say aloud:** why is `x in my_set` faster than `x in my_list`? When does a heap beat sorting?

## 1. Data engineering
**Built:** three collectors that turn different job board formats into one `Job` record, and a batch
job that reduces visa filings to a small JSON file.
**Why:** one schema keeps source differences at the edge. De-duplicating by case number makes the
batch safe if files overlap. Aggregating early keeps contact details out of the public repo.
A failed board is recorded and skipped; a run where every board fails keeps the old page.
**Break it:** point one board at a wrong slug and read the error list.
**Say aloud:** what makes this pipeline safe to re-run? What would you partition by at 100x the size?

## 2. Rules before models
**Built:** role, work type, blockers, tier and score, all with plain patterns.
**Why:** these decisions must be repeatable and explainable. Every score lists its reasons.
A refusal ("No C2C") is checked before a mention ("C2C"), because the reverse order is a bug.
**Know the limit:** the score weights are judgment calls. Nothing has shown they predict interviews.
Log outcomes, then compare reply rates by score band before trusting them.
**Break it:** write a posting the patterns get wrong, add it as a test, then fix the pattern.
**Say aloud:** when would you replace a rule with a model, and how would you prove it is better?

## 3. Vector store
**Built:** TF-IDF vectors, cosine similarity, an inverted index and heap-based top k.
**Why:** a vector database does these jobs: embed, index, find nearest. At this size a library adds
little, and writing it shows what Chroma, pgvector or FAISS do for you (plus persistence, filtering,
approximate search and scale).
**Limit:** TF-IDF matches words, not meaning.
**Do next:** write a neural embedder that satisfies `Embedder`, and adapt `VectorStore` for dense vectors.
**Say aloud:** why normalize vectors? What does approximate nearest neighbor search give up?

## 4. RAG and evals
**Built:** chunk, retrieve, refuse when nothing scores well, optionally generate, check citations,
and measure recall@k and mean reciprocal rank.
**Why:** when an answer is wrong you need to know which stage failed. Retrieval metrics separate
"never found it" from "found it and answered badly". The citation check rejects invented ids; it
does not prove the cited passage supports the claim.
**Limit:** the golden set in the tests is four made-up cases. It checks the wiring, not quality.
**Do next:** label 30 real questions against postings you saved, then compare chunk sizes.
**Say aloud:** recall@3 drops after a chunking change. What do you check first?

## 5. Guardrails
**Built:** injection screening, PII redaction, delimiting of untrusted text, citation checks and a
one-time approval token tied to the exact selection.
**Why:** job postings are untrusted input. Pattern filters are easy to evade, so the design does not
rely on them. The agent has no tool that submits anything, and the API has no approval route.
Redaction is available for logs and prompts; it covers three simple patterns only.
**Break it:** write an injection that slips past `scan_injection`. Explain why it still cannot approve.
**Say aloud:** what is the difference between a filter and a permission boundary?

## 6. Agents by hand
**Built:** state, nodes, one pause for a human, resume.
**Why:** an agent is state plus steps plus stop conditions. Here no model is needed, and that is a
valid design choice. Add a model only to a step that rules cannot do, such as drafting a summary.
**Say aloud:** what state must survive a restart? What makes resume safe to call twice?

## 7. LangGraph
**Built:** the same nodes as a graph with a checkpointer and `interrupt()`.
**Why:** many job descriptions name it. Reusing the nodes shows what the framework adds.
**Remember:** the interrupted node runs again from its start on resume, so a side effect before
`interrupt()` happens twice. `InMemorySaver` loses state on restart; use a database saver for real use.
`Command(resume=...)` is not authentication: protect whoever can call it.
**Say aloud:** hand-written or LangGraph for this app? Defend one with two concrete reasons.

## 8. API design
**Built:** typed requests, size limits, pagination, clear status codes.
**Why:** limits at the edge stop bad input before it costs memory or money. 422 means the request
was understood but cannot be processed.
**Do next:** add API key auth and rate limiting before any deployment.
**Say aloud:** why is there no `POST /approve`?

## 9. CI and publishing
**Built:** tests on each pull request and a daily workflow that rebuilds the page.
**Why:** the build fails when a change breaks a rule. The page shows its build date and board errors,
so stale data is visible.
**Say aloud:** how would you notice a board that silently starts returning zero jobs?

## Two-week order
Days 1-3: lesson 0. Days 4-5: lessons 1-2. Days 6-8: lessons 3-4. Day 9: lesson 5.
Days 10-12: lessons 6-7. Day 13: lesson 8. Day 14: lesson 9 and a five-minute demo, recorded.
