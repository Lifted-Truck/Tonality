"""Chromatic-event classification (gap 25 slice 2 — the composite).

Answers, at the **chord grain**, the question gap 25 opened: *this chord has
notes outside its key area — is that a borrowed chord, an applied dominant, or
the seam of a key change?* It does so by **reading** the layers that already
compute the bearing signals rather than re-deriving any of them:

===========================  ====================================================
signal                       read from
===========================  ====================================================
structural key areas         ``reduce_to_structural_keys`` (versioned thresholds)
absorbed tonicizations       the same result's ``area.tonicizations``
cadence in the area's key    ``confirm_key_areas`` (gap 25 slice 1)
the chord stream             ``segment_to_chords``
special chromatic function   ``name_chord``'s ``function_category`` seam,
                             **re-read in the area's own key** — a chord's
                             special function is key-relative, and the
                             segmentation names every window in one global key
===========================  ====================================================

**Why no single label.** The research swarm's verdict was that a single-label
oracle is *impossible*: trained analysts disagree on a real fraction of passages
given the full score, the DCML standard leaves the call to human discretion, and
full Roman-numeral analysis plateaus at ~45–52% precisely at this seam. What is
squarely computable is (a) every bearing signal and (b) **the boundary of the
contested band**. So this emits a **plural** list of readings, each carrying the
exact tests it passed, plus a ``confident``/``contested`` zone with its
**coordinates** — the measured numbers next to the stated thresholds that
produced the zone, never a feeling.

``single_label`` is the honest refusal made mechanical: it is a label **only**
when the zone is ``confident`` *and* exactly one reading fired. Inside the
contested band it is ``None`` with a reason. Committing past that band needs a
caller-supplied cost model, or the learned sibling (ROADMAP Decisions 14/15).

**"Genuinely ambiguous" is a zone here, not a label** — a deliberate departure
from gap 25's first sketch, which listed it alongside ``borrowed_mixture`` and
friends. Ambiguity is a statement about the *evidence*, not about the chord;
putting it in the same list would make it read as a competing hypothesis, and a
caller taking ``readings[0]`` would silently treat "we cannot tell" as "we can".

**The readings and their tests** (any number may fire; they are not exclusive):

``borrowed_mixture``
    every foreign pc of the chord belongs to the **parallel mode's** collection.
``secondary_dominant`` / ``augmented_sixth_*`` / ``neapolitan``
    ``name_chord``'s special-function seam, read in the area's key. A secondary
    dominant gains a second signal when the **next** chord actually realizes the
    predicted down-a-fifth resolution — a sequential test the single-chord namer
    structurally cannot make, and the composite's real value-add.
``tonicization``
    the chord lies inside a region the structural reduction already **absorbed**
    as a tonicization of this area.
``modulation``
    the chord sits within one chord-window of a structural area boundary **that
    has another area across it** (the piece's own first and last edges are not
    seams), and gains a second signal when the area across that boundary is
    **cadence-confirmed in its own key** (the literature's #1 discriminator).

Readings are ordered by signal count then name. **Signal count is a tally of
independent tests passed, not a probability** — do not read it as one.

Honest limits, stated: the parallel-mode test uses the natural parallel
collection, so mixture drawn from harmonic/melodic minor is not claimed as
mixture (it usually surfaces via the special-function seam instead); and every
chromatic event is only as fine as the segmentation grid — see
``confirm_key_areas`` for the measured grid trap, which applies verbatim here.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..analysis.naming import name_chord
from ..analysis.results import KeyCandidate
from .harmonic_segmentation import segment_to_chords
from .key_confirmation import confirm_key_areas
from .sequence import Sequence
from .structural_key import _MODE_SCALE, _diatonic_pcs, reduce_to_structural_keys

_EPS = 1e-9

#: Zone triggers, each a stated test — see ``ChromaticEvent.contested_reasons``.
CONTESTED_COMPETING = "competing readings: more than one test fired"
CONTESTED_NONE = (
    "no reading: chromatic content that none of this classifier's tests explain"
)
CONTESTED_FLOOR = (
    "the area's duration sits within tolerance of the versioned "
    "min_modulation_beats floor, so the upstream tonicization-vs-modulation "
    "call is itself on a knife edge"
)


@dataclass(frozen=True)
class Reading:
    """One hypothesis for a chromatic event, with the exact tests it passed."""

    label: str
    signals: list[str]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class ChromaticEvent:
    """One chord whose content leaves its key area, and what that might mean."""

    start_beat: float
    end_beat: float
    bar: int
    root_pc: int
    quality: str
    area_tonic_pc: int
    area_mode: str
    foreign_pcs: list[int]          # chord pcs outside the area's diatonic collection
    position: str                   # "interior" | "boundary"
    beats_to_boundary: float | None  # None ⇒ the area has no seam (single-area piece)
    function_category: str | None   # name_chord's seam, read in THIS area's key
    readings: list[Reading]         # plural; ordered by signal count then name
    zone: str                       # "confident" | "contested"
    contested_reasons: list[str]
    zone_coordinates: dict          # the measured numbers behind the zone
    single_label: str | None        # a label ONLY when confident + exactly one reading
    no_label_reason: str | None

    def to_dict(self) -> dict:
        payload = dataclasses.asdict(self)
        payload["readings"] = [r.to_dict() for r in self.readings]
        return payload


@dataclass(frozen=True)
class ChromaticEventResult:
    """Every chromatic event in a sequence, with the tallies that frame them."""

    home_tonic_pc: int
    home_mode: str
    events: list[ChromaticEvent]
    chords_examined: int            # nameable chord windows the scan covered
    diatonic_chords: int            # ...of which stayed inside their area's key
    confident_events: int
    contested_events: int
    prior_version: str              # the structural-key prior the zone cites

    def to_dict(self) -> dict:
        return {
            "home_tonic_pc": self.home_tonic_pc,
            "home_mode": self.home_mode,
            "events": [e.to_dict() for e in self.events],
            "chords_examined": self.chords_examined,
            "diatonic_chords": self.diatonic_chords,
            "confident_events": self.confident_events,
            "contested_events": self.contested_events,
            "prior_version": self.prior_version,
        }


def _area_context(tonic_pc: int, mode: str):
    """An ``AnalyticalContext`` for one area's key, for the special-function seam."""

    from ..analysis.key_induction import candidate_context

    return candidate_context(KeyCandidate(tonic_pc=tonic_pc, mode=mode, score=1.0))


