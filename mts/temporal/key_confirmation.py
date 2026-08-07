"""Cadence-confirmed key areas (gap 25, the shippable slice).

Joins two things the engine already computed but never pointed at each other:
**structural key areas** (``reduce_to_structural_keys``) and **cadence detection**
(``detect_cadences``). For each area, the chords inside it are evaluated against
**that area's own key** — asking the question the theory literature names as the
single strongest modulation discriminator:

    *does this key area contain a cadence confirming its own tonic?*

Open Music Theory states the test directly: **a tonicization does not incorporate
a cadence in the tonicized key; a modulation does.** Before this, the area-level
tonicization-vs-modulation call in ``structural_key`` used only windowed
pitch-class correlation plus duration/relatedness/return heuristics — it had **no
awareness of cadences at all**, and ``detect_cadences`` was never run against an
area's key. The research swarm flagged this as the highest-leverage, lowest-risk
piece of the borrowed-vs-modulation problem: the discriminator was already
implemented, just disconnected.

**Evidence, not a verdict** — the load-bearing distinction:

- a cadence-confirmed area is **strong positive evidence** of a genuine modulation;
- an unconfirmed area is **NOT proof of a tonicization**. It is the *absence of the
  strongest signal*, which is much weaker than its negation — plenty of real
  modulations are confirmed by means other than a textbook cadence (a sustained
  new collection, a phrase boundary, a pedal).

So this module reports both sides with their evidence and **never collapses to
"this is a modulation"**. Committing to that label needs a cost model the caller
supplies, or the learned sibling (ROADMAP Decisions 14/15, gap 25).

**Usage trap, measured — the segmentation grid must match the harmonic rhythm.**
``subdivisions`` controls the chord-segmentation grid; if the grid is COARSER than
the chords change, the cadential approach is collapsed into its arrival's window
and the cadence disappears. On a fixture whose chords change every 2 beats in 4/4,
``subdivisions=1`` (one chord per bar) reported *plagal only, unconfirmed*, while
``subdivisions=2`` recovered the **authentic** cadences and confirmed both areas.
Same music, opposite answer. So an "unconfirmed" area is only meaningful when the
grid resolves the harmony — pass ``subdivisions`` to match, and treat a
low ``chords_considered`` relative to the area's duration as a warning that the
grid, not the music, produced the result.

Honest refusals throughout: an area whose mode is outside the functional
vocabulary (major/minor) makes **no claim** (``mode_supported=False``); an area
with too few nameable chords makes **no claim** and says so, rather than reporting
a confident "unconfirmed".
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..analysis.cadence import detect_cadences
from .harmonic_segmentation import segment_to_chords
from .sequence import Sequence
from .structural_key import area_indices, reduce_to_structural_keys

_EPS = 1e-9


@dataclass(frozen=True)
class AreaConfirmation:
    """One structural key area and the cadential evidence for its own tonic."""

    start_beats: float
    end_beats: float
    tonic_pc: int
    mode: str
    duration_beats: float
    chords_considered: int
    cadence_types: list[str]        # every formula found IN THIS AREA'S KEY
    has_authentic: bool             # the strongest confirmation
    has_final_authentic: bool       # authentic arriving on the area's last chord
    confirmed: bool                 # an authentic cadence in its own key
    claim_possible: bool            # False ⇒ no evidence either way (see reason)
    reason: str | None              # why no claim could be made

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class KeyAreaConfirmationResult:
    """Every structural key area, with its cadence evidence.

    ``confirmed_areas`` / ``unconfirmed_areas`` count only areas where a claim was
    possible; ``no_claim_areas`` are reported separately so an absence of evidence
    is never silently counted as evidence of absence.
    """

    home_tonic_pc: int
    home_mode: str
    areas: list[AreaConfirmation]
    confirmed_areas: int
    unconfirmed_areas: int
    no_claim_areas: int

    def to_dict(self) -> dict:
        return {
            "home_tonic_pc": self.home_tonic_pc,
            "home_mode": self.home_mode,
            "areas": [a.to_dict() for a in self.areas],
            "confirmed_areas": self.confirmed_areas,
            "unconfirmed_areas": self.unconfirmed_areas,
            "no_claim_areas": self.no_claim_areas,
        }


def confirm_key_areas(
    sequence: Sequence,
    *,
    structural: "object | None" = None,
    subdivisions: int = 1,
    session=None,
) -> KeyAreaConfirmationResult:
    """Cadence evidence for each structural key area, in that area's own key.

    ``structural`` reuses an existing ``StructuralKeyResult`` (avoids recomputing
    the windowed track); otherwise one is derived. ``subdivisions`` is passed to
    the chord segmentation. Raises on an empty sequence.
    """

    if not sequence.events:
        raise ValueError("confirm_key_areas needs a non-empty sequence.")

    result = structural if structural is not None else reduce_to_structural_keys(sequence)

    # Chord spans are named per window and are key-INDEPENDENT, which is what lets
    # each area be judged against its own tonic rather than a single global key.
    segmentation = segment_to_chords(sequence, subdivisions=subdivisions, session=session)
    spans = [s for s in segmentation.spans if s.root_pc is not None]

    # Bucket every span into its area in one pass. Previously each area rescanned
    # the whole span list — O(areas x spans), quadratic since both grow with the
    # piece (audit #256).
    inside_area: list[list] = [[] for _ in result.areas]
    for span, index in zip(spans, area_indices(result.areas, [s.start_beat for s in spans])):
        if index is not None:
            inside_area[index].append(span)

    areas: list[AreaConfirmation] = []
    for area, inside in zip(result.areas, inside_area):
        chords = [(s.root_pc, s.quality) for s in inside]
        base = dict(
            start_beats=area.start_beats,
            end_beats=area.end_beats,
            tonic_pc=area.tonic_pc,
            mode=area.mode,
            duration_beats=round(area.duration_beats, 9),
            chords_considered=len(chords),
        )

        if len(chords) < 2:
            areas.append(AreaConfirmation(
                **base, cadence_types=[], has_authentic=False, has_final_authentic=False,
                confirmed=False, claim_possible=False,
                reason="fewer than two nameable chords in the area — a cadence needs "
                       "an approach and an arrival, so no claim either way",
            ))
            continue

        cadences = detect_cadences(chords, tonic_pc=area.tonic_pc, mode=area.mode)
        if not cadences.mode_supported:
            areas.append(AreaConfirmation(
                **base, cadence_types=[], has_authentic=False, has_final_authentic=False,
                confirmed=False, claim_possible=False,
                reason=f"mode {area.mode!r} is outside the functional vocabulary "
                       "(major/minor only) — roles are not claimed, so no cadence claim",
            ))
            continue

        types = [c.type for c in cadences.cadences]
        authentic = [c for c in cadences.cadences if c.type == "authentic"]
        final_authentic = any(c.arrival_index == len(chords) - 1 for c in authentic)
        areas.append(AreaConfirmation(
            **base,
            cadence_types=types,
            has_authentic=bool(authentic),
            has_final_authentic=final_authentic,
            confirmed=bool(authentic),
            claim_possible=True,
            reason=None if authentic else (
                "no authentic cadence in this area's own key — the ABSENCE of the "
                "strongest confirming signal, which is weaker evidence than its "
                "negation (a real modulation may be confirmed by other means)"
            ),
        ))

    claimable = [a for a in areas if a.claim_possible]
    return KeyAreaConfirmationResult(
        home_tonic_pc=result.home_tonic_pc,
        home_mode=result.home_mode,
        areas=areas,
        confirmed_areas=sum(1 for a in claimable if a.confirmed),
        unconfirmed_areas=sum(1 for a in claimable if not a.confirmed),
        no_claim_areas=len(areas) - len(claimable),
    )


__all__ = ["AreaConfirmation", "KeyAreaConfirmationResult", "confirm_key_areas"]
