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
  surfaces are ready render targets).
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
  (needs A6's windowed-track dump — not vendored) before any default flip. The
  scoping decisions that informed the build: DP (global, batch) — the causal/online
  form joins gap 5; flat penalty not distance-weighted (distance-weighting makes
  parallel flips *cheap*, the wrong direction). **Mandate recorded (brief-13):**
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
   vocabulary's coverage — the minor templates' missing bare-major-V-triad
   is pinned as inherited behavior (flagged for a `theory/functions.py`
   fix). MCP: `cadences` (#35). Feeds gap 14's cadential candidates.
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
   `ValueError`s surface as 400s with their actionable messages; CORS open
   because the boundary is loopback, not origin. The tool signatures and
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
    signal) raises. **Deferred follow-ons:** change-point detection / local meter
    (the windowed form, as local key tracking was to `infer_key`); anacrusis/
    phase estimation; agogic (duration) weighting; opt-in wiring into
    `midi_file_analysis`; the online form (gap 5).
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
    `idiom=*` labels); **VL-neighbour candidate generation** (chords reachable by
    smooth voice-leading outside the functional vocabulary — unlocks chromatic
    mediants as candidates); register-aware ranking.
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
10. **C++ is the engine's eventual home — port once, bind back.** (Decided
    2026-06-12 with Julian.) When the 12-TET conception is established, the
    engine migrates to a C++ core with Python bindings (pybind11-class) —
    **not** a second parallel implementation (two implementations drift;
    a fork is the failure mode). Motivations on record: A4's plugin/device
    frame cannot ship a CPython runtime (the one consumer the Python engine
    structurally cannot serve in-process); an embedded profile (below)
    needs it; a C++ core compiles to WASM nearly for free, incidentally
    reopening the declined browser-door commitment as a side effect rather
    than a promise. Sequencing fence: port **after** the 12-TET surface is
    frozen — Phase 6 renegotiates "the mask is the key", so porting before
    it means porting the substrate twice. The migration's spec anchor is
    the **golden-file conformance harness** (delivered 2026-06-12,
    `tests/test_conformance.py` + `tests/golden/conformance.json`): one
    deterministic call per MCP tool, full-JSON comparison with float
    tolerances (rel 1e-9), language-neutral by construction — a C++ engine
    reproducing the goldens is conformant. The harness doubles today as
    regression armor: any output change fails it; intended changes
    regenerate goldens in the same PR, making output drift reviewable.
    Versioned priors and catalogs are JSON and ship to both
    implementations verbatim. See Phase 8.
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
- [ ] *(parked here 2026-06-10)* **Constraint search / "inverse analysis":**
      `search_identities(constraints)` / `search_voicings(identity, constraints)`
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
  - *chord-network / voice-leading graph* (added 2026-06-13 from Julian's
    reference — a "Cube Dance"-family chord mandala: major/minor/augmented/
    dominant-7 nodes with parsimonious voice-leading edges, augmented
    triads as connective hubs). **Delivered (2026-06-13):**
    `representation/chord_network.py` `chord_network_descriptor(chords,
    max_distance=)` — nodes (chord + pcs + rotational `symmetry_order`, the
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

### Phase 8 (future) — C++ core migration (Decision 10)
Port once, bind back: a single C++ core with Python bindings replaces the
Python implementation; every existing consumer keeps working through the
bindings. **Sequencing fence: after the 12-TET surface is frozen** (Phase 6
renegotiates the substrate — porting first means porting twice). Driver:
A4's plugin/device frame; side effects: WASM falls out nearly free.

- [x] **Step 0 — conformance harness** (delivered 2026-06-12, with the
      decision): `tests/test_conformance.py` + `tests/golden/conformance.json`
      — one deterministic call per MCP tool (24 cases; `midi_file_analysis`
      excluded for path-bearing provenance, its components covered by the
      event-based tools), full-JSON golden comparison with float tolerance
      (rel 1e-9 / abs 1e-12), plus a coverage ratchet (a new tool without a
      conformance case fails the suite). Doubles as regression armor today;
      intended output changes regenerate goldens in the same PR.
- [ ] **Versioned-data export (pullable forward — A native consumer can use
      it before the full port).** Stable-schema embeddable artifacts a
      non-Python consumer loads and pins by version: the priors (key
      profiles already JSON; naming weights; the `doubling.1` policy
      constant) plus a *generated* precomputed table for the algorithmic
      pieces (set-class prime forms / DFT magnitudes over the 4096 masks),
      so a consumer can choose data-load *or* documented-algorithm
      reimplementation. Requested by TERRANE brief-3 (its JUCE plugin), and
      the lowest-cost half of the consumer-port corollary (Decision 10) —
      this alone may suffice for a faithful native port, parity-checked
      against the conformance goldens. Independent of the sequencing fence
      (it exports current 12-TET data; no substrate commitment).
- [ ] Core identity layer (bitmask/set-class/symmetry/DFT) — `constexpr`
      tables over the 4096 universe; the cleanest layer, C++-native.
- [ ] Analysis layer (parsers, naming + evidence, induction, VL, containment)
      — the bulk; the ~35 typed results become hand-written or generated
      struct + JSON serialization (the single biggest line-item).
- [ ] Temporal layer (sequence, segmentation, tracking, atoms, swing).
- [ ] MIDI I/O (SMF lib or ~500-line hand-rolled reader/writer; mido retired).
- [ ] Python bindings (pybind11-class); the Python package becomes a shim.
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
