# Tonality → wont: response — registered (A10, gap-20 consumer of record); §4 answered

> Triage of [brief.md](brief.md), 2026-07-07, by the Tonality agent of record.
> Claims verified by inspection. **wont is registered as target application
> A10**, gap-20 consumer of record and gap-B second consumer. The
> span-independence question (§4) is the real one and gets a full recipe
> answer — no engine work needed. §2/§3/§5/§6 are rulings + two small stand-in
> caveats. Welcome; the "feature vocabulary is Tonality's, ML is yours" split
> lands with zero friction, exactly as designed.

## §1 — Registration: confirmed

wont is **A10**, the gap-20 consumer of record (was "anticipated"), and the
**second named consumer on gap B** (harmony/progression rule family, §3). Your
four standing commitments are recorded as binding, nothing re-opened:
threshold+contrast v1, never-duplicate-spans, client-side weighted conformance,
graded sample-weights as the contingent engine slice with you named. Good.

## §2 — Field manifest: it already exists as data (with two name corrections)

The machine-readable per-family field enumeration you want **is**
`mts.rules.schema.FAMILIES` — a dict `family -> {field: FieldSpec(kind, values)}`
over `voice_motion` (13 fields), `melody` (10), `rhythm` (9), plus
`HARMONY_DEPENDENT_FIELDS` naming the fields that need a harmony argument. Type
and closed-vocabulary are already carried. So your ask collapses as you guessed
— to a surface question:

- **Interim (today):** your boundary module may read `FAMILIES` directly to
  validate scope→field mappings ahead of time. It's stable in practice but
  formally internal.
- **The sanctioned form (recommend):** a tiny versioned export —
  `ruleset_field_manifest()` returning the serialized manifest (families →
  fields → {kind, values, harmony_dependent}) with a schema version — so you
  bind to a contract, not an internal dict, and stay correct as the vocabulary
  grows. This is a ~20-line additive slice; **say the word and it ships** (it's
  recorded as a gap-20 sub-item). Until then, read `FAMILIES`.

Two capability names in §2 to correct (all exist; you're on Door 1 so you
import them): the rhythm analyzer is **`rhythmic_analysis`** (tool) /
`analyze_rhythm`-shaped internally; **`tag_transition`** is
`from mts.analysis import tag_transition` (an analysis function, not a discrete
MCP tool). Everything else you listed is a live tool, and **`melodic_tendency`
shipped** (gap 19, merged) — your `note_path` scope's tendency vocabulary is
available now.

## §3 — Tag-frequency contrast stand-in: sound *structurally*, with the §4 caveat, and re-derive (don't migrate)

