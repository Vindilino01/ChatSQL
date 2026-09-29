"""Motor offline de linguagem natural para SQL (sem modelo de linguagem)."""

from .engine import OfflineEngine, OfflineResult
from .text import normalize, singular, strip_accents

__all__ = ["OfflineEngine", "OfflineResult", "normalize", "singular", "strip_accents"]
