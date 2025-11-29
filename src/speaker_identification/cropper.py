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
    w, h = img.size

    x1 = max(0.0, min(1.0, float(bbox.get("x1", 0))))
    y1 = max(0.0, min(1.0, float(bbox.get("y1", 0))))
    x2 = max(0.0, min(1.0, float(bbox.get("x2", 1))))
    y2 = max(0.0, min(1.0, float(bbox.get("y2", 1))))

    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid bbox coordinates")

    # Expand bbox outward by padding fraction to include shoulders/upper torso
    pad_x = padding * (x2 - x1)
    pad_y = padding * (y2 - y1)
    x1 = max(0.0, x1 - pad_x)
    y1 = max(0.0, y1 - pad_y)
    x2 = min(1.0, x2 + pad_x)
    y2 = min(1.0, y2 + pad_y)

    # Enforce minimum box size by expanding symmetrically around center
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    w = x2 - x1
    h = y2 - y1
    w = max(w, min_width)
    h = max(h, min_height)
    x1 = max(0.0, cx - w / 2)
    x2 = min(1.0, cx + w / 2)
    y1 = max(0.0, cy - h / 2)
    y2 = min(1.0, cy + h / 2)

    box = (int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h))
    crop = img.crop(box)
    if crop.size[0] <= 0 or crop.size[1] <= 0:
        raise ValueError("Empty crop")
    if crop.mode not in ("RGB", "RGBA"):
        crop = crop.convert("RGB")

    out_path = out_dir / f"{frame_path.stem}_crop.png"
    crop.save(out_path, format="PNG")
    return out_path
