# mts/search — Constraint search (inverse analysis)

The *inverse* of `analysis/`: instead of "what is this set?", answer "which sets
satisfy these constraints?" by exact, exhaustive enumeration over the 4096-mask
identity universe (ROADMAP Phase 4, the marquee agent-facing tool).

**Generative-side, by the cardinal rule.** A search constraint and a checkable
rule are the same predicate pointed in opposite directions, so the scalar
predicate machinery *is* the ruleset engine's `Condition` (eq/in/gte/lte),
reused over an **identity** field vocabulary — this layer sits above `analysis/`
and `rules/` and never reimplements either.

- `fields.py` — `IDENTITY_FIELDS` (scalar extractors over the `core.setclass` /
  `core.bitmask` substrate: cardinality, ic1..ic6, rotational_period,
  is_achiral, no_consecutive_semitones, and the float `df1..df6` DFT magnitudes
  — range-queried, gte/lte only) + the structural `contains` / `contained_in`
  predicates. Every field is a pure, cached mask function. `df*` are T/I-invariant
  (so honest set-class fields) and the full `|f1..f6|` vector is echoed on every
  match as `dft_magnitudes` for ranking, not just filtering.
- `identities.py` — `search_identities(constraints)`: strict-total validation
  (the blind-agent ruleset contract — collect *all* errors), enumeration,
  typed result. Default universe is the 223 set classes; `expand_transpositions`
  widens to every rooted image.
- `voicings.py` — `search_voicings(pcs, root=, constraints=, from_voicing=)`
  (gap 17 slice 1): bounded register enumeration. **`register: [lo, hi]` is
  required — the engine never defaults a register** (the cardinal rule in API
  form: inventing register is the caller's declared generative act). The raw
  space is computed *before* enumerating and an over-large window **raises**
  with advice — enumeration is never silently truncated, so `count` is always
  the true total (`truncated` only ever means `limit`). Slice 1 voices each pc
  exactly once (doublings/omissions = slice 2). `root=None` searches voicing
  **templates** (the registered+rootless lattice corner). With `from_voicing`,
  matches carry `vl_from` (exact `voice_leading_realized`, `doubling.1`) and
  come back ranked by it — gap 17's ranking half; callers may re-rank (rule 7).
- `repair.py` — `repair_sequence(sequence, ruleset, …)` (conformance repair,
  slice 1): impose a ruleset on existing material via **minimal re-pitch edits**
  — bounded, deterministic search with the Phase 4.6 **evaluator as the oracle**
  (every candidate re-evaluated in full, whole ruleset). Candidates from the two
  pitch-driven families: voice-motion pair transitions (slice 1) + melody note
  locations incl. same-voice neighbors (slice 1b); lexicographic minimality (fewest notes, then |semitones|; exact via
  iterative deepening); **hard-must-hold, budget-must-hold** (an over-budget rule
  gates exactly like a hard one — #230 — the search reduces the rate back to the
  ceiling, not to zero), soft-must-not-worsen; honest refusals (a hard/over-budget
  violation outside voice_motion/melody, search-budget exhaustion). Generative-side
  — edits invent pitches.
- `results.py` — `IdentitySearchResult` / `IdentityMatch` /
  `VoicingSearchResult` / `VoicingMatch` / `RepairResult` / `Repair` /
  `RepairEdit` (`to_dict()`).

**Decision 12 (containment granularity) — read before adding fields.** In the
set-class universe, `contains`/`contained_in` fold inversions (a shape and its
mirror are one class); in `all_masks` they are strictly rooted. Every field must
be a genuine invariant of the universe it is queried in — which is why *signed*
chirality is **not** a set-class field (only `is_achiral` is). Handedness- and
register-sensitive search belongs to the planned `search_voicings` slice.

Plans live in [ROADMAP.md](../../ROADMAP.md) (Phase 4) — link phases here; don't
record plans in this file.
