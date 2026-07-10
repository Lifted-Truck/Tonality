# Tonality — Roadmap & Architecture Decision Record

> **Single source of truth for project direction.** The build sequence,
> decisions on record, target applications, and deferred/demoted scope all live
> here. Forward-looking statements anywhere else in the repo (README, per-layer
> CLAUDE.md files, docstrings) defer to this file — link the relevant phase
> instead of restating the plan. When a planning decision is made *or rejected*,
> fold it in here in the same PR; a decision that isn't recorded here isn't
> decided.

This is the strategic companion to [CLAUDE.md](CLAUDE.md). CLAUDE.md says *how to
work in the code*; this says *where we are going and why*.

## North star

A **foundation library** with an **MCP endpoint** that lets AI agents analyze music
and turn varied notations — both timeless symbolic identities and time-based
material — into **enriched, contextualized datasets**.

Success looks like: an agent feeds in a notation (a chord expression, a scale, a
MIDI clip), and gets back structured records annotated with functional role,
compatible scales, interval/symmetry properties, voicing data, and temporal
context — reproducibly.

Longer term, the engine should not merely *enumerate* the possible names/analyses of
a chord or passage but **choose the reading its context actually warrants** — and,
when readings genuinely conflict, surface the competing interpretations ranked by
corpus statistics, with evidence. The aspiration: a tool that can reveal *novel*
music-theoretical readings of existing music, not just confirm textbook ones.

## Target applications (what the engine must make possible)

Concrete programs we want to plug the engine into. These are **edge consumers,
not in-repo features** (same relationship MCP and rendering have to core —
library-first stands). Their value here is as *acceptance tests*: each one
decomposes into engine capabilities, and any capability no phase provides is a
gap to record, not a thing to improvise later. Added 2026-06-10; extend this
list as new applications come into view.

- **A1 — Key-aware MIDI analyzer.** Read a MIDI file → infer what key/scale it
  is in, split it at key changes, and emit per-section analysis (scale, chords,
  functional roles) as an enriched dataset.
  *Capabilities:* MIDI ingestion ✅ (Phase 2) · segmentation ✅ (Phase 2, literal;
  harmonic refinement parked) · global key induction ✅ (Phase 3.5b) ·
  key-change splitting = local key tracking ✅ shipped (3.5b extension,
  2026-06-11: `track_keys` key regions; `midi_file_analysis` carries them) ·
  per-section enrichment ✅ (Phase 3 dataset records).
- **A2 — Smart MIDI transformer.** Apply musically-aware transformations to an
  existing MIDI file: re-voice chord progressions; add or alter voices; change
  scale intelligently (preserve contour and degree-function, not literal
  pitches); change the time signature; insert key changes with coherent
  movement (circle-of-fifths paths, or some other stated musical bias).
  *Capabilities:* analysis side ✅/planned as above · re-voicing + added voices →
  **Phase 7** (voice-leading realization) · scale re-mapping, meter re-mapping,
  modulation path planning → **Phase 7 extensions** (recorded there) ·
  **groove apply ✅ shipped (gap 10, 2026-06-13)** — A2's first concrete
  transformation (`apply_groove`) · writing
  the result → MIDI export ✅ shipped (Phase 2 addendum).
- **A3 — Complementary part generator.** Given a MIDI file, generate companion
  MIDI for different instrument classes (bass line, pad, lead, counter-melody)
  that is harmonically and rhythmically coherent with the source.
  *Capabilities:* full analysis pipeline (A1) · Phase 7 generation constrained
  by **instrument-class profiles** (register range, polyphony, idiom) — a new
  data vocabulary; ships as versioned priors (Phase 3.5 pattern) · MIDI export.