def _function_of(span, context, catalog) -> str | None:
    """``name_chord``'s special-function flag for THIS chord, in THIS key.

    Pinned to the chord the segmentation already named — the reading is looked up
    among the ranked interpretations rather than taking ``chosen``, so re-reading
    in the area's key can never silently rename the chord underneath the caller.
    """

    naming = name_chord(span.salient_pcs, context, catalog=catalog)
    ranked = ([naming.chosen] if naming.chosen is not None else []) + naming.alternatives
    for r in ranked:
        if (r.interpretation.root_pc, r.interpretation.quality) == (span.root_pc, span.quality):
            return r.function_category
    return None


def classify_chromatic_events(
    sequence: Sequence,
    *,
    structural: "object | None" = None,
    confirmation: "object | None" = None,
    subdivisions: int = 1,
    floor_tolerance_beats: float | None = None,
    session=None,
) -> ChromaticEventResult:
    """Classify every chord that leaves its structural key area.

    ``structural`` / ``confirmation`` reuse an existing ``StructuralKeyResult`` /
    ``KeyAreaConfirmationResult`` instead of recomputing them. ``subdivisions``
    is the chord grid — **match it to the harmonic rhythm** (a coarse grid hides
    cadences and merges chords; see ``confirm_key_areas``).
    ``floor_tolerance_beats`` is the stated half-width of the knife-edge band
    around the versioned ``min_modulation_beats``; it defaults to a quarter of
    that floor. Like the inertia λ of Decision 14 it is a **policy knob**, not a
    measurement — it is stated, cited in every event's coordinates, and
    overridable, never discovered.

    Raises on an empty sequence.
    """

    if not sequence.events:
        raise ValueError("classify_chromatic_events needs a non-empty sequence.")

    from ..io.loaders import load_chord_qualities, load_structural_key_priors

    result = structural if structural is not None else reduce_to_structural_keys(sequence)
    confirmed = confirmation if confirmation is not None else confirm_key_areas(
        sequence, structural=result, subdivisions=subdivisions, session=session
    )
    priors = load_structural_key_priors()
    tolerance = (
        priors.min_modulation_beats / 4.0
        if floor_tolerance_beats is None
        else float(floor_tolerance_beats)
    )

    segmentation = segment_to_chords(sequence, subdivisions=subdivisions, session=session)
    spans = [s for s in segmentation.spans if s.root_pc is not None]
    catalog = load_chord_qualities(session)

    confirmed_by_span = {
        (a.start_beats, a.end_beats): a.confirmed for a in confirmed.areas
    }
    contexts = {
        (a.tonic_pc, a.mode): _area_context(a.tonic_pc, a.mode)
        for a in result.areas
        if a.mode in _MODE_SCALE
    }

    events: list[ChromaticEvent] = []
    diatonic = 0
    for index, span in enumerate(spans):
        area_index = _area_of(result.areas, span.start_beat)
        if area_index is None:
            continue
        area = result.areas[area_index]
        context = contexts.get((area.tonic_pc, area.mode))
        if context is None:
            continue  # a non-major/minor area: no functional vocabulary, no claim

        collection = _diatonic_pcs(area.tonic_pc, area.mode)
        foreign = sorted(pc for pc in span.salient_pcs if pc not in collection)
        if not foreign:
            diatonic += 1
            continue

        events.append(
            _event(
                span=span,
                index=index,
                spans=spans,
                area=area,
                area_index=area_index,
                areas=result.areas,
                confirmed_by_span=confirmed_by_span,
                foreign=foreign,
                context=context,
                catalog=catalog,
                priors=priors,
                tolerance=tolerance,
            )
        )

    return ChromaticEventResult(
        home_tonic_pc=result.home_tonic_pc,
        home_mode=result.home_mode,
        events=events,
        chords_examined=diatonic + len(events),
        diatonic_chords=diatonic,
        confident_events=sum(1 for e in events if e.zone == "confident"),
        contested_events=sum(1 for e in events if e.zone == "contested"),
        prior_version=priors.version,
    )


