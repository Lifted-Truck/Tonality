"""Degree-preserving remap — gap 26's primitive (interscalar transposition).

``remap_by_degree`` moves a piece from one scale to another **by scale degree,
never by proximity**: degree 3 of the source becomes degree 3 of the target,
whatever the chromatic distance. This is Hook's **interscalar transposition**
at index 0 (tonic-anchored) — precisely: the identity on the generic space of
scale steps, composed with two different embeddings into ℤ₁₂. It is *not* a
Lewin GIS transformation (a GIS's interval group acts uniformly; a mode switch
changes the specific interval for a fixed generic one), and it is *not* a
12→12 pitch-class table — no correct one exists, which is the result that
defines this design:

**The impossibility result (ROADMAP gap 26, swarm-verified).** A chromatic
tone's image depends on **which degree it is attached to** — context, not pitch
class (E♭-as-♯2 and E♭-as-♭3 must map differently) — and **totality and
locality are mutually exclusive**: any total map moves some tone out of its
generic step wherever a scale step collapses. Every surveyed DAW ships a 12→12
function anyway (nearest-neighbour snapping with an arbitrary tie-break); this
module instead makes the degree attachment explicit, deterministic, and
**reported**, so the caller can see — and override — every contextual call.

Contrast with ``conform.py``, deliberately its opposite: conform snaps by
**proximity** and forgets degrees; remap preserves **degrees** and ignores
proximity. Conform is many-to-one and lossy; remap is bijective on in-scale
material (equal cardinality is a precondition — **error, no default** — so
degree i ↔ degree i is exact and invertible).

Chromatic (out-of-scale) tones: ``pitch → (degree, alteration) → pitch'``. The
tone attaches to its nearest scale degree, carries its signed offset, and the
offset is re-applied to the mapped degree (rhetoric preserved: a passing tone
stays a passing tone — Julian's recorded default). Two honest reports ride the
result rather than being silently absorbed:

- ``tied`` attachments — a tone equidistant between two degrees attaches to the
  **lower** (it reads as a raised degree, the commoner chromatic rhetoric —
  leading-tone-of figures), deterministically, and the tie is flagged so a
  caller with better context (gap 25's classifier) can re-attach and re-apply.
- ``absorbed_alterations`` — an alteration whose image lands **on** a target
  scale member (markedness lost: the tone was chromatic in the source and is
  diatonic in the target). Kept as computed, reported per note. The corollary
  conservation law says chromatic capacity is never lost globally (#collapsed
  == #opened), but locally an alteration can be absorbed — that is a fact
  about the two scales, not a bug, and the caller decides whether it matters.

``retonicize`` ships alongside because users conflate the two operations: it
**fixes the collection and moves the tonic** (C Ionian rooted at A is Aeolian)
— zero note edits, an identity-layer renaming, the folk operation. If you want
the notes to change, you want ``remap_by_degree``; if you want the same notes
heard from a different tonic, you want ``retonicize``.

Register: preserved the same way conform preserves it — each note moves by the
signed pc difference normalized into [-6, 6) (exact half-octave resolves
downward), so contour is disturbed as little as the degree map allows. Onset,
duration, velocity, voice and count are untouched. Deterministic, freezable.

**The MIDI boundary is the one exception, and it is now reported** (audit #275;
the same defect #262 fixed in ``conform.py`` and left standing here — a rule
corrected where it is READ and not where it is INHERITED). When ``midi + delta``
would leave 0..127 the move is flipped a full octave to stay in range, which
both exceeds the [-6, 6) envelope and can reverse the "half-octave resolves
downward" convention. That is forced by range, not chosen — so
``RemapEdit.range_corrected`` marks it, exactly as ``ConformEdit.tie_resolution
== "range"`` does for the proximity sibling. A caller that cares about the
envelope checks the flag; it is never silently absorbed.

This is the **primitive**. The feature — ``modal_transform`` over a *timeline*
of key areas with per-area remaps, borrowed-chord handling via the gap 25
classifier, and percussion left untouched — is gap 26's next slice and composes
this. Callers using the primitive directly should exclude percussion voices
themselves (the primitive remaps every event it is given).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..temporal.sequence import Sequence

_TIE_ATTACH_NOTE = (
    "equidistant between two degrees; attached to the lower (reads as a raised "
    "degree) — override by re-attaching with better context"
)


def _resolve_degrees(scale, session) -> tuple[str | None, tuple[int, ...]]:
    """``scale`` (catalog name or degree iterable) → (name, sorted degrees)."""

    if isinstance(scale, str):
        from ..io.loaders import load_scales

        catalog = load_scales(session)
        if scale not in catalog:
            raise ValueError(
                f"Unknown scale {scale!r} — not in the catalog"
                + (" or session" if session is not None else "")
                + ". Pass a catalog name or an explicit list of degrees."
            )
        return scale, tuple(sorted(int(d) % 12 for d in catalog[scale].degrees))
    degrees = tuple(sorted({int(d) % 12 for d in scale}))
    if not degrees:
        raise ValueError("remap needs a non-empty scale.")
    return None, degrees


@dataclass(frozen=True)
class InterscalarMap:
    """A tonic-anchored degree correspondence between two equal-size scales.

    Degree i of the source maps to degree i of the target (index-0 interscalar
    transposition). Equal cardinality is a **precondition, not a default** —
    unequal scales have no canonical degree correspondence, so the constructor
    errors rather than inventing one (a declared non-tonic-anchored
    correspondence is the recorded follow-on).
    """

    source_name: str | None
    source_degrees: tuple[int, ...]     # sorted, relative to source root
    source_root: int
    target_name: str | None
    target_degrees: tuple[int, ...]
    target_root: int

    def __post_init__(self) -> None:
        if len(self.source_degrees) != len(self.target_degrees):
            raise ValueError(
                f"InterscalarMap needs equal cardinality: source has "
                f"{len(self.source_degrees)} degrees, target has "
                f"{len(self.target_degrees)}. There is no canonical degree "
                "correspondence between unequal scales — choose one explicitly "
                "(error, not guess)."
            )
        for label, degrees in (("source", self.source_degrees),
                               ("target", self.target_degrees)):
            if 0 not in degrees:
                raise ValueError(
                    f"{label} degrees must include 0 — the map is tonic-anchored, "
                    "and a collection without its root pc is not anchored."
                )

    @property
    def cardinality(self) -> int:
        return len(self.source_degrees)

    def degree_table(self) -> list[dict]:
        """The per-degree correspondence, absolute pcs — the inspectable core."""

        return [
            {
                "degree": i,
                "source_pc": (self.source_root + s) % 12,
                "target_pc": (self.target_root + t) % 12,
            }
            for i, (s, t) in enumerate(zip(self.source_degrees, self.target_degrees))
        ]

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "source_degrees": list(self.source_degrees),
            "source_root": self.source_root,
            "target_name": self.target_name,
            "target_degrees": list(self.target_degrees),
            "target_root": self.target_root,
            "degree_table": self.degree_table(),
        }


@dataclass(frozen=True)
class RemapEdit:
    """One note's move: its degree attachment, alteration, and image."""

    index: int
    voice: str | None
    onset: float
    from_midi: int
    to_midi: int
    delta: int
    degree: int                 # the degree the tone attached to (0-based)
    alteration: int             # signed semitones off that degree; 0 = diatonic
    tied_attachment: bool       # equidistant between two degrees (see note)
    attachment_note: str | None
    range_corrected: bool = False   # the move was flipped an octave to stay in
                                    # 0..127; |delta| then exceeds 6 and the
                                    # half-octave convention may be reversed

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class AbsorbedAlteration:
    """A chromatic tone whose image is diatonic in the target (markedness lost)."""

    index: int
    onset: float
    from_midi: int
    to_midi: int
    degree: int
    alteration: int

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class RemapResult:
    """The remapped piece with every degree decision inspectable.

    ``events`` is canonical form ``[onset, duration, midi, velocity, voice]``,
    the engine's canonical (onset, midi) order — NOT the caller's wire order
    (tonality-live-002; pair via ``edits``). In-scale notes are bijective through the degree
    table; chromatic notes carry their attachment + alteration in ``edits``.
    """

    map: InterscalarMap
    events: list[list]
    edits: list[RemapEdit]
    absorbed_alterations: list[AbsorbedAlteration]
    notes_total: int
    notes_diatonic: int
    notes_chromatic: int
    tied_attachments: int

    def to_dict(self) -> dict:
        return {
            "map": self.map.to_dict(),
            "events": [list(e) for e in self.events],
            "edits": [e.to_dict() for e in self.edits],
            "absorbed_alterations": [a.to_dict() for a in self.absorbed_alterations],
            "notes_total": self.notes_total,
            "notes_diatonic": self.notes_diatonic,
            "notes_chromatic": self.notes_chromatic,
            "tied_attachments": self.tied_attachments,
        }


