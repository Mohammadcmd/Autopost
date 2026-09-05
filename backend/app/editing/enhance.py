"""Fast, local, automatic photo enhancement.

Every function takes and returns an RGB ``numpy`` array (``uint8``,
``H x W x 3``) so stages can be composed cheaply without re-encoding between
steps. These are deliberately simple, classical image-processing techniques
(no ML models) so a whole event's worth of photos can be edited in
milliseconds each.
"""
from __future__ import annotations

import cv2
import numpy as np


def auto_white_balance(image: np.ndarray) -> np.ndarray:
    """Gray-world white balance: scale each channel so its mean matches the
    overall gray-level mean, correcting color casts from mixed lighting."""
    result = image.astype(np.float32)
    mean_per_channel = result.reshape(-1, 3).mean(axis=0)
    gray_mean = mean_per_channel.mean()
    # Avoid dividing by ~0 on near-black images.
    scale = gray_mean / np.clip(mean_per_channel, 1.0, None)
    result *= scale
    return np.clip(result, 0, 255).astype(np.uint8)


def auto_levels(image: np.ndarray, *, clip_percent: float = 0.5) -> np.ndarray:
    """Contrast-stretch each channel using percentile clipping so the
    darkest/lightest ``clip_percent`` of pixels are pushed to black/white."""
    result = image.astype(np.float32)
    for channel in range(3):
        channel_data = result[:, :, channel]
        low, high = np.percentile(channel_data, [clip_percent, 100 - clip_percent])
        if high - low < 1e-3:
            continue
        result[:, :, channel] = np.clip((channel_data - low) * 255.0 / (high - low), 0, 255)
    return result.astype(np.uint8)


def auto_exposure(image: np.ndarray, *, target_mean: float = 128.0) -> np.ndarray:
    """Brighten/darken the image so its overall luminance is closer to
    mid-gray, without clipping highlights harder than necessary."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    current_mean = float(gray.mean())
    if current_mean < 1.0:
        return image

    gain = target_mean / current_mean
    gain = float(np.clip(gain, 0.5, 2.0))  # keep adjustments subtle
    adjusted = image.astype(np.float32) * gain
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def deskew_and_crop(image: np.ndarray, *, max_angle: float = 10.0) -> np.ndarray:
    """Straighten a slightly tilted horizon/verticals and trim any resulting
    border. If no confident, small-angle skew is detected, the image is
    returned unchanged rather than risking a bad crop."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 60, 150)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=120, minLineLength=min(image.shape[:2]) // 4, maxLineGap=10
    )
    if lines is None:
        return image

    angles = []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        # Normalize near-horizontal lines to a signed small angle.
        if angle > 45:
            angle -= 90
        elif angle < -45:
            angle += 90
        if abs(angle) <= max_angle:
            angles.append(angle)

    if not angles:
        return image

    skew = float(np.median(angles))
    if abs(skew) < 0.5:
        return image  # not worth rotating

    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, skew, 1.0)
    rotated = cv2.warpAffine(
        image, rotation_matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )

    # Trim a small margin so the replicated border isn't visible.
    margin_ratio = min(abs(skew) / 90.0 * 2, 0.05)
    margin_x = int(width * margin_ratio)
    margin_y = int(height * margin_ratio)
    if margin_x and margin_y:
        rotated = rotated[margin_y:-margin_y, margin_x:-margin_x]

    return rotated
