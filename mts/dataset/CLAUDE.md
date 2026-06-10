# mts/dataset — The enriched record (unit of analytical output)

The **unit-of-record layer** (Phase 3 Slice 4). It *integrates* the typed results
from `analysis`, `temporal`, and `context` into one reproducible
`DatasetRecord`, and groups records into a `Dataset`. This is the unit Phase 4
(MCP) emits and Phase 4.5 ranks.

**Why a separate package (not `analysis/results.py`).** The record nests analysis
results *and* temporal placement *and* a `DisplayContext` snapshot — so it imports
from `temporal` and `context`. But `temporal` already imports `analysis.results`;
putting the aggregator in `results.py` would invert that dependency and risk a
cycle. The record's whole job is to sit *above* analysis/temporal/context — a layer
they don't import back. Keep it that way: **nothing in `analysis/`, `temporal/`, or
`core/` may import `mts.dataset`.**

## The record shape (`record.py`)

Tiers mirror the core data-model chain `event → realization → identity key`, each
present only when its spec level is satisfied (cardinal rule: reduce never invent):

- `identity` — **always.** The PC-set key (`mask`, `pcs`, `cardinality`,
  `spec_level`). Numeric/PC-only.
- `analysis` — the numeric enrichment: `chord` / `scale` single-reading analyses,
  `interpretations` (every valid naming), `in_key` (chord placed in an
  `AnalyticalContext`). Reuses `analysis.results` / `analytical_context` types —
  don't duplicate fields here.
- `realization` — **register tier**, present only for register-bearing input
  (`midi` + a `VoicingAnalysis` from `analyze_voicing`).
- `placement` — **temporal tier**, present only for time-based material (beats,
  plus seconds + bar/beat when a `Sequence` supplies tempo/meter).

Plus the **reproducibility / presentation layer** (what `minimal()` sheds):
`source` (provenance: original notation + parsed `spec_level`), the
`analytical_context` / `display_context` snapshots, and the **derived** `display`
block. The numeric core is **canonical**; `display` is rendered from the snapshotted
`DisplayContext` so the record reproduces byte-for-byte (same input + same context).

`SCHEMA_VERSION` is explicit on every record/dataset — bump it on a breaking shape
change.

## Granularity: flat leaves + container (and the reflection point)

Records are **flat leaves** grouped by a `Dataset` — *not* a recursive record. This
is the honest fit for today's flat literal-PC-set `segment()` and flat harmonic
rhythm. Forward-compat for an eventual recursive/hierarchical model is preserved by
**composition**, and three things must stay true so that transition is additive, not
a teardown:

1. `kind` is a **level discriminator** (`object` / `event` / `segment`; open set) —
   a future `harmony` / `form` level adds an entry, no migration.
2. `index` is a **stable handle** a future parent/child layer can reference.
3. `Dataset` is a **grouping**, *not* asserted to be a flat, non-overlapping,
   exhaustive timeline partition. Don't add code or docs that assume "one record ==
   one disjoint slice" — that assumption is what would block recursion.

**When does flat-vs-recursive become relevant?** When a genuine parent/child
*musical* layer arrives: (a) harmonic segmentation that nests non-harmonic tones
under their parent harmony (the Phase 2 deferred refinement), or (b) a form/section
layer above progressions. At that trigger, add `Dataset`-nesting or
`DatasetRecord.children` — see ROADMAP Phase 3 Slice 4 "reflection point".

## Builders (`builders.py`)

Assemble only — they call existing analysis entry points and capture context; they
compute nothing new. `record_from_chord` (identity + analysis + optional
register/in_key/display), `record_from_segment` (adds placement; rootless identity →
namings, no single rooted `chord`), `dataset_from_sequence` (segments → indexed
records + `TemporalSummary`). When adding a builder for a new input, follow the same
rule: reuse a typed-analysis function, snapshot any context, never re-derive.

Planned work for this layer is tracked in [ROADMAP.md](../../ROADMAP.md) (the
single source of truth for direction) — link phases from here; don't record
plans here.
