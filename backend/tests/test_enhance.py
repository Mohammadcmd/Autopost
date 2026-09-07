import numpy as np
import pytest

from app.editing.enhance import auto_exposure, auto_levels, auto_white_balance, deskew_and_crop
from app.editing.pipeline import EditingPipeline
from PIL import Image


@pytest.fixture
def sample_image() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(0, 255, size=(120, 160, 3), dtype=np.uint8)


def test_auto_white_balance_preserves_shape_and_dtype(sample_image):
    result = auto_white_balance(sample_image)
    assert result.shape == sample_image.shape
    assert result.dtype == np.uint8


def test_auto_white_balance_neutralizes_a_color_cast():
    # A strong red cast: the red channel mean should dominate before, and be
    # brought back in line with the others after.
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    image[:, :, 0] = 200  # red
    image[:, :, 1] = 80   # green
    image[:, :, 2] = 80   # blue

    result = auto_white_balance(image)
    means = result.reshape(-1, 3).mean(axis=0)
    assert max(means) - min(means) < max(image.reshape(-1, 3).mean(axis=0)) - min(
        image.reshape(-1, 3).mean(axis=0)
    )


def test_auto_levels_stretches_contrast(sample_image):
    dim_image = (sample_image.astype(np.float32) * 0.3 + 50).astype(np.uint8)
    result = auto_levels(dim_image)
    assert result.shape == dim_image.shape
    assert result.std() >= dim_image.std()


def test_auto_exposure_brightens_a_dark_image():
    dark_image = np.full((50, 50, 3), 20, dtype=np.uint8)
    result = auto_exposure(dark_image)
    assert result.mean() > dark_image.mean()


def test_auto_exposure_handles_near_black_image_without_crashing():
    black_image = np.zeros((10, 10, 3), dtype=np.uint8)
    result = auto_exposure(black_image)
    assert result.shape == black_image.shape


def test_deskew_and_crop_returns_same_shape_family(sample_image):
    result = deskew_and_crop(sample_image)
    assert result.shape[2] == 3
    assert result.dtype == np.uint8


def test_deskew_and_crop_handles_images_with_detected_lines():
    # A strong straight edge is exactly what triggers cv2.HoughLinesP to
    # return matches; this regression-tests the line-unpacking logic itself
    # (a previous version crashed here with a shape mismatch).
    import cv2

    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image[:, :] = 30
    cv2.line(image, (10, 10), (190, 15), (255, 255, 255), thickness=3)
    cv2.line(image, (10, 100), (190, 105), (255, 255, 255), thickness=3)

    result = deskew_and_crop(image)
    assert result.shape[2] == 3
    assert result.dtype == np.uint8


def test_pipeline_process_file_writes_output(tmp_path):
    source = tmp_path / "source.jpg"
    Image.fromarray(
        np.random.default_rng(1).integers(0, 255, size=(80, 80, 3), dtype=np.uint8)
    ).save(source)

    dest = tmp_path / "out" / "edited.jpg"
    pipeline = EditingPipeline()
    result_path = pipeline.process_file(source, dest)

    assert result_path.exists()
    with Image.open(result_path) as img:
        assert img.size[0] > 0 and img.size[1] > 0
