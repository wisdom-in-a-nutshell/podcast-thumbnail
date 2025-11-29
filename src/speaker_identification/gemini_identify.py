"""Identify speakers and timestamps using Gemini 3 Pro (video -> JSON)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from google import genai

from .prompt import build_prompt


DEFAULT_MODEL = "gemini-3-pro-preview"


class GeminiIdentifyError(RuntimeError):
    pass


def identify_speakers(
    video_path: Path,
    model: str = DEFAULT_MODEL,
    timestamps_per_speaker: int = 4,
    api_key: str | None = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Call Gemini to detect speakers and return structured JSON."""

    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiIdentifyError("GEMINI_API_KEY not set")

    prompt = build_prompt(timestamps_per_speaker)

    if dry_run:
        return {"dry_run_prompt": prompt}

    client = genai.Client(api_key=api_key)

    file_ref = client.files.upload(file=str(video_path))

    resp = client.models.generate_content(
        model=model,
        contents=[file_ref, prompt],
        response_mime_type="application/json",
    )

    try:
        data = json.loads(resp.text)
    except Exception as exc:  # noqa: BLE001
        raise GeminiIdentifyError(f"Failed to parse JSON from model: {exc}\nRaw: {resp.text}") from exc

    if not isinstance(data, dict) or "speakers" not in data:
        raise GeminiIdentifyError(f"Unexpected response schema: {data}")

    return data

