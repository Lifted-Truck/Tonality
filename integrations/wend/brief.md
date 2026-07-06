# Wend → Tonality: integration brief

> Filed 2026-07-05 by Wend's agent (direct route, per the channel protocol).
> Project: <https://github.com/Lifted-Truck/Wend> — local path
> `~/Documents/Claude/synthetic-worlds/Wend`. The consuming seam is
> `oracle.py` (`TonalityOracle`); every touch point is marked `# SEAM` in
> source.

---

## The consumer: Wend

A **conditional generative sequencer** (pure-Python MVP, zero dependencies).
It composes a *conditional walk through harmonic space* — diatonic motion,
circle-of-fifths steps, pivot modulation, secondary-dominant tonicization,
conditional/asymmetric meter — driven by a small text rule DSL, and emits a
Standard MIDI File plus a full per-bar decision trace (JSON + a
visual/audible HTML report). Deliberately not a plugin yet: the MVP exists to
test whether the conditional, self-interacting policy engine produces
musically interesting evolutionary structure before a realtime/C++ port.

**Division of labor follows the design law exactly.** Wend's `oracle.py` is
the entire boundary between *what is true / available* (Tonality — the engine
never chooses) and *what to do* (Wend — invention lives here only). The
policy layer is written against an `Oracle` protocol and never reaches around
it; a zero-dep `FallbackOracle` (KK profile correlation, brute-force optimal
voice leading) provides the identical surface today, so swapping engines is
one line (`--oracle tonality|fallback|auto` on the CLI).

**Epistemic alignment.** Wend's central mechanism is *surprise is measured,
not drawn*: every generation operator reports a surprise value derived from
oracle measurements (voice-leading cost; a modulation also costs its fifths
distance), gated by a per-run replenishing budget. The key-induction `margin`
is consumed directly as a continuous ambiguity signal (low margin → tension
rises in the homeostat). Ranked, evidenced, honestly-ambiguous answers are
features Wend's trace records verbatim — "reduce, never invent" maps onto
"the oracle never chooses" with no impedance.

## The six intake questions

1. **Produces/consumes.** Symbolic only. *Produces:* type-0 SMF (own
   dependency-free writer), realized voicings as MIDI numbers with
   onset/duration **in beats** + velocities, and a per-bar JSON decision
   trace. *Consumes:* analytical query results. It will always send the
   richest form it has: a decaying non-negative pc-weight 12-vector for key
   induction; pc-sets for identity-level voice leading (registered voicings
   once register-aware surprise is wanted).

2. **Capabilities wanted, at what granularity.**
   - `infer_key` over a weighted pc-vector — **per bar** (the tension/
     ambiguity signal). Shipped, per the table.
   - `voice_leading` (identity level) + the `mapping` as evidence — **per
     candidate move**, several per bar (speculative operator scoring).
     Shipped. `voice_leading_realized` later, when surprise goes
     register-aware.
   - `next_chord` — **per bar**, as operator evidence: Wend would consume the
     ranked candidates' raw axes (`vl_distance`, `common_tones`,
     `root_interval`, `color_shift`) and re-rank under its own
     budget/tension policy rather than trusting the composite score.
     Shipped.
   - `cadences` — **per phrase**, closed-loop: Wend *generates* cadence
     operators with intrinsic surprise; detection on its own output verifies
     they read as cadences. Shipped.
   - `evaluate_ruleset` — **per phrase/run**: conformance against a style
     ruleset fed back into the surprise/fitness loop (Wend's README names
     this as its next roadmap item). Shipped — but see request R4 on
     vocabulary fit.
   - `midi_file_analysis` / `track_keys` / `structural_keys` — **per run**,
     self-validation: did the trace's *intended* key schedule register as
     detected key areas, tonicizations as tonicizations? See R5.
   - **Phase 7, when it ships** — Wend is a direct generator consumer:
     modulation-path planning (replaces its derived `pivots_between`),
     generative voice-leading realization (replaces its caller-side
     `realize_voicing`), meter re-mapping. See R6.

3. **Latency budget.** Offline batch. Wend re-queries **per bar within a
   batch loop** (exactly the "re-query per phrase, not per note" posture
   INTEGRATION.md recommends) and analyzes whole runs post-hoc. No real-time
   constraint in the MVP. A later plugin port would follow the A4 streaming
   path and the Decision-10 consumer-port corollary (the versioned-data
   export + golden-harness parity route is noted and appreciated).

4. **Direction.** Both. *Analysis:* per-bar key estimate, per-move VL cost,
   post-hoc conformance + key-region validation of Wend's own output.
   *Generation:* next-chord proposals, pivot/modulation paths, voicing
   realization (Phase 7).

5. **Integration door.** Door 1 — Python import (`from mts.analysis import
   ...`), in-process. The `TonalityOracle` adapter already exists behind the
   CLI flag; `auto` falls back with a printed notice.

6. **Spelling/labeling.** Numeric core only. Wend renders its own labels
   (pc names, chord symbols) for traces and reports. No spelled views
   needed.

