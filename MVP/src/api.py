from __future__ import annotations

import os
from typing import Optional, Tuple

from openai import OpenAI

from .config import DEFAULT_OPENAI_MODEL, DEFAULT_OPENROUTER_MODEL, OPENROUTER_BASE_URL


def get_api_mode() -> Tuple[Optional[str], Optional[str]]:
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openrouter_key:
        return "openrouter", openrouter_key
    if openai_key:
        return "openai", openai_key
    return None, None


def make_client() -> Tuple[OpenAI, str, str]:
    mode, api_key = get_api_mode()
    if mode == "openrouter" and api_key:
        return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key), mode, DEFAULT_OPENROUTER_MODEL
    if mode == "openai" and api_key:
        return OpenAI(api_key=api_key), mode, DEFAULT_OPENAI_MODEL
    raise RuntimeError("No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY.")
