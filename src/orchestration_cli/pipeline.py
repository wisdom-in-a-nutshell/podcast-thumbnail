"""Pipeline helpers for sampling, headshots, and composition."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from speaker_identification.frame_sampler import sample_frames as ffmpeg_sample_frames
from speaker_identification.gemini_identify import identify_speakers
from speaker_identification.cropper import crop_frame
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

    TTL_SECONDS = 24 * 60 * 60  # 1 day

    # Local manifest cache: if fresh, return without calling Gemini
    if not dry_run and out_manifest.exists():
        age = time.time() - out_manifest.stat().st_mtime
        if age <= TTL_SECONDS:
            try:
                return json.loads(out_manifest.read_text())
            except Exception:
                pass  # fall through to recompute if cache unreadable

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
            frames = speaker.get("frames") or []
            spk_id = speaker.get("id", "speaker")
            spk_root = frames_dir / spk_id
            spk_frame_dir = spk_root / "frames"
            spk_crop_dir = spk_root / "crops"
            spk_frame_dir.mkdir(parents=True, exist_ok=True)
            ts_list = [f.get("timestamp_s") for f in frames if isinstance(f, dict) and "timestamp_s" in f]
            extracted = ffmpeg_sample_frames(video_path, ts_list, spk_frame_dir)
            for f, path in zip(frames, extracted):
                f["frame_path"] = str(path)
                bbox = f.get("bbox")
                if bbox:
                    try:
                        crop_path = crop_frame(path, bbox, spk_crop_dir)
                        f["crop_path"] = str(crop_path)
                    except Exception:
                        # leave crop_path absent if cropping fails
                        pass
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


def compose_thumbnail(
    background: Path | None,
    headshots: Iterable[Path],
    text: str,
    *,
    template: str = "diary_ceo",
    style_reference: Path | None = None,
    model: str | None = None,
    aspect_ratio: str = "16:9",
    use_cache: bool = True,
    output_path: Path | None = None,
    highlight_words: list[str] | None = None,
    jitter: bool = False,
) -> Path:
    """Composite headshots and text using Gemini image model."""

    return compose_with_gemini(
        headshot_paths=list(headshots),
        title_text=text,
        background_path=background,
        template=template,
        style_reference=style_reference,
        model=model,
        aspect_ratio=aspect_ratio,
        use_cache=use_cache,
        output_path=output_path,
        highlight_words=highlight_words,
        jitter=jitter,
    )