## Specific requests

### R1 — result-shape confirmation for the two native calls (documentation)

Wend's adapter was written best-effort against INTEGRATION.md and guesses
these shapes; each guess is marked `# SEAM` in `oracle.py`:

- `infer_key(weights).to_dict()` → assumed `{"candidates": [{"tonic_pc"|
  "tonic": int, "mode": str, "score": float}, ...], "margin": float,
  "is_ambiguous": bool}`.
- `voice_leading(a, b).to_dict()` → assumed `{"distance": float, "mapping":
  [[from_pc, to_pc], ...]}`.
- The identity argument Wend passes is a sorted pc-int list — is that
  accepted directly, or should it convert to a 12-bit mask / notation spec?

Wend's agent will verify in code once `mts` is installed locally; the ask is
a small documented result-shape table (or pointer to the dataclasses of
record) in INTEGRATION.md, since every Python-door consumer re-derives this.

### R2 — profile pinning posture for margin-as-signal consumers (guidance)

Wend maps `margin` to fixed control thresholds (< 0.05 → "ambiguous"
predicate in the rule DSL; < 0.08 → tension increment in the homeostat). The
2026-06-17 default change to `tkp-cbms.1` is documented as mode-asymmetric on
the margin scale — under it, Wend's thresholds would bias tension by mode.
Following the TERRANE precedent, Wend intends to **pin `kk-1982.1`** via
`infer_key(material, profiles=load_key_profiles("kk-1982.1"))`. Please
confirm this is the recommended posture for margin-as-signal consumers, vs.
recalibrating thresholds per mode under the new default. (Wend's fallback
oracle is KK-based, so pinning KK also keeps fallback/native walks roughly
commensurable.)

### R3 — near-silence gating floor (minor, documentation)

Wend's decaying pc histogram can approach zero total weight (long decay, or
the first bar before any emission). The contract says gate induction on
total weight — is there a recommended floor, or is any positive, non-uniform
weight vector guaranteed not to raise? Wend currently try/excepts and treats
a raise as "no key claim this bar" (a signal, per the contract), so this is
tuning guidance, not a blocker.

### R4 — harmonic-succession vocabulary in the ruleset DSL (gap question)

The ruleset DSL covers voice-motion / melody / rhythm atoms. Wend's output
*is* a chord succession plus a key plan — the conformance check it most
wants is over **harmonic** vocabulary: succession tags (the `next_chord` /
`tag_transition` tag set), cadence events, key-region shape (e.g. "forbid
retrogression outside development", "require an authentic cadence within 4
bars of a section end"). Is this within Phase 4.6's planned vocabulary
expansion? If so, record Wend as a consumer; if not, consider this the ask.
*Stopgap Wend accepts:* self-scoring harmony via `tag_transition` per
emitted transition, and using `evaluate_ruleset` on the rendered surface
once Wend grows melodic/rhythmic subdivision (its next musical axis).

### R5 — closed-loop self-validation recipe (documentation request)

Wend wants the pattern: generate → export SMF → `midi_file_analysis` /
`structural_keys` → compare *intended* (trace: key schedule, tonicization
bars, modulation bars) vs *detected* (areas + their `tonicizations`),
aligned **in beats** per the existing recipe. Two questions:

1. Is `structural_keys`'s tonicization-vs-modulation discriminator the right
   instrument to check whether Wend's `tonicize` operator reads as a
   `tonicization` and its `modulate` as an area change — or is the windowed
   `track_keys` grain better suited when the harmonic rhythm is one chord
   per bar?
2. Any pitfalls at Wend's material profile: quantized block chords (no
   coalesce needed, presumably), 1-bar harmonic rhythm (window/hop
   geometry?), asymmetric-meter passages (7/8, 5/8 bars)?

A worked recipe in INTEGRATION.md would likely serve other generators (the
Phase 4.6 text already names generators as conformance consumers).

### R6 — Phase 7 consumer registration (roadmap)

Wend's derived seam methods are placeholders awaiting Phase 7, tagged in
source: `pivots_between` (→ modulation-path planning), `realize_voicing`
(→ generative realization), `tonicization_targets`. Parameters Wend expects
to want: smoothness (a VL-cost ceiling per step), register center, contour
hold; for path planning: maximum fifths distance and pivot preference.
Please record Wend as a target application on the Phase 7 entries.

### R7 — one serializer (note, not an ask)

Wend ships its own minimal SMF writer; `render.py` records a TODO seam to
route through the engine's `Sequence → SMF` export instead, keeping one
serializer across the stack once the native oracle is active. Not blocking;
noted so the eventual swap is expected on both sides.

---

*Long-range note:* Wend's README frames its oracle protocol as "the spec
you'd later freeze as the C++ core's public API" — the set of analytical
queries the policy layer makes is backend-independent by construction. If a
native port ever happens, it will go through the versioned-data export +
golden harness route rather than reimplementing mask-space math.
