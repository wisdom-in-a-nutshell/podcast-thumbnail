"""Helpers for calling Gemini's image model to create cleaned headshots."""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Iterable, List, Sequence

from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "google-genai is required for headshot generation. Install with `pip install google-genai`."
    ) from exc


DEFAULT_MODEL = os.environ.get("PODTHUMB_HEADSHOT_MODEL", "gemini-3-pro-image-preview")
DEFAULT_PROMPT = (
    "Cinematic studio headshot of the same person in the reference photos."
    " Shoulders-up, centered, eyes to camera, relaxed confident expression."
    " Even soft key + fill lighting, natural skin tones, high detail, DSLR look."
    " Neutral light-gray gradient background, no text or logos, no watermarks,"
    " remove clutter and artifacts."
)
MAX_REFERENCE_IMAGES = 14


def _square_center_crop(image: Image.Image, *, min_side: int = 512) -> Image.Image:
    """Center-crop to a square and upscale to the requested minimum side."""

    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    cropped = image.crop((left, top, left + side, top + side))
    if side < min_side:
        cropped = cropped.resize((min_side, min_side), Image.Resampling.LANCZOS)
    return cropped


def _prepare_reference(path: Path, *, crop_square: bool = True) -> Image.Image:
    image = Image.open(path)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    if crop_square:
        image = _square_center_crop(image)
    return image


def _extract_images(response) -> List[Image.Image]:
    """Collect inline image parts from a generate_content response."""

    images: List[Image.Image] = []

    for part in getattr(response, "parts", []) or []:
        if getattr(part, "inline_data", None):
            images.append(part.as_image())

    if not images and hasattr(response, "generated_images"):
        for img in response.generated_images:
            if hasattr(img, "as_image"):
                images.append(img.as_image())
            elif hasattr(img, "image_bytes"):
                images.append(Image.open(io.BytesIO(img.image_bytes)))

    if not images and hasattr(response, "candidates"):
        for candidate in response.candidates:
            for part in getattr(candidate.content, "parts", []) or []:
                if getattr(part, "inline_data", None):
                    images.append(part.as_image())

    return images


def generate_headshot(
    reference_paths: Sequence[Path] | Iterable[Path],
    *,
    prompt: str | None = None,
    output_dir: Path | str | None = None,
    output_name: str | None = None,
    model: str | None = None,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    num_images: int = 1,
    api_key: str | None = None,
    crop_square: bool = True,
) -> List[Path]:
    """Generate a cleaned headshot using Gemini 3 Pro Image Preview.

    Args:
        reference_paths: One or more frame paths representing the same person.
        prompt: Optional style prompt override; defaults to a studio headshot prompt.
        output_dir: Directory to write outputs (defaults to `artifacts/headshots`).
        output_name: Optional fixed filename for the first image. If not provided,
            files are named from the first reference stem.
        model: Model name override (defaults to ``gemini-3-pro-image-preview``).
        aspect_ratio: Image aspect ratio string accepted by the API, e.g. "1:1".
        image_size: Output size hint ("1K", "2K", or "4K").
        num_images: Number of images to request from the model.
        api_key: Gemini API key. Falls back to ``GEMINI_API_KEY`` or ``GOOGLE_API_KEY`` env vars.
        crop_square: Whether to center-crop references to square before sending.

    Returns:
        A list of saved headshot paths (one per generated image).
    """

    refs = list(reference_paths)
    if not refs:
        raise ValueError("At least one reference frame is required for headshot generation.")

    if len(refs) > MAX_REFERENCE_IMAGES:
        refs = refs[:MAX_REFERENCE_IMAGES]

    api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) before generating headshots.")

    out_dir = Path(output_dir) if output_dir else Path("artifacts/headshots")
    out_dir.mkdir(parents=True, exist_ok=True)

    prepared_images = [_prepare_reference(Path(path), crop_square=crop_square) for path in refs]

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            number_of_images=num_images,
        ),
    )

    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=[prompt or DEFAULT_PROMPT, *prepared_images],
        config=config,
    )

    images = _extract_images(response)
    if not images:
        raise RuntimeError("Headshot model returned no images.")

    base_stem = Path(output_name).stem if output_name else f"{Path(refs[0]).stem}_headshot"
    base_suffix = (Path(output_name).suffix or ".png") if output_name else ".png"

    paths: List[Path] = []
    for idx, image in enumerate(images, start=1):
        if num_images > 1:
            filename = f"{base_stem}_{idx}{base_suffix or '.png'}"
        else:
            filename = f"{base_stem}{base_suffix or '.png'}"
        out_path = out_dir / filename
        image.save(out_path)
        paths.append(out_path)

    return paths


__all__ = ["generate_headshot", "DEFAULT_PROMPT", "DEFAULT_MODEL"]
