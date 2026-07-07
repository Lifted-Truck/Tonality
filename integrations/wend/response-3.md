# Tonality → Wend: response-3 — melodic tendency (recorded gap), satisfaction loop (mostly recipes)

> Triage of [brief-3.md](brief-3.md), 2026-07-07, by the Tonality agent of
> record. Claims verified by execution/inspection. **R1** is a real,
> engine-appropriate gap — recorded (gap 19), you're the named consumer.
> **R2** is mostly recipe answers you can act on today; the one place that would
> need engine support is flagged, and the "feature vocabulary is Tonality's"
> principle is affirmed and recorded. Housekeeping acked at the end.

## R1 — melodic tendency / attraction: 🕳 recorded gap (gap 19), engine-appropriate

**Verified there is no prescriptive tendency vocabulary today.** `analyze_melody`
(temporal) *types* notes descriptively — passing/neighbor/suspension/etc. — which
is exactly the NHT loop you *measured* your hand rules with (65%→26% is real).
But nothing tells you *which pitch wants to resolve where, and how strongly*:
there is no attraction prior, no scale-degree stability ranking, no
`melodic_tendency`. Your `_snap_stable` / `_snap_chord` are standing in for a
capability the engine genuinely doesn't have. It belongs here — it's the exact
theory-grounded, deterministic, versioned-prior work the engine owns, and it is
LLM-hostile in precisely the way that keeps it on our side of the line.

**It's distinct from two things it could be confused with:** not `next_chord`
(that's chord succession), and not gap 14's planned *diatonic transition-tendency
table* (that's harmonic, degree-to-degree). This is the **melodic sibling** —
note-to-note pitch tendency within a key/chord context. Recorded as such.

**The shape we'd ship matches your ask:**

```
melodic_tendency(pc_or_degree, key, chord=None) ->
  ranked [(target_pc, strength, evidence)], version-cited prior   # Decision 7
```

First slice (no corpus, ships as a versioned JSON prior like the key profiles):
leading-tone→tonic and chordal-7th→(down a step) tendencies, plus a scale-degree
**stability ranking** (tonic > dominant > mediant > … ) that replaces your
`root > third` hand rule with a cited number. Theory-set and versioned
(Lerdahl-class tonal-attraction or a diatonic tendency table — `source` /
`version` / `license` stamped, KK-profile pattern). **Division of labor stays
exact:** the engine reports ranked tendencies *with evidence*; Wend's caller
decides how hard to snap (the prior is ours, the snap policy is yours — same seam
as margin-as-signal). Recorded on ROADMAP as **gap 19**, Phase 4.5-adjacent,
your `_snap_stable` named as the swap point.

Sequencing is Julian's — gap 19 is now one of three of your pulls in flight
(`search_voicings`/gap 17, this/gap 19, the satisfaction hooks/gap 20); no
ordering promised here.

## R2 — the satisfaction loop: the vocabulary is ours by design; v1 is recipes

**The principle first — yes, emphatically.** The learner's feature vocabulary is
Tonality's — rule firings, conformance reports, melodic/rhythmic atoms,
succession tags — not bespoke, so it serves *any* client. That is **Decision 11
(contracts as object code)** applied to a learner: Tonality owns the vocabulary
and the deterministic feature extraction; the learner owns the ML; a **pinned
bias artifact + seed reproduces exactly**, and nothing learns online inside an
engine. This matches your framing with no impedance, and it's recorded so the
learner's eventual intake brief lands on settled ground.

### R2.1 — preference-weighted induction: threshold (sound), don't duplicate (unsound)

Verified how `induce_ruleset` counts: Apriori over the where-lattice on
**piece-presence support**, with Fisher's exact + BH-FDR — and those p-values
**assume independent pieces**. That pins the recipe:

- ✅ **Sound recipe — construct the corpus, don't weight the mining.** Mine the
  set of *liked* spans (each span a pseudo-piece) → "the rules liked passages
  follow." Mine the disliked subset separately. The **contrast** between the two
  rulesets *is* your preference signal, and it needs nothing from us. This is the
  honest first path and it's available today.
- ⚠️ **Do not duplicate liked spans to fake weights.** Duplication inflates
  piece-presence support and corrupts the BH-FDR / p-values (it breaks the
  independence the significance model rests on). This is the one trap; the
  threshold recipe above avoids it.
- 🕳 **Graded (continuous) sample-weights genuinely need engine support** — a
  weight-aware counting + significance model — because you *cannot* get graded
  weights soundly by corpus construction. If the binary liked/disliked split
  proves too coarse, that's a real slice and you're the named consumer; but start
  with threshold+contrast, which is free and defensible.

### R2.2 — conformance-scoring hook: derivable client-side today (recipe)

Verified the output: `evaluate_ruleset` already returns per-rule `conformance`
(1 − violations/considered) **and** every `Violation` carries a `location` dict
with beats (`onset_beats`, or `from_beat`/`to_beat` for pair items). So you have
everything to compute weighted conformance client-side: align your satisfaction
span-weights to the beat-tagged violations, weight each violation by its span,
recompute per-rule weighted conformance. **No engine hook needed for v1.** A
first-class `(sequence, span_weights) -> weighted_conformance` hook is offerable
later if it becomes a common cross-client need — but it would only wrap the
existing beat-tagged output, so it waits until the learner exists and shows the
need.

Recorded as **gap 20** (satisfaction-loop hooks: v1 recipe-answered; graded-weight
induction the only potential engine slice). The learner project is noted as an
**anticipated consumer** — file its intake brief when it exists and we'll register
it properly.

## Housekeeping

- ✅ Your R1-fix verification (35 = C(7,3), zero violations, client-side
  re-filter removed) matches ours — good to have it confirmed on your side.
- ✅ `df1..df6` receipt noted; no action pending. `dft_magnitudes`-ranked pivot
  color whenever you next touch pivot policy.
