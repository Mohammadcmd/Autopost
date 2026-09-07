"""Loads the caption "style guide": tone notes plus a handful of example
captions used as style references for the local caption-writing model.

Important: the example captions are used purely as a *style* reference
(tone, rhythm, structure) for the model to draw on when writing something
new — see the instructions baked into ``local_llm.build_caption_prompt``.
They are never reproduced verbatim in generated output. If you like how a
particular Instagram account writes captions, paste a few of their captions
in here as inspiration; don't paste captions you don't want your own posts
to closely resemble, since a small local model may echo phrasing more
literally than a larger one would.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CaptionStyle:
    tone_notes: str = ""
    example_captions: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "CaptionStyle":
        path = Path(path)
        if not path.exists():
            return cls()
        with path.open() as f:
            data = json.load(f)
        return cls(
            tone_notes=data.get("tone_notes", ""),
            example_captions=data.get("example_captions", []),
        )

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            json.dump({"tone_notes": self.tone_notes, "example_captions": self.example_captions}, f, indent=2)
