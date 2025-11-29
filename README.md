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

For rapid checkpoints, run `./scripts/auto_commit_push.sh [branch] [commit message]` (defaults to current branch and a timestamped message). Example cron every 15 minutes:

```
*/15 * * * * /Users/adi/GitHub/podcast-thumbnail/scripts/auto_commit_push.sh main >> /tmp/podthumb-autopush.log 2>&1
```
