from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .config import DATA_DIR
from .models import SourceChunk


def load_source_chunks(data_dir: Path = DATA_DIR) -> List[SourceChunk]:
    chunks: List[SourceChunk] = []
    if not data_dir.exists():
        return chunks

    for path in sorted(data_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                chunks.append(
                    SourceChunk(
                        chunk_id=record["chunk_id"],
                        country=record["country"],
                        topic=record["topic"],
                        title=record["title"],
                        publisher=record["publisher"],
                        url=record["url"],
                        last_checked=record["last_checked"],
                        text=record["text"],
                    )
                )
    return chunks
