# podcast-thumbnail

Barebones Python package scaffold for a podcast thumbnail pipeline.

## Setup

- Install editable: `python3 -m pip install -e .`
- Optional dev tools: `python3 -m pip install -e .[dev]`

## CLI

- `podthumb --version` prints the package version.
- More commands will be added as frame sampling, headshot generation, and thumbnail composition are implemented.

## License

MIT

## Auto push helper

For rapid checkpoints, run `./scripts/auto_commit_push.sh [branch] [interval_seconds] [commit prefix]` (defaults: current branch, 900s, `"Auto checkpoint"`). It stays running and pushes on the interval until you exit (Ctrl+C). Example: `./scripts/auto_commit_push.sh main 300 "Hackathon checkpoint"`.
