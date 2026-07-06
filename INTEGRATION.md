# Tonality — Integration Summary

> A capability schematic for **external projects** (synthesizers, MIDI/sound
> generators, visualizers, agents) preparing to plug into this engine. Current
> as of Phase 4 (2026-06). Plans referenced here live in
> [ROADMAP.md](ROADMAP.md) — the single source of truth for direction; this
> document describes **what exists** and links phases for what doesn't yet.

## What Tonality is

A local-first Python **music-theory engine** for 12-TET pitch material. It does
the *exact* pitch-class arithmetic that humans and LLMs get wrong: set-class
identity, exhaustive chord naming, symmetry, key induction, voice-leading
distance — and turns MIDI or symbolic notation into **enriched, reproducible
datasets**. It is a foundation **library with an MCP endpoint**, not an app:
your project keeps its UI, audio, scheduling, and rendering; Tonality supplies
the harmonic brain.

**Division of labor (the design law):** precise combinatorics live in the
engine; fuzzy/semantic/creative judgment lives in the caller. Corollary
(*"reduce, never invent"*): the engine never fabricates what you didn't give
it — no register without real notes, no key without evidence. Analyses that
need missing information **error, they don't guess**.

## The data model in 30 seconds

- **Identity key** — a pitch-class set as a 12-bit bitmask (mod-12, octaveless).
  What you match, name, and catalog on.
- **Realization** — actual pitches (octaves, doublings, bass). Optional, and
  required for register-aware analysis (voicing, inversion, bass-driven
  disambiguation).
- **Time** — `Event` (onset/duration in beats + pitch) → `Sequence` (+ tempo
  & meter maps). Windows reduce to realizations reduce to identity keys.

Integration rule of thumb: **send the richest form you have.** MIDI numbers
beat pitch classes beat names; events with durations beat bare note lists —
each level unlocks more analysis.

## Capabilities (today, shipped and tested)