- **A4 — Live MIDI companion** *(added 2026-06-10)*. A device/plugin that
  listens to what is being played and composes complementary MIDI **in real
  time** — A3's brain under a latency budget. The device frame itself
  (hardware/plugin/app, scheduling, audio I/O) is an edge consumer; the
  engine supplies analysis + generation. This is the most demanding entry on
  the list: it needs essentially everything A1+A3 need, **plus** two
  capabilities no phase currently provides.
  *Capabilities:* offline analysis/generation stack — as A1/A3 ·
  **live MIDI input** — streaming was *explicitly* descoped in Phase 2
  (`events_from_live_midi` is `NotImplementedError`); A4 is its first real
  demand driver (stays descoped until A4 is scheduled — recorded, not
  re-scoped) · **online/incremental analysis APIs** — today every analysis
  is whole-sequence; A4 needs rolling forms (incremental `pc_weights` + key
  tracking, rolling segmentation, per-window naming). Raw compute is *not*
  the gap — the cached mask-space tables answer in microseconds; the gap is
  API shape (update state, don't recompute from zero) · Phase 7 generation
  under a latency budget + instrument-class profiles (A3).

- **A5 — TERRANE** *(added 2026-06-11 from the project's relay brief; intake
  closed by brief 2 — design doc: github.com/Lifted-Truck/Terrane, §11 is the
  TERRANE-side mirror of the exchange)*. An adaptive synthesizer in
  early design: sound is a function of performance history — a particle with
  mass/friction moves through a timbre space whose terrain is reshaped by
  harmonic state, *relational* to a slowly-drifting, confidence-gated "home"
  tonal center. Division of labor mirrors our thesis exactly: TERRANE owns
  dynamics, terrain, and feel; all exact pc analysis is delegated here.
  Queries at chord-event rate (seconds), so **batch APIs suffice for its
  Phase 1** (Python import door, in-process; browser frontend is
  visualization only). *(Destination confirmed brief-3, 2026-06-13: a
  **VST3/AU JUCE plugin for Ableton Live** — Phase 1's no-audio prototype
  is built + passing its ten acceptance criteria and stays throwaway. The
  plugin ships no CPython/sidecar, so TERRANE becomes the motivating
  **native-export** consumer: a fixed four-function subset — weighted key
  induction, `voice_leading_realized`, `dft_magnitudes` evenness, chord
  identity/naming — all harmonic-rate, never audio-rate. Ruled under the
  Decision 10 consumer-port corollary; no blocker for Phase 1, which is
  consuming the Python door correctly today.)* Epistemically aligned by design: key-induction margins
  and ambiguity are *rendered* (terrain ruggedness, gated home-pull), not
  worked around — margin semantics are therefore a stability contract
  (documented in INTEGRATION.md).
  *CBMS default flip + TERRANE's pin (2026-06-18 — notice + `notice-cbms-default-response.md`):*
  when the default key profile flipped to `tkp-cbms.1` (A6 brief-10), TERRANE was
  notified and **pinned `kk-1982.1`** explicitly. Their reason is a durable finding:
  CBMS is **mode-asymmetric on the *margin* scale** (major margins inflate, minor
  compress via the relative-major bias), so while it's better on *which* key, KK's
  major/minor balance is better for **margin-as-a-control-signal**. The clean line:
  **ranking-accuracy consumers (A6/A1) want CBMS; margin-shape consumers (A5) pin
  KK** — any future profile decision must weigh *both* axes. They also caught a real
  doc bug (the notices said `profile_version=` on `infer_key`, which takes
  `profiles=`; the version-string selector is tool-only) — fixed in both notices +
  INTEGRATION.md. The split engine (`profiles=`) vs tool (`profile_version=`) surface
  is a recorded ergonomics wart (a possible future harmonization, not scheduled).
  *Capabilities:* weighted-distribution key induction ✅ shipped — `infer_key`
  takes any non-negative 12-vector, so decaying pc histograms work today;
  profiles are swappable versioned priors, and **Temperley/Aarden profile
  variants are welcome as additional `key_profiles.json` entries** ·
  identity-level VL distance with the voice pairing as evidence ✅ shipped
  (the `mapping` field) · **realization-level VL transitions — gap 6 below** ·
  chord evenness ✅ derivable from the DFT embedding
  (`dft_magnitudes[n-1] / n`; mapping documented in INTEGRATION.md) ·
  **cadence detection — gap 7 below** (TERRANE stopgaps locally meanwhile) ·
  streaming session API — gap 5; TERRANE joins A4 as a named customer while
  explicitly *not* requiring it for Phase 1.
- **A6 — AUDIOLOGY** *(added 2026-06-11 from its brief —
  `integrations/audiology/`; role widened 2026-06-12: Julian is preparing
  Audiology to become **explicitly Tonality's GUI** — the de-facto
  visual front end, while remaining an edge consumer in its own repo per
  the no-in-repo-GUI decision. Consequences on record: A6 is the primary
  customer of the **Phase 5 representation layer**, which rises in
  priority accordingly, and its surfaces define Phase 5's first slices —
  keyboard, piano-roll, clock/bracelet; the HTTP bridge is its lifeline
  door and bridge stability becomes a GUI-availability concern).* A
  browser SPA (TypeScript/React, local-first,
  no backend): a Push-3-style scale/chord **explorer** (8×8 grid + keyboard,
  scale-membership coloring), a MIDI-file **player/analyzer** (WebAudio
  transport, canvas piano-roll), and a **live-play** surface (Web MIDI /
  computer keyboard) with a three-mode chord card. Wants to retire its two
  naive-TS theory functions (`analyzeSelection`, `scalesContaining`) in favor
  of engine calls; already lives by the contracts (plural answers, numeric
  core, errors-as-signals, sends richest form incl. bass). Interactive
  (~60–100 ms) pull-based; no hard real-time.
  *Capabilities:* bass-aware chord naming + inversion recognition ✅ shipped
  (`name_pcs` + `voicing_analysis`) · file-level key induction + per-segment
  dataset with placements ✅ shipped (`midi_file_analysis`) · per-segment keys
  ✅ shipped (local key tracking, 2026-06-11 — key regions in beats+seconds,
  renderable as overlays; `key_tracking` tool + `midi_file_analysis`) ·
  catalog of record ✅
  shipped (`list_scales` / `list_chord_qualities`) · pc-set containment
  query ✅ shipped (gap 8 below; `catalog_containment` — retires its naive
  `scalesContaining`) · voicing recognition/suggestions ✅ shipped ·
  browser door ✅ shipped (gap 9 below; `mts.mcp.bridge`, the local HTTP
  bridge — was the blocking question) · named consumer of the **Phase 5
  representation layer** (keyboard + piano-roll descriptors; its three
  surfaces are ready render targets) · **CHROMA pitch-training module
  (brief-19, 2026-06-30 — design handshake, triaged 2026-07-04,
  `response-19.md`)**: the shared pc/interval **catalog contract** + a
  deterministic pitch-answer scorer — both accepted as **gap 18** (the second
  Decision-11 contract instance); the aggregate confusion classifier declined
  (behavioural aggregation, A6-side); 12-TET explicitly confirmed as the
  product contract.
  *Validation milestone (brief-3, 2026-06-13 — `integrations/audiology/`):* A6
  ran the **A1 pipeline on a hard real-world file** (a 16-track, ~7-min
  performed *Bohemian Rhapsody* transcription) and confirmed it makes the
  structural calls correctly — global key Bb major with the song's actual
  related-key orbit as runners-up, and a local-key timeline that tracks the
  documented sections (incl. the A-major opera pivot and the F-major coda out
  of a Bb whole), cross-checked against raw `identity.pcs`. Both rough edges
  hit were **documented contracts the consumer triggered itself** — strong
  validation of INTEGRATION.md's accuracy. The **Eb solo read as its relative
  minor (Cm)** drove the **relative-key tie-breaker ✅ shipped (2026-06-13,
  `disambiguate_relative_key` / `relative_key` #40 — see 3.5b)**, validated to
  back Eb major on this exact shape; **pipeline wiring ✅ shipped (2026-06-13,
  opt-in `disambiguate_relative[_keys]` on `key_tracking` /
  `midi_file_analysis` / `piano_roll_view`)** so the fix reaches A6's rendered
  key timeline directly. The other finding —
  **residual 1–2 s key-region micro-bands in stable passages** (the
  local-key-tracking axis, untouched by coalescing) — drove the **opt-in
  adaptive hysteresis ✅ shipped (2026-06-13, `smoothing` on `track_keys` /
  `key_tracking`, `smooth_key_regions` on `midi_file_analysis` /
  `piano_roll_view`; versioned prior `key-smoothing.1` — see 3.5b)**, which
  absorbs the weak blips while keeping confident brief modulations. With this,
  all four brief-3 findings are addressed (A documented + recipe, B + C fixed,
  D faithful). The
  triage also added a "Choosing a coalesce window" recipe to INTEGRATION.md and
  affirmed migration to the official `mts.mcp.bridge` (identical `{ok, result}`
  envelope). Net engine work: zero — see `response-3.md`.
  *Validation harness adopted (brief-4, 2026-06-14):* the brief-3 hand-check
  becomes a **Tonality-owned corpus accuracy harness** — `validation/`
  (new top-level dir, peer to `audit/`): runs `midi_file_analysis` over
  human-annotated repertoire (When-in-Rome RomanText + scores; BPS-FH
  cross-check) and scores inferred-key + key-region accuracy. It is the
  **empirical instrument for Findings B & C** — the with/without
  `disambiguate_relative_keys` / `smooth_key_regions` A/B that will *measure*
  whether those flags earn their place. Contract of record (response-4): keys
  reduce to `(tonic_pc, major/minor)` (the engine's space; modal flagged, not
  charged); **frame agreement** is the headline region metric (boundary-tolerance
  secondary); relative-major/minor scored in three buckets (`exact`/`relative`/
  `wrong`) with the **exact-rate Δ** as the Finding-B headline; temporal
  comparisons align in **beats, not seconds**. music21 is a `[validation]`
  optional extra (never runtime); a skip-if-absent smoke test in `tests/` runs a
  vendored ~10-piece set. **License boundary (load-bearing):** scores are PD,
  RomanText annotations are CC BY-SA — read to score, **never derived into an
  engine prior** (the DCML/gap-14 ShareAlike rule). Phase 2 (chord-level scoring
  vs per-beat RNs) recorded as a separate round. Net engine work: zero — see
  `response-4.md`.
  *First corpus results (brief-5, 2026-06-15 — the harness paid off):* it
  produced a **measured negative result on a shipped feature**, the loop working
  as intended. Three durable outcomes (all reads, no immediate build — see
  `response-5.md`):
  (1) **Structural key-areas vs windowed local-fit — the headline gap.**
  `key_regions` is a **tonicization-sensitive local-fit** signal (each window's
  best-fit key; a V/V span reads as the dominant), a *different object* than the
  analyst's **structural key-areas** (which subsume tonicizations under the
  parent). Frame-scoring one against the other lands *below* a no-modulation
  baseline (0.357 vs 0.608 on Mozart) because it measures that category
  difference, not key accuracy. The engine has **no structural-key-area output**
  — a tonicization-aware reduction needing **functional context**, not windowed
  best-fit. This is the empirically-motivated version of the parked
  harmonic-segmentation / functional-context work (Phase 2 deferred refinement).
  **✅ Delivered — structural reduction slice 1 (2026-06-15):**
  `temporal/structural_key.py` `reduce_to_structural_keys` + MCP tool
  `structural_keys` (#43). A single deterministic pass over the local track
  absorbs a brief, **diatonically-related** excursion (a V/V span) into its
  parent key as a `tonicization` (with its scale `degree`) and keeps a
  sustained/structural change as a modulation — discriminator = **relatedness AND
  (brevity OR return)**, the functional context confidence-gating lacked. Home
  key = the **most-prevalent local region** (not the averaging global induction —
  sidesteps Finding 3 for the anchor); global `infer_key` carried as evidence
  alongside the full local `tracking`. Thresholds are a versioned prior
  (`structural-key.1`, `min_modulation_beats=8` set by **phrase-length theory,
  not corpus-fit** — the BY-NC-SA boundary). A derived reduction — never
  overrides. The worked Mozart track collapses 6 over-segmented regions → 2
  structural areas (C-major with V/vi tonicizations + the real G-major
  modulation), which is the fix. **Deferred:** chromatic tonicizations
  (roots outside the parent collection — needs an applied-chord model; *brief*
  chromatic excursions are now absorbed — see the brief-11 fix below — but a
  *sustained* applied-chord region still needs the model); the
  returning-modulation distinction (`require_return` flag); multi-pass
  re-anchoring (`min_area_beats` dormant — *empirically motivated by brief-7:
  phrase-length granularity, boundary recall 0.64→0.10; the floor stays
  phrase/meter-derived, not corpus-fit; distinct from the brief-11 fix — that
  gates establishment, this merges back sustained-but-low-support areas*);
  recursive nesting > 1 level; the online/change-point form.
  **✅ Brief-blip modulation fix (2026-06-18 — A6 brief-11):** the CBMS flip
  surfaced a profile-agnostic reduction bug — a **brief, *unrelated* windowed blip
  was promoted to a structural modulation** (the brevity escape only protected
  *related* excursions: `related AND (brief OR returns)`), so a 2-beat chromatic
  window could anchor a large spurious area (vendored D911-11: a 2-beat G-major
  window — 4 beats total in the piece — anchored a 122-beat area, splitting the
  A-major home). Fixed to `brief OR (related AND returns)`: only a **sustained**
  region (≥ `min_modulation_beats`) establishes a structural key; a brief excursion
  is a tonicization (diatonic, or a brief *chromatic* one). Verified to recover the
  vendored regressions (D911-11/-09/-21 → clean single home areas); **zero
  conformance change** (sustained modulations untouched). A first dent in the
  deferred chromatic-tonicization gap.
  **✅ Frame-weighted home anchor (slice 2, 2026-06-15 — PR follow-on to brief-7):**
  brief-7's "global-key-miss coupling" was diagnosed (reading the code + the
  vendored D911-07) as an **anchor** problem, *not* an `infer_key` one — avoiding
  an XY trap. `reduce_to_structural_keys`'s home key is the **most-prevalent local
  region** (`_anchor`), which over-counts a *repeatedly-tonicized dominant*; it
  does **not** use `infer_key` except as a tie-break, so a structurally-weighted
  `infer_key` would not have moved the anchor. The lever is the anchor itself:
  opt-in `anchor_method="frame_weighted"` adds a theory-set bonus to the opening +
  closing regions (the structural frame is the place least likely to be a
  tonicization — the tonicization-robust home-key signal). Versioned prior
  `structural-key.2` (`frame_anchor_bonus=1.0`, theory-set not SWD-fit — robust
  across 1..3), MCP `structural_keys` `anchor_method` param, new conformance case.
  Verified end-to-end: recovers E-minor on D911-07 where the default anchors on the
  dominant B-major, and breaks none of the 4 correctly-anchored smoke songs.
  **✅ Promoted to default (2026-06-17, brief-8):** A6 scored it on the **full 24**
  with `--ab-anchor` (bonus left at the theory-set 1.0, fence intact) — a **Pareto
  improvement**: global-key-miss subset **+10.1pp** region agreement (0.134→0.235),
  correctly-anchored subset **exactly 0.000** (byte-identical), 0 regressions. Met
  the pre-committed bar, so `anchor_method` now defaults to `frame_weighted`
  (`most_prevalent_region` kept as an explicit legacy option + a parity conformance
  case). *Symmetric risk accepted:* a piece ending in a sustained non-returning
  modulation gets a closing-frame vote for that key — zero such regressions on SWD,
  but it surfaced on a synthetic walk-test (which now pins the legacy anchor).
  *Candidate — a no-home mode (added 2026-07-08, A9 Wend brief-4):* a wandering
  generator that modulates away and never returns wants the `areas` timeline
  **without** a forced anchor; `most_prevalent_region` is the better home for it
  today, and `areas` is already anchor-free, but a first-class
  `anchor_method="none"` (emit `areas`, leave `home_tonic_pc` null) would let the
  result formally decline a home. Small; unscheduled; consume `areas` meanwhile.
  *Honest partial:* it fixes **1 of 6** global-key misses (D911-07 +60pp) — it can
  only promote a tonic region the local track already proposes; the residual 5 are
  **upstream of the anchor** (next paragraph).
  **The residual lever is `infer_key`, not `min_area_beats` (brief-8 partition).**
  A6 dumped the 6 misses: 4 are the engine reading the **dominant** as the key, 1 a
  **parallel-major** flip, 1 the **relative major** — all cases where the
  window/global key-*fit* prefers V or the parallel/relative to the tonic-minor, so
  no tonic-minor region exists for the frame bonus to promote. `min_area_beats`
  (phrase-granularity) can't manufacture a region the fit never proposes — it
  addresses a *different* failure (boundary recall / over-segmentation on
  correctly-anchored songs), so the two stay distinct, not substitutes.
  **Global-key induction lever (Q3) — scoped + sliced 2026-06-17 (brief-9 +
  research-9; see `response-9.md`).** brief-9 dumped the 6 global-key-miss songs'
  pc-vectors on the authoritative SWD edition; diagnosis closed: 3 are
  dominant-substitution (07 anchor-handled, 19, 22), 1 parallel near-tie (24), 1
  dominant+parallel stacked (08), 1 relative-major (03). A cited literature pass
  (Temperley & Marvin 2008; White MTO 2018; Quinn ZGMTH 2010; Noland & Sandler
  ISMIR 2006; Temperley *Music and Probability* 2007) established: histogram
  correlation measures **prevalence, not centricity** (order/function-blind);
  **no single lever fixes both modes**; **naive positional/frame weighting is a
  confirmed dead end** (Temperley & Marvin — so the earlier "structurally-weight
  the whole-sequence vector" idea is dropped); and the **KK profile carries a
  documented dominant bias** (= failure mode 1). **✅ Shipped — CBMS profile,
  opt-in (slice 1):** `data/key_profiles.json` gains `tkp-cbms.1` (Temperley-
  Kostka-Payne, verified vectors), selectable via a `profile_version` arg on
  `key_induction`/`key_tracking`/`structural_keys`/`midi_file_analysis`. CBMS is
  documented "well-balanced for major keys"; on the 6 misses it recovers 3 (19, 22,
  24) as a pure data swap under the existing Pearson core. **✅ Flipped to the
  default (A6 brief-10, 2026-06-17):** the full-24 `--ab` returned a **Pareto win**
  — global-key exact-rate **+12.5pp (18/24 → 21/24), zero regressions** on the 18
  correct songs — clearing the pre-stated decision rule, so `tkp-cbms.1` is now the
  default `key_profiles` entry. **Contract migration (A5/A7):** flipping the default
  changes `infer_key`'s default output (the A5/A7 stability contract), done
  *coordinated, not unilateral* — A5/A7 are notified and **pin
  `profile_version="kk-1982.1"` to retain the exact old margins** (the selector makes
  the old behaviour a one-arg opt-out; additive migration, nothing breaks). *Ripple
  noted:* the flip also changes the windowed track + structural reduction + the
  KK-tuned relative-key tie-breaker (which fires less under CBMS — benign; its tests
  pin KK, the prior being KK-companion); A6 re-scores the **region/structural
  metrics** under CBMS as a validation fast-follow (brief-10 measured global key
  only).
  **Deferred — slice 2, mode-aware / functional-context key induction.** A
  deterministic **cadence/closure-aware** layer (tonic as the point of harmonic
  resolution, leveraging the existing cadence detection) and/or mode-aware induction
  — flagged higher-risk because the literature's closure methods are corpus-trained
  and validated on chorales/opening passages, not modulating lieder; build only
  after prototype-and-measure. The "minor-mode under-detection" sub-signal (brief-8)
  is now explained: it is the natural-minor profile losing the raised leading tone,
  which CBMS's better balance partly addresses. **Acceptance set (post-CBMS, all
  four converge on this one lever — brief-12):** the SWD residuals are D911-**03**
  (relative-major, global), **08** (parallel, global), **07** (dominant-substitution,
  global), and **16** (parallel-mode + sustained foreign fit in the *windowed*
  track — CBMS's mode-asymmetry surfacing locally; `track_keys` shares `infer_key`,
  so the same lever addresses it). That four cases across both the global and
  windowed surfaces reduce to one investment is the signal that this is the right
  next key-accuracy lever. The anchor and induction levers stay distinct fixes.
  **✅ Mechanism settled — the continuity prior / Temperley key-inertia (A6 brief-13,
  2026-06-26; `response-13.md`):** A6's maintainer (Julian) articulated the principle
  the lever needs — **parsimony + a soft continuity prior on the MODE decision**
  (reward fit, penalize switching, let context break ties) — which is exactly the
  **deterministic** remedy research-9 already surfaced: **Temperley's key-inertia**
  (an additive fixed-parameter self-transition penalty over the per-window key+mode
  state, DP-decoded; penalizes spurious modulations, resolves local-vs-global; no
  training — Decision 8 holds). So the slice's mechanism is no longer open. Concrete
  acceptance (Bohemian Rhapsody, A6): short-window mode flips (9/97, near-tie on
  sparse content — already absorbed, so *evidence* not a live bug) and an
  **arbitrary-minor-on-mode-undetermined-content** case (a 100%-F span reads B♭ minor
  by Δ−0.061 under CBMS while the established B♭-major context reads major at margin
  0.315 — *verified locally*; the local face of TERRANE's CBMS mode-asymmetry).
  **Scope/constraints:** a continuity-prior layer on **`track_keys`** (sequential) —
  changes the windowed track + structural reduction + A6 overlays, but **leaves
  `infer_key` (single-vector global) untouched, so the A5/A7 stability contract is NOT
  reopened**; penalty is a theory-set versioned prior (not corpus-fit); opt-in →
  default on a clean `--ab`. **✅ Shipped — opt-in `key_inertia` on `track_keys`
  (2026-06-26):** a deterministic key-inertia Viterbi (`_key_inertia_path`) over the
  per-window full score vectors with a flat `switch_penalty` (versioned prior
  `key-inertia.1` = 0.1, theory-set: between the ~0.05 near-tie noise floor and a
  ~0.3 confident modulation, calibrated to the correlation-margin scale, **not**
  SWD-fit; cited via `inertia_version`). Ties break to the lowest state
  (reproducible). Full key+mode state (subsumes the mode-only ask + cuts tonic
  over-segmentation); composes with `smoothing` and largely subsumes it. Threaded
  through `key_tracking`/`structural_keys`/`midi_file_analysis`; **default off →
  zero golden-content change → `infer_key` and the A5/A7 contract untouched.**
  Verified on the vendored corpus (region counts D911-09 6→5, -07 26→16, -21 20→9;
  home key preserved/strengthened; deterministic). **Pending:** A6 `--ab` validation
  (region/structural agreement under inertia) + the Bohemian Cases 1–2 acceptance
  (needs A6's windowed-track dump — not vendored) before any default flip.
  **✅ Acceptance confirmed (A6 brief-14, 2026-06-26 — `response-14.md`):** on
  Bohemian, `key_inertia` on resolves both cases — Case 1: 9/9 spurious window-flips
  gone (7/9 correct mode, 2 correctly held to their section key; 97→69 regions,
  −29%); Case 2: the frame-weighted home flips B♭ minor → **B♭ major** (the
  ambiguous closing inherits the prevailing mode). Soft-prior verified: home+global
  both B♭ major and the reduction still splits 8→11 areas — the real B♭→E♭→A
  modulations survive. **Still pending the default flip:** the SWD `--ab`
  region/structural *regression* gate (A6 building a `key_inertia` A/B alongside
  `--ab-anchor`/`--ab-profile`). The scoping decisions that informed the build: DP
  (global, batch) — the causal/online form joins gap 5; flat penalty not
  distance-weighted (distance-weighting makes parallel flips *cheap*, the wrong
  direction). **Mandate recorded (brief-13):**
  key/mode/scale determination should live in and be hardened in the engine (the
  division-of-labor law) — a consumer report that turned out to be A6's beat-trim
  corrupting `structural_keys`'s input (engine read B♭ major on original beats)
  validated it.
  Use `structural_keys` for key-area comparison, the windowed track for
  tonicization-grain detail.
  (2) **`disambiguate_relative_keys` empirical negative result.** On real
  classical repertoire it's a **no-op** (A/B Δ ≈ 0 global, −0.018 region). It
  *does* reach the per-window path (`key_tracking.py`); the cause is the
  deliberately-conservative near-tie gate (`near_tie_margin=0.2`, #70) not firing
  on **confident-but-wrong** relative errors (which are real — ~7% of region
  frames). As shipped it doesn't earn its place here. The gate-widening trade-off
  is harness-measurable, **but corpus-calibration against When-in-Rome is barred**
  (BY-NC-SA — fitting a prior to the corpus is derivation); a CC0/BY recalibration
  corpus would lift that *(now satisfied — SWD CC BY 3.0, brief-6; only the license
  leg lifts, the overfit caveat remains)*. Likely a *symptom* of (1) — argues for the structural
  reduction over re-tuning. `smooth_key_regions` (Finding C) similarly can't fix
  it: the over-segmentation is **signal at the wrong grain, not noise** —
  confidence-gating can't remove a confident tonicization.
  (3) **Global induction over modulating forms** — ~26% non-relative miss on
  sonata movements is **expected** (whole-sequence KK-correlation is ill-posed for
  a form that lives off-tonic); a **structurally-weighted induction** (over-weight
  opening + final cadence) is a recorded candidate refinement. Harness landed at
  `validation/validate_corpus.py`; Haydn/music21 RomanText parse failures recorded
  as a corpus-coverage limit.
  *License-clean corpus + the unblock (brief-6, 2026-06-15 — see `response-6.md`):*
  A6 surveyed the field and adopted the **Schubert Winterreise Dataset (SWD)** —
  **CC BY 3.0** (verified firsthand on the live Zenodo record,
  [10.5281/zenodo.5139893](https://zenodo.org/records/5139893); attribution-only,
  no SA/NC) — wiring it into the harness (`--swd` alongside `--corpus`, a 5-song
  vendored smoke set under `validation/corpus/swd/`, measures→beats via an
  empirical beats-per-bar read off the engine's own records). It is the **CC0/BY
  recalibration corpus response-5 said would lift the tuning constraint** — the
  only clean option with full key+chord+modulation truth on symbolic data (TAVERN
  BY-SA, When-in-Rome/DCML BY-SA/BY-NC-SA, PDMX scores-only). Two outcomes:
  (1) **Findings 2 & 3 replicate on CC-BY data** — region tracking below the
  no-modulation baseline (0.472 < 0.515) and `disambiguate_relative_keys` a no-op
  (Δ ≈ 0 global, −0.009 region, no bucket flips), confirming the response-5
  diagnosis is not a Mozart artifact; the ×3 inter-annotator floor bounds the
  interpretive-variance denominator. (2) **The boundary lifts for SWD** — a prior's
  parameters may now be fit/tuned against it with citation (the `near_tie_margin`
  sweep is unblocked), **but only the license leg lifts**: "theory-set, not
  corpus-fit" also rests on a methodological leg (SWD = one composer/one cycle →
  overfit risk), so SWD is a sanctioned **measurement oracle + candidate calibration
  source, not an auto-fit one** — a shipped corpus-fit prior wants corroborating
  breadth or explicit theory-bounding. **State correction:** the brief predates
  #78 and treats the structural-key-area reduction as unshipped; it shipped today
  (`structural_keys` #43). So the genuinely unblocked experiment handed back is
  consumer-side: **score `structural_keys` against the SWD analyst key-areas** (the
  apples-to-apples comparison target response-5 promised — its `areas` spans are
  the same structural object as SWD's local-key annotations), sequenced *before*
  any `near_tie_margin` sweep (the relative errors are likely a symptom of
  over-segmentation the reduction targets). Net engine work: zero.
  *Structural reduction scored on SWD (brief-7, 2026-06-15 — see `response-7.md`):*
  A6 ran the handed-back experiment — `structural_keys`'s `areas` vs the SWD
  analyst key-areas through the frame-agreement pipeline (`--structural`). The
  reduction is confirmed the **right object** (it beats the windowed track by
  **+0.068** on the 18 global-key-correct songs, 0.522 → 0.590) but does **not**
  reach the global-key baseline (0.590 < 0.658); the response-6 prediction that it
  would move *past* baseline was too strong — corrected. The residual gap resolves
  to **two levers, both already recorded, now empirically motivated** (the
  structural-key follow-ons in the brief-5 record above): (3a) region accuracy is **coupled to global-key
  accuracy** — the 6 global-key misses collapse to ~0 and drag the all-24 number
  flat → the **structurally-weighted home-key induction** (Q3) refinement, which
  **must ship additively** (the `infer_key` default is the A5/A7 stability
  contract). *(Build-time correction: diagnosis showed the structural reduction's
  home miss is an **anchor** problem, not an `infer_key` one — fixed by the
  **frame-weighted anchor ✅ shipped** in the follow-ons above; structurally-weighted
  `infer_key` remains a distinct, still-deferred lever for the global baseline +
  A5/A7.)* And (3b) **phrase-length granularity** — boundary recall collapses
  0.64 → 0.10 because the flat `min_modulation_beats=8` (2 bars) is too coarse for
  *Winterreise*'s short strophic phrases → activate the **dormant `min_area_beats`
  re-anchoring** pass, with the floor staying **phrase/meter-derived, not SWD-fit**
  (the methodological overfit leg that did *not* lift with the license). The
  tie-breaker is **confirmed not the lever** (structural disambiguate Δ +0.007,
  no bucket flips) — validating the response-6 sequencing call; with this,
  `disambiguate_relative_keys` is a measured **no-op across three repertoires under
  both scorings**, so no `near_tie_margin` prior is warranted (keep
  `--ab-disambiguate` as a standing instrument). **Repertoire caveat (recorded as a
  new open data gap):** *Winterreise* is mono-tonal strophic lieder, so the
  baseline is unusually high and a correct reduction can at best **tie** it — a
  fair test of whether structural *beats* baseline needs a **modulating
  license-clean corpus with key-area annotations**, which does not yet exist in a
  clean form (SWD was the only clean option even for the mono-tonal case). Net
  engine work at triage: zero — but the follow-on build landed the
  **frame-weighted home anchor** (slice 2; see the structural-key follow-ons above),
  the contract-safe fix for cause (3a) once it was correctly localized to the anchor.
  *Frame-weighted anchor scored on the full 24 (brief-8, 2026-06-17 — see
  `response-8.md`):* A6's `--ab-anchor` A/B on all 24 *Winterreise* songs made it a
  **Pareto improvement** (miss subset +10.1pp, correctly-anchored subset exactly
  0.000, 0 regressions, bonus left theory-set) → **promoted to the default**
  `anchor_method` (the pre-committed bar was met; see the follow-ons above for the
  engine detail). Honest partial: 1 of 6 global-key misses fixed; A6's partition
  showed the residual 5 are **upstream of the anchor** (the window/global key-fit
  preferring the dominant/parallel/relative to the tonic-minor) → the
  **structurally-weighted `infer_key`** lever, with a new **minor-mode
  under-detection** sub-signal (D911-08/-22 recover tonic pc but flip to major —
  possible KK major-bias). `min_area_beats` stays a *distinct* lever (boundary
  recall / over-segmentation), not a substitute. Net engine work: the default flip
  (additive — legacy method retained).
  *infer_key residual diagnosed + CBMS profile shipped (brief-9 + research-9,
  2026-06-17 — see `response-9.md`):* A6 dumped the 6 global-key-miss songs'
  authoritative pc-vectors; a cited literature pass closed the diagnosis (histogram
  correlation = prevalence not centricity; KK has a documented dominant bias; naive
  frame-weighting is a dead end; no single lever fixes both modes). **✅ Shipped the
  opt-in `tkp-cbms.1` profile** (verified Temperley-Kostka-Payne vectors) + a
  `profile_version` selector on the induction tools; it recovers 3 of 6 misses as a
  data swap, default unchanged (A5/A7 contract). Ball back to A6: the full-24 `--ab`
  regression score on `profile_version="tkp-cbms.1"` decides any default flip. The
  relative/parallel tail (03, 08) is deferred to a cadence-closure layer (slice 2,
  research-grade). Net engine work: a new opt-in profile + selector (additive).
  *CBMS A/B + default flip (brief-10, 2026-06-17 — see `response-10.md`):* A6's
  full-24 `--ab-profile` returned a **Pareto win** (global-key exact-rate
  **+12.5pp**, 18/24 → 21/24, recovering D911-19/-22/-24; **zero regressions**),
  clearing the decision rule → **`tkp-cbms.1` flipped to the default**, with A5/A7
  notified to pin `kk-1982.1` for the old margins (coordinated contract migration).
  D911-08 now reads the parallel (G maj, tonic pc recovered) and 03 stays relative
  — both clean hand-offs to the deferred closure layer. **Fast-follow:** A6 re-scores
  the region/structural metrics under CBMS (the flip changes the windowed track too;
  brief-10 measured global key only).
  *Region/structural fast-follow + a regression fix (brief-11, 2026-06-18 — see
  `response-11.md`):* A6 scored the windowed + structural surfaces under CBMS on the
  full 24. **Windowed track: clean win** (+15.5pp, 0 regressions; +11.7pp even on
  the 18 stable songs). **Structural: net +8.8pp** but with a concentrated
  regression tail on a few globally-stable songs — which I diagnosed (on the vendored
  D911-11) as a **profile-agnostic reduction bug** (a brief unrelated windowed blip
  promoted to a spurious structural modulation) and **fixed** (see the structural-key
  follow-ons above: a modulation now requires sustained presence). Validated to keep
  CBMS everywhere — **no pinning**. A6 re-runs `--ab-profile-regions` with the fix to
  confirm the tail closes. Net engine work: a one-condition walk fix.
  *Fix confirmed — CBMS arc closed (brief-12, 2026-06-18 — see `response-12.md`):*
  the full-24 re-run with #89 in closed the diagnosed structural tail (**5 → 2
  regressions**, Δ +0.088 → +0.130; D911-11 −0.47→−0.01, -09/-21 → 0.00), recoveries
  + sustained modulations byte-identical. The CBMS default is now **validated across
  all three surfaces** (global +12.5pp, windowed +15.5pp, structural +13pp). The two
  remaining structural regressions are **explained, neither a reduction bug** — D911-07
  (a global *miss*, sits on a wrong anchor) and D911-16 (a *sustained* windowed-track
  profile difference: CBMS's parallel-mode/major bias surfacing locally) — both routed
  to the deferred mode-aware-induction acceptance set above. A6's `--ab-profile[-regions]`
  harness PR is now unblocked (all dependencies on `main`). Net engine work: zero.
- **A7 — SOLVE ET COAGULA** *(added 2026-06-11 from its brief —
  `integrations/solve-coagula/`; repo: github.com/Lifted-Truck/Automata)*.
  A generative instrument: a K=6-state cellular automaton under Glauber
  dynamics whose musical mode (root-fixed, walking the 2,048-vertex mode
  hypercube) *generates the physics*; a pure deterministic TS core emits a
  byte-exact event chronicle, with Tonality strictly in adapters and offline
  enrichment (core purity is absolute). Chronicle fixtures make **versioned
  priors a regression-grade dependency** — the strongest consumer yet of
  that pattern. MCP + dataset doors; chord/epoch-rate pull; no hard
  real-time for us.
  *Capabilities:* voicing naming + disambiguation ✅ shipped · exhaustive
  12-bit mode identity (prime form / Ring number for arbitrary sets, beyond
  the named catalog) ✅ shipped, verified — with the **root-relative →
  absolute mask rotation contract** documented in INTEGRATION.md · DFT
  magnitudes / evenness as CC signals ✅ shipped · velocity-weighted decaying
  key induction ✅ shipped (margin as confidence CC) · VL distance ✅ both
  levels; its offered test corpus ✅ delivered + adopted (brief-2 — 285/285
  verified, `tests/test_vl_corpus.py`; gap 6 entry has the record) ·
  MIDI export + dataset enrichment ✅ shipped · prospective **Phase
  4.6 induction consumer** ("derive the idiom from the affinity matrix");
  a sibling instrument is noted as a likely second consumer of the same
  doors.
- **A8 — AURICLE** *(added 2026-07-03 from its RFC brief, relayed —
  `integrations/auricle/`; local repo: synthetic-worlds/auricle)*. A grain
  manipulator VST (C++): grain quantization, a modal resonator bank with
  voice-leading glides, and a chroma mask, all driven from one harmonic
  authority. The TERRANE consumer class again — real-time, can ship no
  CPython — but with a sharper proposal: consume **compiled harmony
  contracts** (versioned JSON artifacts freezing pc sets, voicings, and
  voice-leading transition maps) rather than a native port, so the client
  needs *no* Tonality runtime at all. Its RFC is the origin of **Decision 11**
  (contracts as object code) and **gaps 16–17**; TERRANE and wend (a
  harmonic-decision serializer in the same ecosystem) are recorded as
  prospective consumers of the same format.
  *Capabilities:* voice-leading assignment map over concrete voicings
  ✅ shipped (`voice_leading_realized`, gap 6 — the brief's §4.1 assumed it
  missing; verified present, brute-force-tested, corpus-validated 285/285) ·
  cardinality-mismatch policy ✅ shipped as data (`doubling.1`, exported in
  manifest/bundle; voice birth/death recorded as a round-2 design point) ·
  contract schema/validator/emitter — **gap 16 below** · constrained voicing
  enumeration/ranking — **gap 17 below** · division-of-labor table + bounded
  client fallbacks ✅ endorsed (the consumer-port-corollary shape, Decision 10).
- **A9 — WEND** *(added 2026-07-05 from its brief, direct route —
  `integrations/wend/`; repo: github.com/Lifted-Truck/Wend)*. A **conditional
  generative sequencer** (pure-Python MVP): a rule-DSL-driven walk through
  harmonic space (diatonic motion, fifths steps, pivot modulation,
  tonicization, conditional meter) emitting SMF + a per-bar JSON decision
  trace. Consumes through one adapter seam (`oracle.py` — "the engine never
  chooses"; every touch point greppable as `# SEAM`), with a zero-dep
  fallback oracle behind the same protocol. Its central mechanism —
  **surprise is measured, not drawn** — consumes VL cost as move-surprise
  and the induction `margin` directly as a continuous tension signal: the
  first consumer to use margin as a *generative control input*. Offline
  batch; re-queries per bar; Door 1 (Python import); numeric only.
  *Capabilities:* `infer_key` per bar ✅ shipped (pins `kk-1982.1` — the
  TERRANE margin-as-signal posture, confirmed) · identity `voice_leading`
  + mapping-as-evidence per candidate move ✅ shipped (pc-list inputs
  direct) · `next_chord` raw-axes re-ranking ✅ shipped · `cadences`
  closed-loop ✅ shipped · `evaluate_ruleset` ✅ shipped, but its harmonic
  vocabulary is **the Phase 4.6 harmony/progression rule family** — Wend is
  that gap's first named external consumer · generate→detect
  self-validation via `structural_keys` 📖 documented (INTEGRATION.md
  recipe, Wend R5) · **Phase 7 consumer on both halves** (modulation-path
  planning ← `pivots_between`; generative realization ← `realize_voicing`,
  with recorded parameter asks: per-step VL-cost ceiling, register center,
  contour hold, max fifths distance, pivot preference) — the realization
  half also registered on **gap 17** (nearer-term slice of the same need) ·
  serializer unification (its SMF writer → `sequence_to_midi_file`) noted,
  door open, nothing owed · `search_identities` **adopted** (brief-2:
  `pivots_between`/`tonicization_targets`, 576/576 + 24/24 parity; R1 bug fixed,
  `df1..df6` shipped) · **brief-3** (`response-3.md`): melodic tendency prior =
  **gap 19** — slice 1 ✅ **shipped** (`melodic_tendency`, notice
  `notice-melodic-tendency.md`; the `_snap_stable`/`_snap_chord` swap is open) ·
  satisfaction-loop hooks = **gap 20** (v1 recipe-answered; feature vocabulary
  is Tonality's, Decision 11) · **brief-4** (`response-4.md`, 2026-07-08):
  declared-vs-inferred key — coordination, not a bug. Ruled: Wend's "three grains"
  (local `track_keys` / structural `structural_keys` / global `infer_key`) is
  correct and matches the engine's tonicization-vs-modulation model; divergence is
  the surface **under-asserting its centre** (a Wend-side authoring fix), and
  `segment_chords` now gives a declared-vs-inferred **self-consistency check**.
  Durable output: **`integrations/key-grain-alignment.md`** — a consumer-neutral
  contract (grain vocabulary + pinned `window_beats`/`hop_beats`/`profile_version`)
  so Wend + A6 read a key strip identically; relayed to the Audiology channel.
- **A10 — WONT** *(added 2026-07-07 from its intake brief, direct route —
  `integrations/wont/`; project: synthetic-worlds/wont)*. The **modular
  preference-learner** anticipated in Wend brief-3 R2, now real: consumes
  **LabeledRuns** (a client's generation fingerprint + a bar-aligned
  satisfaction curve), mines the liked/disliked span corpora with the engine's
  own vocabulary, and emits **versioned bias artifacts** (validated DSL
  rulesets + contrast evidence) a generator applies deterministically —
  classical ML, offline batch, analysis-only, one boundary module
  (`wont/engine.py`). Division of labor is clean (Decision 11): **Tonality owns
  the feature vocabulary + deterministic extraction; wont owns the ML.** It is
  the **gap-20 consumer of record** and the **second named consumer on gap B**
  (harmony scope). *Triage (`response.md`):* the field manifest is
  `rules.schema.FAMILIES` (a sanctioned `ruleset_field_manifest()` export is a
  recorded gap-20 sub-item); the **span-independence recipe = per-run pooling**
  (concatenate a run's liked spans into one pseudo-piece so `pieces = runs`,
  restoring the Fisher/BH-FDR independence duplication would break — read every
  piece floor against *runs*, not spans); satisfaction labels stay wont-schema
  with engine records embedded by reference (§5 boundary ruling); the one
  contingent engine slice beyond graded-weights is **per-rule firing-location
  extraction** (the "considered-and-held" complement to `evaluate_ruleset`'s
  violation stream — build when its saliency layer needs it, wont named).
  *Brief-2 (`response-2.md`, 2026-07-08) — K scoped labelings of one run:* Wend
  parallel-sessions a single `run_id` (K passes, different scope-sets + labels).
  Ruling (recipe, no v1 engine work): the independence unit is **`(run, scope)`**,
  but because each scope is mined as its **own corpus**, within any one corpus it
  reduces to `pieces = runs` — the K sessions land in K *different* corpora, so
  none sees the run twice (scope-separation = the §4 pooling fix one level up). Do
  not pool across scopes, nor mine K sessions in one corpus. **Extends to the
  distribution layer** verbatim, plus one stamp: `cross_entropy` held-out splits
  must be **by run**, never by span/session (same music leaks). Parallel scoped
  sessions are an **attribution + cross-scope-render-efficiency** lever, **not**
  within-scope power (one run = +1 piece per scope, never +K). **New contingent
  slice, wont named:** a `run_id` **grouping-key** on `induce_ruleset` (group-level
  support) for the residual — *same-scope repeats* or a *cross-scope joint model*;
  not built for v1.
  *Markov/distribution alignment (2026-07-08, `notice-markov-alignment.md`):* two
  `response.md` open asks now **shipped** — `ruleset_field_manifest()`
  (`ruleset-fields.2`) and `evaluate_ruleset(include_firings=True)`. And gap 14
  gave the channel a Markov vocabulary it lacked: wont's deferred "Markov chains
  over succession tags" (its DESIGN §9, trigger = harmony scope post-gap-B) is
  Tonality's **`build_transition_matrix(state="roman"/"role")`** — consume it, do
  not reimplement the transition/smoothing math (rule 3). The distribution half of
  the by-reference discipline: a bias-artifact Markov payload embeds a
  `TransitionMatrix`/`StyleProfile` verbatim (no bespoke wont matrix format); pin
  the `distribution.1` smoothing prior alongside `scoring_prior`/`key_profile`;
  `cross_entropy` is a ready recovery-harness metric. **New contingent slice, wont
  named:** **`compare_transition_matrices`** — a symmetric two-distribution
  contrast (KL divergence + per-transition preference log-odds), the Markov
  analogue of `compare_rulesets` (the asymmetric case is covered today by
  `cross_entropy`). Not built speculatively; file a brief-2 when the Markov scope
  materializes.
  *Closed personalization loop (direction on record, Julian 2026-07-08):* the
  target is a loop where **the same object never leaves Tonality's representation**
  — a `StyleProfile` (base) seeds generation (`walk()` samples the harmonic
  skeleton; the client renders audio — Tonality is seed source, not renderer),
  wont collects satisfaction, and the bias artifact composes back onto the base via
  `combine_rulesets`/`specialize_ruleset` into a *personalized* `StyleProfile`.
  Round-trip object = `StyleProfile`; forward-seed already supported (wont
  `Scenario.seed_rulesets` + `TransitionMatrix.walk`); backward-translate already
  supported (bias artifact = DSL ruleset, composed by the shipped
  combine/specialize). Open rulings (awaiting wont **brief-2**): round-trip
  fidelity of the distribution half (needs `compare_transition_matrices`), the
  delta-composition mechanism (overlay vs re-weight vs both), the three-party
  seed→generate contract, and loop provenance (stamp `base_profile` + run ids +
  `key_profile`/`scoring_prior`/`distribution.1`). No engine work owed until the
  brief lands — the pieces are on the shelf.
  *Preference-method guidance (2026-07-08, notice §7):* "Markov bot" was Julian's
  shorthand; the recommended engine is a **sparse L1 linear/logistic model** over
  the atom feature space (not a Markov chain), whose signed coefficients map
  **directly to weighted soft-rules** (`weight ∝ |coef|`, polarity by sign) — i.e.
  the fitted model *is* a weighted `StyleProfile`. The Markov/transition-contrast
  is retained only as the **representation for sequential structure**;
  contrast-induction stays the significance-tested discovery method. **Reframes
  gap 20:** a graded dial consumed as the linear model's *target* puts the grading
  in the loss, so engine-side graded *sample-weights* may prove unnecessary — wont
  remains the named consumer if a measured case still wants them. Method choice is
  wont's (ML is theirs); Tonality's half is the translation contract (every
  method's output lands as a weighted `StyleProfile`).

- **A11 — CORPUS WORKBENCH** *(anticipated 2026-07-09; seed packet filed —
  `integrations/corpus-workbench/seed.md`; Julian approved the new-tool route and
  will spin its agent; name provisional)*. The **batch corpus-exploration
  surface** for the ruleset/pattern/style-profile stack — renders the corpus
  exercise harness's JSON report + live per-piece descriptors over the HTTP
  bridge. Deliberately NOT Audiology (which stays per-piece/live-instrument):
  one product shape per project. Pure renderer/orchestrator — rule 3: zero
  analysis of its own; one boundary module; refusals rendered as refusals and
  `exploratory` rendered prominently (the engine's honesty must survive
  rendering). First views: pattern-occurrence heatmap · conformance
  distributions · induced-rule evidence browser. Likely the **first web
  consumer** → the named trigger for Horizon H2's typed TS bridge client.
  Registration completes when it files its own intake brief (the seed is
  Tonality's vantage, not the project's voice).

**Gaps this list surfaces (recorded, not yet scheduled):**
1. **MIDI export** — ✅ shipped (Phase 2 addendum): `sequence_to_midi_file`
   (`Sequence → SMF`, single track, tempo/meter/velocity/channel preserved,
   round-trip tested). This entry predated delivery; corrected 2026-06-12.
2. **Generative transformations** (scale re-mapping, meter re-mapping,
   modulation path planning) — Phase 7 extensions; all generative-side per the
   cardinal rule.
3. **Instrument-class profiles** — versioned data vocabulary for A3.
4. **Live MIDI input** (A4) — streaming `events_from_live_midi`; stays
   explicitly out of scope until A4 is scheduled.
5. **Online/incremental analysis APIs** (A4, A5) — rolling-window key
   tracking, segmentation, and naming that update state instead of
   recomputing; a stateful session object (decaying histograms, last-chord
   memory, event emission) is the natural shape (per the TERRANE brief).
   The *online* sibling of the now-shipped batch local key tracking (the
   stateful form would update windows incrementally instead of re-sliding).
   Not required for TERRANE Phase 1 — per-event batch calls over snapshots
   suffice.
6. **Realization-level voice-leading distance** (A5, A7; also Phase 7) — the
   shipped `voice_leading` is identity-level (mod-12 circular). The
   register-aware sibling measures actual semitone motion between two voiced
   `Realization`s, optimal assignment with the pairing as evidence, doubling/
   omission for unequal voice counts. Consumed by TERRANE as "harmonic
   effort" and by Solve et Coagula as a **validation oracle** for its own
   nearest-octave voicing engine — which has offered a concrete test corpus
   (5 voices, permitted doublings, range clamps root+3..root+40) to seed
   this gap's test suite; Phase 7 wants the same metric for scoring realized
   voice leading. **Delivered (2026-06-11):** `voice_leading_realized`
   (analysis + MCP tool #18) — actual-semitone motion over sorted MIDI
   multisets (octaves cost 12; doublings are voices), optimal pairing exact
   via linear non-crossing (sorted index-wise for equal voices; contiguous
   blocks for unequal), brute-force-verified including 5-voice
   doubled/clamped cases shaped like the offered corpus. Register required —
   raises on `None` per the cardinal rule. **Corpus arrived (brief-2,
   2026-06-12): 286 five-voice cases (`solve-coagula.vl-corpus/1`),
   independently re-verified — 285/285 transitions agree exactly with
   `voice_leading_realized` — and adopted as `tests/test_vl_corpus.py`,
   which also pins the artifact (schema, counts, flag coverage) and the
   `doubling.1` policy citation. The validation oracle is bidirectional:
   their corpus pins our metric, our metric validated their `realize()`.**
7. **Cadence detection as evidenced events** (A5, A1, A4) — V–I and related
   root-motion patterns emitted as discrete events with per-signal evidence
   (Decision 7 shape). Kin to the Slice 5 tier-(c) sequential signals —
   build the sequential vocabulary once, serve both. **Delivered
   (2026-06-13):** `analysis/cadence.py` `detect_cadences(chords, tonic_pc,
   mode)` over a named progression — authentic (V/leading-tone→I), plagal
   (IV→I), deceptive (V→vi), half (final arrival on V); each event carries
   the approach/arrival chords (roman + role + degree), root motion, and a
   per-signal evidence list. Honest scope: these are *formulas*, not
   phrase-confirmed cadences (no timing → `is_final` is the strongest
   evidence; a half cadence is flagged only at a *final* V — a
   mid-progression V is just a dominant). A faithful consumer of the
   functional vocabulary (`theory/functions.py`), so major/minor only
   (`mode_supported=false` otherwise, no guessing) and it inherits that
   vocabulary's coverage. **✅ Fixed (2026-06-26): the bare major-V triad** (the
   harmonic-minor dominant, raised leading tone) is now in `TEMPLATES_MINOR`
   degree 7 alongside V7 — so a bare V→i in minor reads as authentic in both
   `cadences` and naming (it was previously recognized by neither). MCP:
   `cadences` (#35). Feeds gap 14's cadential candidates.
8. **Catalog containment query** (A6) — "which catalog scales/qualities
   contain this pc-set, at which roots." Ruled **engine-side** (exact
   combinatorics); the first concrete slice of the parked constraint-search
   vision, cheap over the cached tables. Retires Audiology's naive
   `scalesContaining`. **Delivered (2026-06-11):** `find_containers`
   (`analysis/containment.py`) + MCP tool `catalog_containment` (#19; the
   HTTP bridge exposes it automatically). Reverse of compatibility — the
   container transposes, the query stays absolute (`containing_roots`,
   mask-cached in `pcset_math`). Tightest containers first, exact matches
   flagged (modal spellings of one mask are distinct exact answers),
   symmetric containers report every valid root; takes explicit catalog
   mappings so session catalogs are searchable. No ranking policy — pure
   subset combinatorics, deterministic ordering only.
   *Follow-on — scale/set-class NAME catalog (A6 brief-20, `response-20`,
   2026-07-08):* A6 wants canonical + alternate names (across traditions) keyed by
   set-class, with Forte number. **The structure already ships** — `Scale`/
   `ChordQuality` carry `name` + `aliases` — it's the **breadth** that's the new
   data asset. Ruled shape: a **`scale_names(pcs|prime_form)` tool** returning
   `{canonical, aliases:[{name,tradition?,source?}], prime_form, forte_number,
   cardinality, is_scale}`, buildable as a **v1 over the existing catalog now**
   (zero new data, `forte_number: null` — prime form is the id; Forte stays the
   3.5a deferral pending a vetted table), plus a **bulk versioned export** when the
   data grows. **Crux is sourcing/license — Julian's call, not the engine's:** Ian
   Ring is our integer-convention reference but his *name corpus* is unvetted;
   recommended license-safe path is **engine-authored names first** (modal/
   symmetric/interval-vector structure — zero risk), external aliases (raga/maqam/
   Zeitler) only from CC0/PD/BY-verified sources with per-alias `source`/`tradition`
   provenance. **v1 DELIVERED (2026-07-08, `notice-scale-names-shipped.md`):**
   `interpret_scale` (`analysis/equivalence.py`, the scale sibling of
   `interpret_chord`) + MCP `scale_names(pcs|prime_form)`. Returns the set-class
   identity (`prime_form`/`prime_form_mask`/`interval_vector`/`cardinality`,
   `forte_number: null`, `is_scale`, `rotational_period`) + **plural `names`**
   `[{root_pc, name, aliases, tradition, source}]` — every catalog scale the set
   matches at each tonic (the diatonic set → all 7 modes). **No fabricated single
   `canonical`** — a modal-ambiguous set is honestly plural (pick by root context,
   exactly as with `interpret_chord`); `tradition`/`source` are provenance slots
   empty until a vetted corpus lands. Zero new data, breadth grows with the
   catalog. 11 tests; golden additive; port pin untouched.
9. **The web door** (A6; the Phase 5 visualizer class) — browsers cannot
   spawn the stdio MCP server. Sanctioned shape, ruled 2026-06-11: a thin
   local HTTP bridge over the existing pure `mts.mcp.tools` functions
   (Decision 5-compliant glue; tools already return JSON-ready dicts).
   Hosted endpoint declined (local-first); WASM noted as an explicit
   non-commitment. **Delivered (2026-06-11):** `mts.mcp.bridge` — stdlib-only
   (`http.server`, zero new dependencies), `python -m mts.mcp.bridge`,
   loopback-bound at `127.0.0.1:8012` by default. `GET /tools` introspects
   every tool (name, doc, params from the live signatures — new tools appear
   automatically); `POST /call/<name>` invokes with JSON kwargs; engine
   `ValueError`s surface as 400s with their actionable messages; CORS is an
   origin allowlist since RE-4e (was: open, because the boundary is loopback —
   the allowlist keeps loopback web origins + no-Origin callers free and
   rejects foreign pages; mechanism chosen by A6). The tool signatures and
   `to_dict()` shapes remain the only contract — consumers who stood up
   interim bridges swap by changing a URL.
10. **Groove extract / apply** (added 2026-06-12, prompted by Julian —
    Ableton Live's Extract Groove is the reference model). Two halves on
    opposite sides of the cardinal rule:
    *Extract* (analysis) — distill a `GrooveTemplate` from a symbolic loop:
    per grid slot at a chosen base resolution, the signed onset offset (as a
    fraction of the grid unit) and velocity, cycled over the loop length.
    Builds directly on the rhythmic atoms; `analyze_swing` is the
    one-parameter special case (a groove template generalizes the division
    fraction to arbitrary per-slot offsets). Same honesty bound as swing:
    quantized input yields a null groove — the feel must be in the onsets.
    *Apply* (generative) — **A2's first concrete transformation**: new
    `Sequence` with onsets pre-quantized by a quantize %, interpolated
    toward template offsets by a timing %, velocities scaled by a signed
    velocity % (negative reverses, per the Live model); a random component
    requires an explicit seed (same-input-same-output is an engine
    invariant). Parameter vocabulary maps 1:1 onto Live's Groove Pool
    (Base / Quantize / Timing / Random / Velocity / Amount), so grooves
    round-trip conceptually with DAW workflows. Boundary: extraction from
    *audio* stays consumer-side per Decision 9 — consumers send onsets,
    never audio. Template extraction policy knobs (if any emerge) ship as
    versioned priors. Depends on gap 11 only for *trustworthiness*: a wrong
    declared grid poisons offsets, but extraction against a correct
    declared grid works today.
    **Delivered (2026-06-13):** `temporal/groove.py` — `extract_groove`
    (analysis) + `apply_groove` (generative) + `GrooveTemplate`/`GrooveSlot`
    (JSON round-trip via `to_dict`/`from_dict`); MCP tools `extract_groove`
    (#37) + `apply_groove` (#38) with a velocity-carrying event format
    (`[onset, dur, midi, velocity?, voice?]`, parsed by `_vel_events` so the
    existing voice-at-index-3 convention is untouched). Offsets stored as
    signed fractions of the base unit; velocity as a signed **deviation from
    the loop mean** (flat dynamics → null velocity groove, mirroring swing's
    `mean − 0.5`); empty slots are `None`, distinct from on-grid `0.0`. Base
    resolution + loop length are **caller geometry, cited not prior** (no
    `data/*.json`: extraction is pure arithmetic). The timing **round-trip**
    (extract a loop, re-apply onto its quantized form at quantize=timing=1 →
    onsets reconstruct to 1e-9) is the central pinned invariant; `Random` is
    deterministic per `seed` via blake2b keyed on the onset tick (order-
    independent, byte-reproducible). Two design points settled in build that
    refine the spec text: (a) **extract is polyphony-tolerant** — a groove is
    read from possibly-chordal material (simultaneous onsets share a slot and
    average), so it does *not* use the monophonic `_line_events` contract; and
    (b) velocity apply is **additive accent transfer** (`v + amount·velocity·
    delta`, negative reverses), the literal reading of "scaled by a signed
    velocity %" — so the *timing* round-trip is the clean reconstruction (its
    inverse is quantize), while velocity has no inverse and instead *transfers*
    the accent contour. Conformance goldens added for both tools (38 cases).
11. **Meter estimation** (added 2026-06-12; promoted from the theory-
    grounding review agenda's "we trust the file's time signature"). The
    time system is declarative: `MeterMap` answers every bar/downbeat
    question exactly, but only from file meta — there is no inference of
    time signature, meter changes, or bar lines from note content, and a
    loop exported with default 4/4 meta poisons every metric judgment
    downstream (rhythmic atoms, syncopation, swing, groove extraction).
    Wanted: batch estimation — ranked candidate signatures with scores and
    margin (Decision 7 shape; profile-correlation over onset/accent
    autocorrelation is the classic method family), change-point detection
    for meter changes, and a declared-vs-estimated disagreement signal
    rather than silent override (the engine never replaces the file's
    claim — it evidences against it). Empirical templates ship as
    versioned priors. The *online* form joins gap 5's session, as with
    key tracking.
    **Delivered — slice 1 (global batch + disagreement, 2026-06-13):**
    `analysis/meter_estimation.py` `infer_meter(sequence)` + MCP tool
    `meter_estimation` (#42) — `infer_key` for meter. Each candidate signature
    is scored `period_score × max(profile_score, 0)`: **bar-period
    autocorrelation** of the onset-salience signal (kills the aliasing where a
    3-beat pattern spuriously folds onto a non-dividing 4.5-beat bar) × **metric-
    profile correlation** (the within-bar accent vs the meter's template —
    distinguishes 3/4 from 6/8, which share a 3-beat bar). Onset salience =
    velocity when present, else unit; phase 0 (bar lines from the sequence start,
    as `MeterMap` assumes). Candidate set + GTTM-style metric-grid templates are
    a versioned prior (`data/meter_profiles.json`, `meter-grid.1` — Palmer–
    Krumhansl empirical profiles welcome as a future version). Ranked + margin
    (Decision 7); both sub-scores are evidence. **Never overrides** the file's
    meter: the result carries the declared signature + `agrees_with_declared`,
    leaving the `MeterMap` untouched. Degenerate input (too few onsets / flat
    signal) raises. **✅ Change-point / local meter — delivered 2026-06-28**
    (`mts/temporal/meter_tracking.py`, `track_meter` / the `meter_tracking` tool):
    the windowed form, exactly as `track_keys` is to `infer_key`. A window slides
    over the sequence, each window's metric fit is ranked by the same versioned
    prior, and consecutive same-best-meter windows merge into `MeterRegion`s
    (beats+seconds extents, mean score/margin, per-window evidence); an
    uninformative window (too sparse / no differential accent) makes no claim and
    regions merge across it; raw per-window argmax, deterministic merge, no
    smoothing in v1 (meter is slow-changing). Windows default larger than key
    tracking's (16/4 beats) since period detection needs several bars; boundary
    resolution is the hop grid. **This required solving the phase problem** that
    naive windowing exposes (a meter change at an arbitrary beat aligns to neither
    the sequence-start nor window-start grid): `infer_meter` gained an **additive,
    opt-in `phase_search`** (default off → the global phase-0 contract + its golden
    are unchanged) that scores each candidate's metric profile at its best bar
    phase (the period autocorrelation is already phase-invariant); the tracker uses
    it so off-downbeat windows read correctly. Validated on a synthetic 4/4→3/4
    change (clean two-region split at the true boundary within hop resolution).
    **Wired into `midi_file_analysis`** (2026-06-28): opt-in
    `include_meter_regions` surfaces the local meter track on a real SMF (parallel
    to `include_key_regions`; default off → output unchanged), inferred from
    onsets/accents independent of the file's declared meter map — so a consumer can
    compare the two to catch a mis-tagged or changing meter.
    **✅ Anacrusis / global phase estimation — delivered 2026-06-28**: `phase_search`
    now *surfaces* the winning bar phase it already computed as
    `MeterEstimationResult.downbeat_offset_beats` (None when phase_search is off, so
    the global phase-0 golden is unchanged), and the tracker reports it per window
    (`MeterWindow.downbeat_offset_beats`) and aggregated per region
    (`MeterRegion.downbeat_offset_beats`, the modal window phase). `meter_estimation`
    gained an opt-in `phase_search` tool param; both meter tool outputs carry the
    offset. Geometric, not corpus-fit (offset = the grid-slot rotation that best
    aligns the metric-profile fold). **Still deferred:** agogic (duration)
    weighting; smoothing of the boundary-window transient (a 1-window mixed-meter
    region at a change is honest v1 behaviour — gate on
    `window_count`/`mean_margin`); the online form (gap 5).
12. **Performed-input tolerance** (added 2026-06-12; theory-grounding
    review pass #1's headline finding — A1/A6 feed real MIDI to exactly
    these paths). The temporal analysis layer silently assumes
    **grid-exact onsets**: humanized/performed input is *misread, not
    refused*. Verified: two chords with ~5 ms onset jitter segment into
    **ten** micro-segments including garbage transitional pc sets (each of
    which the A1 pipeline would name as a chord); an on-the-beat melody
    with the same jitter classifies as all-`subdivision` in the rhythmic
    atoms; voice-pair motion fragments across micro-moments. (The melodic
    line extractor at least *refuses* — humanized legato overlaps raise
    "not monophonic".) Wanted: an explicit tolerance layer — an onset
    coalescing window (and optional grid snap) applied at `Sequence`
    construction or as a preprocessing pass, **caller-set and cited in
    results** like window geometry, default off so exactness stays exact.
    Audiology already coalesces at ~60 ms client-side — existing demand
    and a working precedent. **Delivered (2026-06-12):**
    `temporal/tolerance.py` `coalesce(sequence, onset_window_beats=,
    snap_grid_beats=)` — clusters *all* time points (onsets AND offsets,
    healing performed-legato seams) greedily by anchor (the cluster's
    earliest point — the perceived onset of a spread chord; anchoring
    prevents unbounded chaining), optional grid snap after. Explicit
    opt-in preprocessing returning a new `Sequence` — the engine never
    coalesces implicitly, and every downstream analysis benefits without
    learning a tolerance parameter. Result cites the parameters and
    itemizes the changes (moved count, max shift) and any events dropped
    for collapsing (grace notes shorter than the window) — losses are
    reported, never hidden. The review's probe is the acceptance test:
    the 10-micro-segment chords segment cleanly into 2; the
    all-`subdivision` melody places on the beat after snap. MCP:
    `coalesce_events` (#27) + opt-in `coalesce_window_beats` on
    `midi_file_analysis` (metadata cited in the result when used).
13. **Per-region analytical context in the A1 pipeline** (added 2026-06-12;
    review pass #1). `midi_file_analysis` now computes local key regions
    *and* still conditions every segment's naming on the single global
    best key — in a modulating file the foreign-key regions get namings
    under the wrong context (a misread the shipped key tracking already
    knows how to avoid). Wanted: per-segment context selection from the
    key region containing the segment's onset, with the global form kept
    as an option; the region's `mean_margin` rides along as the context's
    confidence evidence. **Delivered (2026-06-12):**
    `dataset_from_sequence(key_regions=)` selects each segment's context
    from the region containing its onset (fallback: the supplied global
    context); `AnalyticalContextSnapshot` gains an additive `margin`
    field carrying the region's `mean_margin` (None when the context was
    supplied directly — confidence is only claimed when inferred).
    `midi_file_analysis` defaults to per-region conditioning
    (`per_region_context=false` restores single-global-key); the
    dataset-level snapshot stays global, per-record snapshots carry the
    local readings. Conformance goldens regenerated (additive field —
    a 4-line reviewable diff, the harness working as designed). Directly
    serves A6's player overlays now that A6 is the explicit GUI.
14. **Next-chord recommendation** (added 2026-06-13, Julian's idea —
    flagged by him as "a big build," recorded so it's decided). Given an
    established context (a key, and a current chord or short progression
    history), return **multiple ranked candidate next chords, each tagged**
    with music-theoretic / qualitative / historical context — the engine's
    plural-and-evidenced contract applied to *succession*, not just
    identity. Decomposes onto existing + planned pieces (so it is a
    *synthesis* target, not greenfield): the **functional-harmony generator**
    (`theory/functions.py`) already enumerates per-degree candidate chords
    with roles (T/PD/D) and tags (borrowed / modal-mix / secondary-dominant)
    — the candidate *set*; **voice-leading distance** ranks/tags smoothness
    and common-tone retention; **set-class/DFT** color gives a
    tension/evenness axis; **cadence detection — gap 7** supplies cadential
    candidates and the sequential vocabulary; **corpus transition statistics
    — Phase 4.5** supply the *historical* tags as a versioned prior (the
    one genuinely new data asset; the engine stays exact + no in-engine ML
    per Decision 8, so this is a shipped transition table, not a model).
    The hard/honest parts: a **tag taxonomy** (which annotations are
    computable today vs corpus-dependent vs subjective) and whether
    transition stats are one table or **per-style** priors. Natural home: a
    Phase 4.5/7 capability built atop gap 7 — sequence it after the cadence
    + statistical-interpretation groundwork it leans on.
    *Research findings (2026-06-13, two background agents):*
    - **Tag taxonomy — a "ship-first" slice needs no new data.** Computable
      today from existing modules: functional-succession tags
      (resolves-cycle, retrogression, prolongation, descending-fifth,
      deceptive, applied-dominant, borrowed — from the role/tag generator),
      voice-leading tags (common-tones=N, vl-smooth, PLR-transform,
      chromatic-mediant — from `voice_leading` + mask intersection), and
      **color-shift** (DFT-magnitude delta — a distinct axis, nearly free).
      Cheap *data* wins next: a **rule-of-octave** table and a small
      **diatonic transition-tendency** table (both fixed, citable, versioned
      JSON). **Defer** the corpus/subjective tags — schema-fragment
      (Gjerdingen), implication-realized/denied (Narmour), and the style
      `idiom=*` *labels* (ship the pattern *detection*; mark the style claim
      low-confidence) — they'd smuggle subjective judgment the architecture
      pushes to the caller. Frameworks: Piston/Kostka-Payne, Schoenberg/
      Meeùs (root-motion strength), Cohn/Tymoczko (parsimony), Lerdahl
      (tonal distance), Amiot (DFT color).
    - **Corpus prior — per-style, not one table.** A style-agnostic matrix
      describes no real style (rock IV→I/♭VII vs classical V→I vs jazz
      ii-V-I genuinely diverge). Ship **per-style first-order, degree-keyed,
      row-normalized transition matrices** (~12–14 states, **2–6 KB JSON**
      each, with `source`/`license`/`version`/`n_transitions` provenance —
      the KK-profile pattern). License-safe sources: **McGill Billboard
      (CC0)** + **RS200 / Rock Corpus (CC BY 4.0)** for pop; **iRealPro
      Zenodo corpus (CC BY 4.0)** for jazz; **classical DEFERRED** — the
      DCML annotated corpora are **CC BY-NC-SA** (NC kills commercial use,
      SA can copyleft-contaminate an MIT library). **Off-limits:** Hooktheory
      (proprietary ToS, no redistribution — despite publishing exactly this
      data). `music21` (BSD) is an *offline derivation tool only*, not a
      runtime dep; its bundled scores carry per-file licenses. Ship the
      aggregate statistic (defensible), never the source chord sequences.
      *Caveat to verify at build time:* McGill Billboard's CC0 is
      well-attested but its canonical DDMAL page moved domains — eyeball the
      live page before pinning it in a prior's metadata.
    **Delivered — slice 1 (the no-new-data tagged recommender, 2026-06-13):**
    `analysis/succession.py` — `recommend_next_chord` (ranked candidates) +
    `tag_transition` (the single-transition primitive, usable on
    out-of-vocabulary chords — the "tag each transition" unit a progression
    annotator wants), MCP tool `next_chord` (#39). Candidate set + each chord's
    (role, roman) come from `load_function_mappings` (the same vocabulary the
    cadence detector consumes); default breadth is a legible core triad+seventh
    vocabulary, caller-overridable via `qualities`. Tags computed today, each
    precisely defined + unit-tested: functional (`prolongation`,
    `descending_fifth`/`ascending_fifth`/`step`, `dominant_resolution`,
    `retrogression`, `applied_dominant`, `borrowed`/`modal_mix`) + the cadential
    formula read straight from `detect_cadences` on the pair; voice-leading
    (`smooth`, `parsimonious` with P/L/R detail, `chromatic_mediant`, scaled
    `common_tone`, `vl_distance` penalty) from `voice_leading`; and `color_shift`
    (DFT-magnitude delta) **reported but unscored** (brightness is the caller's
    call). Scoring is a versioned prior `data/succession_weights.json`
    (`succession.1`, engineering defaults pending corpus calibration; cited in
    results); plural + evidenced per Decision 7, raw axes exposed for re-ranking.
    Major/minor only (modal raises). **Build notes refining the spec:** (a) the
    candidate set is the *functional vocabulary*, which is mostly diatonic — so
    rich `borrowed` candidates appear in **minor** (the harmonic-minor V7/vii°
    family) and `chromatic_mediant` *candidates* don't arise from the default
    set (the tag is implemented + tested via `tag_transition`, but surfacing such
    candidates needs the deferred VL-neighbour source); (b) `applied_dominant` is
    a detect-and-flag heuristic (dominant-type chord whose down-a-fifth target is
    a diatonic non-tonic degree). **Deferred (remaining gap-14 work):** the
    per-style corpus transition priors (the *historical* tags — the genuinely
    new data asset, per the research above); the fixed rule-of-octave +
    diatonic-tendency tables; subjective/corpus tags (Gjerdingen, Narmour, style
    `idiom=*` labels); **✅ VL-neighbour candidate generation — delivered
    2026-06-28:** opt-in `vl_neighbours=True` (+ caller-set `vl_max_distance`,
    default 3) on `recommend_next_chord` / `next_chord` *also* generates chords
    reachable within the smoothness bound but **outside** the functional vocabulary,
    so chromatic mediants etc. now arise as candidates (the `chromatic_mediant` tag,
    previously implemented but never firing in the recommender, now fires — e.g. in
    C major E-major surfaces, vl_distance 2, tagged `chromatic_mediant`+`vl_neighbour`,
    role/roman honestly `None` as out-of-vocabulary). The `vl_neighbour` provenance
    tag is weight-0 (informational, never scores); default off → existing output +
    golden unchanged. Still deferred: register-aware ranking; the per-style corpus
    transition priors (the *historical* tags).
    **Distribution primitive DELIVERED (gap 14 slice 1, 2026-07-08): the
    *sampleable* half of a style profile.** `mts/rules/transition.py`
    `build_transition_matrix(chord_corpus, *, state="degree", smoothing="laplace",
    alpha=None, source=None, session=None)` (MCP `transition_matrix`) — aggregates
    a chord-stream corpus (the same input harmony induction reads) into a
    first-order, degree-keyed, row-normalized `TransitionMatrix`. **Smoothing is a
    selectable, cited knob** (Julian's call): `"laplace"` (default, add-α, no hard
    zeros — right for sampling) or `"none"` (raw empirical, exact zeros); **raw
    integer `counts` are preserved either way** so a caller can re-normalize; α is
    the versioned `distribution.1` prior, cited on the result. `state` keys over
    the atom vocabulary (`degree` default / `role` / `quality` / `roman`).
    Sampleable **deterministically** — seeded `sample` / `walk` (generation is a
    client act, but the seeded draw is reproducible; no wall-clock/unseeded RNG,
    per the AI-boundary). Provenance block (`source`/`prior_version`/`alpha`/
    `n_transitions`/`n_pieces`) + JSON round-trip (`to_dict`/`from_dict`). Composes
    with `segment_chords` — raw MIDI → chords → distribution, no hand annotation.
    16 tests; golden purely additive (2 `transition_matrix` cases); port pin
    untouched. **This is the distribution half the style-profile bundle needs.**
    **Bundle schema DELIVERED (gap 14 slice 2, 2026-07-08): the style-profile
    object.** `mts/rules/style_profile.py` `StyleProfile` +
    `build_style_profile(name, version, *, provenance, ruleset, distributions,
    description)` (MCP `build_style_profile`) — the one object that bundles a
    ruleset (constraints) + 0+ `TransitionMatrix` distributions (the spread) + a
    provenance block into one versioned (`style-profile.1`), round-trippable
    artifact. Pure **assembly** of already-built parts (accepts parsed objects or
    raw payloads), invents nothing; a profile must carry ≥1 half, and an empty
    ruleset (induction found nothing) is coerced to absent. 10 tests; golden
    additive (1 case); port pin untouched. **The style profile is now
    assemblable** — corpus → segment → (induce ‖ transition-matrix) → bundle. Only
    remaining gap-14: **real per-style data priors** derived offline from CC0/CC-BY
    corpora (slice 3 — the license-gated data asset above), and the optional
    Dirichlet smoothing (candidate above).
    *Smoothing extension — Dirichlet prior (candidate, added 2026-07-08, Julian).*
    `build_transition_matrix` ships `smoothing="laplace"` (add-α, the default) and
    `"none"` (raw). Add a third mode `smoothing="dirichlet"` with a per-state
    concentration vector **α_i** — the Bayesian generalization (α_i all equal =
    add-α, so Laplace is the uniform-Dirichlet special case). It lets a caller
    encode an informative prior per target state (e.g. a music-theoretic base rate)
    rather than the flat add-α floor. Small, additive (a new `smoothing` value +
    an `alpha_vector` param, `distribution.2` prior); raw `counts` preserved as
    always. Deferred until a consumer needs a non-uniform floor — the flat add-α
    covers the "no hard zeros for sampling" need today.
Local key tracking shipped 2026-06-11 (the 3.5b extension — see that entry):
A1's key-change splitting and A6's renderable key regions are served by the
windowed batch form; A4's *online* requirement remains with gap 5.
15. **Multi-dimensional validation program** (recorded 2026-06-17; discussed with
    Julian, *discuss/hold* — no build or A6 brief yet). The corpus-accuracy
    harness that paid off for **key** (A6's `validation/validate_corpus.py`:
    ground-truth corpus + a `(label, fn)` producer seam + a scorer + a *metric
    contract* + the license spine + A/B levers) generalizes to other inference
    dimensions. Architecture: each dimension is a **scorer plugin** =
    `(inference entry point, ground-truth parser, metric definition, A/B levers)`
    over the existing producer seam. Dimension readiness differs sharply:
    - **Meter / time-signature — first dimension; contract scoped 2026-06-18
      (`proposal-meter-validation.md`).** `infer_meter` is shipped (gap 11), shaped
      like `infer_key` (ranked candidates + margin + `agrees_with_declared`). A
      5-song vendored prototype reshaped the naive "exact-signature match" plan:
      (a) **ground truth = the MusicXML score `<time>` signatures, NOT the MIDI meta**
      — the meta is degenerate/multi-valued (D911-11 = `[1/8,3/4,2/4,6/8,2/4]`: a
      pickup-bar 1/8 artifact + real meter changes); SWD has no meter annotation.
      (b) **graded buckets, not exact-only** — exact / **hypermetric** (bar-multiple:
      2/4↔4/4, 3/8↔6/8 — same beat, undecidable bar grouping from notes; report
      separately, don't charge as wrong) / **simple↔compound** (3/4↔6/8 — the
      metric-profile sub-score's job) / wrong; raw exact-rate (1/5 on the prototype)
      *understates* the engine, which gets the beat grid right on 3/5. (c) **slice-1
      scope = single-meter songs only** (`infer_meter` is whole-sequence; meter-
      changing songs await the deferred change-point form — gap 11 follow-on). No
      engine work needed — `infer_meter` provides the inference; A6 owns the scorer +
      the score-`<time>` parser. Proposed to A6.
    - **Tempo — gated on a build AND a data decision.** There is **no tempo
      inference** today (only `TempoMap` from file meta); `infer_tempo` (the
      rhythmic analog — onset-IOI / autocorrelation beat induction) would be a new
      capability. And the data is the hard part: score MIDI carries a fixed
      notated tempo (trivial truth); the *interesting* case is performance
      timing / rubato, which lives in audio + performance data — and **audio is
      out of scope (Decision 9)**. So first decide what "tempo deduction" means for
      a symbolic engine (IOI-based beat induction over performed-but-symbolic MIDI
      is the in-scope reading) before building.
    - **Groove — methodology-first.** `extract_groove` is shipped (gap 10) but
      there is no "ground-truth groove" annotation corpus; "correct" isn't a label.
      Validation is either the **round-trip invariant already pinned**
      (extract→apply reconstructs timing) or **distance-to-a-reference-template**
      — a different shape than accuracy-vs-annotation, needing a methodology
      decision before any corpus.
    *Coordination:* A6 owns the harness + corpus infrastructure; Tonality supplies
    the inference tools + the per-dimension **metric contract** (the `response-4`
    pattern that defined the key metrics). A6 is **not yet clued in** — the move,
    when scheduled, is a brief proposing the program + the first dimension (meter)
    with its metric contract and the SWD CC-BY-3.0 read-to-score license spine.
    *Cross-link:* the **closure-aware / functional-context key-finding** slice (the
    cadence/closure reweighting layer for the relative/parallel residual — D911-03,
    D911-08 — recorded in the infer_key follow-ons) is the first *new* analytical
    capability this program would score, and it shares the measure-before-believe
    discipline (the literature's closure methods are validated on non-modulating
    repertoire; transfer to lieder is unproven).
16. **Compiled harmony contracts** (added 2026-07-03 from the A8 AURICLE RFC;
    TERRANE + wend prospective) — a Tonality-owned, versioned, schema-validated
    JSON artifact that freezes theory decisions (pc sets, concrete voicings,
    voice-leading transition maps, quantization policy) so real-time clients
    consume harmony with **zero runtime dependency** on Tonality. Deliverables:
    `contracts/harmony.schema.json` (versioned in-repo) · a `contracts` module
    below the MCP line — `validate(doc)` (schema + semantic checks: **voicing ⊆
    pcs enforced as the cardinal rule in artifact form** — a realization must
    reduce to its stated identity; transition endpoint resolution; voiceMap
    index bounds) and `emit(states, transitions, policy)` (canonical
    serialization, sorted keys, stamped `tonalityVersion` — riding the existing
    `mts/io/export.py` versioning discipline, not a parallel one) · thin MCP
    wrappers per Decision 5. The `voiceMap` serializes the *already-shipped*
    `voice_leading_realized` mapping (gap 6), translated from (source_midi,
    target_midi) value pairs to the contract's (fromIdx, toIdx) index
    convention; cardinality mismatch cites `doubling.1` (voice birth/death is a
    recorded round-2 design point, a second named policy if a consumer makes
    the case). An `evidence` block carries rankings/margins/derivations as
    provenance — ignored by runtimes, preserved for audit. `edo` field reserved
    (12 fixed in v1); no EDO work. Acceptance (adopted from the brief):
    malformed-contract corpus rejected with documented error classes; golden
    contracts round-trip byte-identically; voiceMap cost equals the
    independently computed distance of the returned assignment (the underlying
    metric is already brute-force-pinned); one cross-repo end-to-end fixture —
    chord list in → contract out → AURICLE's vendored validator passes it
    unmodified. AURICLE's draft schema/validator are the starting point,
    adapted not adopted; namespace + field names are Tonality's call.
17. **Constrained voicing enumeration + ranking** (added 2026-07-03, A8; the
    **registered+rootless voicing-template corner** of the identity lattice
    made operational) — given a pc set, a voice count N, and register/spacing
    constraints, return ranked candidate voicings with margins. Two halves on
    opposite sides of the cardinal rule, same split as groove (gap 10):
    *Ranking* (analysis) — the ranking authority already owns its metric
    (`voice_leading_realized` + `doubling.1`); deterministic order, margins
    explicit, ties surfaced not hidden. *Enumeration* (generative) — a thin,
    **explicitly generative** layer producing candidates under the constraints;
    deterministic, any random component seed-explicit. Accepted under Decision
    11's scope rule (multi-client benefit: A8's resonator voicings, TERRANE's
    harmonic states, A9 Wend's `realize_voicing` seam — recorded asks:
    smoothness ceiling vs the previous voicing, register center, contour
    hold — and the Phase 7 generative work all want it). Client-supplied
    voicings remain valid ranking input regardless; this gap lags gap 16
    without blocking it (hand-authored voicings are valid contracts).
    **Slice 1 DELIVERED (2026-07-07): `mts/search/voicings.py` —
    `search_voicings(pcs, root=, constraints=, from_voicing=)`.** Bounded
    register enumeration (`register: [lo, hi]` **required, never defaulted** —
    the cardinal rule as API: the caller declares the generative bound); the
    raw space is computed upfront and an over-large window raises with advice,
    so `count` is never a truncated lie (`truncated` only ever means `limit`).
    Fields: spread / bass_pc / top_pc / top_midi / center / voicing_type
    (named-shape registry) / no_interval_over_bass (directed pc-intervals,
    mod-12) / max_voice_leading. The **ranking half ships in-slice**: with
    `from_voicing`, matches carry exact `vl_from` (`voice_leading_realized`,
    `doubling.1`) and return ranked by it — margins are the continuous vl
    values, ties broken by a deterministic secondary order. `root=None`
    searches **voicing templates** — the registered+rootless corner named
    above, now operational. **Slice 2 (open):** voice count N ≠ cardinality
    (doublings/omissions — A8's resonator ask), contour-hold curves,
    handedness-sensitive fields. MCP tool + conformance case; additive golden;
    22 tests incl. a brute-force-equality oracle.
18. **Catalog contract + pitch-answer scorer** (added 2026-07-04 from A6
    brief-19 — CHROMA, the first music-education module; design handshake in
    `integrations/audiology/response-19.md`). The second **Decision 11**
    contract instance: a versioned, canonically-emitted `catalog contract v1`
    — the 12 pitch classes with canonical names/spellings (lifted from
    `core/enharmonics.py`'s code-resident tables into data) + the interval
    definitions (`mts/data/intervals.json`, gaining an explicit
    `interval_class` field) — riding the `export.py` versioning/sha256
    discipline. **First slice: version strings on the unversioned catalogs**
    (`intervals.json`, the pc table; then `scales.json`/`chord_qualities.json`
    for the sibling modules — the export manifest currently records
    `versions: null` for them honestly). Plus `score(target_pc, response_pc)`
    — pure identity-layer arithmetic: `correct`, `error_magnitude` (interval
    class, 0..6), `relationship` both directed (semitones-up + catalog
    interval name) and undirected (interval_class — A6's P4/P5 contamination
    signature is ic 5 by construction). Deliverable includes the **full
    144-row test-vector table as a data artifact** — vendored, it is CHROMA's
    CI scoring oracle (cross-repo fixture, the gap-16 pattern). Boundary
    rulings on record: the aggregate confusion classifier is behavioural
    aggregation (A6-side, same line as the anchoring index); 12-TET explicit
    (`edo` reserved at 12, no microtonal work). Not yet scheduled — gated on
    A6's module-contract sketch surviving its second module, per the brief.
19. **Melodic tendency / attraction prior** (added 2026-07-07 from A9 Wend
    brief-3 R1; `integrations/wend/response-3.md`). The **melodic sibling** of
    gap 14's chord-succession work: which pitch wants to resolve where, and how
    strongly, per key/chord context. Verified a real gap — `analyze_melody` only
    *types* notes (NHT: passing/neighbor/…); nothing gives a prescriptive
    tendency/attraction value or scale-degree stability ranking. Engine-shaped
    and LLM-hostile (theory-grounded, deterministic), so it stays here.
    Signature: `melodic_tendency(pc_or_degree, key, chord=None) -> ranked
    [(target_pc, strength, evidence)]`, a versioned JSON prior (Lerdahl-class
    attraction / diatonic tendency table; `source`/`version`/`license` stamped,
    KK-profile pattern). **First slice:** leading-tone→tonic + chordal-7th→(step
    down) tendencies + a scale-degree stability ranking (replaces a caller's
    `root > third` hand rule with a cited number). Analysis-side, Decision-7
    plural/evidenced; the caller owns the snap policy. **A9 Wend** named
    consumer, seam `_snap_stable`. Distinct from `next_chord` and from gap 14's
    (harmonic) diatonic transition-tendency table.
    **Slice 1 DELIVERED (2026-07-07): `analysis/tendency.py` —
    `melodic_tendency(pc|degree, tonic_pc=, mode=, chord_pcs=, targets=)`.**
    Anchoring attraction `(s_q/s_p)/d²` (Lerdahl 2001) over the new versioned
    prior `melodic-tendency.1` — stability tables **frozen** from kk-1982.1
    (copied, never read live: a profile default flip must not move tendency
    scales). Returns ranked resolutions with evidence + the full 12-pc
    stability table + `prior_version`. **Fork record (Julian, 2026-07-07):**
    (A) stabilities KK-derived (empirical, in-repo, mode-aware; a Lerdahl
    basic-space table can ship later as an alternate prior version); (B)
    **target policy is a caller parameter** — rulesets/styles select their own
    resolution-target vocabulary; default `diatonic_steps` (a leap is not a
    resolution), `chromatic_steps` widens to all step neighbors so
    chromaticism is never shut out (out-of-key targets flagged); (C) chord
    anchoring ships in slice 1 (chord tones' stability ×1.5 — the Lerdahl
    basic-space triad/diatonic level ratio — in both source and target roles,
    Bharucha). Oracles reproduce the pedagogy from the frozen data: ti→do
    2.2049 tops every major key; fa→mi 1.0709 > fa→sol; stable tones barely
    tend; C minor flips fa's top target to me; the natural-minor-chromatic
    leading tone still pulls 2.0 to do. MCP tool + conformance case; additive
    golden; 20 tests. Major/minor only (the stability data's honest scope).
20. **Satisfaction-loop hooks / preference-weighted rulesets** (added 2026-07-07
    from A9 Wend brief-3 R2). For a **modular preference-learner** (a separate,
    delegated project; classical ML, versioned bias artifacts a generator
    applies deterministically). The governing principle, affirmed and recorded:
    **the learner's feature vocabulary is Tonality's** — rule firings,
    conformance reports, atoms, succession tags — not bespoke, so it serves any
    client (Decision 11 applied to a learner: engine owns the deterministic
    feature vocabulary, learner owns the ML, pinned artifact + seed reproduces).
    **v1 is recipes, no engine work:** (a) preference-weighting via *thresholding*
    — mine the liked spans as a corpus (`induce_ruleset`), contrast against the
    disliked; do **not** duplicate spans to fake weights (it corrupts the
    piece-presence BH-FDR, which assumes independent pieces); (b) weighted
    conformance is client-side-derivable — `evaluate_ruleset` already emits
    per-rule conformance + beat-tagged violation `location`s, so span-weights
    align client-side. **Only potential engine slice:** graded (continuous)
    sample-weights on induction, which *can't* be got soundly by corpus
    construction — build only if the binary liked/disliked split proves too
    coarse.
    **Consumer of record: A10 wont** (intake brief 2026-07-07,
    `integrations/wont/{brief,response}.md`). Recorded outcomes beyond the v1
    recipes: **(1) span-independence recipe — per-run pooling.** Spans from one
    run are correlated siblings (shared seed/config/ruleset), so treating N
    spans from M<N runs as N pieces is pseudo-replication (duplication is its
    ρ=1 limit); pool each run's liked spans into one pseudo-piece so
    `pieces = runs`, restoring independence, and read every piece floor
    (`min_support_pieces`, `exploratory_floor_pieces`) against **runs**, not
    spans. Recipe answer, no engine work. **(2) Field-manifest export —
    DELIVERED (2026-07-07):** `ruleset_field_manifest()` (rules + MCP tool), a
    versioned (`ruleset-fields.1`) machine-readable enumeration of every family's
    where/check fields (kind, closed vocab, harmony-dependence) + ops +
    polarities, pinned by `test_manifest_is_current_with_FAMILIES` so a
    vocabulary change can't silently drift the contract. **(3) Firing-location
    extraction — DELIVERED (2026-07-07):** `evaluate(..., include_firings=True)`
    → each applicable `RuleResult.firings` carries the located *considered-and-
    held* items (the positive complement to violations;
    `considered == firings + violations`). Opt-in, `None` when not requested and
    the key is omitted from `to_dict` — so default output stays byte-identical
    (golden/port surface unchanged for existing callers). **(4) Boundary
    ruling:** satisfaction labels stay wont-schema, engine records embedded by
    reference — no sanctioned satisfaction side-car in Tonality's interchange
    vocabulary (satisfaction is consumer-side aggregation, the AI/deterministic
    boundary). Graded sample-weights on induction remain the one open contingent
    engine slice; the v1 recipes + these two exports unblock wont fully.
21. **Rhythmic constraint search** (added 2026-07-07, prompted by Julian —
    assessment artifact `docs/reviews/2026-07_rhythm-search-assessment.html`).
    Not an analogy — the identity layer's own mathematics on a circle of time:
    a rhythm cycle (onsets in N subdivision slots) is a bitmask over **Z_N**
    exactly as a pc-set is one over Z_12, and the field vocabulary maps
    column-for-column (cardinality→onset density, interval vector→IOI content
    [Toussaint], rotational_period→isorhythmic period, is_achiral→retrograde
    symmetry, df1..df6→pulse alignment / syncopation complement [Amiot],
    maximal evenness→Euclidean rhythms [Bjorklund, Clough–Douthett],
    contains→figure-at-some-rotation, complement_mask→the interlocking part).
    Proof-by-example on record: mask {0,2,4,5,7,9,11} is the diatonic scale
    *and* the bembé bell pattern — same steps 2212221, same ME, same vector.
    **Design constraints (recorded with the gap, not to be relitigated):**
    (a) needs a small **Z_N-generic cyclic substrate** (core is hard-12 by
    doctrine) — deliberately the same machinery Phase 6 needs, so rhythm is
    the low-risk proving ground that pre-pays it (see Phase 6 note); (b) the
    **granularity default flips vs Decision 12**: rotation moves the downbeat
    (a rotated tresillo is a different groove), so the rhythmic default is
    **rooted** (slot 0 = downbeat), necklace/bracelet folding opt-in; (c)
    **identity-only** — onset masks are the rhythmic identity key; durations/
    velocity/micro-timing are the realization side, already owned by groove
    extract/apply + swing analysis (clean seam, no overlap). Build when
    pulled (likely first consumers: A9 Wend — conditional/asymmetric meter,
    groove — or drum-generator work); explicitly does **not** jump gap 19's
    queue. Not scheduled.

## Decisions on record (the "why", so we don't relitigate)

1. **Build on the existing engine, don't greenfield.** The bitmask PC substrate,
   immutable core objects, and the multi-notation parser are correct and tested.
   Greenfield would rebuild them nearly identically. The foundation has the right
   *substance*; we are correcting its *frame* (library/MCP, not standalone app).
2. **Time and timeless identity are layers, not opposites.** The identity layer is
   atemporal; the temporal layer sits above and *references* it. (See CLAUDE.md
   "core data model.")
3. **Identity key + optional realization**, with a two-axis lattice
   (transpositional × registral). Register is a *richer* representation that
   reduces to PC — not "secondary metadata." Voicing-sensitive analysis reads the
   realization; matching/naming reads the key.
4. **Reduce, never invent.** Inventing register = choosing a voicing = a generative
   act. Analysis declares the level it needs and errors when it's missing.
5. **The MCP layer is a thin adapter, not a subsystem.** Intelligence stays in the
   engine. MCP is the first *consumer* and a forcing function for clean APIs.
6. **Keep the tuning system behind a reduction boundary.** "The identity key *is* a
   12-bit bitmask" is a 12-TET-specific choice we accept for now (the substrate is
   correct and tested; a generalized identity type is premature). To keep the
   eventual multi-system generalization (see Phase 6) from being a teardown, the
   **lattice** (transpositional × registral) and the **Realization** API are
   deliberately tuning-agnostic — rooted-ness and register-ness are not 12-TET
   concepts. Only `reduce_to_key()` and `core/bitmask.py` know the substrate is 12.
   New code routes through the reduction rather than open-coding `mask` arithmetic,
   so swapping the substrate later is a localized change, not a rewrite.
7. **Disambiguation is ranked, explicit, and plural — never an opaque guess.** When a
   set or passage admits several names/analyses (the candidates `interpret_chord`
   enumerates), the engine selects the contextually-best reading *and* surfaces the
   competing alternatives with inspectable, data-derived weights and the evidence
   behind them. Statistical scoring stays **reproducible** (same input + same corpus
   → same ranking); it never collapses to a single black-box answer. This preserves
   the division of labor: transparent combinatorics + explicit statistics *here*,
   open-ended semantic leaps in the caller.
8. **Rulesets are declarative, serializable, versioned artifacts over the
   engine's own analytical vocabulary** (added 2026-06-11; see Phase 4.6). A
   compositional ruleset is a set of predicates over facts the typed results
   already expose — scoped (per-event / adjacent-pair / phrase / global), hard
   or soft-weighted, declaring the specification level each rule requires
   (cardinal rule applies: a parallel-fifths rule *errors* on voiceless
   material). Rulesets are versioned priors (the Phase 3.5 pattern; the naming
   weight table is the degenerate first instance). **Rule *proposal* is the
   caller's job; rule *verification and evaluation* are the engine's** — an
   LLM translates a treatise into candidate rules in the DSL, the engine
   validates and evaluates them exactly. Rule *induction* is exact
   version-space mining over a template vocabulary, scored against null
   models — statistics, never an in-engine learned black box. Corollary: the
   engine can only express, check, and induce what its analytical vocabulary
   can say — vocabulary expansion (voice, melody, rhythm) is therefore a
   first-class investment, not a side effect.
9. **Audio stays outside — permanently.** (Decided 2026-06-11 after evaluating
   Magenta DDSP for inclusion.) Audio synthesis and audio-domain DSP — neural
   (DDSP/RAVE-class) or otherwise — are consumer-side, full stop. Reasons on
   record: the division of labor *is* the product (exact combinatorics here;
   a learned controls→audio mapping is the opposite kind of object, and
   Decision 8 just barred in-engine learned components); three consumer
   briefs (A5–A7) signed contracts that depend on the symbolic-only boundary;
   neural synthesis is not byte-reproducible in the versioned-priors sense;
   and the dependency footprint is incompatible with a `mido`-sized engine.
   The engine's audio-facing contribution is **descriptor tracks** (typed
   continuous harmonic control signals — see Phase 5), never sound. Which
   synthesis stack a consumer uses (DDSP, RAVE, analog modeling, …) is a
   per-project choice made in *their* repo.
10. **C++ is the performance home — dual implementation, golden-anchored.**
    (Decided 2026-06-12; **revised 2026-06-29 with Julian** — see the revision
    note.) A C++ core becomes the engine's **performance / generative / embedded
    main**, while the **Python implementation stays a fully-functional peer** (not
    a binding shim). Both are held to one language-neutral spec — the conformance
    golden. Motivations on record: A4's plugin/device frame cannot ship a CPython
    runtime (the one consumer the Python engine structurally cannot serve
    in-process); an embedded profile (below) needs it; a C++ core compiles to WASM
    nearly for free, incidentally reopening the declined browser-door commitment as
    a side effect rather than a promise. Sequencing fence: port **after** the 12-TET
    surface is frozen — Phase 6 renegotiates "the mask is the key", so porting
    before it means porting the substrate twice (and **port by stability** — only
    the frozen subset is ever dual; see Phase 8 / [CPP_PORT.md](CPP_PORT.md)). The
    migration's spec anchor is the **golden-file conformance harness** (delivered
    2026-06-12, `tests/test_conformance.py` + `tests/golden/conformance.json`): one
    deterministic call per MCP tool, full-JSON comparison with float tolerances
    (rel 1e-9), language-neutral by construction — a C++ engine reproducing the
    goldens is conformant. The harness doubles today as regression armor: any output
    change fails it; intended changes regenerate goldens in the same PR, making
    output drift reviewable. Versioned priors and catalogs are JSON and ship to both
    implementations verbatim. See Phase 8.

    **Revision note (2026-06-29):** the original decision said "**not** a second
    parallel implementation (two implementations drift; a fork is the failure
    mode)" and that "the Python package becomes a shim." Reversed deliberately:
    some consumers are better served by **pure-Python** Tonality (no native
    toolchain — agents, notebooks, scriptability, and the MCP live-signature
    introspection a pure C++ port would *lose*), so Python is kept first-class. The
    drift fear that motivated "not parallel" is now mitigated by machinery that
    didn't exist in June: (a) the **conformance golden is CI for both** — neither
    can ship a parity-breaking change, so a golden-anchored pair can't drift
    silently (the failure mode was an *unanchored* fork); (b) **port-by-stability**
    bounds the dual surface to the frozen core — the churning analysis layer lives
    in Python only until it freezes, so no two copies of moving code; (c) **Python
    remains the spec's source of truth** (the golden is generated from it), so a
    disagreement has a defined arbiter, not a fork.
    *Consumer-port corollary (2026-06-13, ruled from TERRANE brief-3 —
    its VST3/AU JUCE plugin can ship neither CPython nor a sidecar):*
    **a consumer MAY maintain a faithful native port of the subset it
    uses, in the interim before the Phase 8 shared core exists** — bounded
    by two contracts so it is sanctioned interim, not a drift-prone fork.
    (1) *Versioned data + documented algorithm:* the port computes the same
    answers from the same versioned data, citing the same version strings.
    Key profiles (`kk-1982.1`) are already portable JSON; the table-driven
    functions (DFT/set-class/prime-form, the `doubling.1` pairing) are
    deterministic algorithms over the 4096 mask-space, documented in their
    docstrings — ported by reimplementation, optionally against a generated
    precomputed-table artifact if a consumer wants pure data. (2) *Parity
    is mechanically checkable, not trust-based:* the **golden conformance
    harness is the oracle for consumer ports too** — a port is faithful iff
    it reproduces the relevant golden cases (within the same tolerances).
    The *destination* still removes the fork entirely: when the Phase 8 C++
    core lands, consumers **link it** rather than maintaining a port. TERRANE
    is the recorded motivating native consumer (four functions: weighted key
    induction, `voice_leading_realized`, `dft_magnitudes` evenness, chord
    identity/naming; all at harmonic-event rate, never audio-rate). A
    **stable-schema versioned-data export** (priors + a generated set-class/
    DFT table artifact) is the concrete deliverable this implies — recorded
    in Phase 8.
11. **Contracts as object code — Tonality is the compiler for real-time
    consumers.** (Decided 2026-07-03 with Julian, from the A8 AURICLE RFC.)
    Real-time clients (VST/JUCE class) cannot call Python and must be
    deterministic; without a Tonality-owned artifact format each grows its own
    dialect — the Audiology divergence repeated per consumer. So Tonality owns
    **compiled contract formats**: versioned, schema-validated, deterministic
    JSON artifacts that freeze theory decisions for consumption without any
    runtime dependency (first instance: the harmony contract, gap 16).
    Analysis/authoring stays in Tonality; clients get a frozen, diffable,
    version-controlled document; the plural/ranked/evidenced discipline
    travels in the artifact as a provenance block runtimes ignore. This
    *complements* Decision 10, not competes: contracts serve consumers whose
    harmonic material is decided ahead of time; the C++ core serves consumers
    who need the engine live.
    **Scope rule (recorded with this decision, Julian 2026-07-03):** add to
    Tonality anything that may benefit **multiple clients** in the future,
    provided it doesn't break the cardinal rules. Generative capabilities are
    in scope under this rule *as* generative — explicitly labeled, never
    disguised as analysis (the groove-apply precedent; applied first to
    voicing enumeration, gap 17).

*Efficiency & realtime-fitness — planned audit + the multithreading frame (added
2026-07-08 with Julian; **first pass shipped same day** — `benchmarks/`,
`baseline-2026-07-08.md`: freezability CLEAN, slowest tool 6.3 ms, contract
artifacts sub-KB / µs-load — all green, nothing to act on).* The realtime contract
is already **Decisions 10 + 11**:
a real-time consumer never calls the engine on its hot path — it either reads a
**frozen contract artifact** (Decision 11) or embeds the **C++ core** (Decision
10). So the engine's own target is **offline / interactive** latency, not the
audio thread; "realtime-safe" here means *freezable, small, fast to load, cheap
to read* — not "fast on the audio callback." A periodic **computational
efficiency audit** (a group effort, sibling to the capability audit loop) is
planned to hold that standard: measure (a) no core reads wall-clock or hides
global mutable state that would bar freezing/reproducibility, (b) contract-artifact
freeze size + load cost (e.g. the 2–6 KB transition-matrix target), (c) per-tool
interactive latency, (d) allocation on the read/`sample` path. Division of labor:
the dev loop keeps hot paths engine-free and results freezable; the **tonality-core
port** owns low-latency in-process throughput (GIL-free, vectorizable); each
consumer owns its own audio thread. The RE-5 series (caching, single-sweep,
branchless mask ops) is the existing lineage this audit extends.
  **Multithreading — where it fits, and where it doesn't.** *Determinism is the
  hard constraint:* any parallelism must yield byte-identical output regardless of
  thread scheduling (the conformance golden + reproducibility), so only
  **embarrassingly-parallel map + canonical-order reduce** — no shared mutable
  state, no race-ordered output. *CPython reality:* the GIL bars CPU-bound thread
  speedup, so true parallelism needs **multiprocessing** or the **C++ port
  releasing the GIL**; pure-Python threads help only I/O-bound concurrency (the
  MCP/bridge serving concurrent requests). *Where it pays (offline/batch only):*
  the **per-piece corpus map** — `induce_ruleset`, `build_transition_matrix`,
  `segment_to_chords`, and dataset ingestion all loop independently over pieces, so
  corpus-scale processing parallelizes cleanly behind a deterministic reduce; and
  the **exhaustive search enumeration** (`search_identities` / `search_voicings`
  over the 4096-identity universe / bounded register windows). *Where it does NOT
  belong:* the identity-layer cores (bitmask / DFT / prime-form ops are
  microseconds — thread dispatch dominates; **vectorization + the C++ port** are
  the lever there), and any realtime consumer thread (barred by Decisions 10/11
  regardless). Net: multithreading is a **batch-harness** concern (offline corpus
  throughput), not a core or realtime one — and the audit should **measure before
  building** (a parallel map pays only when per-piece work ≫ dispatch overhead).

12. **Containment granularity follows universe granularity (constraint search).**
    (Decided 2026-07-07 building `search_identities`.) In the default
    **set-class** universe, `contains`/`contained_in` fold inversions — a shape
    and its mirror are the same set class, so a rooted-shape test against Rahn's
    (arbitrarily-handed) prime form would be ill-posed for chiral sets. In the
    **rooted** universe (`expand_transpositions`/`all_masks`) they are strictly
    transpositional: `[0,4,7]` means the major triad, not the minor. Corollary:
    *signed* chirality is not a set-class field — only `is_achiral` (a genuine
    T/I-invariant) is; handedness-sensitive search awaits the register-aware
    `search_voicings` slice. The rule is teachable and keeps every field a true
    invariant of the universe it is queried in.

## Build sequence

### Phase 0 — Foundation hardening ✅ DONE
- [x] Encapsulate session state in `SessionCatalog`; kill module-level globals.
- [x] Replace `dict[str, object]` analysis returns with typed result dataclasses.
- [x] Project scaffolding: CLAUDE.md, ROADMAP.md, git hygiene, harness.

### Phase 1 — Formalize the identity model ✅ DONE
- [x] Promote the parser's `scope` (abstract/note/absolute) into a first-class
      identity concept: an explicit lattice cell (transpositional × registral).
      `core/spec_level.py` defines the two axes and four named corners; `scope`
      is kept as an additive compat alias bridged in `specs.py` (`from_scope` /
      `to_scope`). The bridge proves `scope` is a diagonal — it cannot express
      the registered + rootless corner.
- [x] Introduce the **Realization** type (ordered pitches, doublings, bass) as a
      sibling to the identity key; define `realization → key` reduction.
      `core/realization.py`; `reduce_to_key()` is the sole 12-TET reduction
      boundary (Decision 6). `ChordParseResult.to_realization()` builds one from
      the absolute pitches the parser already captured.
- [x] Make the **voicing template** (registered + rootless) expressible — a
      `Realization` with `root_pc=None`.
- [x] Audit analysis functions: tag each with the specification level it requires;
      add the "error, don't guess" guard for register-dependent analysis.
      `analyze_chord` is now pure-identity (no fabricated voicings); register
      analysis moved to the guarded `analyze_voicing` (raises
      `SpecificationError` via `require_realization`); the synthetic stack
      generator moved to the explicitly-generative `suggest_voicings`.

### Phase 1.5 — Vocabulary completeness (voicings + enharmonic equivalence)
Near-term enrichment that deepens the identity model just built. Goal: the engine
knows *all* the standard names a chord/voicing can go by, and recognizes when two
specifications are the same object. Builds directly on the Phase 1 lattice and
`Realization`. **Preserve the division of labor:** *naming/recognizing* an
existing object is analytical; *producing* a voicing is generative.

Workstream A — **named voicings (generation + recognition).**
- [x] A named-voicing vocabulary (generative, `suggest_voicings`): closed,
      open/spread, drop-2 / drop-3 / drop-2&3 / drop-2&4, rootless (A/B), and shell.
      Built as an extensible registry (`_VOICING_BUILDERS`) over the closed stack;
      each voicing declares applicability and exact duplicates are collapsed.
      *Deferred:* quartal/quintal, cluster, and idiomatic named voicings (e.g.
      "So What") — these are voicing *styles* less well-defined per-chord; add as
      registry entries when needed.
- [x] Express register-bearing-but-rootless voicings as **voicing templates** (the
      `REGISTERED + SHAPE` corner Phase 1 unlocked); concrete voicings are
      `Realization`s. (Delivered in Phase 1: `Realization(root_pc=None)`.)
- [x] Inversions as first-class (root position + inversions; figured-bass labels).
      The `Inversion` result carries `position_index` / `position_name` /
      `figured_bass` (triads: 5/3,6,6/4; sevenths: 7,6/5,4/3,4/2; generic position
      name otherwise).
- [x] **Recognition** (analytical, register-required): `analyze_voicing` now reports
      the actual bass `inversion`/`figured_bass`, an `openness` (closed/open), and a
      recognized `voicing_type` matched against the *shared* `voicing_shapes`
      vocabulary (same registry that generates them). *Limits (honest None):*
      recognition is shape-based, so doubled or non-vocabulary spacings return
      `voicing_type=None`; inversion-invariant matching is a future refinement.

Workstream B — **enharmonic & naming equivalence (structural, beyond PC spelling).**
- [x] Add an `aliases` field to `ChordQuality` (parity with `Scale`); catalog the
      common alternate names. Loader registers aliases as extra catalog keys (so
      `C:major`, `A:m7`, `G:dom7` resolve); `_classify_qualities` de-dupes by
      canonical name so aliases never appear as separate matches.
- [x] Model structural equivalence for symmetric / ambiguous sets and surface *all*
      valid names+roots, not just one: `interpret_chord` (in `equivalence.py`)
      enumerates every `(root, quality)` naming — diminished-7th (4 roots),
      augmented triad (3), ambiguous sets (C6 = Am7), and the augmented-sixth
      family via its enharmonic dominant interpretation. *Deferred:* full
      *functional* augmented-sixth labelling (It/Fr/Ger + spelling) is Phase 3
      territory; B2 exposes the pitch-class equivalence it rests on.
- [ ] Reproducibility: the chosen spelling and any equivalence are explicit in the
      result / dataset record (dovetails with the Phase 3 analytical-vs-display
      context split).

### Phase 2 — Temporal layer ✅ DONE
- [x] Replace the `timeline.py` stub with real `Event` / `Sequence` types — the new
      `mts/temporal/` package: `Event` (onset/duration in quarter-note beats +
      `Pitch`), `Sequence` with `sounding_at` / `realization_at` (a window's
      pitches → a rootless `Realization` → identity key), plus **full tempo + meter**
      (`TempoMap` beats↔seconds, `MeterMap`/`TimeSignature` → bars/beats/downbeats).
      `analysis/timeline.py` is now a deprecated shim; migrating `workspace`/`io`
      off it is a tracked follow-up.
- [x] Implement `io/midi.py` ingestion (MIDI file → events). **Decision: mido**
      (runtime dependency; thin adapter so the engine never imports mido directly).
      `sequence_from_midi_file` / `events_from_midi_file` map ticks→quarter-beats,
      pair note on/off (incl. velocity-0), and read `set_tempo`→`TempoMap` /
      `time_signature`→`MeterMap`. Live/streaming MIDI stays out of scope.
- [x] Segmentation + harmonic rhythm: `mts/temporal/segmentation.py` — `segment()`
      partitions a `Sequence` into maximal stable-pitch-class-set spans (`Segment`
      carries pcs/mask + a representative `Realization`; `.interpret()` names it via
      `interpret_chord`); `harmonic_rhythm()` reports segment count, mean duration
      (beats/seconds), and changes-per-bar. Silences dropped; octave doublings don't
      split a segment. *Future:* harmonic (chord-level) segmentation that filters
      non-harmonic tones by metric salience. *(Reframed 2026-06-10, parked after
      Phase 3.5:)* treat it as **cover-maximization** — choose boundaries and one
      catalog identity per span to maximize metrically-weighted explained notes;
      the residue is classified as non-harmonic tones by approach/departure
      intervals over the event graph (passing, neighbor, suspension, anticipation
      are decidable combinatorially). Wants VL-distance (chord-change cost) and
      key induction (Phase 3.5) as inputs — sequenced after both. This is the
      demo-vs-tool gap for real performed MIDI: literal PC-set stability
      over-segments badly on passing tones and arpeggiation.
      *Consumer-surfacing note (2026-06-13, Julian — for Audiology/A6):*
      **per-note passing/approach-tone typing already ships** —
      `analyze_melody` / `melodic_analysis` returns `approach_class` &
      `departure_class` (step/skip/leap) and `nht_type` (passing / neighbor /
      appoggiatura / escape / suspension / anticipation / pedal). The catch is
      that it is **harmony-relative and never guessed** (no `(start,end,pcs)`
      spans → no claim), and our *literal* PC-set segmentation folds the NHTs
      *into* the sounding set, so harmony spans auto-derived from
      `midi_file_analysis` are not NHT-clean (the circularity this refinement
      resolves). Two ways to surface NHTs for a consumer, recorded:
      (a) **convenience wiring** — given a sequence with a designated melody
      voice (or a chord track), run voice-separation + `analyze_melody` and
      return the melody NHT-annotated; works *today* when harmony is
      separable (voices exist via `Event.voice`), small build; and
      (b) **this harmonic-segmentation refinement** — NHT-filtered chord spans
      make the *whole* file→passing-tones path turnkey, the principled closer.
      Known limitation to carry: NHT typing is onset-based, so tied
      suspensions are missed (review pass #1, finding 5).
- [x] **Addendum (2026-06-10, application-driven): MIDI export** — the write-side
      mirror of ingestion: `Sequence` (+ `TempoMap`/`MeterMap`) → Standard MIDI
      File via the same thin mido adapter. Surfaced by the Target-applications
      list (every A2/A3 transformation must close the loop back to a file).
      Small and well-bounded; no new dependency. Round-trip
      (`read → write → read`) is the natural invariant to test.
      **Delivered (2026-06-11):** `sequence_to_midi_file` /
      `midi_file_from_sequence` — single track, tempo/meter maps preserved,
      per-pitch velocity/channel round-trip, note_off-before-note_on ordering
      so re-struck notes survive. Quantization is honest: beats exact at
      480ths; bpm to within SMF's integer-microsecond resolution. Round-trip
      and the full write→analyze loop (A2's skeleton) are tested.

### Phase 3 — Contextualization & dataset schema ✅ DONE
- [x] Resolve the **two "context" concepts**: *display* context pushed to the edge
      — analysis is numeric/PC-only and spelling/labels render via
      `mts/context/result_format.py` from a `DisplayContext` (Slices 1a/1b); and
      *analytical* context made first-class as `AnalyticalContext` /
      `contextualize_chord` (Slice 2). All four CLI scripts now build a
      `DisplayContext` and render through the formatters (Slice 3) — the parked
      `wip-context-cli-rewiring` work was **re-done on current main** (incl. the
      `run_specific` shadowing-crash fix) rather than merged, then retired.
- [x] Define the **dataset record schema** — the enriched unit emitted per musical
      object/event. Reproducible (capture spelling/context choices explicitly).
      Delivered as the new `mts/dataset/` package (Slice 4): a flat-leaf
      `DatasetRecord` (tiers `identity` → `analysis` → optional `realization` →
      optional temporal `placement`, mirroring `event → realization → identity key`)
      grouped by a `Dataset` container, with a numeric **canonical core** plus a
      shed-able reproducibility layer (`source` provenance, `analytical`/`display`
      context snapshots, and a *derived* `display` block) and a `minimal()`
      projection. `SCHEMA_VERSION` is explicit. Builders (`record_from_chord`,
      `record_from_segment`, `dataset_from_sequence`) *assemble* existing typed
      results — they compute nothing new. Lives **above** analysis/temporal/context
      (it imports all three; none import it) — which is why it is not in
      `analysis/results.py` (that would invert the `temporal → analysis.results`
      dependency).

      **Granularity decision & reflection point.** Slice 4 ships **flat leaf records
      + a `Dataset` container**, not a recursive record — the honest fit for today's
      *flat* literal-PC-set `segment()` and flat harmonic-rhythm. Forward-compat is
      preserved by composition: records carry a `kind` level discriminator and a
      stable `index` handle, and `Dataset` is a *grouping*, **not** asserted as a
      flat, non-overlapping, exhaustive timeline partition. **Revisit the
      flat-vs-recursive distinction when a genuine parent/child *musical* layer
      arrives** — specifically (a) harmonic segmentation that nests non-harmonic
      tones under their parent harmony (the Phase 2 deferred refinement), or (b) a
      form/section layer above progressions. At that trigger, migrate via `Dataset`
      nesting / `DatasetRecord.children` (additive), **not** a leaf-schema teardown.
- [x] **Context-sensitive naming / disambiguation:** consume the candidate
      `(root, quality)` set from `interpret_chord` and pick the contextually-correct
      reading from key, functional role, and voice-leading context — returning the
      chosen name *with ranked alternatives and the evidence for each*, not a bare
      label. (Resolves the deferred functional augmented-sixth labelling from
      Phase 1.5 at detect-and-flag level. Deterministic/rule-based here;
      corpus-statistical ranking is Phase 4.5.) **Delivered (2026-06-10), per
      the design on record below:** `analysis/naming.py` (`name_chord` +
      `name_chord_across_keys`), signal tiers (a)+(b), weight table as
      versioned prior (`data/naming_weights.json`, `naming-rules.1`),
      special-function seam (aug-6 German/French, secondary dominants,
      Neapolitan), `RecordAnalysis.naming` wired in both record builders, and
      `AnalyticalContextSnapshot` moved down to `analysis/results.py`
      (re-exported from `dataset.record`) so readings label their context
      without an upward import. Behavior pins: C6=Am7 ties honestly in
      C major until a bass note or A-minor frame decides it; dim7 stays a
      three-way diatonic tie pending tier (c). *Follow-ups:* tier (c)
      sequential/VL signals; fully-spelled It/Fr/Ger labels.

      **Sequenced after Phase 3.5** (consult, 2026-06-10): this consumes an
      `AnalyticalContext`, and Phase 3.5b is the upstream *producer* of that
      object — the seam itself is correct (analysis must not hardcode
      key-finding). Building the consumer first would mean validating only on
      hand-authored keys, and inventing an evidence vocabulary against toy
      inputs rather than real producer output. **Design requirements:**
      (a) runnable per-candidate over a *ranked set* of `AnalyticalContext`s —
      key induction returns ranked candidates with margins, and relative
      major/minor near-ties are the canonical hard input; (b) the result
      schema labels each reading as conditional on the context that produced
      it (the door to joint key/chord reasoning stays open); (c) may use
      VL-distance (Phase 3.5) as a signal.

      **Design on record (proposed by the prior session, recovered + adapted
      2026-06-10; merging the PR that adds this block = sign-off):**
      - *Entry point & placement:* new `mts/analysis/naming.py` —
        `name_chord(chord, context, *, realization=None) -> ChordNaming`.
        Pure/numeric; consumes `interpret_chord` + `contextualize_chord` +
        `theory/functions.py` (+ `pcset_math.compatibility_roots` as a scoring
        input). Result types in `results.py`; roman-numeral *string* rendering
        at the display edge (`mts/context/result_format.py`). Nests into the
        Slice 4 record: `RecordAnalysis` gains optional
        `naming: ChordNaming | None` — the "chosen reading."
      - *Signal tiers* — ship (a)+(b) now, (c) as an additive follow-up:
        (a) intrinsic: bass-is-root (when a realization is present), quality
        canonicality; (b) key-relative: root-is-diatonic, functional fit via
        `theory/functions.py` + `compatibility_roots`, all-tones-diatonic
        (unless a recognized special function); (c) sequential/voice-leading:
        resolution behavior + VL smoothness/common-tones between neighbors
        (needs progression context; VL-distance now exists for it).
      - *Result shape* (numeric facts in analysis; strings at the edge):
        `NamingEvidence {signal, weight, detail}` ·
        `RankedInterpretation {interpretation, score, rank, functional_role,
        root_degree, function_category, evidence}` ·
        `ChordNaming {chosen, alternatives, is_ambiguous, context}` — where
        `context` is the `AnalyticalContextSnapshot` the reading is
        conditional on (requirement (b)). Signal weights live in an explicit
        **versioned weight table** (the versioned-priors pattern; cite the
        version in results).
      - *No-context behavior:* graceful intrinsic-only ranking with
        `is_ambiguous` set; never fabricate a key (the don't-guess rule —
        documented as distinct from the register rule).
      - *Augmented-sixth scope:* detect-and-flag `function_category`
        (`augmented_sixth_german`, …) via a general special-function seam
        that also covers secondary dominants / Neapolitan; fully-spelled
        It/Fr/Ger labelling deferred to a follow-up.
      - *Ranked-context adaptation* (the one structural change vs. the
        original proposal, which predated key induction): keep `name_chord`
        **single-context and pure**; add a thin wrapper that maps it over
        ranked key candidates (`infer_key` output → `candidate_context`) and
        returns the per-key conditional namings plus a combined view weighted
        by key confidence. Rationale: the core scorer stays testable in
        isolation; the key-confidence marginalization is its own (versioned)
        policy that can evolve without touching the scorer; and the no-context
        path already gives the core a single-arity shape.

### Phase 3.5 — Identity-analysis primitives & key induction ✅ DONE
Inserted 2026-06-10 after an external consult, before the Phase 3 disambiguation
slice. Rationale: disambiguation consumes an `AnalyticalContext` that nothing in
the pipeline yet *produces* — without a producer, the flagship pipeline
(MIDI → enriched dataset) has a caller-shaped hole, and disambiguation could only
ever be validated on hand-authored keys. **Rejected alternative (recorded so we
don't relitigate):** build disambiguation first on its signed-off design, backfill
key induction after. Rejected because the disambiguator's evidence vocabulary
should be designed against real producer output — correlation margins, the
relative-major/minor near-ties Krumhansl-style profiles are notorious for — not
placeholder contexts. Momentum was the only argument for consumer-first.

- [x] **3.5a — set-class & spectral tables.** Normal order and prime form (Rahn),
      set-class identity (prime-form mask — same integer convention as Ian Ring's
      scale numbers, see References), Z-relation partners, and **DFT magnitudes**
      (|f₁..f₆| of the PC-set characteristic function — a transposition- and
      inversion-invariant set-class fingerprint and continuous 6-D similarity
      embedding: |f₅|≈diatonicity, |f₆|≈whole-tone-ness, |f₄|≈octatonicity,
      |f₃|≈hexatonicity). All cached tables over the 4096-mask space (the PR-#17
      pattern). Includes the transformation operators the table build needs as
      internals, exposed as public named functions at near-zero marginal cost:
      `T_n` (existing rotation), inversion `I_n`, complement, M5/M7
      multiplication. Surfaced as identity/analysis-tier fields on the typed
      results (and thence dataset records). *Note:* the DFT **magnitudes**
      deliberately conflate a set with its inversion (right for similarity);
      phases are kept available — they distinguish T_n/T_nI and feed the later
      DFT-based key-finding refinement. *Deferred:* Forte names need a vetted
      reference table (deriving ordinals algorithmically mislabels the known
      Forte/Rahn discrepancy sets); prime form is the unambiguous set-class name
      until then. **Delivered:** `core/setclass.py` + `SetClassData` on both
      analysis results; prime form = min mask over the 24 zero-rooted images
      (provably Rahn — see module docstring); verified exhaustively over the
      4096-mask space (224 set classes, 23 Z-pairs — textbook counts).
- [x] **3.5b — key induction.** `infer_key(sequence) → ranked (key, score,
      margin, evidence)`, producing `AnalyticalContext` candidates — the producer
      for the Phase 3 disambiguation seam. **v1 is global key only:**
      whole-sequence Krumhansl–Schmuckler-style profile correlation over
      duration-weighted PC content (durations already exist in the temporal
      layer), ranked candidates per Decision 7. Profiles are **versioned
      empirical priors** (pattern below). **Delivered:**
      `analysis/key_induction.py` (`infer_key` + `candidate_context` →
      `AnalyticalContext`), `Sequence.pc_weights()` (duration-weighted PC
      content; `infer_key` duck-types a `Sequence`), Krumhansl–Kessler profiles
      as the first versioned prior (`data/key_profiles.json`, `kk-1982.1`);
      every result carries all 24 candidates, the top-two margin, the input
      weights, and the profile version. Degenerate input (silence / uniform)
      errors rather than guesses. *Extension delivered (2026-06-11):*
      **local key tracking** — `temporal/key_tracking.py` `track_keys`
      (windowed `infer_key` over `Sequence.pc_weights(start, end)`, same
      versioned profiles) merges same-best-key windows into `KeyRegion`s
      with beats+seconds extents, per-region mean score/margin, and the
      per-window evidence. Full-size windows only (a truncated tail is a
      different evidence basis); uninformative windows make no claim and
      never split a region (no evidence ≠ a key change). **v1 surfaces every
      blip** (Decision 7) and that stays the default; **opt-in hysteresis
      ✅ shipped (2026-06-13, Audiology Finding C)** — `track_keys(smoothing=)`
      (+ `smooth_key_regions` on `midi_file_analysis`/`piano_roll_view`) absorbs
      a region shorter than `min_region_windows` whose `mean_margin` is below
      `min_region_margin` into its stronger neighbour, with a margin override
      keeping confident brief modulations; thresholds are a versioned prior
      (`key-smoothing.1`, cited via `smoothing_version`). A *region-level*
      decision: windows keep their raw argmax as evidence, only the grouping is
      smoothed (contrast `disambiguate_relative`, a per-window correction).
      Window geometry is caller-set, cited in the result. MCP: new
      `key_tracking` tool (#20, event triples) + additive `key_regions`
      field on `midi_file_analysis`. The *online* form (A4) remains gap 5.
      *Relative-key tie-breaker delivered (2026-06-13 — the relative-major/minor
      refinement motivated by Audiology brief-3 Findings B/C):*
      `disambiguate_relative_key` (`analysis/key_induction.py`) + MCP tool
      `relative_key` (#40). **`infer_key` is left byte-identical** — its
      scores/margin are a pinned stability contract (A5/A7 control signals), so
      this is an *additive* refinement carrying the untouched induction in its
      result. *(The one coordinated change to that default since: the 2026-06-17
      CBMS key-profile flip — A6 brief-10, a +12.5pp Pareto win; A5/A7 pin
      `profile_version="kk-1982.1"` to retain the old margins. See the A6 brief-9/10
      fold.)* It engages only on a relative near-tie (`near_tie_margin` gap to
      the relative partner) and applies **tonal-hierarchy signals** from the
      weighted 12-vector (no register, preserving the pure-vector contract):
      `leading_tone` (the minor's raised 7th — a pc *outside* the shared
      diatonic collection, near-dispositive), `tonic_triad_salience`,
      `tonic_salience`; signed score (+ = minor) over a versioned prior
      (`rel-key.1`); honest `is_ambiguous` when the break is inconclusive
      (Decision 7). Validated to back Eb major on the Audiology Eb-solo shape
      and A minor when the raised 7th is present. **Chosen form vs the recorded
      "DFT-based" framing (3.5a):** shipped the transparent tonal-hierarchy
      signals (more interpretable, directly decisive on the shared collection);
      DFT-phase signals remain an available future addition. **Pipeline wiring
      ✅ shipped (2026-06-13, the direct A6 win):** opt-in `disambiguate_relative`
      on `track_keys` (applied per window — a relative near-tie adopts the
      tonal-hierarchy reading; cited additive field on `KeyTrackingResult`) +
      `disambiguate_relative_keys` on `midi_file_analysis`/`piano_roll_view`
      (global key context + per-region tracking; the global break surfaced under
      `key_disambiguation`). Off by default — exactness/stability stay default,
      `infer_key`/`key_induction` goldens untouched (the conformance diff is one
      additive cited field + one new flag-on `key_tracking` case). **Remaining
      follow-ons:** register-aware (bass-emphasis) + cadential signals; corpus
      calibration of the weights; per-window flip evidence on `KeyWindow`.
- [x] **Voice-leading distance** (parallel track; leaf primitive with no
      dependencies). Exact minimal voice-leading distance between two identities:
      min-cost bipartite matching for equal cardinality; the unequal-cardinality
      doubling/omission policy is **named and versioned** (multiple defensible
      conventions exist — the choice is an empirical prior, not a fact).
      Analytical, not generative — it measures, it does not realize. Consumers:
      disambiguation signal (3.5→Phase 3), segmentation cost (harmonic
      segmentation), progression similarity (Phase 4.5 features), Phase 7 input.
      In datasets it lives as **Dataset-level edges** between records — the first
      relational structure in the schema; additive container-level fields, same
      SCHEMA_VERSION policy as additive leaf fields. **Delivered:**
      `analysis/voice_leading.py` — exact via the non-crossing theorem (equal
      cardinality: best of n sorted rotations; unequal: non-crossing surjections
      enumerated as circular block compositions), brute-force-verified in tests;
      policy `doubling.1`; `VoiceLeadingResult` carries the optimal mapping as
      evidence. Dataset-edge integration lands with its first consumer.

**Versioned-priors pattern (Decision 7 infrastructure):** every empirical prior
the engine bakes in — key profiles (3.5b), the disambiguation weight table
(Phase 3), VL cardinality policy (3.5), corpus statistics (Phase 4.5) — ships as
a versioned data asset with one shared mechanism; results cite the prior version
they used. Same input + same prior version → same output.

### Phase 4 — MCP endpoint
- [x] Thin adapter: one tool per analysis entry point; schemas derived from
      `results.py`; stateless by default, session-backed where multi-turn is needed.
      **Delivered (2026-06-10):** `mts/mcp/` — `tools.py` holds 17 pure,
      SDK-free adapter functions (each parses agent-friendly inputs, calls one
      engine entry point, returns its `to_dict()`; Decision 5 honored —
      nothing computed in the layer); `server.py` wires them into FastMCP
      behind a guarded import (`mcp` is an optional extra; `python -m mts.mcp`
      runs stdio). Tool set spans identity (parse / chord / scale / set-class /
      interpretations), context (in-key, naming, key induction,
      naming-across-keys, VL distance), register/generative (voicing analysis
      + suggestions), comparison/brief, catalog discovery, and the end-to-end
      `midi_file_analysis` (the A1 pipeline; local key regions added
      2026-06-11). Stateless-only;
      the session-backed variant is deferred until a multi-turn consumer
      exists.
- [x] Error/validation surface suitable for blind agent use.
      **Delivered:** every tool raises `ValueError` with actionable messages
      that point at the discovery tools (`list_scales` /
      `list_chord_qualities`); inputs accept note names or pc ints; the server
      instructions tell agents that ranked alternatives + `is_ambiguous` are
      part of the answer, not noise.
- [x] **Constraint search / "inverse analysis":**
      `search_identities(constraints)` **DELIVERED (2026-07-07)** ·
      `search_voicings(pcs, root=, constraints=)` **DELIVERED (2026-07-07,
      gap 17 slice 1 — see the gap entry for scope + slice 2)**.
      — exhaustive, exact queries over the 4096-identity universe and the small
      voicing spaces ("all 7-note scales containing this tetrachord with no
      consecutive semitones"; "all voicings of Cmaj9 under 19 semitones of spread
      with no m9 against the bass"). Generalizes `suggest_voicings` into a query
      layer; explicitly generative-side (cardinal rule). Parked because demand is
      MCP-shaped — it's the marquee agent-facing tool, not a library-internal
      need. The Phase 3.5a tables are its index, so parking costs nothing: the
      substrate accrues anyway. *(2026-06-11: Phase 4.6 rulesets generalize
      this — a search constraint and a checkable rule are the same predicate
      pointed in different directions; build the constraint vocabulary once,
      there.)*
      **What shipped (`mts/search/`):** `search_identities` reuses the ruleset
      engine's `Condition` predicate over a new *identity* field vocabulary
      (cardinality, ic1..ic6, rotational_period, is_achiral,
      no_consecutive_semitones) plus structural `contains`/`contained_in`;
      strict-total validation (the blind-agent ruleset contract); typed
      `IdentitySearchResult`; MCP tool + conformance case. **Decision 12
      (containment granularity):** `contains`/`contained_in` fold inversions in
      the default set-class universe (a shape and its mirror are one class, so
      the answer can't depend on which handedness Rahn's prime form names) and
      are strictly rooted in `expand_transpositions`/`all_masks` (where `[0,4,7]`
      means the major triad, not the minor). *Signed* chirality is deliberately
      absent from the set-class field vocabulary for the same reason — it awaits
      a register/orientation-aware field slice. **`search_voicings` shipped**
      under the same predicate contract (gap 17 slice 1: required register
      window, upfront space guard, vl_from ranking, templates via `root=None` —
      design deltas from the 2026-07-07 Fable review pass recorded on gap 17).
      **Pilot consumer — A9 Wend (brief-2, 2026-07-07, adopted):** Wend replaced
      both identity seams (`pivots_between`, `tonicization_targets`) on
      `search_identities` with **576/576** + **24/24** exact parity vs its prior
      heuristic (~2.6 ms/query). Outcomes:
      - **R1 bug fixed:** in the rooted (`all_masks`) universe `contained_in`
        transposed the *enumerated identity* then reported it untransposed, so
        matches contradicted their own echo (`(0,1,3)` returned as "⊆ C major").
        The enumerated identity is never transposed — `contained_in` is now a
        literal subset test in `all_masks` (transpositional only in the rootless
        set-class universe). Regression-tested (C(7,k) counts); golden unaffected.
      - **Default-universe posture DECIDED (keep `set_classes`):** despite Wend
        using `expand_transpositions=True` on every query, the default stays the
        223 canonical set classes — the discovery/analytical answer, and the one
        the test+golden suite encodes. Rooted is the *generative* mode declared by
        one explicit kwarg (the permanent posture, not a workaround). Flipping
        would force analytical callers to dedup 12× redundancy — the worse footgun.
      - **Vocabulary (R3) — next field slice, Wend named:** `df5` (and the
        `df1..df6` DFT-magnitude family) as graded diatonicity/fifthiness fields,
        `{"gte": x}`-testable — a clean add (already computed + cached in
        `dft_magnitudes`, T/I-invariant so honest set-class fields). Wend ranks
        enumerated pivots by color as a surprise-budget signal.
        **DELIVERED (2026-07-07):** `df1..df6` float fields (gte/lte only — eq/in
        rejected as float footguns), and every match now carries the full
        `|f1..f6|` `dft_magnitudes` vector so callers rank, not just filter.
        Still open: `contains_at` (rooted-absolute) as a lower-priority ergonomic
        add.
      Exchange: `integrations/wend/{notice-search-identities,brief-2,response-2,notice-df-fields}.md`.

### Phase 4.5 — Contextual & statistical interpretation (corpus-driven)
The intelligence payoff: move from *enumerating* interpretations to *weighing* them
with statistics learned from a corpus. Depends on the temporal layer (Phase 2) for
context, the dataset schema (Phase 3) as the unit of record, and a corpus to learn
from. Governed by Decision 7 (ranked, explicit, reproducible — never a black box).

- [ ] Score / rank competing interpretations (chord names, key & functional
      readings, segmentations) by corpus statistics — e.g. progression n-grams,
      voice-leading likelihood — surfacing conflicts with weights + evidence.
- [ ] Build / ingest a corpus and a **reproducible** statistical model (explicit,
      versioned weights; same input + corpus → same ranking).
- [ ] **North-star use case:** reveal *novel* readings of existing pieces — points
      where a statistically- or structurally-supported reinterpretation diverges
      from the conventional analysis. The engine proposes and evidences; the
      human/agent judges (semantic call stays in the caller, per Decision 7).
- [ ] **Style profiles — the convergence object** (added 2026-07-07 from
      Julian's corpus→style vision; artifacts
      `docs/reviews/2026-07_style-ruleset-vision.html` + `…_gap-b-design.html`).
      The articulated goal: *metabolize a corpus (a genre, an artist's oeuvre,
      an academic text) into a named, citable artifact that captures the spread
      of its basslines, harmonies, and melodies — timing and progression
      tendencies — and lives among other derived profiles.* This is not a new
      track; it is the **union** of ones already moving: corpus ingestion
      (shipped MIDI→Sequence→dataset records), ruleset induction (4.6,
      `induce_ruleset` — soft rules with leverage weights), the per-style
      distribution priors (**gap 14** — degree-keyed transition matrices, the
      literal *sampleable* "spread"), the named-ruleset library (**gap D**,
      shipped — the shelf), and generative consumption (Phase 7 / the proven
      Wend-wont client pattern: Tonality metabolizes + validates, the client
      samples/generates). **The one genuinely new object:** a *style profile*
      that bundles the interpretable ruleset **and** the sampleable
      distributions **and** a provenance block (`source`/`method` — corpus vs.
      academic vs. per-artist, the discipline already used for versioned priors
      and wont's `tag-contrast.1` stamps). A ruleset (constraints) and a
      distribution (the spread) are two representations of a style; the profile
      carries both. **Diagnosis (2026-07-07):** the vertical (identity) and
      timing are largely shipped; the *horizontal* — progression/tendency over
      time — was the frontier, so **gap B** (harmony progressions) was taken as
      the committed unblocker of the harmony row (slice 1 delivered). Remaining
      for a first real style profile: ~~gap-B harmony *induction* (slice 1b)~~
      **✅ delivered 2026-07-08**, ~~the gap-14 distribution priors~~ **✅ the
      distribution *primitive* delivered 2026-07-08 (`build_transition_matrix`;
      real per-style data priors still to derive)**, and ~~the bundle+provenance
      schema~~ **✅ delivered 2026-07-08 (`StyleProfile` / `build_style_profile`)**.
      **A first style profile is now ASSEMBLABLE** end-to-end: corpus →
      `segment_chords` → (`induce_ruleset` ‖ `build_transition_matrix`) →
      `build_style_profile`. The **held-out eval primitive is now also DELIVERED
      (2026-07-08): `TransitionMatrix.cross_entropy(held_out)`** (MCP
      `transition_cross_entropy`) — mean surprisal (bits/transition) + perplexity
      of a distribution on fresh material, OOV-counted, `None` on infinite surprise
      (a raw matrix's unseen transition — which is *why* Laplace is the default).
      This is the symbolic side of the boundary metric. What remains is **content,
      not machinery**: real per-style *data* priors derived offline from CC0/CC-BY
      corpora (gap-14 slice 3, license-gated — needs a corpus + license sign-off),
      and, for the full determinism-boundary metric, the *neural baseline* to take
      the cross-entropy **gap** against (below). The pipeline + its self-eval are
      built; the first *named, real* style profile is a data exercise.
- [ ] **The determinism-boundary program** — *proposal on record, not yet
      assessed/sliced* (`docs/boundary-brief.md`, from the 2026-07-07 assessment
      session; a research-direction superset of the style-profile idea). Thesis:
      empirically map the boundary where explicit rulesets stop advancing musical
      outcomes and only statistical models proceed — reframed from "determinism
      vs ML" to **feasible-set (rules) vs distribution (style)** — and push the
      deterministic machinery to it. Its single most important deliverable is the
      **boundary metric**: held-out cross-entropy gap vs a neural baseline,
      tracked as DSL expressiveness grows (Conklin-style), over a benchmark ladder
      (B1 first-species *generation* → B2 chorale/Riemenschneider → B3 galant
      schemata → B4 long-range form). **Freshness (2026-07-08): the symbolic side
      of that metric now exists** — `TransitionMatrix.cross_entropy(held_out)`
      computes the held-out cross-entropy/perplexity of the deterministic model
      (gap 14). What the boundary metric still needs is the *other* term — a neural
      baseline scored on the same held-out set — to take the **gap**; wiring that
      comparison (+ a held-out corpus split) is the harness this program would
      build. Freshness note vs its `34fff86` snapshot:
      its candidate gap 1 (harmony atom family) = **gap B, delivered**; gap 5
      (soft rules/weights) **already exists** (hard/soft polarity + leverage-
      weighted `induce_ruleset`). Its still-open candidates map to recorded gaps:
      aggregation/quantification (the run-length limit, gap C), ensemble/texture
      scope, ruleset-driven *generation* (B1 — the nearest new capability), the
      corpus cross-entropy harness, and the schema layer (gap-C-adjacent). §5
      trims recorded in the brief ("genre via flat rulesets" restratified;
      "determinism vs ML" reframed). **Next step (agent's + Julian's call per the
      brief's §7): a full assessment pass that slices these into numbered gaps
      and records the boundary metric as a decision — offered, not yet done.**

### Phase 4.6 — Rulesets: a constraint syntax over the analytical vocabulary
Added 2026-06-11 (Decision 8). The articulated vision: **extract, impose, and
compare compositional rulesets** as first-class artifacts. An LLM translates a
theory treatise into the DSL through MCP; the engine validates, evaluates
against material, induces candidate rulesets *from* compositions, and feeds
rulesets into generation as constraints. Lineage: species counterpoint is a
ruleset; constraint programming for music (Ebcioğlu's CHORAL, Anders'
Strasheela) built the imposition half; version-space rule induction builds the
extraction half. What's novel here is the ruleset as a serializable, versioned,
MCP-portable object flowing both directions. Intertwined with Phase 4.5 — soft
rules and corpus statistics are the same object (weighted constraints with
provenance).

*Vision re-articulated + gap review (2026-07-01, Julian):* the destination is a
**symbolic language for musical patterns, abstractable across genres, rulesets,
specific songs, and education systems at different levels of specificity**,
plus the programmatic system that translates music to and from it and imposes
rulesets on existing compositions. Mapped onto shipped work: the language = the
DSL over the atom vocabulary · music→language = induction · levels of
specificity = the `specialize`/`combine` DAG (genre → pedagogy → composer →
piece), with versioned provenance · language→music = generation coupling
(Phase 7) **plus conformance repair** — imposing a ruleset on an *existing*
piece is minimal-edit transformation, a third operation distinct from both
evaluation and from-scratch generation, previously unrecorded; now a named
Phase 7 extension. The review surfaced four gaps, folded in below as the
**named-ruleset library**, the **harmony/progression rule family**, and the
**pattern layer** (+ conformance repair in Phase 7). Doctrine note holding it
together (Decision 8): "abstracted from genres" never means the engine knows
what a genre *is* — it means the language is expressive enough that a genre's
habits can be written down, checked, and induced in it; the semantic leap
stays in the caller. **Sequencing decision:** (1) ruleset library first
(cheapest; stress-tests the DSL and is expected to hit the missing harmony
family + phrase scope immediately), (2) harmony family, (3) conformance
repair's narrowest slice, (4) the pattern layer last (largest design lift,
to be informed by what 1–3 teach about the DSL's seams).

- [ ] **Workstream 0 — vocabulary prerequisites** (per the Decision 8
      corollary, these are first-class engine capabilities in their own right,
      wanted independent of rulesets):
      - [x] **Voice identity** — counterpoint rules (parallel fifths, voice
            crossing) need to know *which voice moved*. **Delivered
            (2026-06-11):** `Event.voice` (optional label; `None` = unvoiced —
            the engine never invents an assignment; explicit voice-separation
            of merged material stays a later refinement) · MIDI seeds one
            voice per (track, channel) as `t{n}c{n}` via a per-track parse
            (which also fixed cross-track note_on/note_off mispairing) ·
            `Sequence.voices()` / `filter_voice()` · first consumer:
            `temporal/voice_motion.py` `voice_motion` classifies every
            voice-pair transition (parallel / similar / contrary / oblique,
            mod-12 interval classes as evidence — compound fifths count) over
            adjacent onset moments; held notes yield oblique, double-stops
            make no claim, static pairs emit nothing. The *rules* (e.g. "no
            parallel fifths") stay in the DSL — they are one-line filters
            over these transitions (demonstrated in tests). MCP:
            `voice_pair_motion` (#21).
      - [x] **Melodic atoms** — contour, step/leap classification,
            approach/departure intervals, NHT typing (shared with the parked
            harmonic-segmentation work). **Delivered (2026-06-12):**
            `temporal/melodic.py` `analyze_melody(sequence, voice=, harmony=)`
            — per-note signed approach/departure intervals with the
            species-counterpoint class vocabulary (unison 0 · step 1–2 ·
            skip 3–4 · leap ≥5; definitional, not an empirical knob),
            Parsons-code contour, ambitus. A line is one voice, monophonic —
            multi-voice without `voice=` errors, overlaps error. **NHT typing
            is harmony-relative and never guessed:** runs only when the
            caller provides `(start, end, pcs)` spans (dataset records, a
            chord track, any external analysis); chord tones are not NHTs;
            non-chord tones classify by approach/departure pattern (pedal /
            suspension / anticipation / passing / neighbor / appoggiatura /
            escape / free, documented precedence); notes outside every span
            get no claim. The sequential vocabulary gap 7 (cadences) and
            harmonic segmentation will reuse. MCP: `melodic_analysis` (#22).
      - [x] **Rhythmic atoms** — duration patterns, syncopation, metric
            placement classes. **Delivered (2026-06-12):**
            `temporal/rhythmic.py` `analyze_rhythm(sequence, voice=)` — per
            note: metric placement (downbeat / beat / offbeat / subdivision)
            against the **felt beat** derived from the signature at the
            onset (compound meters — numerator > 3, divisible by 3 — beat in
            threes: 6/8 → dotted quarter; definitional, not a knob);
            a precise syncopation predicate (an offbeat/subdivision onset
            sounding through the next beat line, or a weak-beat onset
            sounding through the next downbeat — downbeats never syncopate);
            durations + inter-onset intervals per note and as line-level
            sequences. Same line discipline as melodic atoms (one voice,
            monophonic; polyphonic rhythm is per-voice). Pattern *mining*
            (which patterns recur) is Phase 4.5/4.6 statistics, not this
            vocabulary layer. MCP: `rhythmic_analysis` (#23, constant meter
            via numerator/denominator; full meter maps via the library
            door). **Workstream 0 is complete — the DSL is unblocked.**
            *Extension — swing feel (2026-06-12, prompted by Julian's
            review):* `analyze_swing` measures where each **two-way beat
            division** places its interior onset (division fraction: 0.5
            straight, 2/3 triplet swing 2:1, 0.75 dotted shuffle 3:1,
            < 0.5 reversed) and classifies straight / swung / reversed /
            mixed under the first rhythm-side **versioned prior**
            (`data/swing_feel.json`, `swing-feel.1`: straight window,
            consistency ceiling, evidence floor — engineering defaults
            pending corpus calibration; results cite the version). Honest
            bounds: three-way divisions are not swing pairs; too few
            divisions raises (no feel from no evidence); and swing that
            lives only in performance timing (quantized-straight MIDI)
            is invisible to symbolic data by nature — documented in the
            tool. MCP: `swing_analysis` (#24). Generalizes to **groove
            templates — gap 10** (per-slot offsets + velocity, the
            Ableton Extract Groove model).
- [x] **The DSL (v1, slice 1 — schema + validation). Delivered
      (2026-06-12):** `mts/rules/schema.py`. Each rule: an atom **family**
      (`voice_motion` / `melody` / `rhythm` — the scope is the family's
      natural item, a v1 simplification of the free scope axis), an
      optional `where` AND-filter, exactly one of `forbid`/`require`
      (conditions: literal equals, `in`, `gte`, `lte`), and a polarity
      (hard, or soft with weight). Field/enum registries mirror the WS0
      dataclasses exactly. **Validation is strict and total** — unknown
      keys/families/fields/operators/enum values each get an actionable
      message and *all* errors are collected, so a blind LLM repairs a
      translation in one round trip (the design requirement, made real as
      the `validate_ruleset` tool #25). Spec-level honesty is in the
      semantics: a `None` atom value (line edge, no harmony coverage)
      never matches, and an item whose check references a `None` field is
      excluded from consideration — absence of evidence is not a
      violation. *Remaining for later slices:* free scope axis (phrase /
      global / aggregate predicates).
- [x] **Composition + comparison (slice 2). Delivered (2026-06-13):**
      `mts/rules/composition.py` + a serializer round-trip
      (`ruleset_to_payload`, the inverse of `parse_ruleset` — rulesets are
      now data both directions). `combine` unions rulesets (identical
      same-id rules dedup; conflicting same-id rules raise, pointing at
      specialize); `specialize` overlays one onto a base (same-id overlay
      rules replace, new ids append; reports overridden/added — "a style =
      common-practice + these overrides"); `compare` is the structural diff
      — shared / conflicting / unique ids, plus **directly-contradictory
      rule pairs** (same family+filter+check, one `forbid` vs one `require`
      — provably unsatisfiable together on any considered item). Structural
      identity compares condition *sets* (order within an AND is
      irrelevant). MCP: `combine_rulesets` (#32), `specialize_ruleset`
      (#33), `compare_rulesets` (#34). *Empirical* comparison ("which
      conforms more on this corpus") is two `evaluate` calls, not a new
      primitive. Implication-by-enumeration is deferred (the item stream
      isn't a closed finite space — honest scoping, not built).
- [x] **The evaluator (slice 1). Delivered (2026-06-12):**
      `mts/rules/evaluator.py` — `evaluate(ruleset, sequence) →
      ConformanceReport`: per-rule violation lists with locations and the
      referenced atom values as evidence (Decision 7), per-rule
      conformance frequency, hard/soft rollups (weight-averaged soft
      score). Nothing is silently skipped: rules whose stream the material
      cannot supply (pair motion on <2 voices; `nht_type` without harmony
      spans) return `applicable=false` with the reason, and unanalyzable
      voices are listed per-rule. MCP: `evaluate_ruleset` (#26). *Substrate
      note (recorded decision):* v1 evaluates a temporal `Sequence` — the
      atom streams derive from one; the originally-sketched evaluation
      over dataset *records* arrives when atoms join the record schema.
      Ruleset *comparison* (shared rules, conflicts, contradictions) ships
      with slice 2 above; implication-by-enumeration and corpus-conformance
      profiles are recorded there as deferred/derivable.
- [x] **Induction** (the rule-space). **Slice 1 delivered (2026-06-13):**
      `mts/rules/induction.py` `induce_ruleset(sequences, *, family, ...)` + MCP
      tool `induce_rules` (#41). Apriori frequent-pattern mining over the
      `where`-lattice (piece-presence support floor, anti-monotone prune +
      same-field guard, arity cap 3, **closed**-itemset condensation) → rule
      formation over frequent consequent literals → **Fisher's exact test**
      (one-sided in the `leverage` direction, exact `Fraction` hypergeometric
      recurrence — no SciPy) vs an independence-given-marginals null →
      **BH-FDR** (q from the prior) over the realized search space. Emits a
      **validated soft `Ruleset`** (round-trips through `validation_errors`;
      empty when nothing is significant) + a `RuleEvidence` sidecar
      (support/confidence/leverage/contingency/p/q). `leverage` sign picks
      `require` (positive) vs `forbid` (negative — the spurious-forbid defuser);
      weight = `1 + scale·|leverage|`. Mineable fields = categorical / bool /
      low-card-int (`interval_class`, `pc`); floats + high-card ints excluded as
      the explosion vectors (their idiom-bearing projections are already
      fields). Deterministic (canonical ordering throughout); the scoring config
      is a versioned prior (`data/scoring_priors.json`, `induction.fisher-bh.1`)
      cited in the result; below `exploratory_floor_pieces` the result is
      flagged `exploratory` (Fisher has little power on a handful). Tests pin a
      planted "parallel motion forbids the perfect fifth" recovery + a
      null/FDR-load-bearing check + the source-corpus self-conformance.
      **Disjunction merge pass ✅ shipped (2026-06-13):** `merge_disjunctions`
      (default on) collapses same-`(where, kind, field)` single-value rules into
      one `in`-rule (`forbid interval_class in {0,7}` rather than two forbids —
      the human-readable form), **re-tested with Fisher's exact** so rigor holds
      (pooling already-significant findings, not re-FDR'd, never pooling a
      non-significant value to rescue a borderline one); `RuleEvidence.merged`
      marks them. **Deferred follow-ons (recorded):** float-field bucketing +
      high-card ints; the **exception/antecedent merge** ("forbidden everywhere
      except Y" — the AND-only `where` can't say "except"; genuinely harder);
      S/G generality-boundary labeling; MDL rule-*set* scoring; cross-family /
      phrase / global scope; hard-rule promotion. *Original design notes
      (retained):* Version-space
      mining, not learning:
      enumerate which instantiations of the template vocabulary a corpus
      satisfies (or satisfies at frequency ≥ θ). Output is a *rule-space* —
      plural by construction — narrowed by counterexample pieces, thresholds,
      or projection onto one compositional element (filter by atom family).
      The hard part is **interestingness**: score candidates against null
      models (chance material, permuted corpora; MDL flavor — good rulesets
      *compress*), reusing Phase 4.5's statistical machinery. Honest bound:
      induction can only discover what the vocabulary expresses (Decision 8
      corollary) — interpretable by design, and the reason Workstream 0 leads.
      *Research findings (2026-06-13, two background agents — the recommended
      build shape):*
      - **Mining = Apriori-style frequent-pattern mining over the conjunctive
        `where`-condition lattice**, NOT candidate-elimination (Mitchell's
        version spaces are noise-brittle — one inconsistent piece collapses
        them, fatal on real corpora) and NOT full ILP (no relational
        structure to justify it; our atoms are flat propositional records).
        Treat each atom item as a "transaction" of `field=value` literals;
        BFS the `where`-lattice adding one condition at a time (the ILP
        refinement operator as traversal order), using **anti-monotonic
        pruning** (a conjunction infrequent at θ can't be extended into a
        frequent one) + an **arity cap (~3)** to tame the blow-up. Emit only
        **closed/maximal** rules — the single most important step for an
        interpretable, non-redundant rule-space. Borrow Mitchell's S/G-
        boundary *vocabulary* to label the result's generality structure
        (most-general constraints vs tight idioms). Candidate space is huge
        syntactically (~tens of billions naïvely) but the *frequent*
        sub-lattice is tiny on real music. Closest precedent: **MUS-ROVER**
        (interpretable rule discovery from Bach chorales) and **Conklin's**
        maximally-general significant-pattern mining.
      - **Interestingness = Fisher's exact test vs an independence-given-
        marginals null, BH-FDR-corrected (q=0.05), behind a minimum-support
        floor, with leverage as the effect-size tie-break.** Fisher is exact
        integer/rational arithmetic (no stats lib needed) and *defuses the
        spurious-forbid pathology by construction* — a "forbid X" where X is
        merely rare has unsurprising marginals → large p-value → correctly
        demoted. **Avoid lift** (documented instability just above min-
        support). Multiple-testing correction is mandatory (mining many
        candidates inflates false positives); BH-FDR is cheap and the
        correction factor = the realized search-space size. **MDL** (KRIMP
        two-part code) scores whole rule-*sets* (compression), so it's a
        rule-set composition objective, not the per-rule filter. Honest
        floor: **below ~30–50 pieces, induced rules are exploratory, not
        confirmed** — Fisher has little power on a handful. Ship a versioned
        `scoring_prior` (measure, null model, `min_support`, `fdr_q`).
      - **Recorded caveats:** the AND-only `where` can't express
        "forbidden-*except*" disjunctions, so mining fragments one human
        rule into many context-specialized conjunctions (closed-itemset
        condensation mitigates; a disjunction/exception **merge pass** is the
        real fix — a recorded sub-item). High-cardinality int fields
        (`interval_class∈0..11`) and the `where`×consequent cross-product are
        the explosion vectors (bucket / mine consequents only inside
        surviving contexts).
- [ ] **Named ruleset library** (added 2026-07-01 — gap D of the vision
      review). The infrastructure treats rulesets as versioned priors, but
      `data/` ships no actual catalog: no `species-counterpoint.1`, no
      `common-practice.1`. Hand-author the first citable rulesets —
      **species counterpoint first** (the lineage this phase already cites;
      expressible largely in the shipped voice-motion + melody families),
      then a common-practice harmony set once the harmony family below
      exists. Three payoffs: (1) the cheapest possible **stress test of DSL
      expressiveness** (expected to hit the missing harmony family and the
      deferred phrase/global scope within the first ruleset — those hits are
      the deliverable, not a failure); (2) **induction ground truth** — "does
      `induce_rules` on a Palestrina corpus recover the species rules?" is
      the natural acceptance test for the whole extraction half; (3)
      "education systems" from the vision become concrete: a pedagogy is a
      curated, citable ruleset file (and pedagogical *progression* — first
      species, second species… — is a `specialize` chain). Authoring is
      caller-side translation per Decision 8; the engine ships the validated
      artifact with source citations.
      **Slice 1 DELIVERED (2026-07-07): first-species counterpoint.**
      `mts/data/rulesets/first-species-counterpoint.json` (`fux-first-species.1`)
      + `mts/rules/library.py` (`list_named_rulesets` / `load_named_ruleset`,
      shipped rulesets validated through the same strict parser) + MCP tools.
      The 5 authored rules are the *complete, exact* LOCAL first-species law and
      are tested against clean/parallel-fifths/octaves/dissonant/hidden-fifths/
      melodic-tritone fragments: no-parallel-perfects, no-direct-perfects,
      consonant-verticals-only (P4-vs-bass = dissonant, documented), no-melodic-
      tritone, recover-leap-by-step. **The expressiveness findings (the payoff),
      each proven by a test that the rule can't be authored:** (a) **cross-field
      comparison** — "counterpoint stays above the cantus firmus" needs
      `a_to_midi > b_to_midi`, but a condition value is always a literal, never
      another field (`RulesetValidationError` on the attempt) — a NEW recorded
      gap, the cleanest single missing operator; (b) **phrase/global scope** —
      begin/end on a perfect consonance, single climax (no is-first/is-last/
      position/climax field) — the deferred Phase 4.6 scope; (c) **run-length**
      — "no >3 consecutive parallel thirds" (no consecutive-count field) — the
      gap-C pattern layer. Interval semantics confirmed empirically:
      `interval_class_to` is the vertical interval **mod 12** (0=8ve, 7=P5),
      `approach_interval` signed. Golden additive; port pin untouched; 14 tests.
      **Next slices:** second species (adds passing dissonance on weak beats —
      exercises the rhythm family), then a common-practice harmony set once
      gap B ships (which the harmony-scope omissions above motivate).
- [ ] **Harmony/progression rule family** (added 2026-07-01 — gap B; the
      binding vocabulary gap for genre-level rulesets). The DSL's three
      families are voice motion, melody, rhythm — so "V resolves to I",
      "no ♭VII in this style", "avoid the deceptive resolution at a final
      cadence" are **inexpressible today**, even though the analysis
      vocabulary exists (`theory/functions.py` roman numerals + roles,
      `detect_cadences`, chord dataset records). Genre is carried by
      harmonic idiom more than by any current family. Build follows the
      exact WS0 pattern (field/enum registries mirroring the typed results;
      per-item + adjacent-pair checks over a chord stream — items = named
      progression steps carrying roman/role/degree/root-motion, cadence
      events as fields). Substrate note: this is the recorded "evaluation
      over dataset records" follow-on in the evaluator item — the chord
      stream derives from segmentation/dataset records rather than raw
      atom streams. Per the Decision 8 corollary, this vocabulary expansion
      is a first-class investment; induction inherits the new family for
      free (mineable categorical fields). *First named external consumer
      (2026-07-05): **A9 Wend** (brief R4) — wants succession tags, cadence
      events, and key-region shape as rule fields ("require an authentic
      cadence within 4 bars of a section end"); stopgaps via
      `tag_transition` self-scoring meanwhile.* *Second consumer (2026-07-07):
      **A10 wont** — the harmony training scope needs `induce_rules` over this
      family; interim stand-in is a succession-tag frequency contrast (Fisher +
      BH-FDR), ruled sound only with per-run (not per-span) presence counting
      and stamped `method: tag-contrast.1`/`exploratory` for re-derive-not-
      migrate when this ships (`integrations/wont/response.md` §3).*
      **Slice 1 DELIVERED (2026-07-07): harmony evaluation.**
      `mts/rules/harmony_stream.py` + the `harmony` family in `FAMILIES`
      (manifest bumped `ruleset-fields.2`). Item = a chord-in-context carrying
      fields `roman / role / degree / quality / is_diatonic / root_motion
      (directed mod-12) / next_role / next_roman / common_tones / color_shift /
      cadence`, built over an **explicit chord stream + key** (`evaluate(...,
      chords=[(root,quality)], key=(tonic,mode))` — the fork decision: clean and
      deterministic, isolating the vocabulary from segmentation noise). No new
      theory — roman/role from `theory/functions.py`, cadence from
      `detect_cadences`, colour from DFT. Makes "V resolves to I" (where
      role=dominant require next_role=tonic), "no ♭VII", "forbid retrogression"
      (dominant→predominant), "stay diatonic", "not a deceptive cadence"
      authorable + checkable; MCP `evaluate_ruleset` gains `chords`/`key`;
      library gains the illustrative `edm-minor-loop` (soft, hedged — a real
      trance style is corpus-derived). 13 tests; golden additive (2 intended
      message updates: family list + manifest version); port pin untouched.
      **Slice 1b DELIVERED (2026-07-08): harmony induction over a chord-stream
      corpus.** `induce_ruleset(family="harmony", chord_corpus=[(chords, key), …])`
      (and MCP `induce_rules(chord_corpus=[[chords, key], …])`): each progression
      is one *piece*, every chord-in-context one transaction, mined by the same
      family-agnostic Apriori/Fisher/BH-FDR pipeline. Mines the bounded fields
      **role / next_role / cadence / is_diatonic / degree / root_motion** (added
      `degree`, `root_motion` to `_BOUNDED_INT_FIELDS`); recovers the planted
      dominant→tonic idiom on a synthetic corpus. Reuses `build_harmony_stream`,
      so an unknown quality **raises** (the #168 error-not-guess fix) and a
      session threads registered qualities. Golden unaffected (existing
      `induce_rules` note case unchanged; new coverage is unit tests, 9 added);
      port pin untouched. **This unblocks A10 wont's mining** — the interim
      tag-contrast stand-in (`method: tag-contrast.1`/`exploratory`) can now be
      re-derived against real induced rules (see `integrations/wont/`).
      **Slice 2a DELIVERED (2026-07-08): harmonic segmentation — a note
      `Sequence` → a chord stream.** `mts/temporal/harmonic_segmentation.py`
      `segment_to_chords(sequence, *, key=None, subdivisions=1, min_pc_weight=0.1,
      downbeat_emphasis=2.0, session=None)` (MCP `segment_chords`). The chosen
      **metric-grid model** (design brief 2026-07-08): one chord per metric window
      (a bar by default; `subdivisions` splits it), pcs weighted by sounding
      duration × downbeat emphasis, thresholded, and named (`name_chord`) in the
      inferred-or-supplied key. An analytical reduction that **errors, not
      guesses** — a window naming no catalog chord is surfaced (`root_pc=None` +
      reason), never fabricated; consecutive identical labels collapse. Added
      `MeterMap.bar_spans(until_beat)` (meter-aware bar enumeration). Output
      (`.chords` + `.key`) feeds `build_harmony_stream` / `evaluate` /
      `induce_ruleset(family="harmony")` unchanged — so evaluation + induction now
      run on **raw note corpora**, not just hand-annotated progressions. 18 tests;
      golden purely additive (2 `segment_chords` cases appended); port pin
      untouched. **Honest limits (slice-2b+):** (a) the open-vocabulary **roman /
      quality / next_roman** fields are **not** mined (high cardinality; a bounded
      roman/quality enum is the recorded follow-on) — so "no ♭VII" surfaces via
      `is_diatonic` / `degree`, not a `roman` literal; (b) segmentation uses a
      **single global key** (per-window local-key regions deferred) and
      **approximates** non-harmonic tones by the salience threshold only (true NHT
      nesting under a parent harmony deferred — the Phase 2 refinement at line
      1523); (c) Wend's "authentic cadence within 4 bars of a section end" is still
      only half-unblocked — gap B gives the `cadence` field, phrase-position needs
      the deferred phrase scope; (d) major/minor only (functions), consecutive-run
      limits need gap C.
- [ ] **Pattern layer — sequential patterns/schemata as first-class objects**
      (added 2026-07-01 — gap C; the largest design lift, sequenced last).
      Constraints say what is *forbidden/required*; patterns say what is
      *characteristic* — a genre language needs both. Wanted: a serializable
      pattern object — motif, schema (Prinner, 12-bar blues, a clave),
      progression n-gram — i.e. a sequential template with a **declared
      abstraction level**, reusing the identity-lattice idea at pattern
      grain: pitch-exact / degree-relative / contour-only on the pitch axis
      × rhythm-exact / rhythm-free on the time axis (reduce, never invent —
      a pattern declares its level and matching respects it). Patterns and
      rules meet by construction: a high-support pattern projects to a soft
      `require` (the Phase 4.5 intertwining made concrete), and pattern
      *induction* extends the existing miner to sequential mining
      (PrefixSpan/SPADE family) under the same Fisher + BH-FDR rigor and
      versioned scoring priors. The deferred free-scope axis (phrase /
      global / aggregate) is this item's DSL-side landing spot. Design
      round deliberately deferred until the library + harmony family +
      repair slices have exposed the DSL's seams.
      **Slice 1 DELIVERED (2026-07-09, design brief same day — forks decided
      by Julian: melodic-motif domain first; scope = object + matcher, with
      rule-projection and induction as their own slices).** `mts/patterns/`:
      the `Pattern` object (`pattern.1` schema, total validation like
      rulesets, payload round-trip) declaring `abstraction {pitch:
      exact|degree|contour, time: exact|free}` — the lattice made concrete;
      `find_pattern(sequence, pattern, *, key=, voice=)` locating every
      (possibly overlapping) occurrence over contiguous notes of a voice
      line, **exact under the declared abstraction** (the lattice IS the
      fuzziness — no tolerance knobs; a knob would be a versioned prior
      later). Honesty contract: degree-level needs `key=(tonic, mode)` —
      **never inferred** (error, don't guess); a chromatic note has no
      degree and cannot fudge a match; rhythm-free matches surface their
      actual IOIs; chordal "lines" are skipped by name, never silently.
      Named library `mts/data/patterns/` (mirroring gap D): `prinner-descent`
      (degree×free, its description honestly noting the full two-voice
      Prinner needs the cross-voice scope) + `arch-contour` (contour×free).
      MCP `find_pattern` / `list_named_patterns` / `load_named_pattern`
      (61 tools). Also fixed in passing: `package-data` now includes the
      `data/rulesets/` + `data/patterns/` subdirs (a wheel would previously
      have omitted rulesets — pre-existing gap, packaging test updated).
      19 tests; golden additive (3 cases); port pin untouched. **Remaining
      (slices 2+):** harmonic-schema domain (n-grams over the harmony
      atoms — 12-bar blues, ii–V–I chains), rhythmic templates (clave),
      cross-voice patterns (the Prinner proper), rule-projection (pattern
      occurrence as a rule predicate — lands with the phrase/global scope
      design), PrefixSpan-family induction, gapped/subsequence matching.
- [ ] **Part-relationship / texture vocabulary** (added 2026-07-09 — **gap E**,
      from Julian: "will the patterns expose anything about the relationships
      between MIDI sections — drums, harmony, topline, bass?"; the abstract form:
      distinguish melodic vs rhythmic content and derive relationships between
      multiple inputs. Also = the determinism-boundary brief's "ensemble/texture
      scope" candidate, now sourced). What exists today for cross-part
      relationships: `voice_motion` (pairwise pitch motion between voices),
      `analyze_melody(harmony=…)` (topline↔harmony chord-tone/NHT per note),
      per-part rhythm/groove atoms — but no *ensemble* vocabulary relating
      labeled parts as parts. Design (recorded, sliced smallest-first):
      **(1) part content descriptors** — per-voice *descriptive* facts (onset
      density, pitch mobility, sustain ratio, register band) exposing how
      melodic/rhythmic/harmonic a part's content is as continuous evidence,
      never a hard classification (plural/evidenced; the caller judges);
      **(2) pairwise relation atoms** between labeled parts, both axes —
      rhythmic (onset-synchrony rate, interlock/complementarity, density ratio,
      groove congruence) and pitch↔harmony (chord-tone support rate vs a
      harmony part or chords+key, register separation/overlap, aggregate
      motion mix via `voice_motion`); **(3) a `texture` rule family** over
      those atoms ("bass doubles kick ≥ 80%", "topline stays chord-tone-
      dominant") — induction inherits free (Decision 8 corollary); **(4)
      cross-part patterns** — the pattern layer's cross-voice follow-on
      generalized (the two-voice Prinner proper, call–response templates).
      MIDI ingestion already labels parts (per-track voices), so drums/bass/
      topline/harmony arrive as voice labels today. Not yet scheduled; slices
      1–2 are the natural next build after gap-C slice 1.
- [ ] **Generation coupling** (lands with Phase 7): rulesets are the
      constraint/cost input to generative search — hard rules prune, soft
      rules score. This *is* Phase 7's "qualitative characteristics"
      parameterization, in principled, composable form.
- *No neural network required* — evaluation, comparison, and induction are
  exact. Learned components (novel template proposal, treatise translation)
  live in the caller per Decision 8: the LLM proposes, the engine verifies.
- *Long-range bridge (recorded 2026-06-11, from the TERRANE brief):* TERRANE's
  serialized **terrain plasticity** and our rulesets are sibling artifacts —
  both persist extracted musical habit as versioned state. When either is
  designed in detail, keep the bridge in view: a terrain state should be able
  to reference the ruleset version active when it was carved.
- *Prospective induction consumer (2026-06-11, from the Solve et Coagula
  brief):* deriving a ruleset from its deterministic event chronicles
  ("derive the idiom from the affinity matrix") and checking the
  instrument's own output against it — a first-class evaluator+induction
  use case, compatible with its core-determinism requirement by
  construction (rulesets are deterministic + versioned).

### Phase 5 — Representation / projection layer (projections as data)
A render-agnostic layer: the engine emits **typed, structured descriptions** of a
musical object in its canonical representations — and *rendering to pixels/files
is a thin edge consumer, not part of core* (same relationship MCP has to analysis).
Decision: **library-first, no in-repo GUI** (the deferred Qt GUI stays demoted).
This is the "visual analysis suite" expressed as data an agent or a renderer can
consume. *(Charter widened 2026-06-11, from "visuals as data" to "projections as
data": rendering targets include sound engines, not just screens — see the
descriptor-track item below and Decision 9.)*

- [ ] Each representation **declares the specification level it requires** and
      errors when under-specified — lattice-governed, "reduce never invent":
  - *register-less (identity key):* pitch-class **clock / bracelet diagram**,
    **interval-vector / IC spectrum**, **Tonnetz** (coordinates already exist),
    **circle of fifths** projection, set-class / normal-form views.
    **Bracelet + Tonnetz delivered (2026-06-12, slice 3 — closes A6 brief-2's
    descriptor needs):** both register-less (`spec_level="identity_only"`).
    **Bracelet** (`representation/bracelet.py`) — the 12 clock positions with
    the active set flagged + optional scale-backdrop membership, the active
    set's reflection axes (pc-unit centers) and rotational order, and its
    interval vector: one ring-geometry document, mostly assembly of shipped
    set-class math. **Tonnetz** (`representation/tonnetz.py`) — all 12 pcs at
    their canonical lattice coordinates (the Tonnetz layout was promoted from
    a private `chord_analysis` helper to `pcset_math.tonnetz_coordinates`, so
    descriptor and analysis share one source of truth — verified output-
    identical) with the active subset flagged, **plus the genuinely new edge
    derivation**: which active pc pairs are P5/M3/m3 edges (by pc-interval —
    5/7, 4/8, 3/9 — the lit triangles a Tonnetz reads as triads), and the
    active centroid. MCP: `bracelet_view` (#30), `tonnetz_view` (#31). The
    representation layer's four planned views (keyboard, piano-roll,
    bracelet, Tonnetz) are now all shipped.
    **Chord-anatomy maths (A6 brief-15, 2026-06-28):** A6's Chord Anatomy view
    recomputed interval-vector/DFT/chirality client-side; per the division of
    labor those determinations are now the engine's. **✅ Shipped:**
    `set_class_info` exposes **`dft_phases`** (`arg(f1..f6)`; core `dft_phases(mask)`
    — Tn-variant + inversion-negating, so it lives at the tool level, not on the
    TnI-invariant `SetClassData`) and **`trichord_chirality`** (`(a−b)(b−c)(c−a)`
    step-gap product: major −2 / minor +2 / achiral 0 / `null` for non-trichords —
    additive golden change only). `|f5|` consonance was already `dft_magnitudes[4]`;
    prime form + bitmask already returned (Ask 2 confirmed). **✅ General chirality
    (brief-15 refile, 2026-06-28):** `set_class_info.general_chirality` =
    `Im(f1·f2·conj(f3))` (core `general_chirality(mask)`), the bispectrum-slice
    `Im(B(1,2))` A6 derived — transposition-invariant, inversion-odd, works for ANY
    cardinality, major<0/minor>0 (agrees with the trichord sign on triads), 0 for
    achiral sets, and **it separates dom7 ↔ m7♭5** (which the trichord scalar +
    `5·φ3−3·φ5` cannot). Near-zero dust snapped to `0.0`. Both chirality scalars are
    now exposed (they diverge on ~29% of trichords; both valid). **✅ Colour-content
    descriptor (Ask 3, 2026-06-28):** `representation/colour_content.py`
    (`colour_content_view`) — the two somatic-colour resultant vectors as
    render-agnostic data: **interval-content** (root-blind, Tn-invariant — ic1..ic5
    on an engine-fixed pentagon, tritone central, normalized so focus ∈ [0,1];
    inversional pairs collapse) and **fifths-centroid** (root-aware, = `f5/n`). The
    rim geometry is engine-fixed (the resultant angle *is* the determination); the
    hue/OKLCH mapping stays A6's rendering. **Cross-validated against A6's
    independent enumeration: all 4083 pc-sets land on exactly 185 distinct interval-
    colour positions** (a regression fixture in the suite). **✅ Complete signed
    chirality — SOLVED 2026-06-28** (`core.chirality_sign`,
    `set_class_info.chirality_sign`): a handedness in `{-1, 0, +1}`, **0 iff
    achiral**, inversion-odd, agreeing with `general_chirality` wherever that is
    nonzero (major = −1). Construction: the sign of the first nonzero member, in a
    fixed canonical order, of the inversion-odd slice family — the bispectrum slices
    `Im(B(a,b))` plus **one trispectrum term `Im(f1³·conj(f3))`**. Research finding:
    the bispectrum alone is complete for **350 of 351** set classes — the *only*
    blind spot is the chiral hexachord `[0,1,3,4,5,8]` (`f2=f4=0`), which the
    trispectrum term resolves. `general_chirality` stays the smooth magnitude-bearing
    scalar (it false-zeros on a few exotic classes); `chirality_sign` is its complete
    sign-only companion. Verified exhaustively over all 4096 masks (a regression test
    in the suite). **✅ Complete *continuous* signed chirality — SHIPPED 2026-06-29
    (A6 brief-16)** (`core.chirality` / `core.reflection_residual`,
    `set_class_info.chirality`): `chirality = chirality_sign · √R`, with `√R` =
    A6's best-fit reflection-axis residual (`R = min_θ Σ|f_k|²·sin²(φ_k+kθ)`,
    minimized by grid-bracket + golden-section refine; complete magnitude from the
    exposed `f1..f6`). My `chirality_sign` (sign) + A6's `√R` (magnitude) — a
    parallel-derivation synthesis: `0` iff achiral, inversion-odd, major<0/minor>0,
    `dom7 = −m7♭5`, with a real magnitude ordering sets by *how* chiral. Verified
    against A6's full acceptance harness over all 4096 masks. The brief-15/16
    chirality family is now complete: `trichord_chirality` (exact 3-note),
    `general_chirality` (smooth slice), `chirality_sign` (complete ±1/0),
    `chirality` (complete continuous).
    **✅ Pitch-space tonal orientation — SHIPPED 2026-06-29 (A6 brief-17)**
    (`representation/tonal_orientation.py`, `tonal_orientation_view`): the
    **register-aware** sibling of the pc-level fifths centroid — a continuous
    fifths-space angle for a *voicing* (Chew's spiral-array center-of-effect
    projected to the fifths circle). Each sounding pitch placed at its
    circle-of-fifths angle, summed with a register weight (`octave_decay` per octave
    above the bass — caller's aesthetic knob, default 1.0 = uniform); the resultant's
    argument is a **voicing-continuous** angle (inversion/spread/doublings move it).
    Verified: reduces to `arg(f5)` for a neutral closed voicing, rotates predictably
    under transposition, and (`octave_decay<1`) distinguishes inversions/spread.
    Register-REQUIRED (a pc-set has no voicing to orient). Hue/OKLCH + the
    absolute-register→lightness axis stay A6's rendering. The "shared canonical-frame
    machinery with brief-16" the brief hypothesized does **not** exist — that sign
    was combinatorial (bispectrum), not a geometric frame — so this is a fresh build.
    **A6 brief-18 (consumer confirmation):** keep relative-to-bass weighting — the
    `absolute` mode is **declined by the consumer** (absolute register → lightness,
    not hue); the engine default `octave_decay` stays 1.0 (A6 renders at 0.5, their
    choice; no API change). And the **geometric-frame sign follow-up is dropped** —
    `tonal_orientation` covers the continuous voiced-hue angle and the combinatorial
    `chirality` is complete for the harmony map, so the brief-15→18 Chord-Anatomy arc
    is fully settled both sides (A6 consuming `chirality` + `tonal_orientation_view`).
  - *chord-network / voice-leading graph* (added 2026-06-13 from Julian's
    reference — a "Cube Dance"-family chord mandala: major/minor/augmented/
    dominant-7 nodes with parsimonious voice-leading edges, augmented
    triads as connective hubs). **Delivered (2026-06-13):**
    `representation/chord_network.py` `chord_network_descriptor(chords,
    max_distance=)` — nodes (chord + pcs + `rotational_period`, the
    hub signal) and undirected edges between chords within a voice-leading
    distance, each carrying distance + common-tone count + root interval.
    Every edge *is* the engine's `voice_leading.distance` relation (the
    Tonnetz "diagram-can't-disagree-with-analysis" guarantee), so it
    *generates* graphs like the reference; the augmented hub property falls
    out of symmetry (verified: C+ order 4, degree 6 vs median triad degree
    2 over the 12+12 triads). Register-less; MCP `chord_network` (#32 on
    this branch — reconcile tool numbering on merge). **The reference is
    recorded here as the motivating artifact.** Scope: the *voice-leading*
    (parsimony) layer only — the diagram's *functional* V7→I resolution
    arrows are a different directed/key-relative relation (G7→C is far in
    VL terms), recorded as a **gap-14 extension** (the chord-network is
    also the structural substrate for next-chord recommendation: a chord's
    out-edges *are* its candidate set, edge type *is* a tag).
  - *register-required (`Realization`):* **keyboard / piano diagram** of a chosen
    voicing, fretboard. **Keyboard delivered (2026-06-12, slice 1 — the
    layer's first inhabitant, `mts/representation/keyboard.py`):** one
    descriptor serves both keyboard uses across the lattice — register-less
    scale membership (per key: pc, octave, black/white topology, in-scale /
    degree-index / tonic flags; no context → no claim) and activation at a
    **declared** spec level: `active_midi` lights exact keys (registered),
    `active_pcs` lights every octave as an explicit octave-invariant
    projection, both together errors, and the result's `spec_level` names
    which was used so renderers show the difference instead of guessing.
    Numeric only (labels/colors are the renderer's). MCP: `keyboard_view`
    (#28). Sets the layer's conventions for piano-roll / bracelet / Tonnetz.
  - *register + time (depends on Phase 2):* **piano roll**, **staff / sheet-music**
    engraving model. **Piano-roll delivered (2026-06-12, slice 2 —
    `mts/representation/piano_roll.py`):** the register+time projection (the
    highest spec level; reads a `Sequence`, declares
    `spec_level="registered_time"`). Three render layers on one time axis —
    **note rectangles** (midi/pc/voice/velocity, onset+duration in *both*
    beats and seconds via the tempo map — the genuinely new geometry),
    **chord-region overlays** (segmented harmony with the contextually-chosen
    name, conditioned on the local key per onset — built by
    `dataset_from_sequence`, so overlay names equal the dataset's byte-for-
    byte; no divergence), and **key-band backdrop** (from `track_keys`, with
    confidence margins). MCP: `piano_roll_view` (#29, MIDI-file path — carries
    velocity/voice; coalescing + local-key tracking options mirror
    `midi_file_analysis`). A6's player overlay feed.
- [ ] Stable output schemas (coordinates, encodings, an engraving model) with
      parity to `results.py` / the dataset record, so rendering libraries consume
      them at the edge.
- [ ] Reuse existing seeds: `TonnetzAnalysis`, interval vector, reflection
      axes / symmetry (the clock/bracelet math), and re-home `layouts/` out of the
      demoted GUI frame.
- [ ] **Descriptor tracks — control signals as data** *(added 2026-06-11; the
      audio-facing projection family, per Decision 9)*. Given a `Sequence`
      (later: a streaming session, gap 5), emit a typed, time-aligned series
      of the numeric harmonic descriptors the engine already computes — DFT
      embedding, evenness, key-margin, VL effort between adjacent segments —
      per segment or per window, at a declared rate. Entirely symbolic,
      exact, versioned-prior-compatible; the consumer maps tracks onto synth
      parameters / CC streams / lighting. *Demand evidence (ad hoc today):*
      TERRANE's margin→terrain-ruggedness and Solve et Coagula's DFT→CC
      mappings — each privately re-deriving "harmonic state as a control
      signal"; this item is their shared formalization. A DDSP/RAVE-class
      instrument *conditioned on descriptor tracks* is the sanctioned shape
      for "Tonality-aware timbre" (in consumer repos, never here).
- Canonical model for the representation set: **Ian Ring's "A Study of Scales"**
  (see References) — its per-set page enumerates the representations to mirror, and
  it keys every set by our same identity bitmask.

Open question: which rendering targets to support as *reference* edge consumers
(SVG? MusicXML? LilyPond?) — deferred; core commits only to the data layer.

*Named consumer (2026-06-11):* **A6 Audiology** — its 8×8 grid, keyboard, and
canvas piano-roll all map through one pitch axis and are ready render targets
for these descriptors; keyboard + piano-roll view types are confirmed
in-scope. Delivery for the web-visualizer class runs through **gap 9** (the
HTTP door, since shipped). *(2026-06-12: A6 is being prepared as
Tonality's explicit GUI — see its entry. That makes A6 this phase's
primary customer and raises the phase's priority; the first slices
should be A6's surfaces in order of its demand: keyboard membership/
coloring descriptors, piano-roll overlay descriptors, then the clock/
bracelet identity views.)*

### Phase 6 (future) — Beyond 12-TET: generalized identity
- The current substrate is **hard 12-TET** (12-bit bitmask, mod-12 everywhere).
  Other tonal systems — n-TET, just intonation, microtonal, non-octave-repeating —
  will require a more expansive identity system, and "the mask is the key" (Decision
  6, Phase 1) will have to be revisited. This is explicitly **out of scope** until
  the 12-TET foundation, temporal layer, and MCP endpoint are solid.
- Forward-compat contract for earlier phases: don't make choices that would have to
  be *completely* unmade. The lattice and `Realization` stay tuning-agnostic; the
  12-TET assumption stays behind the reduction boundary (Decision 6). When this
  phase lands, generalizing means replacing the reduction + substrate, not the
  identity model layered on top.
- *Sequencing note (2026-07-07):* **gap 21 (rhythmic constraint search) would
  build the Z_N-generic cyclic substrate this phase needs** — masks, rotation,
  IOI/interval vectors, prime forms over arbitrary N — in a domain with no
  enharmonics, no spelling, and no priors. If gap 21 gets pulled first, this
  phase inherits a tested cyclic core instead of greenfielding one.
- **Known 12-TET footprint collisions (accepted limitations, not bugs).** 12-TET
  cannot faithfully hold every named scale, so distinct cultural/tuning scales can
  share a 12-TET footprint. These are *documented equivalences*, allowlisted so the
  audit doesn't flag them (see `audit/AUDIT.md` §7). Current list:
  - `Pelog Selisir` ≡ `Major Pentatonic` `[0,2,4,7,9]` — pelog is non-12-TET; this
    approximation collapses onto the major pentatonic. Faithful representation
    awaits this phase.
  - The long-term goal of cataloguing *all* named scales will surface many more of
    these; each gets recorded here + in the audit allowlist rather than "fixed."

### Phase 7 (future) — Generative: voice leading & progression realization
*Ordering note: the number groups this with the later work, but it depends only on
shipped layers (voicings, `Realization`, temporal/segmentation) plus optionally
Phase 4.5 corpus statistics — so it can land before the Phase 6 tuning work.*
*Named consumer (2026-07-05): **A9 Wend** — both halves, with seams already
tagged in its source awaiting this phase: `realize_voicing` → generative
realization (asks: per-step VL-cost ceiling / "smoothness", register center,
contour hold) and `pivots_between` / `tonicization_targets` → modulation-path
planning (asks: maximum fifths distance, pivot preference). The realization
half is also registered on gap 17, the nearer-term slice.*

- **Generative, not analysis** (the cardinal rule): given a chord *progression* — a
  sequence of identities, from segmentation / `interpret_chord` / user input —
  produce **voice-leading realizations**: concrete `Realization`s per chord,
  connected with controlled motion. This *invents* register/voicing, so it lives on
  the generative side (alongside `suggest_voicings`), never in the analysis path.
- **Parameterized depth & variation:** controls for how elaborate the generation is
  (voice count, register range, how many variant realizations to return) and the
  **qualitative characteristics** that shape the search — smoothness / parsimony
  (total semitone motion), common-tone retention, contrary motion, voice
  independence, openness, tessitura, dissonance treatment. Different settings →
  different stylistic outputs at different depths. *(2026-06-11: the principled
  form of these controls is a Phase 4.6 **ruleset** — hard rules prune the
  search, soft rules score it; "a style" is a ruleset handed to the generator.)*
- Builds on the named-voicing vocabulary + `Realization` + the temporal layer;
  qualitative scoring can draw on Phase 4.5 corpus statistics for "what's idiomatic."
- Output is ranked generative *suggestion data* (each variant tagged with its
  qualitative profile), kept out of analysis; spelling/rendering at the edge.

**Extensions (2026-06-10, from the Target-applications list — same generative
frame, recorded here so A2/A3 decompose onto named work):**
- **Scale re-mapping** — transform material from one scale to another preserving
  contour and degree-function rather than literal pitches (degree-correspondence
  mapping; NHTs re-mapped relative to their resolution targets). Analysis names
  the degrees; the re-mapping *invents* pitches → generative.
- **Meter re-mapping** — re-cast a `Sequence` under a new `TimeSignature`
  (re-group beats, preserve or intelligently re-place metric accents). Lives on
  the temporal types; generative because accent placement is a choice.
- **Modulation path planning** — given source and target keys, plan a key-change
  route with a stated bias (shortest circle-of-fifths walk, chromatic-mediant
  color, pivot-chord availability) and realize the connecting material via the
  voice-leading machinery above. Key-distance metrics come cheap from Phase 3.5a
  (|f₅| phase distance ≈ circle-of-fifths position) and Phase 3.5b key profiles.
- **Instrument-class profiles** — the constraint vocabulary A3 needs (register
  range, polyphony, idiomatic spacing per class: bass/pad/lead/counter-melody),
  shipped as versioned priors (Phase 3.5 pattern) so generation under a profile
  stays reproducible.
- **Conformance repair — ruleset imposition on existing material** (added
  2026-07-01; gap A of the Phase 4.6 vision review — the operation was
  previously unrecorded). Given a piece and a ruleset: find a **minimal set of
  edits** that eliminates hard violations and improves the soft score while
  preserving everything the ruleset does not speak to. A third operation,
  distinct from evaluation (analysis: score, don't touch) and from-scratch
  realization (generate under constraints): constrained search over *edits to
  existing material*, with the Phase 4.6 evaluator as the oracle and edit
  distance as the objective. Generative per the cardinal rule (edits invent
  pitches/register). More tractable than full realization and the operation
  that makes impose-a-ruleset tangible ("this folk melody under species
  rules"); it is also A2's ruleset-driven generalization (a scale re-map or
  re-voicing is a special-case repair). **First slice stays narrow:**
  single-dimension repair — e.g. re-pitch NHTs to fix melodic-rule
  violations, or move one voice to break parallel fifths — before any joint
  multi-dimension search. Ranked plural output with the violated-rule →
  edit trace as evidence (Decision 7 shape).
  **Slice 1 DELIVERED (2026-07-09, design brief same day — forks decided by
  Julian: voice-motion first; minimality = lexicographic fewest-notes-then-
  smallest-|semitone|-motion).** `mts/search/repair.py`
  `repair_sequence(sequence, ruleset, *, max_edits, pitch_window, allowed_pcs,
  max_evaluations, max_repairs)` + MCP `repair_ruleset`. Edit vocabulary:
  re-pitch a single note (no rhythm/insert/delete; one edit per note).
  Candidates come from hard **voice-motion** violations' pair-transition
  locations (the four implicated notes); the **evaluator is the oracle** — every
  candidate re-evaluated over the WHOLE ruleset (an edit that fixes the
  parallels but creates a melodic tritone is rejected), hard must hold, soft
  must not worsen. Iterative deepening ⇒ returned edit count is exactly
  minimal; ranked plural repairs each carry the edit list with per-edit
  violated-rule provenance + the repaired events. Honest refusals: hard
  violations outside voice-motion → unrepairable-in-slice-1 with rules named;
  budget exhaustion flagged; already-conformant reported. Deterministic, capped
  (`max_edits ≤ 6`, oracle-call budget). Proven on the shipped
  `first-species-counterpoint` oracle (fix the parallel fifths, 1 note,
  −1 semitone). 14 tests; golden additive (1 `repair_ruleset` case); port pin
  untouched. **Slice 1b DELIVERED (2026-07-09): melody-driven candidates.**
  A hard melody violation's note location (plus its immediate same-voice
  neighbors — melodic atoms couple neighbors: approach reads the previous note,
  departure the next, so re-pitching either side can repair) feeds the same
  candidate machinery; unvoiced lines supported. The scope check is now by rule
  **family** (voice_motion + melody = the pitch-driven families); rhythm is
  refused as pitch-independent. Proven: a melodic tritone fixed by one note /
  one semitone — including via the *predecessor* (neighbor implication paying
  off). **Remaining (slice 2+):** harmony repair via chord substitution
  (`next_chord`/`search_identities` candidate source — the different edit
  vocabulary), joint multi-dimension search, rhythm edits/insert/delete.

### Phase 8 (future) — C++ core, dual implementation (Decision 10, revised 2026-06-29)
A C++ core becomes the **performance / generative / embedded main**; the **Python
implementation stays a fully-functional peer** (pure-`pip` deploy, scriptability,
live MCP introspection), both held to the one conformance golden. **Sequencing
fence: after the 12-TET surface is frozen** (Phase 6 renegotiates the substrate —
porting first means porting twice), and **port by stability** — only the frozen
core is ever dual; the churning analysis layer stays Python-only until it freezes.
Driver: A4's plugin/device frame; side effects: WASM falls out nearly free. Build +
acceptance plan: **[CPP_PORT.md](CPP_PORT.md)**.

- [x] **Step 0 — conformance harness** (delivered 2026-06-12, with the
      decision): `tests/test_conformance.py` + `tests/golden/conformance.json`
      — one deterministic call per MCP tool (24 cases; `midi_file_analysis`
      excluded for path-bearing provenance, its components covered by the
      event-based tools), full-JSON golden comparison with float tolerance
      (rel 1e-9 / abs 1e-12), plus a coverage ratchet (a new tool without a
      conformance case fails the suite). Doubles as regression armor today;
      intended output changes regenerate goldens in the same PR.
- [x] **Versioned-data export (pullable forward — A native consumer can use
      it before the full port).** *(Delivered 2026-06-26, slice 1:
      `mts/io/export.py` + `scripts/export_versioned_data.py`.)*
      `set_class_table()` precomputes the table-driven combinatorics for **all
      4096 masks** (prime form / prime-form mask / normal order / interval
      vector / DFT magnitudes / Z-partner / complement / rotational period
      + cardinality) — each row **mirrors the `set_class_info` MCP tool's
      conformance-pinned shape, keyed by mask** (list position == mask, a direct
      lookup), so a port consumes pure data instead of reimplementing the
      mask-space math. `versioned_data_manifest()` indexes every `data/*.json`
      prior/catalog with its **version string(s)** + the table schema — the one
      document a port reads to know what to pin and cite. The script emits both
      (manifest 1.6K; table 1.4M, generated on demand, **not committed** — the
      engine is the source of truth, regenerate; the golden conformance harness
      stays the parity oracle). Faithfulness is tested row-vs-engine. Requested
      by TERRANE brief-3 (its JUCE plugin); the lowest-cost half of the
      consumer-port corollary (Decision 10), independent of the sequencing fence.
      *(Slice 2, delivered 2026-06-28:* `versioned_data_bundle()` — a
      self-contained sibling of the manifest that **embeds each `data/*.json`
      asset's parsed content + a per-asset sha256** of the file bytes, so a port
      runs without the repo (manifest stays the thin naming index; the bundle is
      a strict superset, never a second version listing to reconcile). The
      `doubling.1` voice-leading cardinality policy is now **exported as data**
      (`voice_leading_policies()` → id + description, in both manifest and
      bundle) — `voice_leading.py` behaviour unchanged. The script emits
      `bundle.json` alongside `manifest.json` + `set_class_table.json`.*)
      *(Slice 3, delivered 2026-07-05 — **export.2, the slice-1b family**:
      table rows gain `dft_phases` + `trichord_chirality` +
      `general_chirality` + `chirality_sign` + `chirality` +
      `reflection_residual`, computed through the same core functions
      `set_class_info` calls — and `reflection_residual` joins
      `set_class_info` too, preserving the tool/table mirror. Trigger: A6
      declared the briefs-15–17 chirality surface settled
      (`integrations/audiology/note-chirality-settled.md`), satisfying the
      slice-1b hold; asked by the port thread's first brief
      (`integrations/tonality-core/brief.md`). *CI gap (2026-07-09,
      `notice-ci-required.md`, ball: port):* tonality-core has **no CI and no
      branch protection** — the parity ctests run only manually, single-machine,
      while PORT.md's fixtures/PIN contract explicitly assumes "every agent and
      CI run on any machine". The notice asks the port residents to stand up a
      **ubuntu+macos matrix** workflow running the existing three parity ctests
      on every PR + require them for merge (the pin-determinism incident is the
      proof of why: green-on-one-machine is not parity). Tonality's half is
      already enforced (`test_port_pin` in this repo's CI). Loop recorded closed
      when the port replies on-channel. The port pin tripped and was
      regenerated in the same PR with the notice, per the protocol —
      the pin's first live firing.)*
      **Deferred follow-ons:** committing the table artifact + a
      regenerate-and-diff guard if a consumer wants it checked in.
- **Port plan drafted (2026-06-29 — [CPP_PORT.md](CPP_PORT.md), under review).**
      Decision: **port by stability, not wholesale** — slice 1 is exactly the
      identity-layer subset the export table already covers (`SET_CLASS_TABLE_FIELDS`),
      graded by reproducing the exported fixtures + the conformance golden (the
      mechanical parity gate). DFT phase + the chirality family are slice 1b
      (fast-follow once they settle + are added to the export). Analysis/temporal/
      bindings stay behind the freeze fence. Likely a separate `tonality-core` repo
      consuming this repo's fixtures; pybind11 bindings deferred past the core
      subset. **Status: greenlit 2026-07-03 — scaffold + thread contract
      delivered ([port/PORT.md](port/PORT.md)); Julian spawns the port agent.**
      CPP_PORT.md's open questions resolved as defaults, recorded in PORT.md:
      separate sibling repo (`tonality-core`), no bindings in slice 1,
      embedded/WASM as free side-effects not constraints, slice 1b (chirality)
      held until A6's questions settle a quiet cycle. **Accountability protocol
      (decided 2026-07-03):** two-sided and mechanical — Tonality-side,
      `port/pin.json` fingerprints the ported surface (table + fields + schema
      version + ported conformance cases) and `tests/test_port_pin.py` fails
      the suite (and thus the Stop hook) whenever the live engine drifts from
      the pin, forcing pin-regen + a notice in `integrations/tonality-core/`
      in the same PR; port-side, a refresh-fixtures script diffs vendored
      fixtures against a fresh export and re-runs parity on any change. Rides
      the existing pytest hook by design — no new hook plumbing; binds every
      agent/CI on any machine. The port agent never edits `mts/`; engine asks
      arrive as briefs on the integrations channel.
- [ ] Core identity layer (bitmask/set-class/symmetry/DFT) — `constexpr`
      tables over the 4096 universe; the cleanest layer, C++-native.
- [ ] Analysis layer (parsers, naming + evidence, induction, VL, containment)
      — the bulk; the ~35 typed results become hand-written or generated
      struct + JSON serialization (the single biggest line-item).
- [ ] Temporal layer (sequence, segmentation, tracking, atoms, swing).
- [ ] MIDI I/O (SMF lib or ~500-line hand-rolled reader/writer; mido retired).
- [ ] Python bindings (pybind11-class) for the C++ core — an *additional* fast
      path consumers can opt into; the pure-Python implementation remains a
      first-class peer (Decision 10, revised 2026-06-29), not a shim.
- [ ] Tool surfaces: stdio MCP + HTTP bridge with hand-maintained (or
      generated) schemas — the introspect-live-signatures property is the
      one Python nicety that does not survive.
- Sizing on record: full parity ≈ 3–5 focused person-months, ~1.5–2× the
  Python line count; core-only subset ≈ 3–5 weeks.

**Embedded profile (Teensy-class) — exploration, scoped 2026-06-12.**
A stripped C++ subset for microcontrollers (reference target: Teensy 4.1 —
Cortex-M7 @ 600 MHz, 1 MB RAM, 8 MB flash, native USB/serial MIDI). This is
plausibly **A4's device frame**: the embedded profile and the live-companion
hardware are the same artifact. What the scoping says so far:

- *Fits comfortably:* the entire identity layer — the full 4096-set-class
  table (prime form, interval vector, DFT magnitudes, symmetry) is
  ~200–300 KB as flash-resident constants, or computed on demand (an M7
  does the DFT in microseconds); catalogs and priors compile to constants
  (version strings still cited — the reproducibility contract survives);
  key induction (24 Pearson correlations) and the atoms are trivial; a
  compact Event (~12 bytes) puts a 10k-event window at ~120 KB of RAM.
- *Stripped:* JSON serialization and `to_dict` (results are structs consumed
  in-process), MCP/HTTP surfaces (replaced by a direct C API and/or a small
  serial protocol), file-based MIDI I/O (live MIDI input replaces it —
  finally retiring `events_from_live_midi`'s `NotImplementedError`, on
  hardware), dataset records, session catalogs (static).
- *Changes shape:* heap-averse fixed-capacity containers in place of
  evidence lists; error codes/optionals in place of exceptions
  (error-don't-guess survives as a calling convention); and the analyses
  must be the **online/incremental forms — gap 5 and the embedded profile
  are the same API work** (whole-sequence batch calls don't fit a device
  loop anyway).
- Rough size: a 3–5k-LOC subset of the core+atoms+induction. Scoping
  continues when A4 scheduling starts; the conformance harness applies to
  whatever subset ships (subset goldens = subset spec).

## Standing review — theory grounding (scheduled 2026-06-12)

A recurring capability review against the **broader principles of music
theory and real-world musical practice**, to surface embedded assumptions
before they undercut the engine's utility outside the cases we built
against. The swing gap is the type specimen: the rhythmic atoms shipped
straight-grid-first, and only a direct question exposed that swung material
read as `subdivision` noise. Each review walks the shipped capability
surface (INTEGRATION.md's table is the checklist) and asks, per capability:

- What idiom/notation/practice does this silently assume (classical/notated,
  straight-grid, quantized, equal-tempered, Western-functional)?
- What common real-world material would it misread rather than refuse?
  (Misreading is worse than erroring — the contracts promise
  error-don't-guess.)
- Is the assumption *documented as definitional*, *priced as a versioned
  prior*, or *invisible* — only the last is a finding.

Findings become recorded gaps or accepted-limitation entries (the Phase 6
12-TET-collision pattern), never silent. **Cadence:** once before the Phase
4.6 DSL v1 ships (the DSL freezes atom semantics — assumptions baked into
the vocabulary get expensive after that), then at each phase boundary.
Candidate first-pass agenda, from known territory: performance timing vs
symbolic data (swing was one case; rubato, humanization, groove templates
are siblings) · literal vs harmonic segmentation (NHT-blind) · key induction
profile bias (KK profiles are classical-corpus priors; jazz/modal/folk
material may rank oddly — Temperley/Aarden variants already invited by A5) ·
modal vs functional harmony assumptions in `theory/functions.py` · the
melodic step/skip/leap mapping's fit for non-Western melody · meter
inference absent (we trust the file's time signature) — *promoted to
gap 11 (2026-06-12), the review's first graduate; groove extract/apply
(gap 10) was recorded the same day from the same conversation.*

**Pass #1 — run 2026-06-12 (before the 4.6 DSL, as scheduled).** Walked
the INTEGRATION.md capability table against the three questions. Findings
and disposals:

1. **Grid-exactness assumption on performed input** — *invisible →
   misreads; the headline.* Segmentation, rhythmic placement, and voice
   motion all treat onsets as exact: verified that ~5 ms humanization
   turns two chords into ten micro-segments (with garbage transitional
   sets the A1 pipeline would name) and an on-the-beat melody into
   all-`subdivision`. → **gap 12** (tolerance layer); interim consumer
   guidance added to INTEGRATION.md contracts.
2. **Global-key naming in a modulating file** — *invisible → misread.*
   `midi_file_analysis` computes key regions yet names every segment
   under the one global key. → **gap 13** (per-region context).
3. **Key-induction candidate space is the profile modes — today
   major/minor only.** Modal centers (a dorian vamp) rank as relative
   major/minor — a misattribution, not an error. Extension is nearly
   data-only: add modal rows to `key_profiles.json` and entries to
   `candidate_context`'s mode→scale map. → *accepted limitation,
   documented in `key_induction.py` + INTEGRATION.md; modal profiles
   join the standing Temperley/Aarden invitation.*
4. **Functional vocabulary exists only for major/minor keys**
   (`TEMPLATES_MAJOR/MINOR`; `load_function_mappings` errors on other
   modes; naming's `functional_fit` silently doesn't fire for modal
   keys). Honest *absence*, not a misread — the engine doesn't claim
   T/PD/D roles it can't ground. → *accepted limitation; modal function
   templates are future vocabulary (the `TAG_MODAL` seeds in
   `theory/functions.py` are the start), demand-driven.*
5. **NHT typing is onset-based** — a held note is judged in the span
   containing its onset only, so the *tied suspension* (the most common
   suspension!) is invisible: the sustained portion reads chord-tone
   even where the harmony has moved under it. → *consequence documented
   in `melodic.py`; tie-aware typing recorded there as the refinement.*
6. Confirmed already-priced: swing/groove (gaps 10/11), KK profile bias
   (versioned + variants invited), step/skip/leap and felt-beat mappings
   (definitional, documented), literal segmentation (documented
   baseline), 12-TET footprint (Phase 6). One verified non-finding:
   uniform articulation cannot bias key induction — Pearson correlation
   is scale-invariant, so staccato vs legato encoding washes out.

Next pass: at the next phase boundary (post-DSL v1).

## Standing review — operational maturity (external audit 2026-07-07)

An independent agent audited the GitHub repo: **internals ~8/10, release/ops
~3/10** — "internally mature, operationally early." Confirmed findings and
their disposition:
- **No CI** (the biggest gap). FIXED: `.github/workflows/ci.yml` runs
  `pytest tests/` + `pytest audit/checks/` on every PR + main, matrix py3.10 /
  3.13 — the "808 green" is now enforced, not aspirational.
- **Port pin failing on a fresh clone.** The audit led with "forgotten re-pin";
  verification showed the deeper cause — the fingerprint hashed the set-class
  table's **float** fields (DFT magnitudes/phases, the chirality family, and
  reflection_residual, a golden-section minimizer) at full precision via exact
  sha256, so it was platform-specific (green on the machine that generated it,
  red on Linux/CI). FIXED: the fingerprint now hashes **only the exactly-
  reproducible integer/combinatorial fields** — pure bit/integer arithmetic,
  bit-identical everywhere. (A first attempt rounding floats to 1e-10 *still*
  drifted macOS↔Linux in CI — exact-hashing transcendental/iterative floats is
  inherently machine-specific, no rounding is robust; those fields are tolerance-
  compared by the conformance harness + the port's parity harness instead.) Pin
  regenerated; notice to tonality-core. A plain re-pin would have made CI *flap*.
- **Python-floor untested.** CI's 3.10 leg revealed `test_packaging.py` imports
  `tomllib` (stdlib only ≥3.11) — the `requires-python >=3.10` claim had never
  actually run. FIXED: that module skips on 3.10 (the rest of the suite still
  validates the floor); 3.11+ covers the packaging assertions.
- **README tool count stale** (46 → 52). FIXED: reworded to "50+ tools"
  (drift-resistant). The README already frames the Push CLI as legacy and
  features the MCP endpoint, contrary to the audit's read — no other drift. The
  "17 tools" reference is a *dated* delivered-note (accurate for 2026-06-10),
  legitimately frozen, not live drift.
- **No LICENSE** — the one hole NOT patched here: it is a product/legal decision
  (RE-1; the intended BY-NC-SA boundary), Julian's to make. Flagged, not
  assumed. It hard-blocks outside adoption until resolved, but nothing internal.

## Standing review — rigor & efficiency (pass #1 run 2026-07-02)

The theory-grounding review asks *what the engine silently assumes about
music*; this sibling review asks *whether the code does what the recorded
contracts say, and does it without waste*. Pass #1 was a structured walk of
every layer (five parallel deep reads: `core/`, `analysis/`, `temporal/`,
`rules/`+`representation/`+`context/`, `mcp/`+`io/`+infra), each asking three
questions per module: is the output **correct** (rigor), is the work
**necessary** (efficiency), and does the implementation still match the
doctrine this file records (paradigm). Findings marked *(verified)* were
confirmed by executing the code; the rest are code-read findings with
file:line evidence (the full report lives in the review conversation; what
follows is the durable record). Findings are grouped into six named
workstreams so they can be scheduled and checked off independently.

- [x] **RE-1 — Packaging: the library only works from a checkout.** The
      most foundational gap for a "foundation library": `io/loaders.py`
      computes `DATA_DIR` as `parents[2]` of the module (the repo root), and
      `pyproject.toml` packages only `mts*` with no package-data — so an
      *installed* copy raises `FileNotFoundError` on every catalog load,
      which every MCP tool depends on. (This is also why every script
      carries a `sys.path` hack, and the cause of the stale-venv workaround.)
      Fix: move `data/` inside the package (or `importlib.resources`) +
      declare package data. Same PR sweeps the metadata rot: the **MIT
      classifier with no LICENSE file in the repo** (a live hazard given how
      load-bearing the BY-NC-SA boundary is), the `example.com` homepage,
      the stale description, missing console entry points for
      `mts.mcp`/`mts.mcp.bridge`, and `.coverage` joining `.gitignore`.
      *(Delivered 2026-07-03 except the license file:* `data/` → `mts/data/`
      with `DATA_DIR = parents[1]` + declared package-data, pinned by
      `tests/test_packaging.py` — including an installed-copy simulation
      (package tree alone, no repo root) that loads catalogs and runs an MCP
      tool; description/homepage/authors fixed; `tonality-mcp` +
      `tonality-bridge` console scripts declared; `.coverage` gitignored.
      **The one open leg: the repo license is Julian's decision** — the false
      MIT classifier is *removed* rather than replaced, and the classifier +
      LICENSE file should land together once he picks. The `sys.path` script
      hacks and the stale-venv workaround become removable once the venv gets
      an editable install of the now-correctly-packaged library — small
      follow-on, needs a permission-gated `pip install -e`.)*
- [x] **RE-2 — Wrong-output bugs (all verified by execution).** These emit
      incorrect enrichment to A1/A6 today: **(a)** deceptive cadences are
      undetectable in minor (`cadence.py` requires `relative_root == 9` +
      role `tonic`; minor's submediant is pc 8 / `predominant` — doubly
      blocked); **(b)** bVII→i in minor is labeled *authentic* with
      fabricated "leading-tone resolving to tonic" evidence — a direct
      evidence-honesty violation (it's a subtonic/backdoor shape); **(c)**
      figured bass is assigned by cardinality alone, never checking
      tertian-ness (C6 root position gets "7", add9 gets "7"/"6/5") — wrong
      figures instead of `None`; **(d)** `ChordIntervalSummary`
      span/interval fields are computed from absolute pcs, so the same
      identity shape reports different spans at different roots — invented
      register inside a documented pure-identity analysis (cardinal-rule
      violation); **(e)** `inverted_interval_class_histogram` is provably
      always identical to the normal histogram (the interval matrix is
      symmetric under negation mod 12) — a dead-equal result field; **(f)**
      `colour_content_descriptor` consumes its input iterable twice, so a
      generator argument silently yields an all-zero interval vector next to
      correct mask fields.
      *(Delivered 2026-07-03, all six, each with a regression test:*
      **(a)** deceptive keys on the mode's submediant *degree* (vi/9 major,
      VI/8 minor), not the arrival role; **(b)** authentic requires a true
      dominant degree (7 or 11) — the subtonic bVII emits no cadence event
      and the degree rulings are recorded in `cadence.py`'s docstring;
      **(c)** figures gated on tertian-ness (successive thirds from the
      root), shared by `analyze_chord` and `analyze_voicing` — non-tertian
      chords report `None`; **(d)** `interval_summary` computed root-relative
      (transposition-invariant; C-rooted values unchanged); **(e)** the
      dead-equal field removed from `ChordAnalysisResult` (golden regenerated
      — the only golden change); **(f)** input materialized once. Consumer
      notices filed: `integrations/audiology/notice-re2-chord-analysis-
      corrections.md` (figures/summary/removed field/colour input) and
      `integrations/terrane/notice-re2-cadence-corrections.md` (minor-mode
      cadences), the latter flagging "named subtonic cadence type?" as an
      open vocabulary door if TERRANE wants it.)*
- [x] **RE-3 — Silent-loss / silent-no-op fixes (the itemize-losses
      doctrine, applied).** **(a)** MIDI ingestion loses notes without
      report: a second `note_on` for the same `(channel, note)` overwrites
      the open note; dangling note-ons at end-of-track vanish; a
      sub-half-tick note round-trips to note_off-before-note_on and is
      dropped on re-read — `coalesce` itemizes every drop, MIDI reads must
      too. **(b)** `apply_groove`'s `voice` parameter is accepted,
      documented, and completely ignored (and the MCP tool passes it
      through). **(c)** `key_inertia` silently discards
      `disambiguate_relative` when both flags are set (inertia re-decodes
      from raw score vectors), and region `mean_score`/`mean_margin` average
      raw-argmax stats even when inertia/smoothing changed the region's
      label — the advertised gating signal can describe the *wrong key*.
      **(d)** Rules: `description` escapes strict total validation (`null`
      passes and round-trips as the string `"None"`);
      `hard_rules_hold=True` when zero hard rules were applicable ("held"
      conflated with "never tested"); induction's merge pass compares a raw
      p-value against the FDR q-threshold (more lenient than the singleton
      test). **(e)** Input-policy inconsistencies across core: `Pitch` is
      the one unvalidated primitive (contradictory `midi`/`pc`/`octave`
      constructs fine); `parse_pitch_token` accepts `"-3"` as pc 9;
      `Scale.from_degrees`/`Quality` mod-12 *before* validating (silent
      wrap) where `mask_from_pcs` raises; `mask_from_text` guesses
      binary-vs-decimal (`"10"` → mask 2). **(f)** `rotational_steps`
      returns a `(12,)` sentinel for asymmetric sets that leaks into results
      as a false symmetry claim; the empty-set convention disagrees between
      core and analysis. **(g)** Smaller kin, same shape: `Event.sounds_at`
      epsilon asymmetry (a barely-legal event sounds nowhere), voice-motion
      classifying motion across rests unmarked, `changes_per_bar` counting
      segments not changes, session persistence swallowing corrupt entries,
      `load_function_mappings` dropping `role_subtype`, the
      `include_nondiatic` API typo, and `structural_key.py`'s module
      docstring still stating the *pre*-brief-11 discriminator.
      *(Delivered 2026-07-04, all of a–g, each with regression tests:*
      **(a)** `read_midi_file → MidiReadResult` itemizes every loss
      (re-struck notes now KEPT, closed at the re-strike + reported;
      dangling/zero-length dropped + reported); `midi_file_analysis` +
      `piano_roll_view` carry an always-present `midi_read_losses` key.
      **(b)** `apply_groove` honors `voice` (other parts pass through;
      scope cited on the result). **(c)** `track_keys` raises on
      `key_inertia × disambiguate_relative` (the tie-break could never reach
      the inertia path — was silently discarded; MCP validates up front), and
      region `mean_score`/`mean_margin` are measured against the region's own
      label (raw-argmax regions unchanged; relabeled windows go honestly
      negative). **(d)** ruleset `description` validated (null no longer
      round-trips as `"None"`); `hard_rules_hold` is `None` when no hard rule
      was applicable; the merge pass requires the merged p ≤ the weakest
      member's p. **(e)** one input policy: `Pitch` validates its
      three-encodings-of-one-value fields; `parse_pitch_token` rejects
      negatives; `Scale.from_degrees`/`Quality.from_intervals` validate
      before mod-12; `mask_from_text` never guesses binary-vs-decimal and
      never truncates. **(f)** `rotational_steps` drops the `(12,)` sentinel
      (empty = asymmetric); analysis empty-set special cases removed — core's
      convention (trivially invariant, matching export row 0) applies.
      **(g)** `sounds_at` epsilon is onset-inclusion tolerance only (interior
      no longer dead); voice motion across a rest marked per voice
      (`a/b_rested_between`); `changes_per_bar` counts boundaries;
      `SessionCatalog.load` returns an itemized `SessionLoadReport`;
      `FunctionMapping.role_subtype` carried through; `include_nondiatonic`
      typo fixed (Python API rename, no alias); `structural_key.py` docstring
      states the brief-11 discriminator. Consumer notice:
      `integrations/audiology/notice-re3-silent-loss-fixes.md`.)*
- [x] **RE-4 — MCP surface unification (Phase 4 hygiene, coordinated).**
      **(a)** Four incompatible positional event conventions live on the
      tool surface (index 3 = string voice in `structural_keys` — whose
      declared schema says `list[list[float]]` — but velocity in the meter
      tools, voice again in `_flex_events` consumers, velocity-with-voice-
      at-4 in the groove tools; `key_tracking` hard-rejects 4-element events
      entirely). Rule one canonical event form for *all* temporal tools;
      additive migration with consumer notices, per the CBMS-flip pattern.
      **(b)** `midi_file_analysis` and `piano_roll_view` are multi-step
      pipelines whose result shapes exist only as hand-built dicts in the
      MCP layer — intelligence above the line, against Decision 5 and the
      typed-results convention; consequently they are the only two tools
      with no conformance golden. Move the pipelines into
      `analysis/`/`dataset/` as typed entry points; tools become one-liners;
      goldens follow (closes the 44-of-46 ratchet gap — and note the tool
      count is 46, not the 43 stale docs cite). **(c)** Five tools serialize
      via `dataclasses.asdict` because their results lack `to_dict()`
      (`parse_chord`, `voicing_suggestions`, `quality_comparison`,
      `quality_brief`, `set_class_info`) — shapes drift by construction, and
      `export.py` re-implements `set_class_info`'s shape with nothing
      enforcing the mirror. **(d)** `midi_file_analysis`/`piano_roll_view`
      swallow *every* `ValueError` as "no tonal/metric information" — the
      engine needs a typed insufficient-information exception so real input
      errors stop being conflated with honest absence. **(e)** Bridge
      hardening: `Access-Control-Allow-Origin: *` + preflight means any web
      page can invoke path-taking tools on loopback — token or origin
      allowlist (A6 coordinates); and engine `TypeError`s are misreported as
      HTTP 400 client errors.
      *(Delivered 2026-07-06, a–e (CORS mechanism pending A6's design call):*
      **(a)** one `_canonical_events` parser — `[onset, duration, midi,
      velocity?, voice?]` — on all twelve temporal tools; legacy string-at-3
      voice and numeric-at-3 velocity forms still read (JSON types
      disambiguate; the contradictory combination raises); `key_tracking` and
      melodic/rhythmic/swing no longer hard-reject >3-element events; the
      lying `list[list[float]]` annotations fixed. **(b)** the two pipelines
      live below the line as typed entry points (`dataset/pipelines.py`:
      `analyze_midi_file` → `MidiFileAnalysis`, `piano_roll_view_from_file` →
      `PianoRollView`); the tools are one-liners; **conformance goldens added
      via a committed fixture MIDI + `$FIXTURES` placeholder** (machine-
      independent; the stale path-embedding exclusion reason was verified
      false) — the ratchet now covers **54 cases / all 46 tools, zero
      exclusions**; INTEGRATION.md's stale 43 corrected. **(c)** the five
      `asdict` results gained `to_dict()`; the set_class_info/table mirror is
      now an enforced test. **(d)** `InsufficientInformation(ValueError)` at
      the four honest-absence sites; the pipelines catch only it — real input
      errors propagate. **(e)** bridge binds kwargs before invoking (binding
      `TypeError` → 400, engine `TypeError` → 500); the CORS mechanism landed
      2026-07-06 per A6's answer (`ack-re4-and-cors-answer.md`): **origin
      allowlist** — loopback web origins (any port) + no-Origin callers by
      default, foreign origins actively 403'd (not merely denied the header —
      a disallowed page must not execute tools), `--allow-origin` for
      packaged-app schemes (their flagged Tauri/Electron future),
      `--open-cors` the explicit wildcard. Consumer notice:
      `notice-re4-mcp-unification.md`.)*
- [x] **RE-5 — Hot-path efficiency pass (mechanical,
      conformance-protected).** All output-identical by construction, so
      the golden harness is the reviewer: **(a)** `rotate_mask` /
      `invert_mask` are 12-iteration Python loops and the hottest primitives
      in the library (per-root in compatibility/containment, per-tone in
      `interpret_chord`, ×24 in `prime_form_mask`) — the branchless form is
      three int ops; **(b)** `load_function_mappings` is the *only* uncached
      loader and regenerates the full functional table inside per-candidate
      loops (measured ≈2.1 ms per `recommend_next_chord`, mostly redundant;
      `summaries.py` already wraps it in a private lru_cache — the fix
      belongs in the loader, mtime-keyed like the other twelve); **(c)**
      `interpret_chord` rebuilds its catalog mask-index every call, on the
      per-segment path from temporal segmentation — cache it on the catalog;
      **(d)** quadratic temporal scans (segmentation's per-boundary
      `sounding_at`, voice-motion's per-moment-pair position recompute,
      `track_keys`/`track_meter` re-scanning and re-sorting all events per
      window) all become single sweeps over the already-sorted events;
      **(e)** the pair-keyed `pcset_math` caches are sized 4096 over a
      mask-*pair* key space (`voice_leading` already uses 16384); **(f)**
      lesser: `parse_ruleset` parses every rule twice and MCP re-validates
      per call, `versioned_data_bundle` parses every asset twice, the twelve
      near-identical ~40-line loader blocks collapse into one generic
      mtime-keyed helper. Side benefit: simpler table-driven code is exactly
      what ports cleanly in Phase 8.
- [x] **RE-6 — Doctrine-drift cleanup (the GUI-era residue). DELIVERED**
      (a→e across #142–#146; RE-6b closes the review). **(a)**
      `layouts/push_grid.py` is an in-library ANSI renderer (escape tables,
      `isatty()` color policy, spelled labels, no spec level) — the exact
      thing Phase 5 was created to replace; the grid *descriptor* moves to
      `representation/`, the painting to the CLI edge (`cli/push.py` stays
      the example consumer, per Demoted). `layouts/piano.py` is a dead
      placeholder referencing the removed GUI — delete. **(b)**
      `analysis/builders.py` still holds the forbidden module-level mutable
      registry (`_DEFAULT_SESSION` + `SESSION_*` aliases, with import-time
      disk I/O under a bare `except`): sessionless catalog loads merge it,
      so in-process registration leaks into every MCP call of a long-lived
      server — the one consumer where isolation matters most. It also
      creates the `io ↔ analysis` import cycle that forces ~15 lazy imports
      across nine analysis modules; moving `SessionCatalog` below `io/`
      untangles both. **(c)** `workspace.py` keeps listener/notification
      plumbing, "GUI layers" framing, wrong return annotations, and a stale
      TODO claiming MIDI ingestion is unimplemented. **(d)** API
      consistency: `.pcs` is a method on `Scale`, a field on `Chord`, a
      property on `Realization` (naming.py carries a literal `callable()`
      probe to cope); the symmetry/chirality family is split across three
      modules with achirality computed two independent ways; rank starts at
      0 in naming but 1 in succession; frozen result dataclasses carry
      mutable list fields in `temporal/` where `StructuralKeyResult`
      correctly uses tuples. **(e)** Dead code with teeth:
      `chord_degree_labels` (unused *and* semantically wrong — returns
      spelled names from core and mis-handles absolute-pc scales),
      `Chord.spelled`, `transpose_pcs`, `Event.tags`, unreachable
      enharmonics branches, plus stale docstrings ("Analysis toolkit
      *stubs*… future *GUI* integrations") and forward-looking TODO blocks
      that violate this file's own link-the-ROADMAP rule.

**Calibration — verified solid, on record so it isn't relitigated:** layer
hygiene is clean everywhere checked (no upward imports; analysis never
reaches temporal/mcp/representation at runtime); the cardinal rule is
honored in the register-dependent paths (`analyze_voicing`,
`voice_leading_realized` raise on identity-only input); the
lru-cache-over-4096-masks pattern *is* the precomputed set-class table done
right, and the Rahn prime-form-as-min-mask argument checks out; the VL
non-crossing pairing matches the cited Tymoczko construction and is
brute-force validated; the key-tracking priors contract holds (raw
per-window evidence preserved; priors opt-in, versioned, cited) apart from
the RE-3(c) interaction; the golden conformance harness and the mtime-keyed
loader caching are well built.

**Sequencing decision (2026-07-02):** (1) **RE-1** first — it blocks
everything downstream of "library" and is a small diff; (2) **RE-2 + RE-3**
next — wrong output and silent loss reach consumers today, and each item is
a small, well-fenced, golden-policed fix; (3) **RE-4** as one coordinated
additive change with consumer notices (the event-format rule is the
breaking-risk item, so it gets the CBMS-style migration treatment); (4)
**RE-5** as a mechanical pass once RE-4's typed pipelines exist (so the new
entry points are measured, not the old dict assemblies); (5) **RE-6**
last — highest churn, zero consumer-visible behavior. Intended output
changes regenerate goldens in the same PR, per the harness contract.
Cadence: re-run alongside the theory-grounding review at each phase
boundary; the two reviews are complementary instruments (assumptions vs
contracts) and should stay separate passes.

## Horizon — speculative & ecosystem ideas

> The home for **not-yet-committed** ideas — cross-project visions, "wouldn't it be
> cool", things without an owning client yet. **This is not committed direction**
> (that lives in the phases / gaps / target-applications above); entries here are
> recorded so they aren't lost and so any agent can find them, *not* scheduled.
> **Graduation:** when an idea earns a plan it moves *up* into a phase/gap/target-
> application and leaves a pointer here. **Escalation:** if this bucket becomes a
> genuine multi-project planning space (several projects co-owning roadmaps), spin
> out a dedicated ecosystem repo; a single idea recorded from Tonality's vantage
> fits here.

- **H1 — Performance → analysis → personal style → pedagogy (the ecosystem-pull
  build)** *(Julian, 2026-07-08; no owning client yet — likely surfaced through the
  Audiology-as-education-platform effort).* A person performs in their own style;
  the performance becomes MIDI; Tonality analyzes it for **feedback on all aspects
  of performance** and **stylistic analysis**, and — over a corpus of their
  playing — **derives their personal style** as a ruleset/profile. Wont is tagged
  in so the style is both **learned and analyzed**; lesson plans are built (tagging
  in **Portolan**, a curriculum/pathway project); it all surfaces in Audiology
  extended into an **education platform**. Possibly one build that pulls the whole
  ecosystem together, or several that do it different ways (per instrument/pedagogy
  over one Tonality spine).

  *Tonality's vantage — what's already shipped vs. genuinely new:*
  - **performance → MIDI (audio transcription): OUT of scope.** Signal → symbolic
    is not the 12-TET symbolic engine's domain — it's a front-end adapter / separate
    tool. Tonality **consumes** MIDI; it does not transcribe audio. (The one clearly-
    new front-end component.)
  - **MIDI → feedback on all aspects: largely SHIPPED.** The enrichment engine
    (`midi_file_analysis` + melodic / rhythmic / harmonic / key-tracking / groove /
    cadence analysis). "Performance feedback" is mostly a *presentation* framing over
    existing analysis, not new engine.
  - **derive a personal style: SHIPPED this session (the spine).** The corpus →
    style-profile pipeline (`segment_chords` → `induce_ruleset` ‖
    `build_transition_matrix` → `build_style_profile`) pointed at *a person's
    performance corpus* instead of a genre corpus — "perform in your own style →
    derive a `StyleProfile`" is the personal-case instance of the closed loop
    (`integrations/wont/notice-markov-alignment.md` §6).
  - **style learned AND analyzed: the Wont closed loop** (A10) — Wont personalizes;
    the `StyleProfile` is inspectable. Already aligned.
  - **lesson plans: a separate curriculum project (Portolan)** — consumes the
    learner's profile + the gap to a target style. Not Tonality-owned; Tonality
    supplies the analysis + the style-gap signal.
  - **Audiology-as-education-platform: the UI/front-end** (A6, extending into
    education) — the surface that renders feedback, style, and lesson plans.

  *The one genuinely-new Tonality capability it would pull for (candidate, if it
  advances):* a **style-gap / profile-diff** analysis —
  `compare_style_profiles(learner, target)` → per-dimension divergence: which rules
  the learner follows/breaks vs. the target (`compare_rulesets`), the transition-
  distribution divergence (`compare_transition_matrices`, already recorded for
  wont), and the held-out cross-entropy gap (`cross_entropy`). **This is the core
  pedagogical signal** — "how far from the target style, on which dimensions, what
  to practice" — and it unifies three already-recorded pieces into one learner-vs-
  target diff. Recorded here; not built speculatively (it graduates when a consumer —
  Audiology-education or Portolan — needs it).

  *Net:* this is an **integration vision, not a single build**, and Tonality is
  mostly *ready* for its half — the spine shipped this session. The new work is the
  audio→MIDI front-end (not ours), the Portolan curriculum layer (another project),
  and the `compare_style_profiles` style-gap (a candidate gap when a consumer pulls it).

- **H2 — Client-linking middleware** *(Julian asked 2026-07-08; **tabled as a future
  possibility**, not now).* Considered whether to develop middleware between the
  engine and its clients. **Ruling: no central middleware / gateway.** The linking
  roles are already filled — transport+contract by the three transports, coordination
  by the `integrations/` protocol, stability by the golden/port-pin/versioned priors,
  and per-client adaptation by **one boundary module per project** (rule 1,
  deliberately *distributed* — a shared adapter is where forks + god-objects breed,
  and a running gateway would re-implement the loopback bridge while reintroducing the
  operational surface the local-first design avoids). **The one piece worth building,
  on a trigger:** a thin, opt-in, **per-language client SDK** (a *library*, not a
  service) packaging the repeated boundary mechanics — transport selection, canonical
  (de)serialization, the degrade-visibly "which source answered" badge, typed result
  shells — without centralizing client-specific logic. Gate on the **rule of three**
  (2–3 same-language clients re-writing the same seam); the **strongest single case is
  a typed TS/JS bridge client**, since Audiology-into-an-education-platform means more
  web clients (types generatable from the golden/manifest source). Distinct from the
  ecosystem **conductor** that would orchestrate the closed personalization loop (H1)
  — that composes clients, is its own project, and is not "Tonality middleware."
  **Triggers to watch:** (1) a second same-language client duplicating the boundary →
  extract that language's SDK (TS first); (2) the closed loop gets a real consumer →
  a separate conductor.

## Demoted / deferred (built for the old "app" frame)

- `gui/` (Qt) and the audio backend — not on the library/MCP path. Don't delete;
  don't let them shape core architecture.
- `cli/push.py` — keep as an **example consumer**, not a foundation component.

## Parked work (branches)

- ~~**`wip-context-cli-rewiring`**~~ — **RETIRED (Phase 3 Slice 3).** Its intent (the
  four CLI scripts on `DisplayContext`) was **re-done on current `main`** rather
  than merged — the branch was ~30 commits behind, collided with the typed-results
  rewrite, and crashed in `run_specific` (the `context` shadowing bug, now fixed by
  the `session_context` rename). Branch deleted; recoverable from commit `c06270a`
  if ever needed.

## Open questions

- MIDI ingestion dependency: Mido vs. in-house SMF parser?
- ~~Dataset record granularity: per-event, per-segment, or per-progression?~~
  **Resolved (Phase 3 Slice 4):** flat leaf record per object/event/segment, grouped
  by a `Dataset` container; recursion deferred to a future parent/child musical layer
  (see Slice 4 "reflection point").
- Does the temporal layer need tempo/meter awareness in Phase 2, or defer to 2.5?

## References & prior art

- **Ian Ring, "A Study of Scales"** — <https://ianring.com/musictheory/scales/>
  (example entry: <https://ianring.com/musictheory/scales/3055>). An encyclopedic
  catalog of all 4096 twelve-tone pitch-class sets, **each keyed by a number that
  is exactly the 12-bit identity bitmask Tonality uses** (a PC set ↔ an integer
  0–4095). This is the canonical model for two of our workstreams:
  - **Representation suite (Phase 5):** mirror its representations — bracelet /
    necklace diagram (with symmetry axes), Tonnetz, interval vector, prime &
    normal form, Forte class, modes, complement / inverse, rotational & reflective
    symmetry, ridge tones, maximal evenness, Rothenberg propriety, Myhill's
    property, Lewin–Quinn DFT (FC) components, brightness / center of gravity,
    coherence, and the per-set "nearby scales" relational map.
  - **Naming & equivalence (Phase 1.5):** a cross-reference for alternate naming
    traditions (Zeitler, Messiaen modes of limited transposition, dozenal, etc.)
    and for prime-form / inverse equivalence.
  - **Scope caveat:** Ring catalogs *scales / PC-sets* (and the triads embedded in
    each), not chord *voicings* or *realizations* — Tonality's register/voicing
    layer is complementary, not duplicative.
  - **Possible interop:** expose a cross-reference between our `mask` and a Ring
    scale number (mind the bit-order convention) so entries can be linked directly.
