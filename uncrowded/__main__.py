"""python -m uncrowded            collect, rank, and write docs/index.html
python -m uncrowded --import my_listings.csv --no-fetch --out private/index.html"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .industries import industry_table
from .rules import TIERS, Ranked, rank
from .site import render
from .sources import fetch_all, read_csv

DATA = Path(__file__).parent / "data"


def to_row(r: Ranked) -> dict:
    job = asdict(r.job)
    job.pop("description")  # keep the page small and avoid republishing posting text
    return {**job, "role": r.role, "engagement": r.engagement, "remote": r.remote, "tier": r.tier,
            "score": r.score, "reasons": r.reasons, "blockers": r.blockers}


def build(jobs: list, h1b: dict, today: date) -> list[dict]:
    seen, rows = set(), []
    for job in jobs:
        if job.url in seen or not job.url.startswith(("https://", "http://")):
            continue
        seen.add(job.url)
        ranked = rank(job, h1b["employer_transfers"], today)
        if ranked:
            rows.append(to_row(ranked))
    return sorted(rows, key=lambda r: (bool(r["blockers"]) or r["engagement"] == "w2-only", r["tier"], -r["score"], r["company"], r["title"]))


def main() -> None:
    parser = argparse.ArgumentParser(prog="uncrowded")
    parser.add_argument("--import", dest="imports", action="append", default=[], help="CSV of your own listings")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--out", default="docs/index.html")
    args = parser.parse_args()
    boards = json.loads((DATA / "boards.json").read_text())
    h1b = json.loads((DATA / "h1b_summary.json").read_text())
    jobs, errors = ([], []) if args.no_fetch else fetch_all(boards)
    for path in args.imports:
        jobs += read_csv(Path(path))
    today = date.today()
    rows = build(jobs, h1b, today)
    if not args.no_fetch and not jobs:
        raise SystemExit(f"No board returned data, keeping the old page. Errors: {errors}")
    render({"generated": today.isoformat(), "scanned": len(jobs), "boards": 0 if args.no_fetch else len(boards) - len(errors),
            "errors": errors, "tiers": TIERS, "jobs": rows, "industries": industry_table(),
            "h1b": {k: h1b[k] for k in ("source", "decision_window", "certified_h1b_lcas", "roles", "sectors")}},
           Path(args.out))
    print(f"scanned {len(jobs)} postings, {len(rows)} in target roles, {len(errors)} board errors -> {args.out}")
    for tier, label in TIERS.items():
        print(f"  tier {tier} {label}: {sum(r['tier'] == tier for r in rows)}")


if __name__ == "__main__":
    main()