| Capability | What you get |
|---|---|
| **Multi-notation parsing** | `"C3[0,4,7]"`, `"(1,b3,5)"`, `"[C,E,G]"`, `"{60,64,67}"`, `"C:min7"` → one structured spec |
| **Chord / scale analysis** | intervals, interval vector, symmetry axes, inversions + figured bass, Tonnetz coordinates, modes |
| **Set-class identity** | normal order, Rahn prime form, Z-partners, **DFT magnitudes** (a 6-D "harmonic color" embedding: \|f₅\|≈diatonicity, \|f₆\|≈whole-tone-ness) — plus, via `set_class_info` (A6 brief-15): **DFT phases** `arg(f₁..f₆)` (Tn-variant + inversion-negating — the hue/handedness the magnitudes discard) and a **chirality family**: **`trichord_chirality`** (step-gap, exact 3-note: major −2 / minor +2 / achiral 0 / null past 3 notes), **`general_chirality`** = `Im(f₁·f₂·conj(f₃))` (bispectrum slice; any cardinality; smooth magnitude but false-zeros on a few exotic classes; **separates dom7 ↔ m7♭5**), **`chirality_sign`** ∈ {−1,0,+1} (the **complete** discrete handedness, **0 iff achiral**; bispectrum slices + one `Im(f₁³·conj(f₃))` trispectrum fallback), and **`chirality`** — the **complete *continuous*** signed scalar (A6 brief-16) = `chirality_sign · √R`, `R` = best-fit reflection-axis residual `min_θ Σ|f_k|²·sin²(φ_k+kθ)`: 0 iff achiral, inversion-odd, major<0/minor>0, `dom7 = −m7♭5`, with a real magnitude (`|chirality| = √R` orders sets by how chiral). All four verified exhaustively. \|f₅\| consonance = `dft_magnitudes[4]`; prime-form + 12-bit `mask` returned |
| **Exhaustive naming** | every valid (root, quality) reading of a pc set — symmetric/ambiguous sets yield several (C6 = Am7; dim7 names at 4 roots) |
| **Key induction** | ranked key candidates with scores + top-two margin from **any non-negative pc-weight 12-vector** (summed durations, exponentially-decaying histograms, velocity-weighted counts — your weighting policy, our ranking) |
| **Local key tracking** | windowed key induction over a sequence → **key regions** (beats + seconds extents, per-region mean score/margin, per-window evidence) — modulation-aware splitting and renderable overlays; window geometry caller-set and cited. Raw every-blip output by default; opt-in `smoothing=true` (`track_keys`/`key_tracking`, and `smooth_key_regions` on `midi_file_analysis`/`piano_roll_view`) applies **versioned hysteresis** (`key-smoothing.1`, cited via `smoothing_version`): a region shorter than `min_region_windows` with `mean_margin` below `min_region_margin` is absorbed into its stronger neighbour, while a confident brief modulation survives (margin override). Windows keep their raw argmax as evidence — only the grouping is smoothed. Opt-in `key_inertia=true` (on `track_keys`/`key_tracking`/`structural_keys`/`midi_file_analysis`) applies a **continuity prior** (A6 brief-13): a deterministic Viterbi over the per-window candidate scores with a flat `switch_penalty` (versioned `key-inertia.1`, cited via `inertia_version`) that rewards fit + penalizes switching, holding near-tie mode flips to their context and cutting over-segmentation; a sustained, well-fit modulation still wins (the penalty is paid once). It is a **`track_keys`-only** layer — `infer_key`'s single-vector global output is untouched (so the margin stability contract is unaffected). **Semantics (important):** `key_regions` is a **tonicization-sensitive local-fit** signal — each window reports the key its content best correlates with, so a V/V span reads as the dominant's key. This is **not** a *structural key-area* reduction (which would subsume tonicizations under the parent key); validating it frame-wise against human key-area annotations measures a category difference (Audiology brief-5). The tonicization-aware structural reduction is **`structural_keys`** (below) — use *it* for key-area comparison, the windowed track for tonicization-grain detail |
| **Structural key-areas** | `structural_keys` reduces the windowed local track to **structural key-areas** — the tonicization-vs-modulation distinction. A brief, **diatonically-related** excursion (a V/V span) is absorbed into its parent key as a `tonicization` (recorded with its scale `degree`); a sustained/structural change is kept as a modulation. The discriminator is **relatedness AND (brevity OR return)** — the functional context `smooth_key_regions` (confidence-gating) lacks, since a tonicization can be a *confident* window. Output: `areas` (each with its `tonicizations` + home key), carrying the underlying `tracking` + global key as evidence; the home key is the **most-prevalent local region** (not the averaging global induction). Thresholds are a versioned prior (`structural-key.1`, theory-set, cited). A derived reduction — never overrides. Slice 1 is whole-sequence; diatonic relatedness (chromatic tonicizations + local change-point deferred) |
| **Meter estimation** | infer the time signature from note content (`meter_estimation`) — ranked candidate signatures with scores + margin (Decision 7), each scored by **bar-period autocorrelation × metric-profile correlation** (distinguishes e.g. 3/4 from 6/8, which share a 3-beat bar). Templates are a **versioned prior** (`meter-grid.1`, cited); both sub-scores ride along as evidence. **Never overrides the file's meter** — `declared_numerator`/`declared_denominator` carry the file's claim and `agrees_with_declared` evidences against it (the `MeterMap` is untouched). Velocity (event index 3) weights the accent; raises on too few onsets / no metric information. Opt-in `phase_search=true` scores each candidate's profile at its best bar phase (off by default → the global phase-0 contract + golden are unchanged) — needed when the downbeat isn't at beat 0 — and **reports** that winning phase as `downbeat_offset_beats` (None when off; the tracker surfaces it per window + per region): geometric anacrusis estimation, not corpus-fit. **Local meter tracking** is the windowed form (`meter_tracking` / `track_meter`, as `key_tracking` is to `key_induction`): a window slides over the sequence, each ranked with the same prior + per-window phase search, consecutive same-meter windows merging into **meter regions** (beats+seconds extents, mean score/margin, per-window evidence); uninformative windows make no claim. Reachable on a real SMF via `midi_file_analysis(include_meter_regions=true)`, inferred independent of the file's declared `MeterMap` — compare them to catch a mis-tagged or changing meter. Raw per-window argmax, no smoothing in v1 (a 1-window transient at a change boundary is honest — gate on `window_count`/`mean_margin`) |
| **Relative-key tie-breaker** | additive refinement that disambiguates relative major/minor (`relative_key`) — the pair shares a diatonic collection, so KK correlation separates them weakly. Tonal-hierarchy signals (leading-tone = the minor's raised 7th, outside the shared collection; tonic-triad + tonic salience) choose between the pair, evidenced + versioned (`rel-key.1`). **`key_induction` is unchanged** (its scores/margin stay a pinned stability contract) and carried in the result as `induction`; `applied=false` when the top key and its relative partner aren't a near-tie (nothing to second-guess), `is_ambiguous` flags an honestly inconclusive break. Positive `tiebreak_score` favors minor. **Wired into the pipeline (opt-in, off by default):** `key_tracking`, `midi_file_analysis`, and `piano_roll_view` all take `disambiguate_relative[_keys]` to apply it per window/region (and to the global key context); cited on the tracking result, the global break surfaced under `key_disambiguation` |
| **Contextual disambiguation** | *the* chosen reading in a key, with ranked alternatives and per-signal evidence; flags aug-6ths, secondary dominants, Neapolitans; honest `is_ambiguous` |
| **Cadence detection** | cadential formulas in a named progression (`cadences`): authentic / plagal / deceptive / half, each an evidenced event with approach+arrival roman/role/degree, root motion, and per-signal evidence. Formulas (not phrase-confirmed) — `is_final` is the strongest signal; major/minor only (`mode_supported` flag) |
| **Next-chord recommendation** | ranked candidate next chords from a current chord in a key (`next_chord`), each **tagged** with succession context — functional (`dominant_resolution`, `descending_fifth`, `prolongation`, `retrogression`, `applied_dominant`, `borrowed`, + the cadential formula), voice-leading (`smooth`, `parsimonious` with P/L/R detail, `chromatic_mediant`, common-tone count), and a reported-but-unscored `color_shift` (DFT delta). Plural + evidenced (Decision 7); scoring weights are a **versioned prior** (`succession.1`, cited), and every candidate exposes raw axes (`vl_distance`, `common_tones`, `root_interval`, `color_shift`) so you can re-rank. `tag_transition` annotates a single transition (incl. out-of-vocabulary chords). Major/minor only; the per-style *historical/corpus* tags are a planned follow-on (ROADMAP gap 14) |
| **Voice-leading distance** | exact minimal motion between two chord identities + the optimal voice mapping; **register-aware form** for voiced chords (actual MIDI notes — octaves cost 12, doublings are voices) via `voice_leading_realized` |
| **Voice identity & pair motion** | `Event.voice` part labels (MIDI seeds one voice per track/channel as `t{n}c{n}`); `voice_motion` classifies every voice-pair transition — parallel / similar / contrary / oblique with mod-12 interval classes as evidence. Counterpoint predicates are one-line filters (parallel fifths = `parallel` + `interval_class 7`) |
| **Melodic atoms** | per-note approach/departure intervals with step/skip/leap classes, Parsons contour, ambitus (`analyze_melody`); **NHT typing** (passing, neighbor, appoggiatura, escape, suspension, anticipation, pedal) against caller-provided harmony spans — no harmony, no claim |
| **Rhythmic atoms** | per-note metric placement (downbeat / beat / offbeat / subdivision) against the felt beat (compound meters beat in threes), a precise **syncopation** predicate (weak onset sounding through the next stronger grid line), durations + inter-onset intervals (`analyze_rhythm`) |
| **Swing feel** | straight / swung / reversed / mixed from two-way beat divisions, with the division-fraction evidence and ratio (2/3 → 2:1 triplet swing, 0.75 → 3:1 shuffle); thresholds are a **versioned prior** (`swing-feel.1`, cited). Only reads swing encoded in the onsets — quantized-straight MIDI carries none (`analyze_swing`) |
| **Groove extract / apply** | `extract_groove` distils a **GrooveTemplate** from a played loop — per grid slot (at a caller-set base resolution), the signed onset offset (fraction of the grid unit) + velocity accent (deviation from the loop mean), cycled over the loop; quantized input → **null groove** (the swing honesty bound, generalized; polyphony shares a slot). `apply_groove` (generative) re-times a sequence toward a template with Live Groove Pool parameters — **Base / Quantize / Timing / Random / Velocity / Amount** — onsets shift, durations preserved, `Random` requires an explicit seed (reproducible jitter). Templates JSON-round-trip; the write-back loop closes via MIDI export |
| **Rulesets (DSL) + conformance evaluator** | declarative JSON rules over the atom vocabulary (voice motion / melody / rhythm): `where`-filtered `forbid`/`require`, hard or soft-weighted. Strict total validation (`validate_ruleset` returns *every* error — built for LLM-translated rulesets); `evaluate_ruleset` → per-rule violations with locations + atom evidence, conformance frequencies, hard/soft rollups. Rules the material can't ground come back `applicable: false` with the reason — never silently skipped |
| **Ruleset composition + comparison** | rulesets compose and compare as data: `combine_rulesets` (union, dedup identical, conflict on divergent same-id), `specialize_ruleset` (overlay overrides base + reports overridden/added — "style = base + overrides"), `compare_rulesets` (shared / conflicting / unique ids + directly-contradictory rule pairs). Deterministic, no evaluation |
| **Ruleset induction** | mine a corpus for the compositional rules it follows (`induce_rules`) — version-space mining, **not** learning. Apriori frequent-pattern mining over the `where`-lattice (closed itemsets, arity cap 3) + **Fisher's exact test** vs an independence-given-marginals null, **BH-FDR** at q=0.05, behind a piece-presence support floor; `leverage` sign picks `require` (positive association) vs `forbid` (negative — defusing the spurious-forbid pathology). Emits a **validated soft `Ruleset`** in the DSL (round-trips through `validate_ruleset`) + per-rule evidence (support, confidence, leverage, p/q). Exact integer/rational arithmetic, deterministic; weights are a versioned `scoring_prior` cited in the result; below ~30 pieces the result is flagged `exploratory`. A **disjunction merge pass** (default on, `merge_disjunctions`) collapses same-`where`/field single-value rules into one `in`-rule — `forbid interval_class in {0,7}` rather than two forbids (the human-readable form), re-tested with Fisher so rigor holds (the `merged` evidence flag marks them). Categorical/bool/low-card-int fields (slice 1) |
| **Performed-input tolerance** | opt-in coalescing of humanized timing before analysis (`coalesce_events`): clusters near-simultaneous onsets *and* offsets, optional grid snap; result cites the window and itemizes moves/drops. Repairs the micro-segment + all-`subdivision` misreads on real performances; never applied implicitly |
| **Keyboard descriptor** (Phase 5) | render-agnostic piano-key data (`keyboard_view`): per key — midi/pc/octave, black-white topology, scale membership + degree index + tonic flag under a tonal context, activation at a **declared spec level** (`active_midi` = exact keys; `active_pcs` = every octave, explicit projection). Numeric only — labels, spelling, colors stay renderer-side |
| **Piano-roll descriptor** (Phase 5) | render-ready overlay for a MIDI file (`piano_roll_view`): note rectangles (midi/pc/voice/velocity, onset+duration in **beats and seconds**) + segmented chord-region overlays with the contextually-chosen chord name (conditioned on the local key per onset) + local-key backdrop bands with confidence. Overlay names match `midi_file_analysis` byte-for-byte. Numeric only |
| **Bracelet descriptor** (Phase 5) | pitch-class clock (`bracelet_view`): 12 ring positions with the active set flagged + optional scale backdrop, the active set's **reflection axes** + rotational order, and its **interval vector** — one ring-geometry document. Register-less; numeric only |
| **Tonnetz descriptor** (Phase 5) | neo-Riemannian lattice (`tonnetz_view`): all 12 pcs at canonical lattice coordinates with the active subset flagged, the **P5/M3/m3 edges** among active pcs (the lit triads), and the active centroid. Shares the lattice with chord analysis. Register-less; numeric only |
| **Chord network** (Phase 5) | voice-leading parsimony graph over a chord vocabulary (`chord_network`): nodes (chord + pcs + rotational symmetry — augmented/dim hubs stand out) and undirected edges between chords within a voice-leading distance, each with distance + common-tone count + root interval. Generates the "Cube Dance" chord-mandala family; every edge is the exact `voice_leading` relation. Register-less; numeric only |
| **Colour-content descriptor** (Phase 5 — A6 brief-15) | the somatic-colour resultant vectors (`colour_content_view`): **interval-content** (root-blind, transposition-invariant — ic1..ic5 on an engine-fixed pentagon, tritone central, normalized so focus ∈ [0,1]; inversional pairs collapse, maj=min/dom7=m7♭5) and **fifths-centroid** (root-aware, = `f5/n`: angle `arg(f5)`, focus `|f5|/n`). The rim geometry is engine-fixed (the resultant angle *is* the determination, so other systems compute the same surface); map angle→hue, focus→saturation at the display edge. Cross-validated: all 4083 pc-sets → exactly 185 distinct interval-colour positions. Register-less; numeric only |
| **Tonal orientation** (Phase 5 — A6 brief-17) | the **register-aware** fifths-space orientation of a *voicing* (`tonal_orientation_view`): a continuous angle (Chew's spiral-array center-of-effect projected to the fifths circle) that varies with voicing — each sounding pitch at its circle-of-fifths angle, summed with a register weight (`octave_decay` per octave above the bass; 1.0 = uniform, <1 weights the bass). **Reduces to `arg(f5)`** for a neutral closed voicing; **rotates predictably** under transposition; `octave_decay<1` distinguishes inversion/spread/doublings — for a voicing-responsive hue (map `angle_radians`→hue; absolute-register→lightness stays yours). **Register-REQUIRED** (`registered` spec level — a pc-set has no voicing to orient) |
| **Voicing analysis / suggestions** | recognition of real voicings (inversion, spread, named type); generative suggestions (closed, drop-2/3, rootless, shell) |
| **MIDI file pipeline** | SMF → events → stable-harmony segments → inferred key → enriched per-segment dataset records (JSON-ready) |
| **MIDI export** | `Sequence` → SMF (single track; tempo/meter, velocity, channel preserved) — the write-back loop for transformers/generators |
| **Catalog** | ~35 scales / ~40 chord qualities with aliases, extensible per session |
| **Catalog containment query** | every catalog scale/quality that **contains** a pc set, at which roots — tightest containers first, exact matches flagged, absolute rooted masks (`find_containers` / `catalog_containment`) |

**Performance:** identity analyses are table-driven over the 4096 possible
pitch-class sets and answer in **microseconds** after first touch. Current
APIs are whole-sequence (batch), not incremental — see "Coming" below.

### Recipes (derived values consumers asked about)

- **Chord evenness** (distance from the nearest perfectly even chord, for
  spectral/timbral mappings): for a chord of cardinality *n*,
  `evenness = set_class.dft_magnitudes[n-1] / n` ∈ [0, 1]. Verified anchors:
  augmented triad / dim7 / whole-tone = 1.0 exactly; major triad ≈ 0.745;
  dominant 7th ≈ 0.661; a 4-note chromatic cluster = 0.25.
- **Voice pairing as evidence**: both VL metrics return not just the distance
  but the optimal `mapping` of voice pairs — `[from_pc, to_pc]` at identity
  level (`voice_leading`), `[from_midi, to_midi]` at register level
  (`voice_leading_realized`) — consume them directly as per-voice motion
  vectors. Same named cardinality policy (`doubling.1`) on both.
- **Key-induction margin as a control signal**: `margin` is the difference
  between the top two candidates' Pearson correlation scores under the cited
  profile version — a continuous confidence value in [0, 2], in practice
  ~0–0.5. **Stability contract:** these semantics hold per profile version;
  a different prior version may shift absolute values, which is exactly why
  results cite the version — pin it if you map margin to a control curve.
  **The default profile changed (2026-06-17): `kk-1982.1` → `tkp-cbms.1`**
  (Temperley-Kostka-Payne; a +12.5pp global-key accuracy win, A6 brief-10). It
  is more accurate on *which* key, but **mode-asymmetric on the margin scale**:
  major margins inflate and minor margins compress (the documented relative-major
  bias). So **ranking-accuracy** consumers want the new default; **margin-as-signal**
  consumers (margin mapped to a control curve) may prefer `kk-1982.1`'s
  major/minor balance — TERRANE measured exactly this and pinned KK. **How to pin:**
  the engine functions take a profile *object* — `infer_key(material,
  profiles=load_key_profiles("kk-1982.1"))` (same `profiles=` on `track_keys` /
  `reduce_to_structural_keys`); the **MCP tools** take a version *string* —
  `profile_version="kk-1982.1"` (`key_induction` / `key_tracking` /
  `structural_keys` / `midi_file_analysis`). Note the surfaces differ — there is
  **no `profile_version` kwarg on `infer_key` itself** (passing one raises
  `TypeError` and would silently fall through to the default).
- **Near-silence contract**: all-zero or perfectly uniform pc weights raise
  `ValueError` ("no tonal information" — the engine won't guess); **any
  positive, non-uniform vector succeeds at any scale** (the profile
  correlation is scale-invariant — verified down to 1e-12 totals), so there
  is no magnitude floor to tune. Treat the raise as a signal ("no key claim
  here"), not an error: try/except is the intended consumption. Near-uniform
  vectors won't raise but carry tiny margins — an ambiguity threshold on
  `margin` composes cleanly with the raise. (Wend R3.)
- **Result shapes for the Python door** (the dataclasses of record live in
  `mts/analysis/results.py` and each module; the two every consumer asks
  about — verified by execution, Wend R1):
  - `infer_key(weights).to_dict()` → `{"candidates": [{"tonic_pc": int,
    "mode": str, "score": float}, …ranked…], "margin": float,
    "pc_weights": [12 floats], "profile_version": str}`. There is **no
    `is_ambiguous` field** — `margin` is the continuous ambiguity signal
    (Decision 7; the boolean flag exists on *naming* results only).
  - `voice_leading(source_pcs, target_pcs).to_dict()` → `{"distance": int,
    "mapping": [[from_pc, to_pc], …], "policy": "doubling.1",
    "source_pcs": […], "target_pcs": […]}`. Inputs are **iterables of
    pitch-class ints** directly — no mask conversion, no notation spec;
    `policy` is a keyword selecting the cited cardinality convention.
- **Mask bit convention**: Tonality masks are *absolute* — bit *n* = pitch
  class *n* (C=0), the same integer convention as Ian Ring's scale numbers.
  If your project keeps *root-relative* masks (bit 0 = your root), convert
  with `rotate_mask(mask, root_pc)`. Set-class identity (prime form, Ring
  number, DFT) is exhaustive over all 4096 sets — catalog *names* exist only
  for cataloged sets, but identity never requires the catalog.
- **Per-segment records, not roll-ups**: `midi_file_analysis` /
  `dataset_from_sequence` return one record per stable-harmony segment, each
  carrying `placement` (onset/duration in beats *and* seconds, bar/beat),
  `interpretations`, and key-conditional `naming` — directly renderable as
  timeline overlays. Shape: `DatasetRecord.to_dict()` with `SCHEMA_VERSION`
  for pinning (`mts/dataset/record.py` is the schema of record).
- **Align temporal comparisons in beats, not seconds.** Every region/placement
  carries beats *and* seconds; beats are exact and tempo-independent, seconds are
  a derived convenience. To compare engine output against another timeline (e.g.
  RomanText quarter-length offsets), compare in **beats** — no tempo conversion
  on either side, no multi-tempo caveat. (The engine *is* multi-tempo and
  multi-meter correct: `io/midi.py` builds a piecewise `TempoMap`/`MeterMap` from
  every `set_tempo`/`time_signature`; seconds derive from the full tempo map.)
  Region boundaries sit on the `window_beats`/`hop_beats` grid — don't read them
  finer than `hop_beats`.
- **Choosing a coalesce window** (performed/humanized MIDI): the engine never
  coalesces implicitly — a *performed* file fed to `midi_file_analysis` with no
  `coalesce_window_beats` fragments into micro-segments (the gap-12 contract,
  working as specified). There is no universal default; the *principle* is **set
  the window to the smallest rhythmic subdivision you intend to keep distinct**,
  so it heals sub-grid jitter without merging real changes. For dense
  multi-voice transcriptions, **0.25–0.5 beat** (a 16th to an 8th) is the sane
  starting band — validated on a 16-track performed file where it collapses
  sub-0.1 s segments from 68% to 4% (0.25) / 0% (0.5) without trivializing the
  harmonic rhythm. Coalescing is **lossy and reported** (it can drop grace notes
  shorter than the window; `moved`/`dropped` are itemized), so surface that
  metadata and keep the window **overridable down to 0** (a quantized or
  programmatic clip must stay byte-exact). A visualizer defaulting its own
  file-analysis path to a small window is sound; the engine adopting one is not.
  Note: this is the **chord-segmentation** axis — spurious **key-region** bands
  are a separate axis (local key tracking), tuned by `window_beats`/`hop_beats`
  + a margin (and optionally a minimum region-duration) gate, not by coalescing.
- **Closed-loop self-validation for generators** (did my output *read* as I
  intended? — Wend R5; Phase 4.6 names generators as conformance consumers):
  generate → export SMF → analyze → compare **intended vs detected, aligned
  in beats**. Use `structural_keys` as the instrument for key plans — compare
  your intended key schedule against `areas[]` (`tonic_pc`/`mode`/
  `start_beats`/`end_beats`) and intended tonicizations against each area's
  `tonicizations[]`; drop to `track_keys` only to inspect the *raw* windowed
  evidence when an intent didn't register. Pitfalls, in order of bite:
  **(1) window geometry vs harmonic rhythm** — the defaults
  (`window_beats=8.0, hop_beats=2.0`) dilute 1-bar events across ~4
  overlapping windows; for one-chord-per-bar material use
  `window_beats=4.0, hop_beats=1.0` or expect bar-grain tonicizations to be
  invisible (not misclassified). **(2) the discriminator floor** — a key
  change shorter than the structural prior's `min_modulation_beats` reads as
  a tonicization *by design* ("brief OR (related AND returns)"); sustain
  intended modulations past the floor, and check the cited `prior_version`.
  **(3)** start with `key_inertia`/`disambiguate_relative`/`smoothing` all
  off — validate against the detector's raw reading first (and note
  `key_inertia` + `disambiguate_relative` together raises). **(4)** exact
  quantized output needs no coalesce window; asymmetric meters (7/8, 5/8)
  are a non-issue for key machinery (everything is beat-based — just write
  the SMF meter map honestly). Free integrity check: read your own emitted
  file back with `read_midi_file` and assert `losses == []`.

## Four doors in

1. **Python import** (in-process): `from mts.analysis import analyze_chord,
   infer_key, name_chord, voice_leading, ...` — typed frozen dataclasses, each
   with `to_dict()`. Best for Python-native projects and lowest latency.
2. **MCP endpoint** (cross-language / agent-facing): `pip install 'mts[mcp]'`,
   then `python -m mts.mcp` (stdio). 43 tools mirroring the library surface,
   including `midi_file_analysis` (file → key-aware dataset in one call) and
   catalog discovery (`list_scales`, `list_chord_qualities`). Inputs accept
   note names (`"C"`, `"F#"`, `"Bb"`) or pc ints; MIDI numbers for register.
3. **Dataset artifacts** (offline/pipeline): JSON `DatasetRecord`s with an
   explicit `SCHEMA_VERSION`, a numeric canonical core, provenance, and
   context snapshots — built for reproducible interchange between projects.
4. **Local HTTP bridge** (browser / non-Python consumers): `python -m
   mts.mcp.bridge` (stdlib only — no extra install) serves every MCP tool
   over loopback HTTP, default `http://127.0.0.1:8012`. Discover with
   `GET /tools` (name, doc, params per tool); invoke with
   `POST /call/<tool_name>` and a JSON object of keyword arguments →
   `{"ok": true, "result": ...}`. Bad input is a 400 carrying the engine's
   actionable message; CORS is open (the boundary is loopback, not origin).
   Same signatures and `to_dict()` shapes as the MCP endpoint — the bridge
   is glue, not a second API (ruled 2026-06-11; shipped as ROADMAP gap 9).
   Hosted endpoints remain declined (local-first); a WASM core remains an
   explicit non-commitment.

## Contracts to design around (important)

- **Answers are plural and evidenced.** Results carry ranked alternatives,
  per-signal evidence, and `is_ambiguous`. C6 vs Am7 *without a bass note or
  key is genuinely ambiguous and the engine says so* — consume the ranking;
  don't assume a single label.
- **Conditional on context.** Namings are labeled with the key context that
  produced them. Different key → possibly different reading, by design.
- **Versioned priors.** Anything empirical (key profiles, naming weights,
  VL cardinality policy) is a versioned asset cited in results. Pin versions
  if you need byte-stable outputs across engine upgrades.
- **Native-port consumers — the versioned-data export.** If you reimplement a
  subset of the engine natively (no CPython; the Decision-10 consumer-port
  corollary, e.g. a plugin), run `scripts/export_versioned_data.py` to emit a
  bundle: a **`set_class_table`** with the table-driven combinatorics (prime
  form, interval vector, DFT magnitudes, Z-partner, symmetry) precomputed for all
  4096 pc-set masks — consume it as pure data instead of porting the mask-space
  math — and a **`manifest`** naming every versioned prior/catalog + its version
  string(s). The port computes the same answers from the same versioned data,
  citing the same versions; the **golden conformance harness is the parity
  oracle** (a port is faithful iff it reproduces the golden cases). The engine
  stays the source of truth — regenerate after upgrades. The script also emits a
  self-contained **`bundle.json`** that embeds each prior/catalog's parsed content
  + a per-asset sha256 (plus the `doubling.1` voice-leading policy id/description),
  so a port can run without the repo.
- **Performed timing needs an explicit coalesce.** The temporal analyses
  (segmentation, metric placement, voice motion) treat onsets as exact:
  humanized/performed timing fragments segmentation into micro-segments and
  reads on-the-beat notes as off-grid subdivisions. The engine never repairs
  this implicitly — call `coalesce_events` (or `coalesce` in-process, or
  `coalesce_window_beats` on `midi_file_analysis`) before analysis; the
  result cites the window used and itemizes what moved or was dropped.
  Client-side coalescing (Audiology's ~60 ms) remains equally valid — same
  contract, either side of the wire. Swing/groove material is the exception
  that *should* keep its encoded offsets — see the swing row's caveat.
- **Key candidates span the loaded profile modes** — major and minor under
  `kk-1982.1`. Modal material (a dorian vamp) will rank as its relative
  major/minor rather than its modal tonic; modal profile rows join the
  standing Temperley/Aarden invitation if you need modal centers ranked.
- **Numeric core, spelling at the edge.** Analysis results are pitch-class
  numbers; note *spelling* (F# vs Gb) and label style are rendered separately
  from a display context. Visualizers: consume the numeric core and either
  render your own labels or request spelled views.
- **Errors over guesses.** No realization → register-aware analysis raises.
  No key → naming runs intrinsic-only and flags ambiguity. Silence/uniform
  input → key induction raises. Handle these as signals, not failures.

## Coming (prepare for, don't depend on yet — phases in ROADMAP.md)

- **Cadence detection as evidenced events** (gap 7) — V–I and related
  root-motion patterns as discrete, evidence-carrying events. Consumers:
  TERRANE home-center impulses, A1, A4.
- **Representation layer** (Phase 5) — *for visualizers*: typed, render-
  agnostic descriptions of clock/bracelet diagrams, Tonnetz, circle of
  fifths, piano-roll/keyboard views, each declaring the input it requires.
  Plan to consume structured description data, not pixels.
- **Generative voice-leading realization** (Phase 7) — *for generators*:
  progression → concrete voicings with parameterized smoothness/contour/
  register, plus scale re-mapping, meter re-mapping, modulation path
  planning, instrument-class profiles.
- **Live/streaming + incremental APIs** (A4 gaps) — *for real-time tools*:
  today's APIs are batch; rolling/incremental forms are recorded, not built.
  Real-time integrators: design a clean event boundary now (note on/off with
  timestamps) so a streaming adapter can slot in later, and prefer pull-based
  queries against the batch API in the interim (it is fast enough to re-query
  per phrase, just not per note).
- **Compositional rulesets** (Phase 4.6 / Decision 8) — *for everyone,
  eventually the biggest one*: a declarative, JSON-serializable constraint
  syntax over the engine's analytical vocabulary. Rulesets will be
  first-class versioned artifacts flowing in both directions: **impose** one
  on generation or analysis (conformance reports with violation locations),
  **derive** candidate rulesets from existing material (a narrowable
  rule-space), and **compare** rulesets (shared rules, conflicts, empirical
  profiles). An LLM can translate a theory text into the DSL through MCP;
  the engine validates and evaluates it exactly. *What to anticipate:*
  generators — a ruleset becomes the "style" parameter, and your output can
  be checked against one; analyzers/visualizers — conformance reports are a
  new renderable result type; all projects — rulesets are JSON artifacts you
  can store, version, and trade between projects like patches. The
  supporting vocabulary expansion (voice identity, melodic contour,
  rhythmic patterns) is recorded alongside it.

## What to send back (per candidate project)

To prepare an integration schematic, each project should answer:

1. **What it produces/consumes:** MIDI events? note lists? audio (out of
   scope — Tonality is symbolic-only)? Does it have durations/velocities?
2. **Which capabilities it wants** (from the table above) and at what
   granularity (per note / per chord / per phrase / per file).
3. **Latency budget:** offline, interactive (~100ms), or hard real-time.
4. **Direction:** analysis only (Tonality reads your output), generation
   (Tonality proposes material you realize), or both.
5. **Integration door:** Python import, MCP, or dataset files.
6. **Spelling/labeling needs:** raw numbers, or spelled note names / chord
   symbols / roman numerals for display.

**Where answers land:** file them as `integrations/<project>/brief.md` in
this repo (directly via a PR, or relayed through Julian) — see
[integrations/README.md](integrations/README.md) for the channel protocol.
Tonality's agent triages every brief into a per-request verdict
(`integrations/<project>/response.md`), verifies "already shipped" claims in
code, records the project as a target application in
[ROADMAP.md](ROADMAP.md), and documents anything usable today back into this
file. Worked example: [integrations/terrane/](integrations/terrane/).
