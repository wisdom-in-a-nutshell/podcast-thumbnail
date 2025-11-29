# Podcast Thumbnail Agent Guide

This repo builds a simple pipeline to produce podcast thumbnails from an edited video.

## Goal
1) Sample video frames (via ffmpeg) per speaker/timestamp. 2) Generate clean headshots (Gemini Nano Banana Pro / Gemini 3 Pro as external API). 3) Compose a thumbnail (headshots + background + short text) at YouTube-friendly dimensions.

## Current State
- Python scaffold in `src/` with subpackages for `orchestration_cli`, `speaker_identification`, `headshot_generation`, `thumbnail_composition`. CLI entry is `python -m orchestration_cli.cli`.
- Implemented headshot generation via Gemini 3 Pro Image Preview (Nano Banana Pro), with auto env loading, prompt to remove headgear, and local caching by hash of refs/prompt/model.
- Implemented thumbnail composition via Gemini 3 Pro Image Preview: takes 2+ headshots + title text, optional background, generates 16:9 thumbnail; local cache keyed by inputs.
- Frame sampling exists via ffmpeg helper; speaker identification helper present; manifests still minimal.
- MCP: Gemini docs MCP installed (disabled by default), Context7 available; use `codex-gemini` alias to enable both + web search.

## Per-Agent Guides (paths)
- Speaker identification: `src/speaker_identification/AGENTS.md`
- Headshot generation: `src/headshot_generation/AGENTS.md`
- Thumbnail composition: `src/thumbnail_composition/AGENTS.md`
- Orchestration/CLI: `src/orchestration_cli/AGENTS.md`

## Environment & Tools
- Use Python 3.11 venv + pip (keep it simple). Install: `python3 -m venv .venv && source .venv/bin/activate && python3 -m pip install -e .[dev]`.
- ffmpeg is assumed installed system-wide; call via subprocess (or `ffmpeg-python` if added later).
- Image ops: plan to use Pillow; optional OpenCV for face crops if needed. Keep deps minimal.
- MCP helpers:
  - Gemini docs server: binary at `/Users/adi/Library/Python/3.11/bin/gemini-docs-mcp`.
  - Alias `codex-gemini` -> enables gemini_docs + context7 + web search.

## Suggested Implementation Steps
1) (Done) Frame sampling helper exists (ffmpeg).
2) (Done) Headshot gen: Gemini 3 Pro Image Preview; prompt removes headgear; square-crops refs; cached outputs; CLI `headshots` subcommand.
3) (Done) Thumbnail composition: Gemini 3 Pro Image Preview; uses headshots + text (and optional background); cached outputs; CLI `compose` subcommand.
4) Speaker ID: stub exists; integrate manifests so `sample → headshots → compose` can chain cleanly.
5) Config: auto-loads `.env` (repo, win/.env, cwd, home). Consider manifest schemas and `run` pipeline command next.

## Open Questions for User
- Will you supply exact timestamps per speaker, or should we auto-sample at fixed intervals and cluster faces locally?
- Desired thumbnail specs: resolution (1280x720?), file format (PNG/JPEG), font/color preferences, logos?
- Background source for compose (user-provided vs gradient)?
- Do we need a `run` command to chain sample→headshots→compose with manifests?

## Quick Commands
- Activate venv: `source .venv/bin/activate`
- Install dev deps: `python3 -m pip install -e .[dev]`
- CLI smoke test: `podthumb --version`
- Run Codex with Gemini docs + Context7: `codex-gemini /status`
