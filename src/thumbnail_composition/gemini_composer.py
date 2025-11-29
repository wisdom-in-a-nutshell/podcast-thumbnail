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
        " Symmetric sizing: both faces the same apparent size, eyes aligned on the same horizontal line,"
        " occupying most of the left/right thirds (each face fills ~40% of width), cropped at shoulders/chest, small outer margin."
        " Dark/black vignette backdrop. Title in a compact two-line block centered near top-middle; maximum width 60%"
        " of the frame; place the title near the top of the frame (not middle). Bold white text; highlight 1–2 key words with a red box and white text."
        " Keep minimal empty space under the title; keep clear padding above and below the text block; avoid large blank gaps." 
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
    highlight_words: tuple[str, ...],
    prompt_signature: str,
) -> str:
    hasher = hashlib.sha256()
    for part in (model, title_text, aspect_ratio, template, "|".join(highlight_words), prompt_signature):
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
    highlight_words: Sequence[str] | None = None,
    jitter: bool = False,
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

    style_prompt = TEMPLATES.get(template, "")
    highlight_prompt = ""
    if highlight_words:
        highlight_prompt = (
            " Highlight the following words/phrases with a red box and white text: "
            + ", ".join(f'\"{w}\"' for w in highlight_words)
            + "."
        )

    prompt_signature = f"{DEFAULT_PROMPT}|{style_prompt}|{highlight_prompt}"

    cache_hash = _cache_key(
        model=model or DEFAULT_MODEL,
        title_text=title_text,
        aspect_ratio=aspect_ratio,
        headshots=shots,
        background=background_path,
        template=template,
        style_reference=style_reference,
        highlight_words=tuple(highlight_words or ()),
        prompt_signature=prompt_signature,
    )

    final_path = out_path.with_name(f"{out_path.stem}_{cache_hash[:10]}{out_path.suffix or '.png'}")
    if use_cache and final_path.exists():
        return final_path

    def _jitter(img: Image.Image) -> Image.Image:
        # Tiny brightness bump to break dedup; visually negligible.
        return ImageEnhance.Brightness(img).enhance(1.01)

    images: List[Image.Image] = []
    for idx, p in enumerate(shots[:4]):
        img = _load_image(Path(p))
        if jitter and idx == 0:
            img = _jitter(img)
        images.append(img)
    if background_path:
        images.append(_load_image(Path(background_path)))
    if style_reference:
        images.append(_load_image(Path(style_reference)))

    client = genai.Client(api_key=api_key)
    safety = [
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    ]

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        safety_settings=safety,
    )

    style_prompt = TEMPLATES.get(template, "")
    highlight_prompt = ""
    if highlight_words:
        highlight_prompt = (
            " Highlight the following words/phrases with a red box and white text: "
            + ", ".join(f'"{w}"' for w in highlight_words)
            + "."
        )

    prompt = (
        f"{DEFAULT_PROMPT} {style_prompt} Title text to render: \"{title_text}\"."
        f"{highlight_prompt} Place the title at the top, compact, filling the upper third; keep tight line spacing and avoid excessive empty space."
        " Ensure both people remain clear and unoccluded."
    )

    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=[prompt, *images],
        config=config,
    )

    # Extract first image candidate using BytesIO fallback (SDK as_image() is unreliable)
    result_image: Image.Image | None = None
    for cand in getattr(response, "candidates", []):
        for part in getattr(cand.content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and hasattr(inline, "data"):
                result_image = Image.open(io.BytesIO(inline.data))
                break
        if result_image:
            break

    if result_image is None and hasattr(response, "parts"):
        for part in response.parts:
            inline = getattr(part, "inline_data", None)
            if inline and hasattr(inline, "data"):
                result_image = Image.open(io.BytesIO(inline.data))
                break

    if result_image is None:
        raise RuntimeError("Thumbnail model returned no image content.")

    result_image.save(final_path)
    return final_path


__all__ = ["compose_thumbnail", "DEFAULT_MODEL", "DEFAULT_PROMPT"]
