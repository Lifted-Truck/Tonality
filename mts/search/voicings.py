"""``search_voicings`` — exact, bounded enumeration of registered voicings.

The register-aware sibling of :func:`~mts.search.identities.search_identities`
(gap 17): given a pitch-class identity, enumerate every concrete registered
voicing inside a caller-supplied MIDI window that satisfies spacing / bass /
smoothness constraints. **Explicitly generative** (the cardinal rule): this
layer *invents register on purpose* — which is exactly why the ``register``
window is required, never defaulted. The engine does not choose a register for
the caller; supplying the bound is the caller's generative act.

Space and honesty:

- The raw space is the product of per-pc candidate counts inside the window —
  exactly computable **before** enumerating. If it exceeds the guard the call
  raises with an actionable message (narrow the window); enumeration is never
  silently truncated, so ``count`` is always the true total. ``truncated``
  means only that ``limit`` cut the *reported* list (the identities contract).
- Slice 1 voices each pitch class exactly once (voices == cardinality).
  Doublings / omissions (voice count N ≠ cardinality — the rest of A8's gap-17
  ask) are the recorded second slice.
- ``root=None`` searches **voicing templates** — the registered+rootless corner
  of the identity lattice (gap 17's own framing). Named-shape labels require a
  root and are skipped for templates.

Ranking (the analysis half of gap 17): when ``from_voicing`` is given, every
match carries ``vl_from`` — the exact :func:`voice_leading_realized` cost
(``doubling.1``) from the reference — and matches are **sorted** by it (then
spread, then pitch content). Without a reference the order is (spread, pitch
content). Both orders are total and deterministic; ``vl_from`` stays a
continuous signal the caller may re-rank (rule 7: plural outputs).
"""

from __future__ import annotations

from collections.abc import Mapping
from itertools import product

from ..analysis.voice_leading import voice_leading_realized
from ..analysis.voicings import VOICING_LABELS, voicing_shapes
from ..core.realization import Realization
from ..rules.schema import Condition
from .fields import ScalarField
from .identities import SearchConstraintError, _is_number, _parse_scalar
from .results import VoicingMatch, VoicingSearchResult

# Upfront guard on the raw register-assignment space (product of per-pc
# candidate counts). Chosen so realistic queries (a 7-note set across ~5
# octaves ≈ 78k) pass while degenerate windows fail fast with advice.
_MAX_RAW_SPACE = 200_000

# Scalar per-voicing fields, checked with the same Condition machinery as
# identity search. Extraction happens against the computed per-voicing value
# dict (not a mask), so `extract` is unused here — kind/values still drive
# validation.
VOICING_FIELDS: dict[str, ScalarField] = {
    "spread": ScalarField("int", None, "total span in semitones, lowest to highest voice"),
    "bass_pc": ScalarField("int", None, "pitch class of the lowest voice", values=tuple(range(12))),
    "top_pc": ScalarField("int", None, "pitch class of the highest voice", values=tuple(range(12))),
    "top_midi": ScalarField("int", None, "MIDI number of the highest voice (contour handle)"),
    "center": ScalarField("float", None, "mean MIDI of the voicing (register center; gte/lte only)"),
    "voicing_type": ScalarField(
        "str", None,
        "named shape from the voicing registry (closed/drop2/…); requires a root",
        values=VOICING_LABELS,
    ),
}


def _pc_list(name: str, raw: object, errors: list[str]) -> tuple[int, ...] | None:
    if not isinstance(raw, (list, tuple)) or not raw:
        errors.append(f"{name}: must be a non-empty list of ints")
        return None
    out: list[int] = []
    for i, v in enumerate(raw):
        if isinstance(v, bool) or not isinstance(v, int):
            errors.append(f"{name}[{i}]: expected an int, got {v!r}")
        else:
            out.append(v)
    return tuple(out)


