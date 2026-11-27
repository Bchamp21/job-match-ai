"""Render the static showcase page. Job text is untrusted, so the page builds DOM nodes with textContent."""
from __future__ import annotations

import json
from pathlib import Path

TEMPLATE = Path(__file__).parent / "page.html"


def embed(data: dict) -> str:
    return json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")


def render(data: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", embed(data)), encoding="utf-8")
