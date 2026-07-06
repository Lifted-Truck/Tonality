"""Specification-level errors for the analysis layer.

Analysis functions declare the specification level they require. When a
register-dependent analysis is handed a register-less identity, it must
**error, not guess** a voicing (ROADMAP "cardinal rule"). That error is
:class:`SpecificationError`, raised via the :func:`require_realization` guard.
"""

from __future__ import annotations

from ..core.realization import Realization
from ..core.spec_level import SpecLevel


class InsufficientInformation(ValueError):
    """Raised when the *input carries no evidence for the question* — honest
    absence, not an input error (RE-4d).

    Subclasses ``ValueError`` so every existing consumer try/except keeps
    working; the point of the subclass is the other direction: pipeline code
    that treats "nothing to claim" as a null result (``midi_file_analysis``'s
    ``key_regions: null``) can catch **only** this, so a real input error
    (bad flag combination, malformed events) propagates instead of being
    silently absorbed as "no tonal information". Raise sites: uniform/empty
    pc weights (`infer_key`), no informative window (`track_keys` /
    `track_meter`), metrically-uniform onsets (`infer_meter`).
    """


class SpecificationError(Exception):
    """Raised when analysis is given less specification than it requires.

    Carries the ``required`` and ``actual`` lattice cells (when known) so
    callers — including blind agent callers via MCP — can see exactly what was
    missing rather than receiving an invented result.
    """

    def __init__(
        self,
        message: str,
        *,
        required: SpecLevel | None = None,
        actual: SpecLevel | None = None,
    ) -> None:
        super().__init__(message)
        self.required = required
        self.actual = actual


def require_realization(
    realization: Realization | None,
    *,
    analysis: str,
) -> Realization:
    """Return ``realization`` or raise if register is absent.

    The guard for register-dependent analysis: ``analysis`` names the operation
    for the error message. A :class:`~mts.core.realization.Realization` is
    always registered by construction, so the only failure mode is ``None`` —
    i.e. a caller holding a register-less identity (a PC-set / named chord /
    interval shape) asking for register-dependent output.
    """

    if realization is None:
        raise SpecificationError(
            f"{analysis} requires register (a realization); none was provided. "
            "Reduce never invents: choosing a voicing is a generative act, not "
            "an analytical one.",
        )
    return realization


__all__ = ["InsufficientInformation", "SpecificationError", "require_realization"]
