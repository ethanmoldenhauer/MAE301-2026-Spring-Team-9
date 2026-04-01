from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import LOGO_CANDIDATES


def find_logo() -> Optional[str]:
    for name in LOGO_CANDIDATES:
        if Path(name).exists():
            return name
    return None
