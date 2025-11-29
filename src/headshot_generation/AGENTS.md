# Agent: Headshot Generation

Purpose: take representative frames per speaker and produce clean headshot images (ideally transparent background) using the external headshot model (Gemini 3 Pro Image Preview / "Nano Banana Pro"). See top-level `AGENTS.md` for overall scope, context, and tooling.

## Inputs
- Frame paths per speaker (from speaker_identification manifest).
- Optional crop hints (face boxes) if precomputed.

## Outputs
- Headshot image per speaker (PNG preferred, transparent BG if model supports it).
- Updated manifest linking speaker IDs to headshot paths.

## Approach
- Preprocess: center square-crop references; ensure square aspect and min size; convert to RGB.
- Model call: Gemini 3 Pro Image Preview via `google-genai`; prompt enforces studio headshot, removes headphones/earbuds/hats, neutral gradient BG; uses up to 14 refs.
- Caching: local hash cache (model+prompt+refs etc.) saves generated PNGs; CLI supports `--no-cache` to force fresh calls.
- Validation: raises if no images returned; returns saved paths.

## Open Questions
- Preferred output size / aspect beyond 1:1? Need alpha background or solid?
- Whether to keep multiple shots per speaker or just best-one manifest.
- Should we expose seed/consistency controls if Gemini adds it for image preview?

## Next Actions
- Define `manifests/headshots.json` schema and write it from the CLI (speaker id -> headshot path, ref frames, prompt hash).
- Optional: add face-detection crop step for messy inputs.
- Add tests for cache-hit vs miss and env loading.

## If you take over this agent
- Read top-level `AGENTS.md` and `speaker_identification/AGENTS.md` to align on manifests.
- Keep inputs from `manifests/speakers.json`; outputs under `artifacts/headshots/` and `manifests/headshots.json`.
- Document the exact API contract once known; keep a mock/dry-run path for offline use.
