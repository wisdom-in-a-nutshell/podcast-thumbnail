"""CLI entry point for the podcast thumbnail toolchain."""

import argparse
from pathlib import Path

from . import __version__
from . import pipeline
from headshot_generation import DEFAULT_MODEL, DEFAULT_PROMPT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Podcast thumbnail helper")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    headshots = subparsers.add_parser(
        "headshots",
        help="Generate a cleaned headshot using Gemini 3 Pro Image Preview",
    )
    headshots.add_argument(
        "--frames",
        nargs="+",
        required=True,
        help="Reference frame paths for the same speaker",
    )
    headshots.add_argument(
        "--outdir",
        default="artifacts/headshots",
        help="Directory to store generated headshots",
    )
    headshots.add_argument(
        "--prompt",
        default=None,
        help="Override the default studio headshot prompt",
    )
    headshots.add_argument(
        "--model",
        default=None,
        help=f"Model override (default: {DEFAULT_MODEL})",
    )
    headshots.add_argument(
        "--aspect-ratio",
        default="1:1",
        help="Aspect ratio hint, e.g. 1:1 or 3:4",
    )
    headshots.add_argument(
        "--image-size",
        default="1K",
        choices=["1K", "2K", "4K"],
        help="Output resolution hint",
    )
    headshots.add_argument(
        "--num-images",
        type=int,
        default=1,
        help="Number of headshots to request",
    )
    headshots.add_argument(
        "--output-name",
        default=None,
        help="Optional filename (without directory) for the first image",
    )
    headshots.add_argument(
        "--no-crop",
        action="store_true",
        help="Skip square center-crop on references",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.version:
        print(__version__)
        return

    if args.command == "headshots":
        frame_paths = [Path(p) for p in args.frames]
        outputs = pipeline.create_headshots(
            frame_paths,
            output_dir=Path(args.outdir),
            prompt=args.prompt or DEFAULT_PROMPT,
            model=args.model or DEFAULT_MODEL,
            aspect_ratio=args.aspect_ratio,
            image_size=args.image_size,
            num_images=args.num_images,
            crop_square=not args.no_crop,
            output_name=args.output_name,
        )
        for path in outputs:
            print(path)
        return

    print("No command specified. Use `podthumb headshots --frames ...` to generate headshots.")


if __name__ == "__main__":
    main()
