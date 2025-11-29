# Agent: Orchestration & CLI

Purpose: provide a simple CLI that chains identification → headshots → composition, manages config, and produces manifests. See top-level `AGENTS.md` for project scope/environment/tooling, and the three phase agents for contract details.

## Inputs
- Video path.
- Optional timestamps per speaker.
- Optional template/background and text.
- Model endpoints/keys via env vars.

## Outputs
- Manifests: frames manifest, headshot manifest, final thumbnail path(s).
- Exit codes and logs for each stage.

## Approach
- CLI subcommands implemented: `sample` (stubs to Gemini speaker ID), `headshots` (Gemini 3 Pro Image Preview), `compose` (Gemini 3 Pro Image Preview two-up thumbnail).
- Env loading: auto-load `.env` from repo/win/.env/cwd/home before commands; flags allow API key override.
- Caching: headshots and compose both cache locally by hashed inputs to avoid repeat calls.
- Outputs: headshots to `artifacts/headshots/`, thumbnails to `artifacts/thumbnails/`; manifests still TBD.
- Prompt signature is included in the compose cache hash to ensure text/layout changes invalidate cache.

## Open Questions
- Should we add a `run` command to chain sample→headshots→compose with manifests?
- Manifest schemas and locations for headshots/thumbnails?
- Need parallelism/batching or retries around Gemini calls?

## Next Actions
- Define and write manifest schemas (speakers, headshots, thumbnails) so stages chain cleanly.
- Add `run` command with optional dry-run, and a `--config` loader.
- Optional: retry/backoff wrappers and verbose logging flags.

## If you take over this agent
- Read top-level `AGENTS.md` plus each phase agent to align inputs/outputs.
- Keep manifests under `manifests/` and artifacts under `artifacts/` to stay consistent.
- Ensure CLI flags map cleanly to downstream function params; avoid hidden defaults.