def _signed_delta(from_pc: int, to_pc: int) -> int:
    """pc difference as a register-preserving move in [-6, 6) — half-octave down."""

    d = (to_pc - from_pc) % 12
    return d if d < 6 else d - 12


def _attach_degree(rel: int, degrees: tuple[int, ...]) -> tuple[int, int, bool]:
    """(degree_index, alteration, tied) for a relative pc outside ``degrees``.

    The one chromatic-attachment rule, shared with ``modal.py`` so the feature
    and the primitive can never drift: nearest degree wins; a tie between the
    degree below (+alteration) and above (−alteration) attaches BELOW (the
    raised-degree reading) and is flagged.
    """

    candidates = [
        (abs(_signed_delta(d, rel)), idx, _signed_delta(d, rel))
        for idx, d in enumerate(degrees)
    ]
    best_dist = min(c[0] for c in candidates)
    nearest = [c for c in candidates if c[0] == best_dist]
    _dist, degree, alteration = max(nearest, key=lambda c: c[2])
    return degree, alteration, len(nearest) > 1


def remap_by_degree(
    sequence: Sequence,
    source_scale,
    source_root: int,
    target_scale,
    target_root: int,
    *,
    session=None,
) -> RemapResult:
    """Remap a piece degree-for-degree from one scale/root to another.

    ``source_scale``/``target_scale`` are catalog names or explicit degree
    lists; roots are pcs 0-11. Equal cardinality required (error, no default).
    In-scale tones map bijectively degree→degree; chromatic tones attach to
    their nearest degree (tie → the lower, flagged) and carry their signed
    alteration across. Raises on an empty sequence — error, not guess.
    """

    if not sequence.events:
        raise ValueError("remap_by_degree needs a non-empty sequence.")

    source_name, source_degrees = _resolve_degrees(source_scale, session)
    target_name, target_degrees = _resolve_degrees(target_scale, session)
    imap = InterscalarMap(
        source_name=source_name, source_degrees=source_degrees,
        source_root=int(source_root) % 12,
        target_name=target_name, target_degrees=target_degrees,
        target_root=int(target_root) % 12,
    )

    # relative source pc -> degree index, for the in-scale (exact) path
    degree_of = {d: i for i, d in enumerate(imap.source_degrees)}
    target_pcs = frozenset((imap.target_root + d) % 12 for d in imap.target_degrees)

    out_events: list[list] = []
    edits: list[RemapEdit] = []
    absorbed: list[AbsorbedAlteration] = []
    diatonic = chromatic = 0

    for i, event in enumerate(sequence.events):
        midi = event.pitch.midi
        rel = (midi - imap.source_root) % 12

        if rel in degree_of:
            diatonic += 1
            degree, alteration, tied = degree_of[rel], 0, False
        else:
            chromatic += 1
            # Alteration signed so rel = degree_pc + alteration (positive = the
            # tone sits ABOVE its degree, a raised degree); see _attach_degree.
            degree, alteration, tied = _attach_degree(rel, imap.source_degrees)

        target_rel = (imap.target_degrees[degree] + alteration) % 12
        target_abs = (imap.target_root + target_rel) % 12
        delta = _signed_delta(midi % 12, target_abs)
        new_midi = midi + delta
        range_corrected = not 0 <= new_midi <= 127
        if range_corrected:
            new_midi = midi + delta + (12 if delta < 0 else -12)

        out_events.append([
            event.onset, event.duration, new_midi,
            event.pitch.velocity, event.voice,
        ])
        if new_midi != midi or alteration != 0:
            edits.append(RemapEdit(
                index=i, voice=event.voice, onset=event.onset,
                from_midi=midi, to_midi=new_midi, delta=new_midi - midi,
                degree=degree, alteration=alteration, tied_attachment=tied,
                attachment_note=_TIE_ATTACH_NOTE if tied else None,
                range_corrected=range_corrected,
            ))
        if alteration != 0 and new_midi % 12 in target_pcs:
            absorbed.append(AbsorbedAlteration(
                index=i, onset=event.onset, from_midi=midi, to_midi=new_midi,
                degree=degree, alteration=alteration,
            ))

    return RemapResult(
        map=imap,
        events=out_events,
        edits=edits,
        absorbed_alterations=absorbed,
        notes_total=len(sequence.events),
        notes_diatonic=diatonic,
        notes_chromatic=chromatic,
        tied_attachments=sum(1 for e in edits if e.tied_attachment),
    )


