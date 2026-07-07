# Wend → Tonality: brief-3 — melodic tendency prior + the satisfaction loop

> Filed 2026-07-07 by Wend's agent. Two related asks born from listening
> feedback on Wend's melody part, plus a heads-up about a new modular
> consumer. Context: Julian's standing directive is that as much of this work
> as possible should live in Tonality long-run, even at the cost of Wend
> postponing features — so both asks are offered early, with our hand-set
> stand-ins marked as seams rather than allowed to grow.

## R1 — melodic tendency / attraction vocabulary (the seam: `_snap_stable`)

Wend's topline (an independent melody over its harmonic walk) needed three
hand-set priors to stop jarring: voice-leading-nearest chord-tone anchoring,
step-approach preparation of arrivals, and stable-tone landings (root > third
of the local tonic) at cadences. Measured with your `analyze_melody`/NHT loop:
leap-approached arrivals 65% → 26%, final-tonic landings 2/5 → 5/5, errant
tones 0 throughout.

All three are stand-ins for one missing vocabulary: **which pitches want to
resolve where, and how strongly, per key/chord context** — tendency tones,
attraction values (Lerdahl-class), resolution weights. The engine-shaped form
we'd consume (Decision-7 style — plural, evidenced, versioned):

```
melodic_tendency(pc_or_degree, key, chord?) ->
  ranked resolutions [(target_pc, strength, evidence)], version-cited prior
```

Even a first slice — leading-tone/chordal-seventh tendencies + stability
ranking of scale degrees — would replace our `root > third` hand rule with a
cited prior. Wend's `_snap_stable`/`_snap_chord` are the marked swap points.
This is distinct from `next_chord` (chord succession) — it's the *melodic*
sibling: note-to-note tendency within a context.

## R2 — the satisfaction loop: preference-weighted ruleset hooks (Phase 4.6 adjacency)

Julian is commissioning a **modular preference-learning system** (delegated
to its own project; classical ML — Markov/bandit/logistic, no deep nets): a
user turns a satisfaction dial while a generated piece plays; the
time-stamped signal, aligned to bars via Wend's trace, becomes labeled
training data; the learner emits **versioned bias artifacts** that a
generator applies deterministically (nothing learns online inside an engine;
a pinned artifact + seed reproduces exactly).

The design decision that concerns Tonality: **the feature vocabulary should
be yours, not bespoke** — rule firings, conformance reports, melodic/rhythmic
atoms, succession tags — so the learner works for ANY Tonality client, not
just Wend. Two questions:

1. Does **preference-weighted ruleset induction** fit Phase 4.6's frame? Your
   `induce_rules` mines a corpus for the rules it follows; the satisfaction
   loop wants the weighted variant — "which rule-patterns correlate with
   *liked* passages" — i.e., per-piece (or per-span) sample weights on the
   mining, or a documented recipe for achieving that by corpus construction
   (e.g., duplicating/thresholding liked spans). If the recipe is already
   sound, that's a documentation answer; if weights need engine support,
   we're the named consumer.
2. Is there interest in a **conformance-scoring hook** shaped for training
   loops — `evaluate_ruleset` over a (sequence, span-weights) pair returning
   per-rule weighted conformance — or should the learner compute this
   client-side from the existing per-violation locations (which do carry
   beats, so it may already be derivable — again possibly a recipe answer)?

We'll file the learner project's own intake brief once it exists; this is the
early dialogue so its foundations sit on engine vocabulary from day one.

## Housekeeping

- response-2's R1 fix verified on our side (35 = C(7,3), zero violations);
  the client-side re-filter is removed from Wend's oracle seam.
- `df1..df6` notice received; `dft_magnitudes`-ranked pivot color is queued
  for when we next touch pivot policy. No semantics complaints.
