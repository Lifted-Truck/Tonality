"""Scale-run detection (gap 31b): maximal stepwise walks through a scale.

Finds every maximal span where one voice walks the scale — each note moving to
the **register-adjacent scale tone** in a constant direction (G-F-E-D-C in C
major: five notes, four descending scale steps). The detection exists because
of a measured consumer failure (`integrations/Tonality-Live/`, gap 31): a walk
is a *span-level* characteristic, invisible to per-note transforms — proximity
conform destroys one even at equal cardinality — so anything that wants to
*preserve* a walk must first be able to *see* it.

**Why this is a detector and not a named Pattern** (a design correction to
gap 31's first sketch): `pattern.1` templates are **fixed-length** with
concrete elements (the prinner is literally degrees 6-5-4-3). A scale run is
variable-length — "N or more consecutive steps" quantifies over lengths, which
the DSL deliberately cannot express (matching is exact under a declared
abstraction; there are no wildcards). Adding a `run` element type is a
recorded `pattern.2` follow-on; until a second variable-length need appears,
one dedicated detector is honest scope.

Definitions, precisely:

- **Register-adjacent**: the next note is the scale tone immediately above or
  below the current one *in pitch space* — an octave leap to the neighbouring
  pitch class is a leap, not a step. This is what makes a walk a walk.
- **Maximal**: a run is never reported inside a longer run. Direction is
  constant; a turnaround (his "partway back up") ends one run and may start
  another, and the shared turning note belongs to both.
- **Strict diatony** (slice 1): a chromatic note breaks the run — it is not a
  scale tone, so it cannot be a scale step. Chromatic-tolerant runs (a walk
  decorated with passing chromatics) are a recorded follow-on.
- ``min_notes`` is the consumer's "minimum consecutive steps" gate (default 4
  notes = 3 steps), which is what keeps ordinary stepwise motion from
  triggering everywhere.

Same line conventions as ``analyze_melody``: one voice's monophonic stream
(overlap ⇒ error, multi-voice without ``voice=`` ⇒ error — the engine does not
pick a part for you). Key: declare a scale + root, or leave ``scale=None`` to
infer the key globally (``infer_key``; the reading is cited on the result).
Per-key-area runs compose with ``reduce_to_structural_keys`` at the caller —
or in gap 31(c), where these spans become grouped plan decisions.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from .sequence import Sequence
from .melodic import _line_events

_EPS = 1e-9


@dataclass(frozen=True)
class ScaleRun:
    """One maximal constant-direction walk through the scale."""

    voice: str | None
    direction: str              # "descent" | "ascent"
    note_count: int             # steps = note_count - 1
    start_beat: float
    end_beat: float             # last note's onset
    start_index: int            # indices into the analyzed LINE (time order)
    end_index: int
    midis: list[int]
    degrees: list[int]          # 1-based scale degrees, aligned with midis

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class ScaleRunResult:
    """Every maximal run in one line, with the scale the walk was read against."""

    voice: str | None
    scale_name: str | None
    root_pc: int
    degrees: list[int]          # the collection, relative pcs
    key_inferred: bool
    min_notes: int
    runs: list[ScaleRun]
    descents: int
    ascents: int

    def to_dict(self) -> dict:
        return {
            "voice": self.voice,
            "scale_name": self.scale_name,
            "root_pc": self.root_pc,
            "degrees": list(self.degrees),
            "key_inferred": self.key_inferred,
            "min_notes": self.min_notes,
            "runs": [r.to_dict() for r in self.runs],
            "descents": self.descents,
            "ascents": self.ascents,
        }


def find_scale_runs(
    sequence: Sequence,
    scale=None,
    root_pc: int | None = None,
    *,
    min_notes: int = 4,
    voice: str | None = None,
    session=None,
) -> ScaleRunResult:
    """Every maximal scale walk of at least ``min_notes`` notes in one line.

    ``scale``/``root_pc`` declare the collection (catalog name or degree list —
    both or neither); ``scale=None`` infers the key globally and reads runs
    against its mode's scale. Raises on an empty/polyphonic line, an unknown
    scale, ``min_notes < 2``, or a declared scale without a root — error, not
    guess.
    """

    if min_notes < 2:
        raise ValueError(f"min_notes must be >= 2 (a step needs two notes), got {min_notes}.")
    if (scale is None) != (root_pc is None):
        raise ValueError(
            "declare scale AND root_pc together, or neither (inferred key) — "
            "a collection without a root is not a scale."
        )

    from ..generate.remap import _resolve_degrees

    if scale is None:
        from ..analysis.key_induction import infer_key
        from .structural_key import _MODE_SCALE

        best = infer_key(sequence).best
        scale_name, degrees = _resolve_degrees(_MODE_SCALE[best.mode], session)
        root, inferred = best.tonic_pc, True
    else:
        scale_name, degrees = _resolve_degrees(scale, session)
        root, inferred = int(root_pc) % 12, False

    line = _line_events(sequence, voice)
    scale_pcs = [(root + d) % 12 for d in degrees]
    degree_of_pc = {pc: i for i, pc in enumerate(scale_pcs)}
    n = len(degrees)

    def step_of(a: int, b: int) -> int | None:
        """+1/-1 if b is the register-adjacent scale tone above/below a."""

        da, db = degree_of_pc.get(a % 12), degree_of_pc.get(b % 12)
        if da is None or db is None or a == b:
            return None
        up_deg = (da + 1) % n
        up_semis = (degrees[up_deg] - degrees[da]) % 12
        if db == up_deg and b - a == up_semis:
            return 1
        down_deg = (da - 1) % n
        down_semis = (degrees[da] - degrees[down_deg]) % 12
        if db == down_deg and a - b == down_semis:
            return -1
        return None

    midis = [e.pitch.midi for e in line]
    steps = [step_of(a, b) for a, b in zip(midis, midis[1:])]

    runs: list[ScaleRun] = []
    i = 0
    while i < len(steps):
        d = steps[i]
        if d is None:
            i += 1
            continue
        j = i
        while j < len(steps) and steps[j] == d:
            j += 1
        count = j - i + 1                      # notes spanned by steps i..j-1
        if count >= min_notes:
            span = line[i:j + 1]
            runs.append(ScaleRun(
                voice=voice if voice is not None else (span[0].voice),
                direction="ascent" if d == 1 else "descent",
                note_count=count,
                start_beat=span[0].onset,
                end_beat=span[-1].onset,
                start_index=i,
                end_index=j,
                midis=[e.pitch.midi for e in span],
                degrees=[degree_of_pc[e.pitch.midi % 12] + 1 for e in span],
            ))
        # the turning note may start the next run: resume AT the boundary step
        i = j

    return ScaleRunResult(
        voice=voice,
        scale_name=scale_name,
        root_pc=root,
        degrees=list(degrees),
        key_inferred=inferred,
        min_notes=min_notes,
        runs=runs,
        descents=sum(1 for r in runs if r.direction == "descent"),
        ascents=sum(1 for r in runs if r.direction == "ascent"),
    )


__all__ = ["ScaleRun", "ScaleRunResult", "find_scale_runs"]
