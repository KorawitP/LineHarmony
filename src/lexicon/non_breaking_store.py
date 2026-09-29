"""
Non-breaking words storage interface and helpers.
"""

from __future__ import annotations

from typing import Iterable, Protocol, Set, Tuple


class NonBreakingStore(Protocol):
    def get_all(self) -> Set[str]:
        ...

    def add(self, words: Iterable[str]) -> Tuple[int, int]:
        """Add words; returns (added, skipped)."""
        ...

    def remove(self, words: Iterable[str]) -> int:
        """Remove words; returns removed count."""
        ...

    def save(self) -> None:
        ...


def normalize_word(w: str) -> str:
    """Normalize a word for storage: trim and keep non-empty only."""
    if w is None:
        return ""
    w = w.strip()
    return w

