# Agent: Headshot Generation

Purpose: take representative frames per speaker and produce clean headshot images (ideally transparent background) using the external headshot model (Gemini Nano Banana Pro / Gemini 3 Pro pipeline). See top-level `AGENTS.md` for overall scope, context, and tooling.

## Inputs
- Frame paths per speaker (from speaker_identification manifest).
- Optional crop hints (face boxes) if precomputed.

## Outputs
- Headshot image per speaker (PNG preferred, transparent BG if model supports it).
- Updated manifest linking speaker IDs to headshot paths.

## Approach
- Preprocess: crop faces from frames (OpenCV/mediapipe) to reduce background; ensure square aspect and sufficient resolution (>=512px on shortest side).
- Model call: treat the headshot model as an external API/CLI stub. Package multiple reference crops; request one cleaned headshot (PNG, transparent if supported).
- Validation: basic quality checks (min dimensions, face present, optional transparency); retry with alternate frame if needed.

## Open Questions
- Exact API contract for the headshot model (endpoint, auth, expected payload/response format)?
- Desired output size (e.g., 512x512 or 1024x1024) and background (transparent vs solid)?
- Should we store intermediates and retries, or only the best headshot per speaker?

## Next Actions
- Implement `create_headshots(frame_paths)` in `orchestration_cli/pipeline.py` (or a dedicated helper) to call external model; accept a dry-run mode that just copies/crops inputs.
- Add CLI `podthumb headshots --frames-manifest ... --outdir ... --dry-run`.
- Write manifest `manifests/headshots.json` linking speaker IDs to headshot paths and source frames.

## If you take over this agent
- Read top-level `AGENTS.md` and `speaker_identification/AGENTS.md` to align on manifests.
- Keep inputs from `manifests/speakers.json`; outputs under `artifacts/headshots/` and `manifests/headshots.json`.
- Document the exact API contract once known; keep a mock/dry-run path for offline use.
