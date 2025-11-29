"""Frame sampling utilities using ffmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List


def sample_frames(
    video_path: Path,
    timestamps: Iterable[float],
    out_dir: Path,
    quality: int = 2,
) -> List[Path]:
    """Extract frames at given timestamps using ffmpeg."""

    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for i, ts in enumerate(timestamps):
        ts_str = f"{ts:.3f}"
        frame_path = out_dir / f"frame_{i:03d}_{ts_str.replace('.', 'p')}.jpg"
        cmd = [
            "ffmpeg",
            "-ss",
            ts_str,
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            str(quality),
            "-y",
            str(frame_path),
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            # Skip timestamps outside duration or other ffmpeg errors.
            continue
        written.append(frame_path)
    return written


def frange(start: float, stop: float, step: float) -> Iterable[float]:
    cur = start
    while cur < stop:
        yield cur
        cur += step


def uniform_timestamps(duration_s: float, stride_s: float, limit: int | None = None) -> List[float]:
    """Generate uniformly spaced timestamps across the video duration."""

    if stride_s <= 0:
        raise ValueError("stride_s must be > 0")
    ts = [t for t in frange(0, duration_s, stride_s)]
    return ts[:limit] if limit else ts
