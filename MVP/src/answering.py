from __future__ import annotations

from typing import List, Optional

from openai import OpenAI

from .models import SourceChunk


SYSTEM_PROMPT = """You are NestGPT, an AI assistant for finding housing abroad.

You must answer only from the provided source excerpts.
Rules:
- Be practical and concise.
- If the context is incomplete, say what is missing.
- Never claim legal certainty.
- Include inline citations like [1], [2] that match the provided sources.
- Do not invent facts outside the context.
"""

TRANSLATE_PROMPT = """You are a professional translator.
Translate the text into the requested language.
Keep the meaning, tone, and formatting.
Do not add commentary.
"""

SUMMARIZE_PROMPT = """You summarize housing, lease, and immigration-related documents.
Return a practical summary with:
1. key points
2. action items
3. red flags or missing information
"""


def build_context(chunks: List[SourceChunk]) -> str:
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(
            f"[{i}] title={chunk.title} | publisher={chunk.publisher} | country={chunk.country} | topic={chunk.topic} | last_checked={chunk.last_checked}\n"
            f"url={chunk.url}\n"
            f"text={chunk.text}"
        )
    return "\n\n".join(blocks)


def answer_from_sources(
    client: Optional[OpenAI],
    model: Optional[str],
    user_query: str,
    chunks: List[SourceChunk],
) -> str:
    if client is None or model is None:
        raise RuntimeError("No API client available.")

    context = build_context(chunks)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question:\n{user_query}\n\nSources:\n{context}"},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def translate_text(client: Optional[OpenAI], model: Optional[str], text: str, target_language: str) -> str:
    if client is None or model is None:
        raise RuntimeError("No API client available.")

    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": TRANSLATE_PROMPT},
            {"role": "user", "content": f"Target language: {target_language}\n\nText:\n{text}"},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def summarize_document(client: Optional[OpenAI], model: Optional[str], text: str) -> str:
    if client is None or model is None:
        raise RuntimeError("No API client available.")

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SUMMARIZE_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return (response.choices[0].message.content or "").strip()
