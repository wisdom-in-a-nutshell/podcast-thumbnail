"""Compose a thumbnail using Gemini image model with provided headshots and title."""

from __future__ import annotations

import hashlib
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
        "google-genai is required for thumbnail composition. Install with `pip install google-genai`."
    ) from exc

from headshot_generation.gemini_client import _load_env_key


DEFAULT_MODEL = os.environ.get("PODTHUMB_COMPOSE_MODEL", "gemini-3-pro-image-preview")

TEMPLATES = {
    "diary_ceo": (
        "Two speakers side by side, slight inward head tilt, warm/approachable expressions."
        " Large close-up framing: faces should occupy most of the left/right thirds; crop at shoulders/chest"
        " similar to Diary of a CEO thumbnails. Dark/black backdrop with soft vignette."
        " Bold white title centered at top; pick 1–2 key words to highlight in red box with white text."
        " No 'NEW' badge. No headphones/earbuds/hats."
    ),
    "clean_two_up": (
        "Two-up interview layout, neutral gradient background, evenly lit faces, bold sans title with high contrast."
    ),
}

DEFAULT_PROMPT = (
    "You are designing a YouTube thumbnail. Keep the provided people looking like their references."
    " Place them side by side, shoulders-up, facing camera, slight inward tilt, warm approachable expression,"
    " remove headphones/earbuds/hats. Faces should be large and fill the left/right thirds; crop at shoulders/chest."
    " Use a clean background appropriate to the chosen template. Add the exact title text provided; choose 1–2"
    " important words to highlight with a red box and white text; ensure legibility on mobile."
    " No extra stickers, no watermarks, no logos. 16:9 composition, polished and professional."
)


def _cache_key(
    *,
    model: str,
    title_text: str,
    aspect_ratio: str,
    headshots: Sequence[Path],
    background: Path | None,
    template: str,
    style_reference: Path | None,
) -> str:
    hasher = hashlib.sha256()
    for part in (model, title_text, aspect_ratio, template):
        hasher.update(part.encode("utf-8"))

    for path in headshots:
        p = Path(path)
        hasher.update(p.name.encode("utf-8"))
        try:
            hasher.update(p.read_bytes())
        except FileNotFoundError:
            continue

    if background:
        p = Path(background)
        hasher.update(p.name.encode("utf-8"))
        try:
            hasher.update(p.read_bytes())
        except FileNotFoundError:
            pass

    if style_reference:
        p = Path(style_reference)
        hasher.update(p.name.encode("utf-8"))
        try:
            hasher.update(p.read_bytes())
        except FileNotFoundError:
            pass

    return hasher.hexdigest()


def _load_image(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def compose_thumbnail(
    headshot_paths: Sequence[Path] | Iterable[Path],
    *,
    title_text: str,
    background_path: Path | None = None,
    output_path: Path | str | None = None,
    model: str | None = None,
    aspect_ratio: str = "16:9",
    use_cache: bool = True,
    template: str = "diary_ceo",
    style_reference: Path | None = None,
) -> Path:
    """Generate a composed thumbnail via Gemini using headshots and a title.

    Args:
        headshot_paths: Two (or more) headshot PNGs to guide likeness.
        title_text: Exact title to render.
        background_path: Optional background image to blend in.
        output_path: Where to save the thumbnail (defaults to artifacts/thumbnails/thumb.png).
        model: Model override; defaults to gemini-3-pro-image-preview.
        aspect_ratio: Aspect ratio hint for the output (e.g., "16:9").
        use_cache: Return existing output if a cached version for the same inputs exists.
    """

    shots = list(headshot_paths)
    if len(shots) < 2:
        raise ValueError("Provide at least two headshots for composition.")

    _load_env_key()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) before composing thumbnails.")

    out_path = Path(output_path) if output_path else Path("artifacts/thumbnails/thumb.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cache_hash = _cache_key(
        model=model or DEFAULT_MODEL,
        title_text=title_text,
        aspect_ratio=aspect_ratio,
        headshots=shots,
        background=background_path,
        template=template,
        style_reference=style_reference,
    )

    final_path = out_path.with_name(f"{out_path.stem}_{cache_hash[:10]}{out_path.suffix or '.png'}")
    if use_cache and final_path.exists():
        return final_path

    images: List[Image.Image] = [_load_image(Path(p)) for p in shots[:4]]  # limit refs
    if background_path:
        images.append(_load_image(Path(background_path)))
    if style_reference:
        images.append(_load_image(Path(style_reference)))

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
    )

    style_prompt = TEMPLATES.get(template, "")
    prompt = (
        f"{DEFAULT_PROMPT} {style_prompt} Title text to render: \"{title_text}\"."
        " Place the title cleanly and ensure both people remain clear and unoccluded."
    )

    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=[prompt, *images],
        config=config,
    )

    # Extract first image candidate
    img_parts = []
    for cand in getattr(response, "candidates", []):
        for part in getattr(cand.content, "parts", []) or []:
            if getattr(part, "inline_data", None):
                img_parts.append(part.as_image())

    if not img_parts and hasattr(response, "parts"):
        for part in response.parts:
            if getattr(part, "inline_data", None):
                img_parts.append(part.as_image())

    if not img_parts:
        raise RuntimeError("Thumbnail model returned no image content.")

    image = img_parts[0]
    image.save(final_path)
    return final_path


__all__ = ["compose_thumbnail", "DEFAULT_MODEL", "DEFAULT_PROMPT"]
