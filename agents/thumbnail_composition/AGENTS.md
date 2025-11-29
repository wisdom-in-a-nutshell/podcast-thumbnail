# Agent: Thumbnail Composition

Purpose: combine headshots, background, and short text into a final thumbnail asset. See top-level `AGENTS.md` for context and tooling.

## Inputs
- Headshot images per speaker (PNG preferred).
- Background image/template (user-provided or default).
- Short text (5–6 words) supplied by user.
- Optional template config (positions, fonts, colors).

## Outputs
- Final thumbnail image (default 1280x720, PNG or JPEG).
- Optional layered/save metadata (JSON) describing placements.

## Approach
- Canvas: default 1280x720; allow override via CLI flags; optionally generate square 1080x1080 variant.
- Layout: simple templates (1-up, 2-up, 3-up) with headshot positions, drop-shadows, and strokes for contrast.
- Text: render with Pillow; pick legible font/size, add outline/box for readability; support user font path.
- Background: user-provided or fallback gradient; ensure contrast with text and faces.
- Export: save to `artifacts/thumbnails/` with naming convention (`thumb_<title_slug>.png`).

## Open Questions
- Brand guidelines? Fonts/colors/logo lockups to respect?
- Required format (PNG vs JPEG) and max file size?
- Need mobile-safe variants (e.g., square 1080x1080)?

## Next Actions
- Implement `compose_thumbnail(background, headshots, text)` using Pillow.
- Add CLI `podthumb compose --headshots ... --text "..." --background ... --out thumb.png --template template.json`.
- Define template JSON structure (positions, sizes, font, colors) under `templates/`.

## If you take over this agent
- Read top-level `AGENTS.md` and `agents/headshot_generation/AGENTS.md` to align inputs.
- Expect headshot manifest at `manifests/headshots.json`; write outputs to `artifacts/thumbnails/`.
- Keep at least one default template and font bundled or documented.
