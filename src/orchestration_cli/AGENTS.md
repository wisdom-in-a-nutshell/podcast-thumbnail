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
- CLI subcommands: `sample`, `headshots`, `compose`, plus a `run` that chains all.
- `sample`: calls speaker_identification helpers to extract frames and manifest.
- `headshots`: consumes frames manifest, calls headshot generator (or dry-run copies).
- `compose`: consumes headshots manifest + text/background/template to render thumbnail.
- Config: accept JSON/YAML configs; allow env overrides for model URLs/keys.
- Logging: concise stdout logs; optional verbose mode. Keep artifacts/manifests in predictable folders.

## Open Questions
- Should `run` auto-clean temp files or keep all intermediates?
- Preferred manifest schema and file locations?
- Need parallelism or batching for model calls?

## Next Actions
- Flesh out `podthumb` CLI with subcommands and wiring to pipeline stubs.
- Define manifest schemas under `manifests/` (JSON examples) and ensure all agents reference them.
- Add `--config` flag to load a single JSON/YAML file and `--dry-run` for headshots.

## If you take over this agent
- Read top-level `AGENTS.md` plus each phase agent to align inputs/outputs.
- Keep manifests under `manifests/` and artifacts under `artifacts/` to stay consistent.
- Ensure CLI flags map cleanly to downstream function params; avoid hidden defaults.
