"""Pluggable "remove background clutter" pipeline stage.

The ask this stage exists for — automatically erasing distracting background
objects like a garbage can or a broom leaning in a corner — is a generative
inpainting problem, not a classical image-processing one. Doing it well
requires chaining several local ML models:

1. Open-vocabulary object detection (e.g. Grounding DINO or YOLO-World) to
   locate clutter by natural-language class names that aren't in a fixed
   label set like COCO.
2. Segmentation (e.g. Segment Anything) to turn each detection's box into a
   precise pixel mask.
3. Inpainting (e.g. LaMa) to fill the masked region convincingly.

Each of those is a meaningfully heavy model to bundle, download, and run
compared to the rest of this pipeline (all plain numpy/OpenCV so far), so
it's intentionally out of scope for this first pass. What ships here is the
seam it plugs into: any future implementation just needs to satisfy
``CleanupStage`` and be swapped in wherever ``NoOpCleanupStage`` is
instantiated today.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class CleanupStage(ABC):
    """A pipeline stage that may remove or paint over unwanted content."""

    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class NoOpCleanupStage(CleanupStage):
    """Phase-1 placeholder: passes the image through unchanged.

    Swap this out for a real detector+segmenter+inpainter implementation
    once that follow-up work is scoped.
    """

    def apply(self, image: np.ndarray) -> np.ndarray:
        return image
