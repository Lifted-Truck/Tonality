"""Scale/key conform — the engine's first note-out surface (Phase 7 slice 0).

``conform_to_scale`` snaps every out-of-scale pitch class to the nearest scale
member; ``fit_to_key`` is the thin wrapper (a key *is* a scale — one primitive,
one snap rule, one set of tests). Accepted from Tonality-Live brief-001;
rulings R1/R2 from its ratification (`integrations/Tonality-Live/ratify.md`).

**Generative, register-preserving.** Only the pitch class moves; octave, onset,
duration, velocity, voice and note count are all preserved (order is the
engine's canonical (onset, midi) sort — see ``ConformResult``) — no
register is invented, so the cardinal rule is cleared. Deterministic and
freezable (no RNG, no clock).

Two guarantees hold **by construction**, not merely by test:

- **≤ 6-semitone move** — the snap distance is the minimal circular pc distance,
  which cannot exceed 6.
- **Idempotent on in-scale input** — an in-scale pc is returned untouched, so
  ``conform(conform(x)) == conform(x)`` always.

**R1 — ties are the COMMON case, and the default is melodic (ratified
2026-08-09).** The original design treated equidistant snaps as a rare corner
and defaulted ``"down"``. Tonality-Live's ratification corrected the premise
with an exhaustive count this module's tests reproduce: a tie needs an **even**
gap with the pc at its midpoint, and whole-tone gaps dominate diatonic scales —
in a major scale **all five** out-of-scale pcs tie (harmonic minor 3/5,
whole-tone 6/6, pentatonic 3/7). A fixed ``"down"`` therefore decides *every
accidental in an ordinary clip*, sagging chromatic lines uniformly flat. (The
originally cited counter-example — the augmented second — was wrong: an odd gap
can never tie, its interior pcs sit at distances 1 and 2.) So the default,
``tie_break="previous"``, resolves a tie toward the **previous note in the same
voice** (its already-conformed pitch — melodic continuity); ``"down"`` is the
documented deterministic fallback when there is no previous note or the
candidates are equidistant from it. Fixed ``"down"`` / ``"up"`` remain available
as explicit choices.

**R2 — the map is many-to-one, and collisions are kept and reported (ruled
2026-08-09).** C and C♯ at the same onset both conform to C: two output notes
identical in every field. This is the ROADMAP's totality/locality exclusion
("any *total* map necessarily moves some tone out of its generic step" —
wherever a step collapses, neighbours merge). The ruling is **keep-and-report**:
note count is preserved (the contract test stands) and every collision *created
by the snap* is itemized in ``collisions``, so nothing is silent and a consumer
that wants clip hygiene can dedupe with full information. Deduping here would
break count parity and silently choose a survivor — a musical decision this
module refuses to make. Pre-existing duplicates in the input are the input's
business and are not reported.

The MIDI boundary is the one real edge: at the extremes one snap direction can
leave 0..127, in which case the in-range direction is taken (both cannot be out:
the two candidates lie within one octave of the source). A boundary-forced
direction overrides the tie preference — range is a hard constraint, taste is
not.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..temporal.sequence import Sequence

_TIE_BREAKS = ("previous", "down", "up")
_MODE_SCALE = {"major": "Ionian", "minor": "Natural Minor"}


@dataclass(frozen=True)
class ConformEdit:
    """One snapped note: what moved, by how much, and how any tie was resolved."""

    index: int                  # position in the original (and output) event order
    voice: str | None
    onset: float
    from_midi: int
    to_midi: int
    delta: int                  # signed semitones, |delta| <= 6 by construction
    tied: bool                  # both directions were equidistant
    tie_resolution: str | None  # "previous" | "down" | "up" | "range" (boundary-forced)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class Collision:
    """Notes made identical BY the snap (R2: kept in the output, reported here)."""

    voice: str | None
    onset: float
    duration: float
    midi: int
    count: int
    source_midis: list[int]     # the distinct input pitches that merged

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class ConformResult:
    """The conformed piece, with every snap and every snap-created collision.

    ``events`` is the full piece in canonical event form
    ``[onset_beats, duration_beats, midi, velocity, voice]``, in the engine's
    **canonical order** — ``Sequence`` sorts events by ``(onset, midi)`` at
    construction, so this is NOT the caller's wire order (tonality-live-002:
    a positional diff against an unsorted input pairs the wrong notes).
    The preservation contract is a **multiset** claim: count, timings,
    velocities and voices are preserved and pitch is the only field that may
    differ — position-by-position it holds only for already-sorted input.
    Pair input↔output through ``edits`` (``(onset, from_midi)``), never by
    raw-list position.
    """

    scale_name: str | None      # None when raw degrees were supplied
    degrees: list[int]          # absolute pcs of the target collection, sorted
    root_pc: int
    tie_break: str
    events: list[list]
    edits: list[ConformEdit]
    collisions: list[Collision]
    notes_total: int
    notes_snapped: int
    ties_resolved: int

    def to_dict(self) -> dict:
        return {
            "scale_name": self.scale_name,
            "degrees": list(self.degrees),
            "root_pc": self.root_pc,
            "tie_break": self.tie_break,
            "events": [list(e) for e in self.events],
            "edits": [e.to_dict() for e in self.edits],
            "collisions": [c.to_dict() for c in self.collisions],
            "notes_total": self.notes_total,
            "notes_snapped": self.notes_snapped,
            "ties_resolved": self.ties_resolved,
        }


def _target_pcs(scale, root_pc: int, session) -> tuple[str | None, frozenset[int]]:
    """Resolve ``scale`` (catalog name or iterable of degrees) to absolute pcs."""

    if isinstance(scale, str):
        from ..io.loaders import load_scales

        catalog = load_scales(session)
        if scale not in catalog:
            raise ValueError(
                f"Unknown scale {scale!r} — not in the catalog"
                + (" or session" if session is not None else "")
                + ". Pass a catalog name or an explicit list of degrees."
            )
        degrees = catalog[scale].degrees
        name = scale
    else:
        degrees = tuple(int(d) % 12 for d in scale)
        name = None
    if not degrees:
        raise ValueError("conform_to_scale needs a non-empty scale.")
    return name, frozenset((root_pc + d) % 12 for d in degrees)


def _snap(midi: int, targets: frozenset[int]) -> tuple[int, int, bool]:
    """(down_candidate, up_candidate, tied) for one out-of-scale midi note."""

    pc = midi % 12
    down = min((pc - t) % 12 for t in targets)
    up = min((t - pc) % 12 for t in targets)
    return midi - down, midi + up, down == up


def conform_to_scale(
    sequence: Sequence,
    scale,
    root_pc: int,
    *,
    tie_break: str = "previous",
    session=None,
) -> ConformResult:
    """Snap every out-of-scale pitch class to the nearest scale member.

    ``scale`` is a catalog scale name (e.g. ``"Ionian"``; ``session`` merges a
    session's registered scales) or an explicit iterable of degrees.
    ``tie_break`` resolves equidistant snaps: ``"previous"`` (default — toward
    the previous note in the same voice, falling back to down), ``"down"``,
    ``"up"``. Raises on an empty sequence, an empty scale, an unknown scale
    name, or an unknown ``tie_break`` — error, not guess.
    """

    if tie_break not in _TIE_BREAKS:
        raise ValueError(f"tie_break must be one of {_TIE_BREAKS}, got {tie_break!r}.")
    if not sequence.events:
        raise ValueError("conform_to_scale needs a non-empty sequence.")

    root_pc = int(root_pc) % 12
    scale_name, targets = _target_pcs(scale, root_pc, session)

    # Melodic continuity needs each voice's notes in time order, but the output
    # must keep the sequence's canonical order — so walk a per-voice order and write
    # back by original index. Unvoiced events (voice=None) form their own stream.
    order = sorted(range(len(sequence.events)),
                   key=lambda i: (sequence.events[i].onset, i))
    new_midis: list[int | None] = [None] * len(sequence.events)
    prev_in_voice: dict = {}
    edits: list[tuple[int, int, int, bool, str | None]] = []

    for i in order:
        event = sequence.events[i]
        midi = event.pitch.midi
        if midi % 12 in targets:
            new = midi
            tied, resolution = False, None
        else:
            down_c, up_c, tied = _snap(midi, targets)
            in_range = [c for c in (down_c, up_c) if 0 <= c <= 127]
            if len(in_range) == 1:
                new, resolution = in_range[0], "range"
            elif not tied:
                new = down_c if (midi - down_c) < (up_c - midi) else up_c
                resolution = None
            elif tie_break == "down":
                new, resolution = down_c, "down"
            elif tie_break == "up":
                new, resolution = up_c, "up"
            else:  # "previous"
                prev = prev_in_voice.get(event.voice)
                if prev is None or abs(down_c - prev) == abs(up_c - prev):
                    new, resolution = down_c, "down"      # documented fallback
                else:
                    new = down_c if abs(down_c - prev) < abs(up_c - prev) else up_c
                    resolution = "previous"
            edits.append((i, midi, new, tied, resolution))
        new_midis[i] = new
        prev_in_voice[event.voice] = new

    out_events: list[list] = []
    for i, event in enumerate(sequence.events):
        out_events.append([
            event.onset, event.duration, new_midis[i],
            event.pitch.velocity, event.voice,
        ])

    # R2: collisions CREATED by the snap — output-identical groups whose input
    # pitches were not already identical. Kept in the output; reported here.
    groups: dict[tuple, list[int]] = {}
    for i, event in enumerate(sequence.events):
        key = (event.voice, event.onset, event.duration, new_midis[i])
        groups.setdefault(key, []).append(i)
    collisions = [
        Collision(
            voice=voice, onset=onset, duration=duration, midi=midi,
            count=len(members),
            source_midis=sorted({sequence.events[i].pitch.midi for i in members}),
        )
        for (voice, onset, duration, midi), members in sorted(
            groups.items(), key=lambda kv: (kv[0][1], str(kv[0][0]), kv[0][3])
        )
        if len(members) > 1
        and len({sequence.events[i].pitch.midi for i in members}) > 1
    ]

    edit_rows = [
        ConformEdit(
            index=i, voice=sequence.events[i].voice, onset=sequence.events[i].onset,
            from_midi=old, to_midi=new, delta=new - old,
            tied=tied, tie_resolution=resolution,
        )
        for i, old, new, tied, resolution in sorted(edits)
    ]

    return ConformResult(
        scale_name=scale_name,
        degrees=sorted(targets),
        root_pc=root_pc,
        tie_break=tie_break,
        events=out_events,
        edits=edit_rows,
        collisions=collisions,
        notes_total=len(sequence.events),
        notes_snapped=len(edit_rows),
        ties_resolved=sum(1 for e in edit_rows if e.tied),
    )


def fit_to_key(
    sequence: Sequence,
    tonic_pc: int,
    mode: str,
    *,
    tie_break: str = "previous",
    session=None,
) -> ConformResult:
    """Conform to a key's scale — the thin wrapper (a key IS a scale).

    ``mode`` is ``"major"`` (→ Ionian) or ``"minor"`` (→ Natural Minor, the
    collection convention the key layer uses throughout). Everything else —
    guarantees, tie policy, collision reporting — is ``conform_to_scale``.
    """

    scale_name = _MODE_SCALE.get(mode)
    if scale_name is None:
        raise ValueError(
            f"mode must be 'major' or 'minor', got {mode!r} — for any other "
            "collection call conform_to_scale with the scale itself."
        )
    return conform_to_scale(
        sequence, scale_name, tonic_pc, tie_break=tie_break, session=session
    )


__all__ = [
    "Collision",
    "ConformEdit",
    "ConformResult",
    "conform_to_scale",
    "fit_to_key",
]
