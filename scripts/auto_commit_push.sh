#!/usr/bin/env bash

# Auto-add, commit, and push changes in this repo on a loop. Useful for quick hackathon checkpoints.
# Usage: ./scripts/auto_commit_push.sh [branch] [interval_seconds] [commit prefix]
# Stops when you exit (Ctrl+C).

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"
interval="${2:-900}"
prefix="${3:-Auto checkpoint}"

echo "Auto committing to branch '$branch' every ${interval}s. Press Ctrl+C to stop."

trap 'echo "Stopping auto commits."' INT TERM

while true; do
  if git diff --quiet --ignore-submodules HEAD -- && git diff --quiet --ignore-submodules --cached --; then
    echo "$(date -u +%FT%TZ) - No changes to commit."
  else
    message="$prefix $(date -u +%FT%TZ)"
    git add -A
    git commit -m "$message"
    git push origin "$branch"
    echo "$(date -u +%FT%TZ) - Pushed '$message'."
  fi
  sleep "$interval"
done