@dataclass(frozen=True)
class RetonicizeResult:
    """The same collection heard from a new tonic — a renaming, never an edit."""

    collection_pcs: list[int]
    old_root: int
    old_name: str | None
    new_root: int
    new_degrees: list[int]
    new_names: list[str]        # every catalog scale matching the rotation
    notes_changed: int          # always 0 — stated, not implied

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def retonicize(scale, root_pc: int, new_tonic_pc: int, *, session=None) -> RetonicizeResult:
    """Fix the collection, move the tonic — the folk operation, exactly defined.

    C Ionian retonicized to A is A Aeolian: **zero notes change**; only the
    anchor does. The new tonic must be a member of the collection (error
    otherwise — a tonic outside the collection is a different question, namely
    ``remap_by_degree`` or a modulation, and guessing which would be wrong).
    Returns every catalog name matching the re-rooted collection (plural — a
    rotation can match several registered scales).
    """

    name, degrees = _resolve_degrees(scale, session)
    root_pc = int(root_pc) % 12
    new_tonic_pc = int(new_tonic_pc) % 12
    pcs = sorted((root_pc + d) % 12 for d in degrees)
    if new_tonic_pc not in pcs:
        raise ValueError(
            f"new tonic pc {new_tonic_pc} is not in the collection {pcs} — "
            "retonicize keeps the collection fixed. To move to a tonic outside "
            "it, you want remap_by_degree (change the notes) or a modulation "
            "(change the key), and those are different operations."
        )
    new_degrees = sorted((pc - new_tonic_pc) % 12 for pc in pcs)

    from ..io.loaders import load_scales

    catalog = load_scales(session)
    matches = sorted(
        n for n, s in catalog.items()
        if tuple(sorted(int(d) % 12 for d in s.degrees)) == tuple(new_degrees)
    )
    return RetonicizeResult(
        collection_pcs=pcs,
        old_root=root_pc,
        old_name=name,
        new_root=new_tonic_pc,
        new_degrees=new_degrees,
        new_names=matches,
        notes_changed=0,
    )


__all__ = [
    "AbsorbedAlteration",
    "InterscalarMap",
    "RemapEdit",
    "RemapResult",
    "RetonicizeResult",
    "remap_by_degree",
    "retonicize",
]
