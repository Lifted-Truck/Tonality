# TERRANE → Tonality: relay brief (verbatim)

> Received 2026-06-11 via relay from Julian; recorded verbatim per the
> channel protocol. Triage: [response.md](response.md).

---

Relay brief: TERRANE → Tonality (candidate roadmap entries)

From Julian, June 2026. Purpose: make Tonality aware of an impending consumer
project so the two can be bent intentionally toward each other. Frame the
items below as candidate ROADMAP.md entries / INTEGRATION.md additions. Full
design doc available on request.

## The consumer: TERRANE (working title)

An adaptive synthesizer in early design. The sound is a function of
performance history, not just current input: a particle with mass and
friction moves through a low-dimensional timbre space, pushed by
gestural/rhythmic forces, while harmonic state reshapes the terrain (a
Gaussian-sum potential field) the particle moves through. Terrain is
relational — defined by harmonic displacement from a slowly-drifting "home"
tonal center, not absolute key. Four nested timescales: particle (ms–s),
terrain (harmonic rhythm), home (minutes), terrain plasticity (sessions).

Division of labor follows Tonality's thesis exactly: all exact pitch-class
analysis is delegated to Tonality; TERRANE owns dynamics, terrain, and feel.
TERRANE queries at chord-event rate (seconds) — only its particle physics is
control-rate, and that is purely local. Batch APIs are therefore adequate for
TERRANE v1; the items below are about fit, and would also serve target app A4
(live MIDI companion).

Epistemic alignment: TERRANE's home-center drift is confidence-gated —
ambiguous harmony exerts no pull on home and is rendered as terrain
instability instead. This consumes "reduce, never invent" directly: honest
is_ambiguous flags and ranked answers with margins are features TERRANE
renders, not problems it works around.

## Specific functionality requests

### 1. Key induction over a weighted (decaying) pitch-class distribution

TERRANE maintains exponentially-decaying pitch-class histograms (fast
~10–30 s window; slow session window) and needs ranked key induction over a
weighted pc-distribution snapshot, not only over discrete sets or MIDI files.
Reference algorithm: Krumhansl-Schmuckler profile correlation. Two notes of
fit:

- The Krumhansl key profiles are a textbook case of Tonality's "empirical
  knobs as versioned priors" — they should be cited, versioned priors in
  results, swappable (Temperley, Aarden variants exist).
- Required outputs: ranked (key, mode) candidates with margin-based
  confidence and is_ambiguous. TERRANE uses the margin as a continuous
  control signal (terrain ruggedness, home-pull gain), so margin semantics
  should be stable across versions.

If exhaustive key induction already accepts weighted distributions, this
collapses to an INTEGRATION.md documentation item.

### 2. Minimal voice-leading distance per chord transition, with pairing as evidence

TERRANE needs, per successive sounding-chord pair: the minimal voice-leading
distance (taxicab metric over the optimal voice assignment —
Hungarian-algorithm class problem, including unequal-cardinality cases via
splits/doublings) plus the voice pairing itself returned as evidence, per
Decision 7's plural/ranked/evidenced model. TERRANE integrates this as
"harmonic effort" (kinetic-energy injection). If exact VL distance as shipped
already covers transition-pairs with pairings exposed, this is again a
documentation item; if it covers identity-level sets only, the
realization-level transition query is the ask.

### 3. Cadence detection as an evidenced event (smaller, later)

V–I and related root-motion detection emitting discrete events with
per-signal evidence. Consumed by TERRANE's home-center impulse mechanism
("keys are established by cadence more than exposure"). TERRANE will
implement a local stopgap; flagging it as a shared-vocabulary candidate since
it likely serves A1/A4 too.

### 4. Evenness via the DFT embedding (documentation request)

TERRANE maps chord evenness (distance from nearest perfectly even chord /
orbifold centrality) to spectral character. This is presumably derivable from
the existing DFT harmonic-color embedding's coefficient magnitudes — if so,
the ask is simply a documented mapping in INTEGRATION.md rather than new
code.

### 5. Umbrella: incremental/streaming session API

Items 1–3 are instances of a general shape: a stateful session object
(decaying histograms, last-chord memory, event emission) for real-time
consumers. TERRANE and A4 are the motivating consumers. Not required for
TERRANE Phase 1 (per-event batch calls over snapshots suffice given
microsecond identity answers) — recording it as the direction of fit.

## Integration shape

- TERRANE Phase 1 is a local Python backend importing Tonality directly
  (browser frontend for visualization only) — no MCP hop needed in-process.
- Requesting a TERRANE row in INTEGRATION.md: consumer of key induction, VL
  distance, set-class/DFT, chord naming, at harmonic-event rate.
- Long-range note for the record: Tonality's RULESETS vision (Phase 4.6) and
  TERRANE's serialized terrain plasticity are sibling artifacts — both
  persist extracted musical habit as versioned state. A future bridge
  (terrain states referencing the ruleset active when carved) should be kept
  in view when either is designed.
