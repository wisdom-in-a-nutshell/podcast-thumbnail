"""Pipeline helpers for sampling, headshots, and composition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from speaker_identification.frame_sampler import sample_frames as ffmpeg_sample_frames
from speaker_identification.gemini_identify import identify_speakers
from headshot_generation import generate_headshot
from thumbnail_composition import compose_thumbnail as compose_with_gemini


def sample_frames(video_path: Path, timestamps: Iterable[float]) -> List[Path]:
    """Extract frames at given timestamps using ffmpeg."""

    return ffmpeg_sample_frames(video_path, timestamps, out_dir=Path("artifacts/frames"))


def extract_frames_with_gemini(
    video_path: Path | None,
    video_url: str | None,
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
        video_url=video_url,
        model=model,
        timestamps_per_speaker=timestamps_per_speaker,
        api_key=api_key,
        dry_run=dry_run,
    )

    if dry_run:
        return data

    out_manifest.parent.mkdir(parents=True, exist_ok=True)

    if video_path:
        frames_dir.mkdir(parents=True, exist_ok=True)
        for speaker in data.get("speakers", []):
            ts_list = speaker.get("timestamps_s", [])
            extracted = ffmpeg_sample_frames(video_path, ts_list, frames_dir)
            speaker["frame_paths"] = [str(p) for p in extracted]
    else:
        # No local video -> we cannot extract frames; leave frame_paths absent.
        data["note"] = "frame extraction skipped (no local video provided)"

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
    use_cache: bool = True,
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
        use_cache=use_cache,
    )


def compose_thumbnail(background: Path, headshots: Iterable[Path], text: str) -> Path:
    """Composite headshots and text using Gemini image model."""

    return compose_with_gemini(
        headshot_paths=list(headshots),
        title_text=text,
        background_path=background,
        template="diary_ceo",
    )
