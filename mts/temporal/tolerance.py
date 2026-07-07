"""Performed-input tolerance: onset coalescing + optional grid snap (gap 12).

The temporal analyses treat onsets as exact, so humanized/performed MIDI is
*misread, not refused*: ~5 ms of chord jitter fragments segmentation into
micro-segments with garbage transitional pc sets, reads on-the-beat notes as
off-grid subdivisions, and splinters voice-pair moments (theory-grounding
review pass #1, finding 1). This module is the explicit, **opt-in** repair —
nothing in the engine calls it for you, exactness stays exact by default,
and the result cites the parameters used (the window-geometry contract).

``coalesce(sequence, onset_window_beats=w)``:

- collects every time point (onsets *and* offsets — note endings make
  segmentation boundaries too, and coalescing both heals the tiny gaps and
  overlaps of performed legato);
- clusters greedily over the sorted points: a point joins the open cluster
  while it lies within ``w`` of the cluster's **anchor** (its earliest
  point) — anchoring prevents unbounded chaining, and the earliest attack
  is the perceived onset of a spread chord;
- snaps every event's onset/offset to its cluster anchor; with
  ``snap_grid_beats=g`` the anchors are then snapped to the nearest multiple
  of ``g``;
- events whose coalesced duration collapses to nothing (notes shorter than
  the jitter window, e.g. grace notes) are **dropped and reported** — the
  caller opted into lossy preprocessing and gets the loss itemized, never
  hidden.

This is deliberately a *preprocessing pass returning a new Sequence*, not a
behavior switch inside the analyses: every downstream analysis (segmentation,
atoms, key tracking, rulesets) benefits without learning a tolerance
parameter, and the provenance of the cleanup is one explicit call site.
Consumers who already coalesce client-side (Audiology, ~60 ms) can keep
doing so — same contract, either side of the wire.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, replace

from .sequence import Event, Sequence

_EPS = 1e-9


@dataclass(frozen=True)
class DroppedEvent:
    """An event lost to coalescing (shorter than the jitter window)."""

    onset: float
    duration: float
    midi: int
    voice: str | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class CoalesceResult:
    """The cleaned sequence plus the cited parameters and what changed."""

    sequence: Sequence
    onset_window_beats: float
    snap_grid_beats: float | None
    moved_events: int
    max_shift_beats: float
    dropped: tuple[DroppedEvent, ...]

    def to_dict(self) -> dict:
        """Parameters + evidence (the sequence itself is not JSON; events are
        re-exported by callers that need them on the wire)."""
        return {
            "onset_window_beats": self.onset_window_beats,
            "snap_grid_beats": self.snap_grid_beats,
            "moved_events": self.moved_events,
            "max_shift_beats": self.max_shift_beats,
            "dropped": [d.to_dict() for d in self.dropped],
        }


def _cluster_anchors(points: list[float], window: float) -> dict[float, float]:
    """Map each distinct time point to its cluster anchor (earliest member)."""

    mapping: dict[float, float] = {}
    anchor: float | None = None
    for point in sorted(set(points)):
        if anchor is None or point - anchor > window + _EPS:
            anchor = point
        mapping[point] = anchor
    return mapping


def coalesce(
    sequence: Sequence,
    *,
    onset_window_beats: float,
    snap_grid_beats: float | None = None,
) -> CoalesceResult:
    """Coalesce near-simultaneous time points (and optionally snap to a grid).

    ``onset_window_beats`` ≥ 0 (0 = no coalescing, snap only);
    ``snap_grid_beats`` > 0 when given. At least one of the two must be
    active — a no-op call is a caller error, not a silent identity.
    """

    if onset_window_beats < 0:
        raise ValueError("onset_window_beats must be >= 0.")
    if snap_grid_beats is not None and snap_grid_beats <= _EPS:
        raise ValueError("snap_grid_beats must be positive.")
    if onset_window_beats <= _EPS and snap_grid_beats is None:
        raise ValueError(
            "Nothing to do: set onset_window_beats > 0 and/or snap_grid_beats."
        )

    points = [e.onset for e in sequence.events] + [e.offset for e in sequence.events]
    mapping = _cluster_anchors(points, onset_window_beats)
    if snap_grid_beats is not None:
        g = snap_grid_beats
        mapping = {p: max(0.0, int(a / g + 0.5) * g) for p, a in mapping.items()}

    kept: list[Event] = []
    dropped: list[DroppedEvent] = []
    moved = 0
    max_shift = 0.0
    for event in sequence.events:
        new_onset = mapping[event.onset]
        new_offset = mapping[event.offset]
        if new_offset - new_onset <= _EPS:
            dropped.append(
                DroppedEvent(event.onset, event.duration, event.pitch.midi, event.voice)
            )
            continue
        shift = max(abs(new_onset - event.onset), abs(new_offset - event.offset))
        if shift > _EPS:
            moved += 1
            max_shift = max(max_shift, shift)
            kept.append(
                replace(event, onset=new_onset, duration=new_offset - new_onset)
            )
        else:
            kept.append(event)

    return CoalesceResult(
        sequence=Sequence(
            events=tuple(sorted(kept, key=lambda e: (e.onset, e.pitch.midi))),
            tempo=sequence.tempo,
            meter=sequence.meter,
        ),
        onset_window_beats=onset_window_beats,
        snap_grid_beats=snap_grid_beats,
        moved_events=moved,
        max_shift_beats=max_shift,
        dropped=tuple(dropped),
    )


__all__ = ["CoalesceResult", "DroppedEvent", "coalesce"]
