"""Pipeline helpers for sampling, headshots, and composition."""

from __future__ import annotations

import json
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

from speaker_identification.frame_sampler import sample_frames as ffmpeg_sample_frames
from speaker_identification.gemini_identify import identify_speakers
from speaker_identification.cropper import crop_frame
from headshot_generation import generate_headshot
from thumbnail_composition import compose_thumbnail as compose_with_gemini
import shutil


def sample_frames(video_path: Path, timestamps: Iterable[float]) -> List[Path]:
    """Extract frames at given timestamps using ffmpeg."""

    return ffmpeg_sample_frames(video_path, timestamps, out_dir=Path("artifacts/frames"))


def _get_duration_seconds(video_path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


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
        duration = _get_duration_seconds(video_path)
        for speaker in data.get("speakers", []):
            frames = speaker.get("frames") or []
            spk_id = speaker.get("id", "speaker")
            spk_root = frames_dir / spk_id
            spk_frame_dir = spk_root / "frames"
            spk_crop_dir = spk_root / "crops"
            spk_frame_dir.mkdir(parents=True, exist_ok=True)
            # Filter timestamps within duration and pad to requested count
            valid_frames: list[Dict[str, Any]] = []
            for f in frames:
                ts = f.get("timestamp_s")
                if ts is None:
                    continue
                if duration is not None and ts > duration - 0.5:
                    continue
                valid_frames.append(f)

            needed = max(0, timestamps_per_speaker - len(valid_frames))
            if needed and duration:
                step = duration / (timestamps_per_speaker + 1)
                for i in range(timestamps_per_speaker):
                    if len(valid_frames) >= timestamps_per_speaker:
                        break
                    ts = step * (i + 1)
                    valid_frames.append(
                        {
                            "timestamp_s": ts,
                            "bbox": {"x1": 0.2, "y1": 0.0, "x2": 0.8, "y2": 1.0},
                        }
                    )

            valid_frames = valid_frames[:timestamps_per_speaker]
            speaker["frames"] = valid_frames

            ts_list = [f.get("timestamp_s") for f in valid_frames if isinstance(f, dict) and "timestamp_s" in f]
            extracted = ffmpeg_sample_frames(video_path, ts_list, spk_frame_dir)
            for f, path in zip(valid_frames, extracted):
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


def run_end_to_end(
    *,
    video_path: Path,
    title: str,
    sample_model: str = "gemini-3-pro-preview",
    headshot_model: str | None = None,
    compose_model: str | None = None,
    manifest_path: Path,
    frames_dir: Path,
    headshots_dir: Path,
    timestamps_per_speaker: int = 4,
    template: str = "diary_ceo",
    aspect_ratio: str = "16:9",
    api_key: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run sample -> headshots -> compose. Returns summary dict."""

    summary: dict[str, Any] = {"steps": []}

    print(f"[sample] starting (model={sample_model})")
    sample_result = extract_frames_with_gemini(
        video_path=video_path,
        video_url=None,
        model=sample_model,
        out_manifest=manifest_path,
        frames_dir=frames_dir,
        timestamps_per_speaker=timestamps_per_speaker,
        dry_run=dry_run,
        api_key=api_key,
    )
    print(f"[sample] done -> {manifest_path}")
    summary["manifest"] = manifest_path
    summary["steps"].append("sample")

    if dry_run:
        return summary

    # Generate headshots per speaker (skip if already exists)
    headshot_paths: list[Path] = []
    for speaker in sample_result.get("speakers", []):
        spk_id = speaker.get("id", "speaker")
        out_dir = headshots_dir / spk_id
        existing_headshot = out_dir / "headshot.png"
        
        # Check if headshot already exists
        if existing_headshot.exists():
            print(f"[headshots] speaker {spk_id}: using existing {existing_headshot}")
            headshot_paths.append(existing_headshot)
            continue
        
        frames = speaker.get("frames") or []
        print(f"[headshots] speaker {spk_id}: {len(frames)} frame entries")
        # prefer crops, fall back to frames; max 3
        refs: list[Path] = []
        for f in frames:
            if len(refs) >= 3:
                break
            if f.get("crop_path"):
                refs.append(Path(f["crop_path"]))
            elif f.get("frame_path"):
                refs.append(Path(f["frame_path"]))
        if not refs:
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"[headshots] speaker {spk_id}: generating from {len(refs)} refs -> {out_dir}")
        shots = generate_headshot(
            refs,
            model=headshot_model,
            output_dir=out_dir,
            output_name="headshot.png",
            api_key=api_key,
            use_cache=True,
        )
        if not shots:
            raise RuntimeError(f"Headshot model returned no images for speaker {spk_id}")
        headshot_paths.append(shots[0])
        print(f"[headshots] speaker {spk_id}: saved {shots[0]}")
    summary["headshots"] = [str(p) for p in headshot_paths]
    summary["steps"].append("headshots")

    if len(headshot_paths) < 2:
        summary["warning"] = "Need at least two headshots for compose"
        return summary

    print(f"[compose] using {headshot_paths[:2]} template={template}")
    thumb_path = compose_thumbnail(
        background=None,
        headshots=headshot_paths[:2],
        text=title,
        template=template,
        model=compose_model,
        aspect_ratio=aspect_ratio,
        use_cache=True,
    )
    print(f"[compose] done -> {thumb_path}")
    summary["thumbnail"] = str(thumb_path)
    summary["steps"].append("compose")
    return summary


def run() -> None:
    """Interactive pipeline: prompts for video path and title text."""

    # Prompt for video file path
    print("\n=== Podcast Thumbnail Pipeline ===\n")
    video_input = input("Enter video file path: ").strip()
    if not video_input:
        print("No video path provided. Exiting.")
        return

    video_path = Path(video_input).expanduser().resolve()
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        return

    print(f"\n[info] Video: {video_path}")

    # Fixed artifact paths
    manifest_path = Path("artifacts/manifests/speakers.json")
    frames_dir = Path("artifacts/frames")
    headshots_dir = Path("artifacts/headshots")

    # Step 1: Sample frames and identify speakers
    print("\n[step 1/3] Sampling frames and identifying speakers...")
    sample_result = extract_frames_with_gemini(
        video_path=video_path,
        video_url=None,
        model="gemini-3-pro-preview",
        out_manifest=manifest_path,
        frames_dir=frames_dir,
        timestamps_per_speaker=4,
        dry_run=False,
    )
    print(f"[sample] Manifest saved to {manifest_path}")

    # Step 2: Generate headshots per speaker
    print("\n[step 2/3] Generating headshots...")
    headshot_paths: list[Path] = []
    for speaker in sample_result.get("speakers", []):
        spk_id = speaker.get("id", "speaker")
        out_dir = headshots_dir / spk_id
        existing_headshot = out_dir / "headshot.png"

        if existing_headshot.exists():
            print(f"  [headshots] {spk_id}: using cached {existing_headshot}")
            headshot_paths.append(existing_headshot)
            continue

        frames = speaker.get("frames") or []
        refs: list[Path] = []
        for f in frames:
            if len(refs) >= 3:
                break
            if f.get("crop_path"):
                refs.append(Path(f["crop_path"]))
            elif f.get("frame_path"):
                refs.append(Path(f["frame_path"]))

        if not refs:
            print(f"  [headshots] {spk_id}: no reference frames, skipping")
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"  [headshots] {spk_id}: generating from {len(refs)} refs...")
        shots = generate_headshot(
            refs,
            output_dir=out_dir,
            output_name="headshot.png",
            use_cache=True,
        )
        if shots:
            headshot_paths.append(shots[0])
            print(f"  [headshots] {spk_id}: saved {shots[0]}")
        else:
            print(f"  [headshots] {spk_id}: generation failed")

    if len(headshot_paths) < 2:
        print("\nError: Need at least 2 headshots for composition. Exiting.")
        return

    print(f"\n[info] Generated {len(headshot_paths)} headshots")

    # Prompt for title text
    print("\n[step 3/3] Thumbnail composition")
    title_text = input("Enter title text for thumbnail: ").strip()
    if not title_text:
        print("No title provided. Exiting.")
        return

    print(f"\n[compose] Creating thumbnail with: \"{title_text}\"")
    thumb_path = compose_thumbnail(
        background=None,
        headshots=headshot_paths[:2],
        text=title_text,
        template="diary_ceo",
        use_cache=True,
    )
    print("\n=== Done! ===")
    print(f"Thumbnail saved to: {thumb_path}\n")


if __name__ == "__main__":
    run()
