"""Utilities to crop faces using normalized bounding boxes."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from PIL import Image


def crop_frame(
    frame_path: Path,
    bbox: Dict[str, float],
    out_dir: Path,
    padding: float = 0.35,
    min_width: float = 0.35,
    min_height: float = 0.5,
) -> Path:
    """Crop a frame to the provided bbox (normalized 0-1) and save.

    Args:
        frame_path: path to the full frame image.
        bbox: dict with keys x1,y1,x2,y2 (normalized floats 0-1).
        out_dir: directory to write the crop.

    Returns:
        Path to the cropped image.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(frame_path)
    w_px, h_px = img.size

    x1 = max(0.0, min(1.0, float(bbox.get("x1", 0))))
    x2 = max(0.0, min(1.0, float(bbox.get("x2", 1))))
    # Use full height irrespective of model y-bbox
    y1, y2 = 0.0, 1.0

    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid bbox coordinates")

    # Expand bbox outward horizontally; keep full vertical span
    pad_x = padding * (x2 - x1)
    x1 = max(0.0, x1 - pad_x)
    x2 = min(1.0, x2 + pad_x)

    # Enforce minimum box size by expanding symmetrically around center
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    w_rel = x2 - x1
    h_rel = 1.0  # full height
    w_rel = max(w_rel, min_width)
    x1 = max(0.0, cx - w_rel / 2)
    x2 = min(1.0, cx + w_rel / 2)
    y1, y2 = 0.0, 1.0

    box = (int(x1 * w_px), int(y1 * h_px), int(x2 * w_px), int(y2 * h_px))
    crop = img.crop(box)
    if crop.size[0] <= 0 or crop.size[1] <= 0:
        raise ValueError("Empty crop")
    if crop.mode not in ("RGB", "RGBA"):
        crop = crop.convert("RGB")

    out_path = out_dir / f"{frame_path.stem}_crop{frame_path.suffix}"
    crop.save(out_path, format="PNG")
    return out_path
