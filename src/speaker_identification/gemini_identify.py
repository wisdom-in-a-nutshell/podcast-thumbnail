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
    video_path: Path | None = None,
    video_url: str | None = None,
    model: str = DEFAULT_MODEL,
    timestamps_per_speaker: int = 4,
    api_key: str | None = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Call Gemini to detect speakers and return structured JSON."""

    if not (video_path or video_url):
        raise GeminiIdentifyError("Provide video_path or video_url")
    if video_path and video_url:
        raise GeminiIdentifyError("Provide only one of video_path or video_url")

    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiIdentifyError("GEMINI_API_KEY not set")

    prompt = build_prompt(timestamps_per_speaker)

    if dry_run:
        return {"dry_run_prompt": prompt, "dry_run_video_url": video_url, "dry_run_video_path": str(video_path) if video_path else None}

    client = genai.Client(api_key=api_key)

    parts = []
    if video_path:
        file_ref = client.files.upload(file=str(video_path))
        parts.append(file_ref)
    elif video_url:
        parts.append({"file_data": {"file_uri": video_url}})

    parts.append(prompt)

    resp = client.models.generate_content(
        model=model,
        contents=parts,
    )

    try:
        data = json.loads(resp.text)
    except Exception as exc:  # noqa: BLE001
        raise GeminiIdentifyError(f"Failed to parse JSON from model: {exc}\nRaw: {resp.text}") from exc

    if not isinstance(data, dict) or "speakers" not in data:
        raise GeminiIdentifyError(f"Unexpected response schema: {data}")

    return data
