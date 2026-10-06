"""Engine-layer errors — independent of Django."""

from __future__ import annotations


class EngineError(Exception):
    """Base class for conversion engine failures."""


class UnsupportedConversionError(EngineError):
    """Raised when a source/target pair is not registered."""


class ConversionFailedError(EngineError):
    """Raised when an engine runs but fails to produce output."""
