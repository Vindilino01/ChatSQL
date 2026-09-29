"""Compatibilidade: o Motor Offline agora vive em `chat_sql.nl`."""

from .nl.engine import OfflineEngine, OfflineResult
from .nl.text import normalize, singular
from .nl.text import strip_accents as _strip_accents

__all__ = ["OfflineEngine", "OfflineResult", "normalize", "singular", "_strip_accents"]
