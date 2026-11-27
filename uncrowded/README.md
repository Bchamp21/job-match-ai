# Uncrowded

A demand-first job finder: which industries are short of hires, which employers file H-1B transfers,
and which openings in five data and AI roles to look at first. Remote C2C ranks highest.

## Run
```bash
pip install -r requirements.txt
python -m uncrowded                       # collect and rebuild docs/index.html
python -m uncrowded --no-fetch --import my_listings.csv --out private/index.html
uvicorn uncrowded.api:app --reload        # local API, docs at /docs
pytest -q
pip install -r requirements-langgraph.txt # optional LangGraph version
```
Keep your own listings in `private/` (ignored by git). Import columns:
`title,company,url,location,description,posted,employment,easy_apply`.

## Data
| Data | Source | Refresh |
|---|---|---|
| Openings | Public Greenhouse, Lever and Ashby job board APIs for the companies in `data/boards.json` | Each run |
| H-1B wage filings | [DOL OFLC disclosure files](https://www.dol.gov/agencies/eta/foreign-labor/performance), decisions April to September 2026 | `pip install python-calamine && python -m uncrowded.build_h1b <files>` |
| Industry openings and hires | BLS JOLTS tables [1](https://www.bls.gov/news.release/jolts.t01.htm) and [2](https://www.bls.gov/news.release/jolts.t02.htm), September 2026 preliminary | Edit the snapshot by hand |

## What it cannot tell you
- No source here counts applicants. "Less competition" is a proxy, not a measurement.
- A certified wage filing is not a petition approval, a hire or an open job.
- Industry figures cover all occupations, not only tech roles.
- The board list is a hand-picked sample, not the whole market, and leans toward tech employers.
- Agency C2C listings rarely appear on company boards. Import them.
- Employer name matching is approximate. Score weights are untested judgment calls.
- Not legal or immigration advice.

It never applies to a job or sends a message.

Learn how it works in [LEARN.md](LEARN.md).
