"""Conversion engine contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ConversionPair:
    """Explicit source → target registration entry."""

    source: str
    target: str
    label: str
    best_effort: bool = False
    max_bytes: int = 25 * 1024 * 1024
    timeout_sec: int = 120
    category: str = "documents"


class ConversionEngine(Protocol):
    """Protocol every converter must satisfy (Dependency Inversion)."""

    source_format: str
    target_format: str

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        """Convert ``source_path`` into ``destination_path`` and return it."""
        ...