def search_voicings(
    pcs,
    *,
    root: int | None = None,
    constraints: Mapping,
    from_voicing=None,
    limit: int | None = None,
) -> VoicingSearchResult:
    """Enumerate every registered voicing of *pcs* satisfying *constraints*.

    ``constraints`` must include ``register: [lo, hi]`` (inclusive MIDI window —
    required: the engine never invents a default register). Optional fields:
    the scalars in :data:`VOICING_FIELDS`, ``no_interval_over_bass`` (directed
    pc-intervals 1..11 forbidden above the bass), and ``max_voice_leading``
    (requires ``from_voicing``). ``root=None`` searches voicing templates.
    Raises :class:`SearchConstraintError` with every problem at once.
    """

    errors: list[str] = []

    # --- identity -----------------------------------------------------------
    pc_tuple = _pc_list("pcs", pcs, errors)
    pc_set: tuple[int, ...] = ()
    if pc_tuple is not None:
        bad = [p for p in pc_tuple if not 0 <= p < 12]
        if bad:
            errors.append(f"pcs: pitch classes must be ints in 0..11, got {bad}")
        else:
            pc_set = tuple(sorted(set(pc_tuple)))
    if root is not None and (isinstance(root, bool) or not isinstance(root, int) or not 0 <= root < 12):
        errors.append(f"root: must be an int in 0..11 or None, got {root!r}")
        root = None

    # --- constraints --------------------------------------------------------
    if not isinstance(constraints, Mapping):
        raise SearchConstraintError(
            [f"constraints must be a mapping, got {type(constraints).__name__}"]
        )

    register: tuple[int, int] | None = None
    forbidden_iob: tuple[int, ...] = ()
    max_vl: int | float | None = None
    conditions: list[Condition] = []

    for field, raw in constraints.items():
        if field == "register":
            window = _pc_list("register", raw, errors)
            if window is not None:
                if len(window) != 2 or not all(0 <= m <= 127 for m in window) or window[0] > window[1]:
                    errors.append(
                        f"register: must be [lo, hi] with 0 <= lo <= hi <= 127, got {list(window)!r}"
                    )
                else:
                    register = (window[0], window[1])
        elif field == "no_interval_over_bass":
            ivs = _pc_list("no_interval_over_bass", raw, errors)
            if ivs is not None:
                bad = [i for i in ivs if not 1 <= i <= 11]
                if bad:
                    errors.append(
                        f"no_interval_over_bass: directed pc-intervals must be in 1..11 "
                        f"(mod-12 above the bass), got {bad}"
                    )
                else:
                    forbidden_iob = tuple(sorted(set(ivs)))
        elif field == "max_voice_leading":
            if not _is_number(raw) or raw < 0:
                errors.append(f"max_voice_leading: must be a non-negative number, got {raw!r}")
            else:
                max_vl = raw
        elif field in VOICING_FIELDS:
            cond = _parse_scalar(field, VOICING_FIELDS[field], raw, errors)
            if cond is not None:
                conditions.append(cond)
        else:
            known = ", ".join(
                sorted([*VOICING_FIELDS, "register", "no_interval_over_bass", "max_voice_leading"])
            )
            errors.append(f"{field!r}: unknown field (known: {known})")

    if register is None and not any(e.startswith("register") for e in errors):
        errors.append(
            "register: required — [lo, hi] MIDI window. The engine never invents a "
            "default register (cardinal rule); bounding the space is the caller's choice."
        )

    # --- cross-field requirements --------------------------------------------
    ref: tuple[int, ...] | None = None
    if from_voicing is not None:
        ref_list = _pc_list("from_voicing", from_voicing, errors)
        if ref_list is not None:
            bad = [m for m in ref_list if not 0 <= m <= 127]
            if bad:
                errors.append(f"from_voicing: MIDI numbers must be in 0..127, got {bad}")
            else:
                ref = ref_list
    if max_vl is not None and from_voicing is None:
        errors.append("max_voice_leading: requires from_voicing (the reference voicing)")
    uses_type = any(c.field == "voicing_type" for c in conditions)
    if uses_type and root is None:
        errors.append(
            "voicing_type: requires a root — named shapes are root-relative; "
            "a rootless template search cannot be shape-labeled"
        )
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
        errors.append(f"limit: must be a non-negative int or None, got {limit!r}")
    if errors:
        raise SearchConstraintError(errors)
    assert register is not None

    # --- bound the space (before enumerating — count stays honest) -----------
    lo, hi = register
    candidates = [
        [m for m in range(lo, hi + 1) if m % 12 == pc] for pc in pc_set
    ]
    space = 1
    for cand in candidates:
        space *= len(cand)
    if space > _MAX_RAW_SPACE:
        raise SearchConstraintError(
            [
                f"register: the window [{lo}, {hi}] gives a raw space of {space} register "
                f"assignments for {len(pc_set)} pitch classes (guard: {_MAX_RAW_SPACE}). "
                "Narrow the window (or split the search); the guard exists so 'exhaustive' "
                "never silently truncates."
            ]
        )

    # Named-shape fingerprints (root-relative registry; slice 1 labels exact
    # root-position spacings only — inversions report voicing_type=None).
    shapes: dict[tuple[int, ...], str] = {}
    if root is not None:
        closed_stack = sorted((pc - root) % 12 for pc in pc_set)
        for label, fingerprint in voicing_shapes(closed_stack).items():
            shapes.setdefault(fingerprint, label)

    reference = Realization.from_midi(ref) if ref is not None else None

    matches: list[VoicingMatch] = []
    for combo in product(*candidates) if space else ():
        midi = tuple(sorted(combo))
        bass = midi[0]
        iob = tuple(sorted({(m - bass) % 12 for m in midi[1:]}))
        if forbidden_iob and any(i in forbidden_iob for i in iob):
            continue
        values: dict[str, object] = {
            "spread": midi[-1] - bass,
            "bass_pc": bass % 12,
            "top_pc": midi[-1] % 12,
            "top_midi": midi[-1],
            "center": sum(midi) / len(midi),
            "voicing_type": shapes.get(tuple(m - bass for m in midi)),
        }
        # Condition.matches(None) is False (absent claims never match), so a
        # voicing_type filter passes labeled voicings only — rules semantics.
        if not all(cond.matches(values[cond.field]) for cond in conditions):
            continue
        vl_from: int | None = None
        if reference is not None:
            vl_from = voice_leading_realized(reference, Realization.from_midi(midi)).distance
            if max_vl is not None and vl_from > max_vl:
                continue
        matches.append(
            VoicingMatch(
                midi=midi,
                spread=values["spread"],  # type: ignore[arg-type]
                bass_pc=values["bass_pc"],  # type: ignore[arg-type]
                top_pc=values["top_pc"],  # type: ignore[arg-type]
                top_midi=values["top_midi"],  # type: ignore[arg-type]
                center=values["center"],  # type: ignore[arg-type]
                intervals_over_bass=iob,
                voicing_type=values["voicing_type"],  # type: ignore[arg-type]
                vl_from=vl_from,
            )
        )

    if reference is not None:
        matches.sort(key=lambda m: (m.vl_from, m.spread, m.midi))
    else:
        matches.sort(key=lambda m: (m.spread, m.midi))

    # Echo the normalized query (the blind-agent transparency contract).
    echo: dict = {"register": [lo, hi]}
    for c in conditions:
        if c.op == "eq":
            echo[c.field] = c.value
        elif c.op == "in":
            echo[c.field] = {"in": list(c.value)}  # type: ignore[arg-type]
        else:
            echo[c.field] = {c.op: c.value}
    if forbidden_iob:
        echo["no_interval_over_bass"] = list(forbidden_iob)
    if max_vl is not None:
        echo["max_voice_leading"] = max_vl

    count = len(matches)
    truncated = limit is not None and count > limit
    reported = tuple(matches[:limit]) if limit is not None else tuple(matches)
    return VoicingSearchResult(
        pcs=pc_set,
        root=root,
        constraints=echo,
        from_voicing=ref,
        space=space,
        count=count,
        matches=reported,
        truncated=truncated,
    )


__all__ = ["search_voicings", "VOICING_FIELDS"]
