# Podcast Thumbnail Agent Guide

This repo builds a simple pipeline to produce podcast thumbnails from an edited video.

## Goal
1) Sample video frames (via ffmpeg) per speaker/timestamp. 2) Generate clean headshots (Gemini Nano Banana Pro / Gemini 3 Pro as external API). 3) Compose a thumbnail (headshots + background + short text) at YouTube-friendly dimensions.

## Current State
- Python scaffold in `src/` with subpackages for `orchestration_cli`, `speaker_identification`, `headshot_generation`, `thumbnail_composition`. CLI stub `podthumb` lives in `orchestration_cli/cli.py`; pipeline stubs in `orchestration_cli/pipeline.py`.
- No real logic yet; ffmpeg/headshot/compositor are NotImplemented.
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
1) Frame sampling: implement `sample_frames(video_path, timestamps)` using ffmpeg (`ffmpeg -ss <t> -i <video> -vframes 1 -q:v 2 frame_<t>.jpg`). Accept list of floats; return saved paths.
2) Headshot prep: crop faces from sampled frames (OpenCV/face detection) and export clean crops for the external headshot model; treat the model call as a stub (`create_headshots` taking frame paths and returning output paths from the model).
3) Thumbnail composition: use Pillow to place headshots on a background (1280x720 default), add provided 5–6 word text overlay; allow a simple JSON/YAML template for positions/colors/fonts.
4) CLI: add subcommands `sample`, `headshots`, `compose`, with input/output dirs and JSON for timestamps/speakers.
5) Config: allow env vars for model endpoints/keys; keep defaults local.

## Open Questions for User
- Will you supply exact timestamps per speaker, or should we auto-sample at fixed intervals and cluster faces locally?
- Desired thumbnail specs: resolution (1280x720?), file format (PNG/JPEG), font/color preferences, logos?
- How should headshot model be invoked (HTTP endpoint, local CLI)? Expected inputs/outputs?
- Do we need to auto-generate the 5–6 word text, or will it always be provided?

## Quick Commands
- Activate venv: `source .venv/bin/activate`
- Install dev deps: `python3 -m pip install -e .[dev]`
- CLI smoke test: `podthumb --version`
- Run Codex with Gemini docs + Context7: `codex-gemini /status`
