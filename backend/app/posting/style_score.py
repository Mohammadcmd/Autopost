"""Scores how closely a caption matches the reference style examples.

This measures *style* closeness (tone, rhythm, structure) via the local
model's embeddings and cosine similarity — not literal text overlap, which
we deliberately avoid checking for or optimizing toward, since the goal is
an original caption in a similar voice, never a reproduction of someone
else's actual words.
"""
from __future__ import annotations

import math

from app.posting.local_llm import LocalLLMClient, LocalLLMUnavailableError
from app.posting.style import CaptionStyle


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def score_caption_style(caption: str, style: CaptionStyle, llm: LocalLLMClient) -> float | None:
    """Return a 0-100 style-match score against the reference examples, or
    ``None`` when scoring isn't possible (no examples yet, or no local
    model reachable)."""
    if not style.example_captions:
        return None

    try:
        caption_embedding = llm.embed(caption)
        example_embeddings = [llm.embed(example) for example in style.example_captions]
    except LocalLLMUnavailableError:
        return None

    similarities = [_cosine_similarity(caption_embedding, example) for example in example_embeddings]
    average_similarity = sum(similarities) / len(similarities)
    return round(max(0.0, min(1.0, average_similarity)) * 100, 1)