def _area_of(areas, beat: float) -> int | None:
    for i, area in enumerate(areas):
        if area.start_beats - _EPS <= beat < area.end_beats - _EPS:
            return i
    return None


def _event(
    *, span, index, spans, area, area_index, areas, confirmed_by_span,
    foreign, context, catalog, priors, tolerance,
) -> ChromaticEvent:
    # --- position: interior or boundary -------------------------------------
    # "Within one chord-window of the edge" self-scales to the segmentation grid,
    # so no magic beat count is needed and the test means the same thing at every
    # `subdivisions` — a chord is at a boundary when no other chord separates it
    # from the seam.
    #
    # Only a seam with ANOTHER AREA across it counts. The first area's start and
    # the last area's end are the *piece's* edges, not key-area boundaries — and
    # scoring them as boundaries put a spurious `modulation` reading on the
    # opening chord of every piece (measured, not hypothesized).
    window = span.end_beat - span.start_beat
    edges: list[tuple[float, int]] = []          # (distance, neighbour index)
    if area_index > 0:
        edges.append((abs(span.start_beat - area.start_beats), area_index - 1))
    if area_index < len(areas) - 1:
        edges.append((abs(area.end_beats - span.end_beat), area_index + 1))

    if edges:
        distance, neighbour = min(edges)
        position = "boundary" if distance <= window + _EPS else "interior"
    else:
        distance, neighbour = None, None         # a single-area piece has no seam
        position = "interior"

    # --- the readings -------------------------------------------------------
    readings: list[Reading] = []

    parallel = "minor" if area.mode == "major" else "major"
    parallel_pcs = _diatonic_pcs(area.tonic_pc, parallel)
    if all(pc in parallel_pcs for pc in foreign):
        readings.append(Reading(
            label="borrowed_mixture",
            signals=[f"every foreign pc {foreign} belongs to the parallel "
                     f"{parallel} collection on the same tonic"],
        ))

    function_category = _function_of(span, context, catalog)
    if function_category is not None:
        signals = [f"name_chord's special-function seam reads this chord as "
                   f"{function_category} in the area's own key"]
        if function_category == "secondary_dominant":
            target = (span.root_pc + 5) % 12
            following = next(
                (s for s in spans[index + 1:] if s.root_pc != span.root_pc), None
            )
            if following is not None and following.root_pc == target:
                signals.append(
                    f"the next chord realizes the predicted resolution: root pc "
                    f"{target}, down a fifth — a sequential test single-chord "
                    f"naming cannot make"
                )
        readings.append(Reading(label=function_category, signals=signals))

    for tonicization in area.tonicizations:
        if (tonicization.start_beats - _EPS <= span.start_beat
                < tonicization.end_beats - _EPS):
            readings.append(Reading(
                label="tonicization",
                signals=[f"inside a region the structural reduction already "
                         f"absorbed as a tonicization of pc {tonicization.tonic_pc} "
                         f"{tonicization.mode} (confidence {tonicization.region_score:.3f})"],
            ))
            break

    if position == "boundary":
        across = areas[neighbour]
        signals = [f"within one chord-window ({window:g} beats) of the structural "
                   f"key-area boundary with pc {across.tonic_pc} {across.mode}"]
        if confirmed_by_span.get((across.start_beats, across.end_beats)):
            signals.append(
                f"the area across that boundary (pc {across.tonic_pc} "
                f"{across.mode}) is cadence-confirmed in its own key"
            )
        readings.append(Reading(label="modulation", signals=signals))

    readings.sort(key=lambda r: (-len(r.signals), r.label))

    # --- the zone -----------------------------------------------------------
    reasons: list[str] = []
    if len(readings) > 1:
        reasons.append(CONTESTED_COMPETING)
    elif not readings:
        reasons.append(CONTESTED_NONE)
    if abs(area.duration_beats - priors.min_modulation_beats) <= tolerance + _EPS:
        reasons.append(CONTESTED_FLOOR)

    zone = "contested" if reasons else "confident"
    single = readings[0].label if zone == "confident" and len(readings) == 1 else None
    no_label = None if single is not None else (
        "the evidence is inside the contested band — committing to one label "
        "needs a caller-supplied cost model, not a default (ROADMAP Decisions 14/15)"
    )

    return ChromaticEvent(
        start_beat=span.start_beat,
        end_beat=span.end_beat,
        bar=span.bar,
        root_pc=span.root_pc,
        quality=span.quality,
        area_tonic_pc=area.tonic_pc,
        area_mode=area.mode,
        foreign_pcs=foreign,
        position=position,
        beats_to_boundary=None if distance is None else round(distance, 9),
        function_category=function_category,
        readings=readings,
        zone=zone,
        contested_reasons=reasons,
        zone_coordinates={
            "readings": len(readings),
            "beats_to_boundary": None if distance is None else round(distance, 9),
            "boundary_threshold_beats": round(window, 9),
            "area_duration_beats": round(area.duration_beats, 9),
            "min_modulation_beats": priors.min_modulation_beats,
            "floor_tolerance_beats": tolerance,
            "prior_version": priors.version,
        },
        single_label=single,
        no_label_reason=no_label,
    )


__all__ = [
    "ChromaticEvent",
    "ChromaticEventResult",
    "Reading",
    "classify_chromatic_events",
]
