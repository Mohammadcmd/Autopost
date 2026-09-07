"""Orchestrates the ordered editing stages applied to each photo."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from app.editing.cleanup import CleanupStage, NoOpCleanupStage
from app.editing.enhance import auto_exposure, auto_levels, auto_white_balance, deskew_and_crop


class EditingPipeline:
    def __init__(self, cleanup_stage: CleanupStage | None = None) -> None:
        self._cleanup_stage = cleanup_stage or NoOpCleanupStage()

    def process_array(self, image: np.ndarray) -> np.ndarray:
        image = auto_white_balance(image)
        image = auto_levels(image)
        image = auto_exposure(image)
        image = deskew_and_crop(image)
        image = self._cleanup_stage.apply(image)
        return image

    def process_file(self, source_path: str | Path, dest_path: str | Path) -> Path:
        source_path = Path(source_path)
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(source_path) as img:
            img = img.convert("RGB")
            array = np.array(img)

        edited = self.process_array(array)
        Image.fromarray(edited).save(dest_path, quality=90)
        return dest_path
