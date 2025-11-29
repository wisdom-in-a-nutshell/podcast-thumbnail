#!/usr/bin/env bash

# Auto-add, commit, and push changes in this repo. Useful for quick hackathon checkpoints.
# Usage: ./scripts/auto_commit_push.sh [branch] [commit message]

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"
message="${2:-Auto checkpoint $(date -u +%FT%TZ)}"

if git diff --quiet --ignore-submodules HEAD -- && git diff --quiet --ignore-submodules --cached --; then
  echo "No changes to commit."
  exit 0
fi

git add -A
git commit -m "$message"
git push origin "$branch"