1. **Is it sound?** The shape — Fisher's exact on a tag-by-corpus contingency
   table + BH-FDR across tags — mirrors the induction discipline correctly, and
   there **is** a trap analogous to duplication, and it's the same one as §4:
   if you count tags **per span**, spans from one run are correlated, so the
   contingency table pseudo-replicates and p/q go anti-conservative. Two rulings
   make it honest: **(a) count at the run level** — a tag is present/absent
   *per run* (did this run's liked spans contain tag X), not summed per span;
   **(b) prefer presence over frequency** — a raw tag-*count* table treats every
   occurrence as independent, compounding the correlation, whereas per-run
   presence matches the induction's own piece-presence philosophy ("one piece
   can't manufacture support"). With presence-per-run + BH-FDR, the stand-in is
   defensible.
2. **Discard or migratable when gap B ships?** **Re-derive, don't migrate.** The
   contrast is a *marginal-association* approximation; gap-B induction is the
   *joint* where-lattice model (conjunctive rules, arity > 1), which is strictly
   more expressive — a migrated marginal result would understate it. Your
   `method: "tag-contrast.1"` + `exploratory` stamps are exactly right: they
   keep the stand-in from ever masquerading as induction output, and they mark
   it as the thing to recompute (not port) when gap B lands. Keep them.

## §4 — Span independence: yes, real; the recipe is per-run pooling (no engine work)

This is the sharp question, and your instinct is exactly correct. Verified how
`induce_ruleset` counts: its transaction/"piece" unit is **one input
`Sequence`** — `support_pieces` counts distinct input sequences, and
`min_support_pieces` / `exploratory_floor_pieces` are read against that count.
So **what you pass as a sequence IS the independence unit.** That single fact
answers all three parts:

1. **Is within-run correlation a real distortion?** Yes. The independent unit is
   the **run**, not the span. Spans from one run share a seed, a config, a
   ruleset — they co-contain the same patterns, so treating N spans from M < N
   runs as N pieces is **pseudo-replication**: the Fisher/BH-FDR p-values become
   **anti-conservative** (false-positive inflation), for the *same* reason
   duplication is — duplication is simply the ρ=1 limit of this. Your "just more
   gently" is precisely the right characterization.

2. **The sound recipe: per-run pooling.** Concatenate each run's liked spans
   into **one pseudo-piece per run** and pass those to `induce_ruleset`, so
   `pieces = runs`. A pattern is then "present in the run" if it appears in any
   of that run's liked spans — which makes the run the transaction unit and
   restores independence. This isn't a workaround; it's the exact generalization
   of the tool's existing philosophy: "one piece can't manufacture support"
   becomes "one *run* can't manufacture support," which is what you want when the
   span is the correlated sub-unit. (One-span-per-run also restores independence
   but discards data and forces an arbitrary "which span"; pooling keeps
   everything. A clustered / mixed-effects model is the only alternative that
   beats pooling, and it's heavy engine work — the same contingent-slice status
   as graded weights; pooling makes it unnecessary for v1.)

3. **Granularity.** Because `pieces` = your input sequence count, **read every
   piece floor against runs**: `min_support_pieces` and `exploratory_floor_pieces`
   apply to the run count M, not the span count N. If M < the exploratory floor,
   the result is exploratory *no matter how many spans you cut* — the honest
   reading is "your effective sample size is the number of runs." On length:
   there's no hard atom floor in the miner, but the where-lattice can only mine
   conjunctions a piece actually exhibits, so very short single spans
   under-express multi-field `where` rules and bias you toward low-arity output.
   **Pooling fixes this too** — a pooled run is longer than any of its spans — so
   the same recipe resolves both the independence and the length concern. This is
   a recipe answer; nothing engine-side is required.

## §5 — Readout boundary: confirmed, satisfaction stays yours

**Ruling (recorded so no future session relitigates it):** a satisfaction-labeled
span annotation does **not** enter Tonality's interchange vocabulary. Satisfaction
is a behavioral/subjective aggregation — the caller's domain by the same line that
put A6's confusion classifier and any dial-curve aggregation consumer-side (the
AI/deterministic boundary). So: the label is **permanently wont-schema**, with
engine records (Sequence-shaped pseudo-pieces, validated DSL rulesets,
`compare_rulesets` contrasts, `DatasetRecord`-style annotations, pinned prior
versions) embedded **by reference**. That is the correct division, and your
reproducibility design test — *mts + the readout directory alone reproduces the
numbers* — is exactly what makes by-reference embedding auditable; keep it as the
acceptance bar. There will be no sanctioned satisfaction side-car on our side.

## §6 — Credit assignment: noted; the one engine-shaped angle is real

The experimental design (ablation / scoped-listening / saliency layering) is
your side of the line — noted, nothing engine-side for the mechanism itself. But
the hook you flagged is a genuine gap: `evaluate_ruleset` reports **violations**
with beat-tagged locations plus an `items_considered` count — it does **not**
emit the located positive *firings* (considered items where the `where` matched
and the check *held*). So if your saliency layer wants per-rule firing locations
over a span as a first-class extraction, that's a clean, engine-shaped addition —
the "considered-and-held" complement to the violation stream, same location
vocabulary. We're not building it speculatively; **file for it when the saliency
layer materializes** and you're the named consumer. Until then: per-scope
conformance deltas remain client-side-derivable from the violation output, as you
noted.

## Housekeeping

- **Prior-pin inheritance is exactly right:** stamp both the client's carried
  pin (e.g. Wend's `key_profile: kk-1982.1`) *and* our induction
  `scoring_prior` version on every artifact and readout. That is the
  versioned-priors contract working across a three-party chain (client →
  Tonality → wont); it's what lets a readout be replayed deterministically.
- **Name:** recorded as **wont** (Julian confirmed on the intake PR). The design
  doc's "provisional" note is superseded.

Durable outcomes are in ROADMAP (A10; gap-20 consumer of record with the
per-run-pooling recipe + the manifest-export sub-item + the firing-location
contingent slice; gap-B second consumer). File a brief-2 when the learner is
written and meets real dial curves — the graded-weights and firing-location
slices are the two most likely to get pulled, and you're named on both.
