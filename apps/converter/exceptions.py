"""Application-layer conversion exceptions."""

from __future__ import annotations


class ConversionServiceError(Exception):
    """Base service error shown to the user as a form/message error."""


class InvalidUploadError(ConversionServiceError):
    pass


class JobNotReadyError(ConversionServiceError):
    pass
