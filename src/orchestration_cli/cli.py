"""CLI entry point for the podcast thumbnail toolchain."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from headshot_generation import DEFAULT_MODEL as DEFAULT_HEADSHOT_MODEL
from headshot_generation import DEFAULT_PROMPT as DEFAULT_HEADSHOT_PROMPT
from headshot_generation.gemini_client import _load_env_key
from . import __version__
from .pipeline import create_headshots, extract_frames_with_gemini


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Podcast thumbnail helper")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )

    sub = parser.add_subparsers(dest="command")

    sample = sub.add_parser("sample", help="Identify speakers via Gemini and extract frames")
    sample.add_argument("--video", type=Path, help="Path to local video file")
    sample.add_argument("--url", help="Public video URL (YouTube or direct)")
    sample.add_argument("--model", default="gemini-3-pro-preview", help="Gemini model")
    sample.add_argument(
        "--timestamps-per-speaker",
        type=int,
        default=4,
        help="How many timestamps to request per speaker",
    )
    sample.add_argument(
        "--out-manifest",
        type=Path,
        default=Path("manifests/speakers.json"),
        help="Where to write the speakers manifest",
    )
    sample.add_argument(
        "--frames-dir",
        type=Path,
        default=Path("artifacts/frames"),
        help="Directory to store extracted frames",
    )
    sample.add_argument("--dry-run", action="store_true", help="Print prompt; do not call Gemini")

    headshots = sub.add_parser("headshots", help="Generate cleaned headshots from reference frames")
    headshots.add_argument("--frames", nargs="+", required=True, type=Path, help="Reference frame paths")
    headshots.add_argument(
        "--outdir", type=Path, default=Path("artifacts/headshots"), help="Directory for outputs"
    )
    headshots.add_argument(
        "--prompt", default=None, help="Override the default studio headshot prompt"
    )
    headshots.add_argument(
        "--model", default=None, help=f"Model override (default: {DEFAULT_HEADSHOT_MODEL})"
    )
    headshots.add_argument(
        "--aspect-ratio", default="1:1", help="Aspect ratio hint, e.g. 1:1 or 3:4"
    )
    headshots.add_argument(
        "--image-size", default="1K", choices=["1K", "2K", "4K"], help="Resolution hint"
    )
    headshots.add_argument(
        "--num-images", type=int, default=1, help="Number of images to request"
    )
    headshots.add_argument(
        "--output-name", default=None, help="Optional filename (no directory)"
    )
    headshots.add_argument(
        "--no-crop", action="store_true", help="Skip square center crop on references"
    )
    headshots.add_argument(
        "--api-key", default=None, help="API key override (else GEMINI_API_KEY/GOOGLE_API_KEY)"
    )
    headshots.add_argument(
        "--no-cache", action="store_true", help="Disable local cache and always call the API"
    )

    return parser


def main() -> None:
    # Load .env if present (ignored if values already in env)
    _load_env_key()

    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    if args.command == "sample":
        if not args.video and not args.url:
            parser.error("--video or --url is required for 'sample'")
        if args.video and args.url:
            parser.error("Use only one of --video or --url")
        result = extract_frames_with_gemini(
            video_path=args.video,
            video_url=args.url,
            model=args.model,
            out_manifest=args.out_manifest,
            frames_dir=args.frames_dir,
            timestamps_per_speaker=args.timestamps_per_speaker,
            dry_run=args.dry_run,
        )
        if result is not None:
            print(json.dumps(result, indent=2))
        return

    if args.command == "headshots":
        outputs = create_headshots(
            frame_paths=args.frames,
            output_dir=args.outdir,
            prompt=args.prompt or DEFAULT_HEADSHOT_PROMPT,
            model=args.model or DEFAULT_HEADSHOT_MODEL,
            aspect_ratio=args.aspect_ratio,
            image_size=args.image_size,
            num_images=args.num_images,
            api_key=args.api_key,
            crop_square=not args.no_crop,
            output_name=args.output_name,
            use_cache=not args.no_cache,
        )
        for path in outputs:
            print(path)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
