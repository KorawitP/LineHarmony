"""
JSON-backed implementation for NonBreakingStore.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Set, Tuple

from .non_breaking_store import NonBreakingStore, normalize_word


class JSONNonBreakingStore(NonBreakingStore):
    def __init__(self, json_path: str | Path):
        self._path = Path(json_path)
        self._words: Set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._words = set()
            return
        try:
            with self._path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            words = data.get("non_breaking_words", []) if isinstance(data, dict) else []
            cleaned = {normalize_word(w) for w in words if isinstance(w, str)}
            self._words = {w for w in cleaned if w}
        except Exception:
            # On malformed file, keep empty set to avoid crash
            self._words = set()

    def get_all(self) -> Set[str]:
        return set(self._words)

    def add(self, words: Iterable[str]) -> Tuple[int, int]:
        added = 0
        skipped = 0
        for w in words:
            nw = normalize_word(w)
            if not nw:
                skipped += 1
                continue
            if nw in self._words:
                skipped += 1
                continue
            self._words.add(nw)
            added += 1
        return added, skipped

    def remove(self, words: Iterable[str]) -> int:
        removed = 0
        for w in words:
            nw = normalize_word(w)
            if not nw:
                continue
            if nw in self._words:
                self._words.remove(nw)
                removed += 1
        return removed

    def save(self) -> None:
        data = {
            "non_breaking_words": sorted(self._words)
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

