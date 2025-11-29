"""Prompt template for Gemini-based speaker identification."""

from __future__ import annotations


def build_prompt(timestamps_per_speaker: int) -> str:
    return f"""
You are selecting frames for clean headshots to build a podcast thumbnail.
Input: one edited podcast video.

Tasks:
1) Identify each distinct speaker (person) appearing in the video.
2) For each speaker, choose {timestamps_per_speaker} timestamps (seconds, ascending) that give the best waist-up candidates:
   - Face is frontal or 3/4, well-lit, sharp focus, minimal motion blur.
   - Include head AND shoulders AND upper torso (waist/chest up), not a face-only crop.
   - Avoid occlusions, cut-off faces, extreme angles, or heavy overlays.
3) Add a short visual note per speaker (e.g., "male, beard, glasses, dark hoodie").
4) Mark likely role if obvious: host | guest | unknown. Only one host should be marked host unless clearly multiple hosts.
5) Return confidence 0–1 for each speaker grouping.
6) For EACH chosen timestamp, return a face bounding box (relative coords 0–1) so we can crop later.
7) Do NOT include images—only metadata.

Return JSON ONLY in this schema (no prose):
{{
  "speakers": [
    {{
      "id": "speaker_1",
      "role": "host|guest|unknown",
      "note": "short visual description",
      "confidence": 0.92,
      "frames": [
        {{
          "timestamp_s": 12.3,
          "bbox": {{"x1": 0.25, "y1": 0.18, "x2": 0.65, "y2": 0.92}}
        }}
      ]
    }}
  ]
}}

If two clusters seem to be the same person, merge and pick the best {timestamps_per_speaker} frames overall.
Ensure bounding boxes tightly enclose the face; coordinates are normalized to [0,1] relative to the frame (x1< x2, y1< y2).
"""
