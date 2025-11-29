"""CLI entry point for the podcast thumbnail toolchain.

This is intentionally minimal for now. Flesh out subcommands once
frame sampling, headshot extraction, and thumbnail composition are wired.
"""

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Podcast thumbnail helper")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.version:
        from . import __version__

        print(__version__)
        return

    print("podcast-thumbnail: CLI stubs ready. Add commands for frames/headshots/thumbnails.")


if __name__ == "__main__":
    main()
