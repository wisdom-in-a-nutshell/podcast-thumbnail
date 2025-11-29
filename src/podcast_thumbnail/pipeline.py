"""Stubs for the thumbnail generation pipeline.

Fill these out with real implementations when we wire ffmpeg frame sampling,
Gemini headshot generation, and thumbnail composition.
"""

from pathlib import Path
from typing import Iterable, List


def sample_frames(video_path: Path, timestamps: Iterable[float]) -> List[Path]:
    """Extract frames at given timestamps. Replace with ffmpeg logic later."""
    raise NotImplementedError


def create_headshots(frame_paths: Iterable[Path]) -> List[Path]:
    """Send frames to the headshot model and return cleaned headshot paths."""
    raise NotImplementedError


def compose_thumbnail(background: Path, headshots: Iterable[Path], text: str) -> Path:
    """Composite headshots and text onto a background and return the output path."""
    raise NotImplementedError
