from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SourceChunk:
    chunk_id: str
    country: str
    topic: str
    title: str
    publisher: str
    url: str
    last_checked: str
    text: str
    score: float = 0.0


@dataclass
class Apartment:
    title: str
    city: str
    country: str
    rent: float
    deposit: float
    furnished: bool
    utilities_included: bool
    url: str
    notes: str
