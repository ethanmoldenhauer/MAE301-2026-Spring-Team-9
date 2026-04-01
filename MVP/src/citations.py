from __future__ import annotations

from datetime import datetime
from typing import List

from .models import SourceChunk


def freshness_label(last_checked: str) -> str:
    try:
        checked = datetime.strptime(last_checked, "%Y-%m-%d").date()
        age = (datetime.utcnow().date() - checked).days
    except Exception:
        return "Unknown freshness"

    if age <= 30:
        return "Fresh"
    if age <= 90:
        return "Check soon"
    return "Possibly outdated"


def format_citations(chunks: List[SourceChunk]) -> str:
    if not chunks:
        return "No citations available."

    lines = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] {chunk.title} — {chunk.publisher}  \n"
            f"Country: {chunk.country} | Topic: {chunk.topic} | Checked: {chunk.last_checked} | Status: {freshness_label(chunk.last_checked)}  \n"
            f"{chunk.url}"
        )
    return "\n\n".join(lines)
