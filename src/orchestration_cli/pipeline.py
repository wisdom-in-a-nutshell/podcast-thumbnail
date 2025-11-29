"""Pipeline helpers for sampling, headshots, and composition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from speaker_identification.frame_sampler import sample_frames as ffmpeg_sample_frames
from speaker_identification.gemini_identify import identify_speakers
from headshot_generation import generate_headshot


def sample_frames(video_path: Path, timestamps: Iterable[float]) -> List[Path]:
    """Extract frames at given timestamps using ffmpeg."""

    return ffmpeg_sample_frames(video_path, timestamps, out_dir=Path("artifacts/frames"))


def extract_frames_with_gemini(
    video_path: Path,
    model: str,
    out_manifest: Path,
    frames_dir: Path,
    timestamps_per_speaker: int,
    dry_run: bool,
    api_key: str | None = None,
) -> Dict[str, Any] | None:
    """Run Gemini to get speaker timestamps, then extract frames with ffmpeg."""

    data = identify_speakers(
        video_path=video_path,
        model=model,
        timestamps_per_speaker=timestamps_per_speaker,
        api_key=api_key,
        dry_run=dry_run,
    )

    if dry_run:
        return data

    frames_dir.mkdir(parents=True, exist_ok=True)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)

    for speaker in data.get("speakers", []):
        ts_list = speaker.get("timestamps_s", [])
        extracted = ffmpeg_sample_frames(video_path, ts_list, frames_dir)
        speaker["frame_paths"] = [str(p) for p in extracted]

    out_manifest.write_text(json.dumps(data, indent=2))
    return data


def create_headshots(
    frame_paths: Iterable[Path],
    *,
    output_dir: Path | None = None,
    prompt: str | None = None,
    model: str | None = None,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    num_images: int = 1,
    api_key: str | None = None,
    crop_square: bool = True,
    output_name: str | None = None,
) -> List[Path]:
    """Send reference frames to Gemini and return saved headshot paths."""

    return generate_headshot(
        frame_paths,
        prompt=prompt,
        output_dir=output_dir,
        model=model,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        num_images=num_images,
        api_key=api_key,
        crop_square=crop_square,
        output_name=output_name,
    )


def compose_thumbnail(background: Path, headshots: Iterable[Path], text: str) -> Path:
    """Composite headshots and text onto a background and return the output path."""
    raise NotImplementedError
