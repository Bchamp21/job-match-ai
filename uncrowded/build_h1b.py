"""Aggregate DOL OFLC LCA disclosure files into a small JSON. Needs: pip install python-calamine

A certified LCA is an employer's wage filing. It is not an approved petition, a hire or an open job.
Only employer names and aggregates are kept; contact names, emails and phones are never read out.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
from pathlib import Path

from python_calamine import CalamineWorkbook

from .rules import ROLES, employer_key

YEARLY = {"Year": 1, "Hour": 2080, "Month": 12, "Bi-Weekly": 26, "Week": 52}
SECTORS = {"11": "Agriculture", "21": "Mining and oil", "22": "Utilities", "23": "Construction",
           "31": "Manufacturing", "32": "Manufacturing", "33": "Manufacturing", "42": "Wholesale trade",
           "44": "Retail trade", "45": "Retail trade", "48": "Transportation and warehousing",
           "49": "Transportation and warehousing", "51": "Information", "52": "Finance and insurance",
           "53": "Real estate", "54": "Professional and technical services", "55": "Company management",
           "56": "Administrative and support", "61": "Education", "62": "Health care",
           "71": "Arts and recreation", "72": "Accommodation and food", "81": "Other services",
           "92": "Government"}
KEEP = ("CASE_NUMBER", "CASE_STATUS", "VISA_CLASS", "DECISION_DATE", "JOB_TITLE", "EMPLOYER_NAME", "NAICS_CODE",
        "CHANGE_EMPLOYER", "WAGE_RATE_OF_PAY_FROM", "WAGE_UNIT_OF_PAY", "SECONDARY_ENTITY")


def load(paths: list[str]) -> list[dict]:
    cases: dict[str, dict] = {}
    for path in paths:
        rows = CalamineWorkbook.from_path(path).get_sheet_by_index(0).to_python()
        col = {name: i for i, name in enumerate(rows[0])}
        for row in rows[1:]:
            if row[col["VISA_CLASS"]] == "H-1B" and row[col["CASE_STATUS"]] == "Certified":
                cases[row[col["CASE_NUMBER"]]] = {k: row[col[k]] for k in KEEP}
    return list(cases.values())


def wage(case: dict) -> float | None:
    unit, raw = case["WAGE_UNIT_OF_PAY"], case["WAGE_RATE_OF_PAY_FROM"]
    if unit not in YEARLY or raw in ("", None):
        return None
    value = float(raw) * YEARLY[unit]
    return value if 20_000 <= value <= 1_500_000 else None  # drop unit-entry errors


def summarize(cases: list[dict]) -> dict:
    transfer = [c for c in cases if float(c["CHANGE_EMPLOYER"] or 0) > 0]
    wages = [w for c in cases if (w := wage(c))]
    names = collections.Counter(c["EMPLOYER_NAME"].strip() for c in transfer)
    return {"filings": len(cases), "transfer_filings": len(transfer),
            "employers": len({employer_key(c["EMPLOYER_NAME"]) for c in cases}),
            "third_party_site": sum(c["SECONDARY_ENTITY"] == "Yes" for c in cases),
            "median_wage": round(statistics.median(wages)) if wages else None,
            "top_transfer_employers": names.most_common(10)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--out", default=str(Path(__file__).parent / "data" / "h1b_summary.json"))
    args = parser.parse_args()
    cases = load(args.files)
    dates = [c["DECISION_DATE"] for c in cases if c["DECISION_DATE"]]
    sectors: dict[str, list] = collections.defaultdict(list)
    transfers: collections.Counter = collections.Counter()
    for c in cases:
        sectors[SECTORS.get(str(c["NAICS_CODE"])[:2], "Unclassified")].append(c)
        if float(c["CHANGE_EMPLOYER"] or 0) > 0:
            transfers[employer_key(c["EMPLOYER_NAME"])] += 1
    out = {
        "source": "https://www.dol.gov/agencies/eta/foreign-labor/performance",
        "files": [Path(f).name for f in args.files],
        "decision_window": [str(min(dates)), str(max(dates))],
        "certified_h1b_lcas": len(cases),
        "roles": {r: summarize([c for c in cases if re.search(p, c["JOB_TITLE"], re.I)]) for r, p in ROLES.items()},
        "sectors": {k: summarize(v) for k, v in sectors.items()},
        "employer_transfers": {k: n for k, n in transfers.items() if k and n >= 3},
    }
    Path(args.out).write_text(json.dumps(out, separators=(",", ":")))
    print(f"{len(cases)} certified H-1B filings -> {args.out}")


if __name__ == "__main__":
    main()
