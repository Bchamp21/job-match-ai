import pytest

from uncrowded.practice import ds_exercises as ex

J = [{"url": "a", "score": 3, "role": "AI"}, {"url": "b", "score": 9, "role": "Data"},
     {"url": "a", "score": 1, "role": "AI"}, {"url": "c", "score": 5, "role": "Data"}]


def test_dedupe():
    assert [j["score"] for j in ex.dedupe_by_url(J)] == [3, 9, 5]


def test_count():
    assert ex.count_by_role(J) == [("AI", 2), ("Data", 2)]


def test_top_k():
    assert ex.top_k(J, 2) == ["b", "c"] and ex.top_k(J, 0) == []


def test_index_and_search():
    index = ex.build_inverted_index({"1": "Spark and SQL", "2": "sql server"})
    assert index["sql"] == {"1", "2"}
    assert ex.search_all(index, ["sql", "spark"]) == {"1"} and ex.search_all(index, []) == set()
    assert ex.search_all(index, ["nothing"]) == set()


def test_window():
    assert ex.seen_recently(["a", "b", "a", "c", "d", "a"], 2) == [False, False, True, False, False, False]
    assert ex.seen_recently(["a", "a", "b", "a"], 2) == [False, True, False, True]


def test_build_order():
    order = ex.build_order({"approve": ["shortlist"], "shortlist": ["screen"], "screen": []})
    assert order == ["screen", "shortlist", "approve"]
    with pytest.raises(ValueError):
        ex.build_order({"a": ["b"], "b": ["a"]})
