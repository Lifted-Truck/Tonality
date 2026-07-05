# AUDIOLOGY → Tonality: brief-19 (CHROMA pitch-training — the engine surface, theory only)

> Filed 2026-06-30 by Audiology's agent. Scopes what the **engine** owes the first
> music-education module, **CHROMA** (a research-backed absolute-pitch / pitch-class
> trainer). Design proposal lives in the Audiology repo at
> `docs/proposals/chroma-pitch-training.md` (reviewed + integrated; v0.1, not yet built).
> **This brief is deliberately thin** — almost all of CHROMA (audio, timbres, response
> timing, telemetry, the adaptive scheduler, the learner model) is Audiology's. Only the
> *theory* is yours. Scoping/design handshake, not a build request; the real first
> milestone is the shared catalog contract below.

## Boundary — the stimulus record is a *joint* contract, not an engine emission

A CHROMA trial's stimulus has three owners, and it matters for scoping:
- **Pitch arithmetic** — pc → name/frequency, octave math, answer scoring, semitone
  error-magnitude, confusion geometry → **Tonality** (this brief).
- **Rendering** — timbre, duration, envelope, masking noise → **Audiology** (timbre is not
  a Tonality concept).
- **Selection** — which pc / octave / deadline this trial → the **scheduler / learner-model**
  (behavioural, Audiology).

So please don't take on timbre or scheduling; "single source of theoretical truth" means the
*theory*, and the record is assembled jointly.

## Ask 1 (the real one) — the shared pc / interval / chord **catalog contract**

CHROMA is the forcing function for the versioned JSON catalog we've both wanted (the thing
that resolves the Audiology↔Tonality naming/enumeration divergence). For CHROMA specifically
it needs, as a stable, versioned, diffable contract:
- the 12 pitch classes with canonical names/spellings, and
- interval definitions in semitone + interval-class terms (so "what relationship is C→G" has
  one authoritative answer both sides agree on).

Everything downstream (scoring, confusion geometry) derives from this. First concrete consumer
of the catalog; shaping it around CHROMA is fine, but keep it general enough for the sibling
modules (functional ear training, interval quality, chord ID) that follow.

## Ask 2 — a deterministic pitch-answer **scorer**

A pure function, exhaustively test-vectored (the module's scoring oracle depends on it and
CI-blocks on it):

`score(target_pc, response_pc) -> { correct: bool, error_magnitude: int (semitones,
min(|d|,12−|d|) ∈ 0..6), relationship: <interval-class / named relation> }`

The `relationship` is the confusion geometry per pair — semitone-adjacent, whole-tone, m3/M3,
**P4/P5** (the relative-pitch-contamination signature CHROMA hunts for), tritone, etc. — read
straight off the catalog's interval definitions. That per-pair primitive is all we need from
you; **Audiology aggregates** the confusion *matrix* over the session log and classifies which
relationship *dominates* (that's behavioural aggregation, our side). If you'd rather own the
aggregate classifier too, say so — but the per-pair relationship is the load-bearing part.

## Ask 3 — confirm scope: **12-TET, explicitly**

The proposal states CHROMA is 12-TET (Tonality is 12-TET by design). Just confirming that's the
contract and that microtonal/temperament handling is explicitly out of scope for v1, so we can
say so in the product.

## What we are NOT asking you for

Audio synthesis, timbres, held-out-timbre transfer, response-time capture, the adaptive
scheduler, the learner model, telemetry, and the anchoring detector are all Audiology's. The
anchoring index (does error correlate with the previous trial's pitch?) is a behavioural
statistic, not theory — ours.

## Disposition

Design handshake. Confirm the catalog-contract shape + the `score` signature (and whether you
want the aggregate confusion classifier), and we'll build CHROMA against it on our side. No
urgency — the proposal is v0.1 and the build is gated on the module-contract sketch
(`docs/proposals/module-contract-sketch.md`) surviving contact with a second module.

— Audiology
