# Agent: Speaker Identification & Timestamps

Purpose: determine how many speakers are present, map them to stable IDs, and capture representative timestamps/frames for each. See the top-level `AGENTS.md` for overall goals, tooling, and aliases.

## Inputs
- Edited podcast video (single file path).
- Optional: user-provided coarse timestamps per speaker.

## Outputs
- JSON with detected speakers and timestamps (e.g., `[{"speaker_id": "spk1", "timestamps": [12.3, 85.1]}]`).
- Saved representative frames per speaker (paths) to feed headshot generation.

## Approach
- Frame sampling: use ffmpeg (`-ss <t> -i <video> -vframes 1 -q:v 2`) at either fixed stride (e.g., every 5–10s) or user-provided timestamps.
- Face detection & clustering: use a lightweight face detector/embedding model (OpenCV/face_recognition/mediapipe) locally; cluster embeddings to assign speaker IDs.
- Deduplicate timestamps: pick 3–5 confident frames per cluster (frontal, well-lit) to reduce noise for headshots.
- Persist metadata: write a JSON manifest with speaker IDs, timestamps, and extracted frame paths (e.g., `manifests/speakers.json`).

## Open Questions
- Do we always receive timestamps per speaker, or should we default to auto-sampling + clustering?
- Minimum/maximum number of frames per speaker to keep? (default: 3–5)
- Any privacy constraints on storing frames?

## Next Actions
- Implement `sample_frames(video_path, timestamps)` in `pipeline.py` using ffmpeg subprocess.
- Add a face-detect/cluster helper to produce `manifests/speakers.json` with stable IDs.
- Wire a CLI subcommand `podthumb sample --video ... --timestamps ... --outdir ...`.

## If you take over this agent
- Read top-level `AGENTS.md` for environment/aliases and the other agent scopes.
- Align manifest schema with downstream headshot/compose agents.
- Keep outputs under `manifests/` and `artifacts/frames/` to keep repo tidy.
