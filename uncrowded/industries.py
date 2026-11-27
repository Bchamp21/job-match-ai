"""Industry demand from the BLS JOLTS snapshot."""
import json
from pathlib import Path

SNAPSHOT = Path(__file__).parent / "data" / "jolts_2026_09.json"


def industry_table(path: Path = SNAPSHOT) -> list[dict]:
    """openings_per_hire = openings rate / hires rate. Higher means openings are high relative to
    the pace of hiring. It is a proxy for hard-to-fill work, not a count of applicants.
    JOLTS divides the two rates by slightly different bases, so treat the ratio as approximate."""
    data = json.loads(path.read_text())
    rows = [
        {"industry": name, "openings_rate": o, "hires_rate": h, "openings_per_hire": round(o / h, 2)}
        for name, (o, h) in data["industries"].items()
    ]
    return sorted(rows, key=lambda r: (-r["openings_per_hire"], -r["openings_rate"]))
