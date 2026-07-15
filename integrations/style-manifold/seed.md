# SEED — the learned style manifold (a sibling engine; research first, then a project)

> 2026-07-14, Tonality dev loop, from Julian's question and its correct intuition.
> This is a **seed packet + research brief**, not an intake brief: the project does
> not exist, and *whether it should* is partly the research. Tonality states the
> mission and the boundaries from its vantage. If it proceeds, the new agent's
> FIRST protocol act is to read this + [INTEGRATION.md](../../INTEGRATION.md) +
> [integrations/README.md](../README.md), set up its repo, and file its OWN
> `brief.md` here — this seed then becomes historical context and the
> brief↔response exchange takes over. Name **"style-manifold" is provisional**;
> the project may rename itself (its channel directory follows the final name).
>
> **What is already decided** (ROADMAP Decision 15): this engine is a **sibling**,
> not a Tonality layer, and Tonality is its featurizer / instrument / oracle.
> **What is open**: everything about the engine itself — what it learns, in what
> representation, with what architecture, and whether it earns its existence.

## The question that produced this

*"Are rules probability-gated? Can I say 'parallel fifths no greater than 5% of the
time'?"* — and the intuition underneath it:

> messy spaces like this have rulesets too nuanced and complex and interdependent to
> enumerate prescriptively, and the right tool for the job is a system which derives
> them in a high-dimensional space.

That intuition is **correct**, and it is the lesson that ended hand-built expert
systems. Two answers follow, and they are different:

1. **The frequency budget is crisp and stays here.** "≤ 5% of the time" is a
   threshold on a *measured rate* — no learning required. That is **gap 23** (quota
   rules), built in Tonality.
2. **The nuanced, interdependent, unenumerable part is real and does NOT belong
   here.** That is this engine.

## Mission (if it proceeds)

Derive the soft, interdependent constraints of a musical style **from data**, in a
high-dimensional space, and expose what it learned as a signal other systems can
consume — where an explicit rule/pattern vocabulary provably cannot reach.

## The boundary (non-negotiable, from Decision 15)

- **The line is an epistemic KIND, not a topic.** Tonality is exact, inspectable,
  reproducible. This engine is trained, continuous, opaque. Those are different
  kinds of thing and they do not live in one library — not for tidiness, but
  because hosting the second inside the first dissolves what makes the first
  trustworthy, and couples a churning research artifact to a stable foundation.
- **It is NOT "learned vs. not-learned."** Tonality already learns —
  `induce_ruleset` mines rules, `build_transition_matrix` fits distributions,
  `build_style_profile` bundles them — but every artifact it emits is
  **transparent, versioned, deterministic** (a rule you can read; a matrix you can
  sample). **Transparent learned artifacts stay in Tonality; opaque learned
  manifolds live here.**
- **Never reimplement Tonality's domain core** (rule 3). No set-class math, no
  voice-leading distance, no key induction, no conformance evaluation. If a feature
  seems to need new analysis, that is a **brief to Tonality**, not code here.

## What Tonality gives this engine (its four jobs)

1. **Featurizer — the coordinates of the space.** You cannot learn "avoid parallel
   fifths at rate X" without an exact parallel-fifth detector to compute the
   feature. Tonality supplies the axes: interval vectors · set-class/DFT
   descriptors · voice-leading distance + mapping · conformance rates per rule ·
   transition probabilities + cross-entropy · texture atoms (onset synchrony,
   interlock, chord-tone support, register separation) · pattern/schema occurrences
   · melodic tendency. **The manifold is learned in Tonality's coordinates.**
2. **Measurement instrument.** When the model does something, measure *what* it did
   against explicit rules — "it broke the diatonic constraint 3% of the time" is a
   sentence only the crisp engine can say. The explicit layer is how a black box
   becomes debuggable.
3. **Ground-truth oracle.** Deterministic, non-negotiable gates the model is graded
   against (in-scale, in-range, hard-rule conformance) — Layer-0 to the model's
   Layer-E.
4. **Stimulus generator.** Rule-conforming vs. rule-violating material, generated on
   demand, as the controlled stimulus for preference testing (the Wont pattern).

## What it returns (the contract, when it has one)

Whatever it learns comes back as a **versioned learned prior** and/or a **plural,
ranked, evidenced signal** — the same discipline as `kk-1982.1`: stamped with its
version, never a hidden default, never silently collapsed to one answer (Decision 7
applies to a learned prior exactly as to a hand-authored one). A consumer must
always be able to ask *which model said this, and how confidently*.

## Open research questions (the actual brief)

1. **Does it earn its existence?** The honest null hypothesis: quota rules + induced
   rulesets + transition distributions + style profiles already capture enough, and
   the marginal value of a learned manifold does not justify a second engine. **Kill
   criteria should be stated before building**, not after.
2. **What does it learn — preference, or style?** A *preference* model (what does
   Julian like — few labels, active learning, the Wont shape) and a *style* model
   (what does this corpus do — many samples, unsupervised) are different problems
   with different data regimes. Probably start with one.
3. **Representation.** Learn over Tonality's *symbolic features* (a modest, legible
   vector — the neuro-symbolic path) or over raw note/piano-roll tensors (the
   end-to-end path)? The feature path is smaller, more interpretable, needs far less
   data, and directly reuses the four jobs above. **Recommended starting posture:
   symbolic features first** — earn the right to go end-to-end.
4. **Architecture.** Given (3), the honest ladder is *sparse linear / logistic →
   gradient-boosted trees → small MLP → sequence model*. Start at the bottom; a
   sparse linear model over good features is interpretable, data-cheap, and a real
   baseline any fancier model must beat. (This is the same conclusion reached for
   Wont: prefer a sparse L1 model over a "Markov bot.")
5. **Data.** Where does supervision come from — corpus (license-gated: CC0/BY only,
   the standing rule) or elicited preference (the stimulus-generator path)? Both
   have provenance obligations.
6. **Relationship to Wont.** Wont is *already* a statistical/preference sibling. Is
   this the same project, Wont's successor, or a genuinely distinct style engine?
   **Resolve this before spinning a new repo** — the cheapest outcome may be that
   this work belongs *in Wont*.

## Consumer state meanwhile

Nothing is blocked. Tonality proceeds with the transparent layer (quota rules,
induction, distributions, patterns); consumers keep consuming exact outputs. This
engine is **unscheduled and unstarted**; no Tonality work waits on it, and no
placeholder is built for it.

## What Tonality owes this seed

Nothing yet — every feature listed above is shipped today. If the research proceeds
and its brief asks for a new feature (a missing coordinate), that gets the normal
`response.md` treatment.
