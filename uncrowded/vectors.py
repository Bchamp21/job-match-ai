"""A small vector store written from scratch: TF-IDF vectors, cosine similarity, top-k with a heap.

TF-IDF matches words, not meaning ("ETL" will not find "pipelines"). The Embedder protocol is the
seam where a neural embedding model can replace it, and the eval in rag.py shows whether that helps.
"""
from __future__ import annotations

import heapq
import math
import re
from collections import Counter, defaultdict
from typing import Protocol

Vector = dict[str, float]
STOP = set("a an and are as at be by for from in is it of on or our that the this to we will with you your".split())


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]", text.lower()) if t not in STOP]


def normalize(v: Vector) -> Vector:
    length = math.sqrt(sum(x * x for x in v.values()))
    return {k: x / length for k, x in v.items()} if length else {}


class Embedder(Protocol):
    def fit(self, texts: list[str]) -> None: ...
    def embed(self, text: str) -> Vector: ...


class TfidfEmbedder:
    def __init__(self) -> None:
        self.idf: dict[str, float] = {}

    def fit(self, texts: list[str]) -> None:
        df = Counter(t for text in texts for t in set(tokens(text)))
        self.idf = {t: math.log((1 + len(texts)) / (1 + n)) + 1 for t, n in df.items()}

    def embed(self, text: str) -> Vector:
        counts = Counter(t for t in tokens(text) if t in self.idf)
        return normalize({t: (1 + math.log(n)) * self.idf[t] for t, n in counts.items()})


class VectorStore:
    """An inverted index means a query only touches documents that share a term with it."""

    def __init__(self, embedder: Embedder | None = None) -> None:
        self.embedder = embedder or TfidfEmbedder()
        self.texts: dict[str, str] = {}
        self.index: dict[str, list[tuple[str, float]]] = defaultdict(list)

    def build(self, documents: dict[str, str]) -> None:
        self.texts = dict(documents)
        self.embedder.fit(list(documents.values()))
        self.index = defaultdict(list)
        for key, text in documents.items():
            for term, weight in self.embedder.embed(text).items():
                self.index[term].append((key, weight))

    def search(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        scores: dict[str, float] = defaultdict(float)
        for term, q_weight in self.embedder.embed(query).items():
            for key, weight in self.index.get(term, []):
                scores[key] += q_weight * weight  # both unit length, so the dot product is the cosine
        return heapq.nlargest(k, scores.items(), key=lambda item: (item[1], item[0]))
