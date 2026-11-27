"""Data structures drills taken from this project. Replace each NotImplementedError, then run:
    pytest uncrowded/practice/check_ds.py -q
Standard library only. Say the time complexity out loud before you run the check.
"""


def dedupe_by_url(jobs: list[dict]) -> list[dict]:
    """set: keep the first job for each url, in the original order. Target O(n)."""
    raise NotImplementedError


def count_by_role(jobs: list[dict]) -> list[tuple[str, int]]:
    """dict: (role, count) pairs, highest count first, ties by role name. O(n + r log r)."""
    raise NotImplementedError


def top_k(jobs: list[dict], k: int) -> list[str]:
    """heap: urls of the k highest 'score' values, best first. O(n log k), so no full sort."""
    raise NotImplementedError


def build_inverted_index(docs: dict[str, str]) -> dict[str, set[str]]:
    """dict of sets: lowercase word -> ids of documents containing it."""
    raise NotImplementedError


def search_all(index: dict[str, set[str]], words: list[str]) -> set[str]:
    """set intersection: ids containing every word. No words means an empty set."""
    raise NotImplementedError


def seen_recently(urls: list[str], window: int) -> list[bool]:
    """deque + dict: True where the url appeared in the previous `window` items. O(n)."""
    raise NotImplementedError


def build_order(deps: dict[str, list[str]]) -> list[str]:
    """graph: each node after everything it depends on. Raise ValueError on a cycle.
    This is how an agent graph decides what can run next."""
    raise NotImplementedError
