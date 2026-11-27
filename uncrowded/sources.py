"""Collectors for public, no-login job board APIs, plus a CSV import for listings you gather yourself."""
from __future__ import annotations

import csv
import html
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .rules import Job

URLS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{}",
}


def plain(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()


def parse_greenhouse(data: dict, company: str) -> list[Job]:
    return [Job(j["title"], company, j["absolute_url"], (j.get("location") or {}).get("name", ""),
                plain(j.get("content", "")), (j.get("first_published") or "")[:10], source="greenhouse")
            for j in data.get("jobs", [])]


def parse_lever(data: list, company: str) -> list[Job]:
    jobs = []
    for j in data:
        cats = j.get("categories") or {}
        location = cats.get("location", "")
        if (j.get("workplaceType") or "").lower() == "remote":
            location = f"Remote - {location}"
        if j.get("country") not in (None, "", "US") and location:
            location = f"{location} ({j['country']})"
            if "remote" in location.lower():
                continue
        posted = ""
        if j.get("createdAt"):
            posted = datetime.fromtimestamp(j["createdAt"] / 1000, tz=timezone.utc).date().isoformat()
        body = " ".join(plain(j.get(k, "")) for k in ("descriptionPlain", "additionalPlain"))
        jobs.append(Job(j["text"], company, j["hostedUrl"], location, body, posted,
                        cats.get("commitment", ""), "lever"))
    return jobs


def parse_ashby(data: dict, company: str) -> list[Job]:
    jobs = []
    for j in data.get("jobs", []):
        if not j.get("isListed", True):
            continue
        location = j.get("location", "")
        # Ashby's isRemote can be true for hybrid roles, so rely on workplaceType.
        if (j.get("workplaceType") or "").lower() == "remote":
            location = f"Remote - {location}"
        country = (((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry") or "")
        if country and country.lower() not in ("us", "usa", "united states"):
            location = f"{location} ({country})"
        jobs.append(Job(j["title"], company, j["jobUrl"], location, plain(j.get("descriptionPlain", "")),
                        (j.get("publishedAt") or "")[:10], j.get("employmentType", ""), "ashby"))
    return jobs


PARSERS = {"greenhouse": parse_greenhouse, "lever": parse_lever, "ashby": parse_ashby}


def fetch_board(board: dict) -> tuple[list[Job], str | None]:
    url = URLS[board["ats"]].format(board["slug"])
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "uncrowded-jobs"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
        return PARSERS[board["ats"]](data, board["company"]), None
    except Exception as exc:  # one broken board must not stop the run
        return [], f"{board['company']}: {type(exc).__name__}"


def fetch_all(boards: list[dict]) -> tuple[list[Job], list[str]]:
    jobs, errors = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for found, error in pool.map(fetch_board, boards):
            jobs.extend(found)
            if error:
                errors.append(error)
    return jobs, errors


def read_csv(path: Path) -> list[Job]:
    """Columns: title, company, url, then optional location, description, posted, employment, easy_apply."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return [Job(row["title"], row["company"], row["url"], row.get("location") or "",
                    row.get("description") or "", row.get("posted") or "", row.get("employment") or "", "import",
                    {"true": True, "false": False}.get((row.get("easy_apply") or "").strip().lower()))
                for row in csv.DictReader(handle)]
