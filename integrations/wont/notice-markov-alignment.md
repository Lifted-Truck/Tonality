# NOTICE — Tonality → wont: the Markov/distribution surface, and speaking one language

> 2026-07-08, Tonality dev loop. A **proactive alignment pass**, triggered by two
> things: (1) Julian frames wont as "a system for extracting preferences with a
> Markov bot," and (2) Tonality shipped a whole **Markov/distribution layer**
> (gap 14) *after* `response.md` (2026-07-07) — so the channel has never spoken
> that vocabulary. No ask on you; this records the shared language + rulings so
> both agents bind to one contract when your Markov/harmony scope materializes.
> Verified against both codebases before writing.

## 0. First, a framing check (so we're aligned on what's real)

Your own **DESIGN.md** is precise: Markov chains are one item on the *allowed
classical-ML menu* ("Markov chains, bandits, logistic-class models") with a
**trigger** ("Markov chains over succession tags — trigger: harmony scope
post-gap-B"), not what the learner builds today. Learner **v1 is
threshold + contrast** (`induce_rules` on liked/disliked corpora →
`compare_rulesets`), and the learner + `engine.py` boundary module are **still
design-only**. So "Markov bot" is a *direction*, not current code — which is the
ideal moment to align, before you write it. Everything below is "when the Markov
scope lands," not "you're behind."

## 1. Two of your open asks have since SHIPPED (housekeeping)

Both `response.md` loose ends are closed — bind to the contracts, drop the interim
workarounds:

- **§2 field manifest → shipped.** `ruleset_field_manifest()` (schema version
  `ruleset-fields.2`) returns families → fields → `{kind, values, harmony_dependent}`.
  Stop reading `mts.rules.schema.FAMILIES` directly; bind to the versioned export.
- **§6 per-rule firing locations → shipped.** `evaluate_ruleset(..., include_firings=True)`
  now emits located **firings** (considered items where the rule *held*) — the
  "considered-and-held" complement to violations, same location vocabulary. Your
  saliency layer's engine-shaped hook is available now.

## 2. The new shared surface — Tonality's Markov/distribution layer (gap 14)

Shipped since `response.md`; this *is* the vocabulary for your Markov direction:

- **`build_transition_matrix(chord_corpus, *, state="degree"|"role"|"quality"|"roman", smoothing="laplace"|"none", …)`**
  → a first-order, row-normalized transition distribution over the harmony-atom
  vocabulary. **This is literally "a Markov chain over succession tags."** Laplace
  add-α by default (no hard zeros — samplable), raw counts always preserved,
  seeded `sample()`/`walk()`, provenance block, JSON round-trip. Versioned prior
  `distribution.1`.
- **`TransitionMatrix.cross_entropy(held_out)`** → mean bits/transition + perplexity
  of the model on *fresh* material (OOV counted; `None` on infinite surprise).
- **`StyleProfile`** = a bundle of **ruleset (constraints) + distributions (spread)
  + provenance** — one versioned, round-trippable artifact.

## 3. Rulings for the Markov scope

**(a) Consume, don't reimplement — the same rule-3 line, now for the Markov math.**
When your harmony scope goes Markov, **do not hand-roll transition counting,
Laplace smoothing, or perplexity** — that math is now Tonality's domain core,
versioned. `induce over succession tags` → `build_transition_matrix(state="roman")`
(or `role`/`degree`). Your job stays exactly where the division already puts it:
the **contrast, the thresholding, the bias artifact** — the ML/orchestration.

**(b) The Markov preference signal = a distribution *contrast* — and it's the one
genuine gap.** Your whole method is contrast (liked vs disliked). The Markov
analogue of your `induce_rules → compare_rulesets` pipeline is
`build_transition_matrix(liked) vs build_transition_matrix(disliked)`, contrasted.
Tonality gives you the **two matrices + `cross_entropy`** today (an *asymmetric*
contrast: how surprised is the liked-model by disliked material). What does **not**
yet exist is the *symmetric* two-distribution contrast — a **`compare_transition_matrices`**
(KL divergence + per-transition preference log-odds), the exact Markov analogue of
`compare_rulesets`. **Recorded as a candidate engine slice with wont as named
consumer** — same posture as graded-weights (gap 20) and firing-locations: *we
don't build it speculatively; file for it when the Markov scope materializes and
it's yours.* Until then, `cross_entropy` + two matrices cover the asymmetric case.

**(c) Bias-artifact distribution payloads travel by reference, as Tonality types.**
Your `response.md` §5 discipline — engine records embedded *by reference*, never a
parallel Tonality schema on your side — extends cleanly to the distribution half:
a `wont.bias-artifact` that carries a Markov payload should embed
**`TransitionMatrix.to_dict()`** (or a whole `StyleProfile`) verbatim, not a
bespoke wont matrix format. `BiasArtifact` stays wont-schema (it wraps the
*satisfaction-derived contrast*, which is yours); its distribution content is
Tonality's type, by reference. This keeps your "mts + the readout reproduces the
numbers exactly" acceptance bar intact.

**(d) `cross_entropy` is a recovery-harness metric.** Your D11 synthetic-recovery
harness (plant a preference, verify recovery) gets a quantitative check for free:
does the learned *liked* transition-model assign lower perplexity to held-out
*liked* material than the *disliked* model does? A number for "did we recover the
signal," in the engine's own metric.

**(e) Pin `distribution.1` in your provenance chain.** You already stamp
`key_profile` (client) + `scoring_prior` (induction). The Markov side adds a third
versioned prior — the smoothing prior `distribution.1`. Stamp it on any artifact
carrying a transition distribution, same three-party replay discipline.

## 4. The shared glossary (the point of this notice)

| wont term | Tonality term | one-language note |
|---|---|---|
| span (liked/disliked slice) | *not* a piece — pool to a **piece** | per-run pooling (response §4): `pieces = runs`, never spans |
| "Markov chain over succession tags" | **`build_transition_matrix(state="roman"/"role")`** | the engine owns the transition math + smoothing |
| liked-vs-disliked *rule* contrast | `induce_rules` → **`compare_rulesets`** | shipped; your v1 |
| liked-vs-disliked *distribution* contrast | **`compare_transition_matrices`** (KL / log-odds) | the gap — candidate slice, wont named |
| asymmetric distribution fit | **`TransitionMatrix.cross_entropy`** | available today; recovery metric |
| bias artifact (rules) | `Ruleset` DSL JSON, by reference | your container, engine payload |
| bias artifact (distribution) | **`TransitionMatrix` / `StyleProfile`**, by reference | new — don't invent a wont matrix format |
| preference / bias | *(no Tonality equivalent)* | yours; satisfaction is permanently wont-schema (response §5) |
| smoothing prior | **`distribution.1`** | pin it alongside `scoring_prior` / `key_profile` |

Everything else already aligns exactly (atoms, rule DSL, `evaluate_ruleset`,
`tag_transition`, the versioned-priors chain). The division of labor is unchanged
— **satisfaction / contrast / thresholding / bias = wont; feature vocabulary /
transition math / smoothing / cross-entropy = Tonality.** Gap 14 didn't move the
line; it just means the *distribution* half of the shared vocabulary now lives on
Tonality's side, so you **consume** it instead of building it.

## 5. No ask on you

The Markov learner is your design-only future; nothing here is owed now. When the
harmony/Markov scope materializes, **file a brief-2** — you're the named consumer
on the `compare_transition_matrices` slice (and still on graded-weights +
firing-locations). Durable outcomes are in ROADMAP (A10). Welcome to the second
half of the vocabulary.
