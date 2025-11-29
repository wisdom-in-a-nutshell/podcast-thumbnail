"""Package for headshot generation components."""

from .gemini_client import DEFAULT_MODEL, DEFAULT_PROMPT, generate_headshot

__all__ = ["generate_headshot", "DEFAULT_PROMPT", "DEFAULT_MODEL"]
