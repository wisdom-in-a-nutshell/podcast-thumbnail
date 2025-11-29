# Agent: Thumbnail Composition

Purpose: combine headshots, background, and short text into a final thumbnail asset. See top-level `AGENTS.md` for project scope, context, and tooling.

## Inputs
- Headshot images per speaker (PNG preferred).
- Background image (optional; fallback gradient).
- Short text (5–6 words) supplied by user.
- Optional template config (positions, fonts, colors) — currently not required when using Gemini.

## Outputs
- Final thumbnail image (default 1280x720, PNG) generated via Gemini 3 Pro Image Preview.
- Optional cached file reuse when inputs match.

## Approach
- Use Gemini 3 Pro Image Preview to compose: prompt enforces two-up layout, removes headgear, preserves likeness. Templates provide style cues.
- Inputs passed as reference images (2–4 headshots + optional background + optional style reference) plus text embedded in prompt.
- Templates: `diary_ceo` (dark backdrop, slight inward head tilt, bold white text with red highlight blocks, no "NEW" tag), `clean_two_up` (neutral gradient, bold sans title).
- Local cache keyed on model+text+aspect+refs+template+(background/style ref) to avoid duplicate calls.
- Outputs saved under `artifacts/thumbnails/thumb_<hash>.png`.

## Open Questions
- Brand guidelines? Fonts/colors/logo lockups to respect?
- Required format (PNG vs JPEG) and max file size?
- Need mobile-safe variants (e.g., square 1080x1080)?
- Should we support a manual (Pillow) path as fallback if Gemini quota is hit?

## Next Actions
- Optional: add manifest schema for thumbnails (inputs, prompt hash, output path).
- Add CLI flags for square/9:16 variants if needed.
- Consider a deterministic seed if/when Gemini image preview exposes it.

## If you take over this agent
- Read top-level `AGENTS.md` and `headshot_generation/AGENTS.md` to align inputs.
- Expect headshot manifest at `manifests/headshots.json`; write outputs to `artifacts/thumbnails/`.
- Keep at least one default template and font bundled or documented.
