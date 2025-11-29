"""Helpers for calling Gemini's image model to create cleaned headshots."""

from __future__ import annotations

import io
import os
import hashlib
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
    " Remove headphones, earbuds, hats, or other headgear; show natural hair and ears."
    " Even soft key + fill lighting, natural skin tones, high detail, DSLR look."
    " Neutral light-gray gradient background, no text or logos, no watermarks,"
    " remove clutter and artifacts."
)
MAX_REFERENCE_IMAGES = 14


def _load_env_key() -> None:
    """Best-effort load GEMINI_API_KEY/GOOGLE_API_KEY from .env files.

    Checks (in order): existing environment, local project .env, cwd .env,
    the sibling "win" repo .env if present, and HOME/.env. Values already in
    the environment are never overwritten.
    """

    candidates = [
        Path("/Users/adi/GitHub/win/.env"),
        Path(__file__).resolve().parents[2] / ".env",  # this repo root
        Path.cwd() / ".env",
        Path.home() / ".env",
    ]

    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in os.environ:
                continue
            os.environ[key] = value


def _cache_key(
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
    image_size: str,
    num_images: int,
    crop_square: bool,
    reference_paths: Sequence[Path],
) -> str:
    """Create a stable hash for the input set to drive local caching."""

    hasher = hashlib.sha256()
    for part in (model, prompt, aspect_ratio, image_size, str(num_images), str(crop_square)):
        hasher.update(part.encode("utf-8"))

    for ref in reference_paths:
        path = Path(ref)
        hasher.update(path.name.encode("utf-8"))
        try:
            hasher.update(path.read_bytes())
        except FileNotFoundError:
            continue

    return hasher.hexdigest()


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
    use_cache: bool = True,
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

    _load_env_key()

    api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) before generating headshots.")

    out_dir = Path(output_dir) if output_dir else Path("artifacts/headshots")
    out_dir.mkdir(parents=True, exist_ok=True)

    cache_hash = _cache_key(
        model=model or DEFAULT_MODEL,
        prompt=prompt or DEFAULT_PROMPT,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        num_images=num_images,
        crop_square=crop_square,
        reference_paths=refs,
    )

    base_stem = Path(output_name).stem if output_name else f"{Path(refs[0]).stem}_headshot"
    base_suffix = (Path(output_name).suffix or ".png") if output_name else ".png"

    def _fname(idx: int) -> str:
        idx_part = f"_{idx}" if num_images > 1 else ""
        return f"{base_stem}_{cache_hash[:10]}{idx_part}{base_suffix}"

    candidate_paths = [out_dir / _fname(i) for i in range(1, max(1, num_images) + 1)]

    if use_cache and all(p.exists() for p in candidate_paths):
        return candidate_paths

    prepared_images = [_prepare_reference(Path(path), crop_square=crop_square) for path in refs]

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
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

    paths: List[Path] = []
    for idx, image in enumerate(images, start=1):
        filename = _fname(idx)
        out_path = out_dir / filename
        image.save(out_path)
        paths.append(out_path)

    return paths


__all__ = ["generate_headshot", "DEFAULT_PROMPT", "DEFAULT_MODEL"]
