from __future__ import annotations

import re
from typing import Iterable, List, Optional

from .config import MAX_RETRIEVAL_RESULTS
from .models import SourceChunk


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_+-]+", text.lower())


def score_chunk(query: str, chunk: SourceChunk, country: Optional[str] = None) -> float:
    q_tokens = set(tokenize(query))
    c_tokens = set(tokenize(chunk.text + " " + chunk.title + " " + chunk.topic))
    overlap = len(q_tokens & c_tokens)
    if overlap == 0:
        return 0.0

    score = float(overlap)
    if country and chunk.country.lower() == country.lower():
        score += 2.5
    for token in q_tokens:
        if len(token) >= 6 and token in chunk.text.lower():
            score += 0.15
    return score


def retrieve(
    query: str,
    chunks: Iterable[SourceChunk],
    country: Optional[str] = None,
    topic: Optional[str] = None,
    top_k: int = MAX_RETRIEVAL_RESULTS,
) -> List[SourceChunk]:
    results: List[SourceChunk] = []
    for chunk in chunks:
        if country and chunk.country.lower() != country.lower():
            continue
        if topic and topic != "general" and chunk.topic.lower() != topic.lower():
            continue
        score = score_chunk(query, chunk, country=country)
        if score > 0:
            results.append(
                SourceChunk(
                    chunk_id=chunk.chunk_id,
                    country=chunk.country,
                    topic=chunk.topic,
                    title=chunk.title,
                    publisher=chunk.publisher,
                    url=chunk.url,
                    last_checked=chunk.last_checked,
                    text=chunk.text,
                    score=score,
                )
            )

    results.sort(key=lambda x: x.score, reverse=True)
    if results:
        return results[:top_k]

    # fallback: same-country docs even if lexical overlap is low
    fallback = [c for c in chunks if not country or c.country.lower() == country.lower()]
    return fallback[:top_k]
