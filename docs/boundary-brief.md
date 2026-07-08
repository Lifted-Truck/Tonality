# Intake brief — the determinism boundary program

> **Status: proposal, not decision.** Per ROADMAP.md's own rule, nothing here is
> decided until folded into ROADMAP.md. This brief is for the dev agent to
> assess, slice into numbered gaps, and record — including any *rejections*,
> which should be recorded with the same care. Author: Julian (via assessment
> session, 2026-07-07). Source of empirical claims: the repo at commit
> `34fff86` (PR #164, gap-D slice 1).

## 1. The north-star extension

Tonality's existing north star is an engine that turns notation into enriched,
contextualized datasets. This brief proposes a research-direction extension:

**Map, empirically, the boundary beyond which explicit rulesets stop advancing
musical outcomes and only learned statistical models can proceed — and push
Tonality's deterministic machinery as close to that boundary as it can go.**

The framing matters. The boundary is *not* "determinism vs ML." Forty years of
literature locates it more precisely:

- Constraint/ruleset systems capture **well-formedness** — membership in a
  feasible set. They are complete for local syntax and prohibitions.
- What they cannot capture is **preference within the feasible set**. Style is
  a probability distribution over well-formed material, not a membership
  predicate. (Ebcioğlu's CHORAL, the strongest pure-rule system ever built for
  this, harmonized Bach chorales from ~350 rules — its known failure mode was
  output that is *correct but characterless*.)
- The empirical frontier: local syntax → rules; long-range dependency, schema
  *selection*, and expressive preference → statistics. The middle ground
  (constrained stochastic generation, learned-but-inspectable rule formats) is
  well-mapped territory and is where Tonality should live.

A successor project (ML that *derives* rulesets and emits them in a
deterministically manipulable format) is anticipated downstream. Tonality's
job is to make the ruleset format, evaluator, and benchmarks strong enough
that such derived rulesets have somewhere rigorous to land. Note that
`induce_rules` already exists — the derivation arc has a deterministic seed in
this repo today.

## 2. Where the rules layer stands (empirical, as of `34fff86`)

Findings from direct inspection of `mts/rules/schema.py` and the MCP surface:

- **Three atom families**: `voice_motion`, `melody`, `rhythm`. Rules are
  conjunctions of per-item field conditions, scoped to the family's natural
  item (a voice-pair transition, one note).
- **No voice-count or ensemble concept.** `voice_a`/`voice_b` are string
  identities on pairwise transitions. "When ≥3 voices are sounding" is
  inexpressible. Texture, spacing, and crossing have no global scope.
- **No aggregation or quantification.** Conditions AND over fields on a single
  item. "At most one leap per bar," "no more than N consecutive parallel
  thirds" — inexpressible. This is an expressiveness-class limit, not a
  missing field.
- **`voice_motion` cannot see harmony.** Harmony-dependent fields
  (`is_chord_tone`, `nht_type`) exist only in the `melody` family. Movements
  conditioned on harmonic context (e.g., resolution rules) cannot be stated
  where the motion lives.
- **No phrase / section / cadence-plan / form vocabulary.** Rules see a flat
  stream of local atoms.
- **The evaluator checks; nothing generates.** `evaluate_ruleset` reports
  firings. No component searches the space a ruleset defines (the bounded
  voicing enumerator in `search/` is the nearest relative, but it is not
  ruleset-driven).

These are not defects — they are the honest current perimeter, and the program
below is a plan for moving it deliberately.

## 3. Benchmark ladder

Four benchmarks, ordered by distance from the current DSL. Each is an
acceptance test in the ROADMAP's existing sense: it decomposes into engine
capabilities, and any capability no phase provides is a gap to record.

**B1 — First-species counterpoint generation.** Given a cantus firmus, emit a
valid counterpoint line by search over the existing
`first-species-counterpoint.json` ruleset. The ruleset exists; the generator
does not. Precedent proving feasibility: Herremans' **FuX** (metaheuristic
search over Fux's rules). This is the cheapest benchmark and the one that
converts the rules layer from checker to generator. Extend to later species as
DSL vocabulary allows.

**B2 — Chorale harmonization, graded against the Riemenschneider corpus.**
The canonical shared benchmark of the field: CHORAL (symbolic), BachBot and
DeepBach (neural) all report against Bach's 371. Using it lets Tonality's
symbolic ceiling be compared against neural systems on identical ground.
Requires substantial DSL growth (§4). Target claim to test: a plausible
baroque chorale *can* be produced from rulesets alone — CHORAL proved it in
1988 — and the interesting result is *where its quality plateaus relative to
statistical systems*, which is the boundary made visible.

**B3 — Galant schema recognition and production.** Gjerdingen's schemata
(*Music in the Galant Style*) are precisely "rulesets with slots": partially
ordered event patterns with soft expectations. This is the richest middle
territory between hard constraints and distributions, and the natural home
for a schema atom family or a schema layer atop rulesets.

**B4 — Long-range form (binary/da-capo structure, fugal exposition).**
Explicitly *beyond* flat conjunctive rulesets — reachable only with a
hierarchical grammar stratum (GTTM territory, already researched for this
project). Registered as a horizon marker, not near-term scope.

**The boundary metric.** For each benchmark corpus: the **cross-entropy gap
on held-out data between Tonality's best constraint(+Markov) system and a
neural baseline**, tracked as DSL expressiveness grows (Conklin-style
evaluation). Where the gap stops closing under further DSL enrichment, the
boundary has been located *empirically* rather than by argument. This metric
is the program's single most important deliverable.

## 4. Candidate gaps for registration

For the agent to assess, re-slice, renumber, and record (or reject with
reasons) per ROADMAP conventions:

1. **Harmony atom family.** Chord-to-chord transitions as first-class rule
   items (root motion, quality change, function change, inversion), plus
   harmonic context made visible to `voice_motion` atoms. Prerequisite for B2.
2. **Aggregation in the DSL.** Counting and windowed quantification ("at most
   N per bar/phrase," "no run of K consecutive X"). This is a schema-version
   bump (`ruleset-fields` manifest) and an evaluator change; assess cost
   honestly — it changes the DSL's complexity class.
3. **Ensemble/texture scope.** Voice count, global spacing, crossing, and
   register envelope as a scope rules can condition on.
4. **Ruleset-driven generation.** A search layer that treats a ruleset as a
   constraint system and enumerates/samples satisfying continuations. B1 is
   its acceptance test. Natural relatives: the existing `search/` bounded
   enumeration and `next_chord`.
5. **Soft rules / weights.** Preference expressed as weighted rules rather
   than hard predicates — the minimal concession to "style is a distribution"
   that keeps everything deterministic and inspectable. Bridges toward
   Markov-constraint hybrids (Pachet & Roy) without importing ML.
6. **Corpus evaluation harness extension.** Held-out cross-entropy scoring
   against the existing `validation/` corpus machinery; add Riemenschneider
   ingestion. This is what makes §3's boundary metric real.
7. **Schema layer (B3).** Deferred until 1–5 settle; record as assessed,
   unscheduled, in the existing gap-21 style.

Suggested near-term order: 4 (with existing DSL, against B1) → 1 → 6 → 2 →
3/5 as evidence demands. Generating *before* enriching keeps every DSL
addition accountable to a measurable benchmark delta.

## 5. Trimmed under scrutiny

Recorded so it is not re-litigated silently:

- **"Genre breakdown by structure" via flat rulesets — trimmed as stated,
  restratified instead.** Genre lives simultaneously in surface syntax
  (current DSL stratum), schema inventory (B3), and hierarchical form (B4).
  A flat conjunctive DSL reaches only the first stratum; no amount of field
  vocabulary fixes this, because it is an expressiveness-class problem. The
  claim "our rulesets can break down genres" is therefore replaced by: *the
  ruleset layer captures a genre's syntax stratum; schema and form strata
  require the B3/B4 machinery respectively.*
- **"Determinism vs ML" as the boundary framing — trimmed.** Replaced by
  feasible-set vs distribution (§1), with the cross-entropy gap (§3) as its
  measurable form.

## 6. Research anchors

For grounding, citation, and further reading as gaps are worked:

- Ebcioğlu, *An Expert System for Harmonizing Four-Part Chorales* (CHORAL,
  1988) — the pure-rule ceiling, empirically demonstrated.
- Herremans et al., FuX and MorpheuS — rule-based counterpoint via
  metaheuristic search; constrained optimization with tension profiles.
- Pachet & Roy, Markov constraints — steerable stochastic generation under
  hard constraints; the canonical middle-ground formalism.
- Conklin & Witten, multiple viewpoint systems — learned, inspectable,
  manipulable predictive models; the closest existing relative to "ML-derived
  rulesets in a deterministic format," and the recommended template for the
  successor project's output format.
- Meredith, SIA/COSIATEC and MDL pattern discovery — compression-based
  pattern induction; relevant to `induce_rules`' future.
- Gjerdingen, *Music in the Galant Style* — schema theory (B3).
- Lerdahl & Jackendoff, GTTM — the hierarchical stratum (B4); prior research
  for this project already exists.
- Liang et al. (BachBot), Hadjeres et al. (DeepBach) — the neural baselines
  for §3's boundary metric.

## 7. What this brief does not decide

License questions, phase numbering, C++ port interaction, and whether any of
this outranks currently scheduled gaps are all the agent's and ROADMAP's call.
If the program is adopted, the boundary metric (§3) should be recorded as a
decision; everything else can enter as ordinary gaps.
