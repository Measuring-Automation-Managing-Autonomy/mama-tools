"""Typed errors for mama-tools. Fail closed on structural problems."""
from __future__ import annotations


class MamaToolsError(Exception):
    """Base class for all mama-tools errors."""


class RecordValidationError(MamaToolsError):
    """A use-case record (or other document) failed schema/cross-checks."""


class MetricError(MamaToolsError):
    """A metric calculation could not be performed honestly."""


class AutonomyUnavailable(MamaToolsError):
    """Autonomy inputs requested but mama-integrations is not installed."""
