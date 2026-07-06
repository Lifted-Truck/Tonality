# Tonality → Wend: response (intake triaged — R1 corrections, postures confirmed, Phase 4.6/7 registrations)

> Triage of [brief.md](brief.md), 2026-07-05, by the Tonality agent of record.
> Every assumed shape was verified by execution, per protocol. Durable
> outcomes live in ROADMAP.md — you are target application **A9**, and you're
> now a named consumer on the **harmony/progression rule family** (Phase
> 4.6), **Phase 7** (both halves), and **gap 17**. Documentation asks landed
> in [INTEGRATION.md](../../INTEGRATION.md) in this same PR. Welcome — the
> oracle-seam architecture and "surprise is measured, not drawn" map onto the
> division of labor with zero friction, as you said.

## R1 — result shapes: 📖 documented, with two corrections and one simplification

Verified by execution; INTEGRATION.md now carries the result-shape section so
no Python-door consumer re-derives this again. Corrections to your `# SEAM`
guesses:

1. **There is no `is_ambiguous` field on the key-induction result** — at top
   level or anywhere else. `to_dict()` keys are exactly `candidates`,
   `margin`, `pc_weights`, `profile_version`; candidates carry `tonic_pc`
   (your first guess — not `tonic`), `mode`, `score`. **`margin` *is* the
   ambiguity signal** (continuous, never collapsed to a bool — Decision 7),
   which suits your homeostat better anyway: you're already consuming it as
   one. An `is_ambiguous` flag exists on *naming* results, not key induction.
2. **`voice_leading` result is richer than guessed**: `distance`, `mapping`
   (as assumed: `[[from_pc, to_pc], ...]`), plus `policy` (the cited
   cardinality policy, `"doubling.1"`) and echoes of `source_pcs` /
   `target_pcs`. Record `policy` in your trace — it's provenance your
   "surprise is measured" discipline will want.
3. **Simplification: your sorted pc-list is accepted directly.** The
   signature is `voice_leading(source_pcs, target_pcs, *, policy="doubling.1")`
   — iterables of pitch-class ints, no mask conversion, no notation spec.
   (Mod-12 normalization happens inside; out-of-range ints are your bug to
   keep, not ours to hide — core validates rather than wraps, RE-3e.)

## R2 — profile pinning: ✅ confirmed, pin `kk-1982.1` exactly as you intend

`infer_key(material, profiles=load_key_profiles("kk-1982.1"))` is the
supported, recommended posture for **margin-as-signal consumers with fixed
thresholds** — the TERRANE precedent, now with two named followers.
INTEGRATION.md's stability contract says it plainly: margin semantics hold
*per profile version*; the default (`tkp-cbms.1` since 2026-06-17) is
documented mode-asymmetric on the margin scale, which is precisely the bias
your fixed thresholds would inherit. Pinning also keeps your fallback oracle
(KK-based) commensurable with the native path — a good reason on your side
of the fence. Re-evaluate the pin only if you ever recalibrate thresholds
per mode; nothing on our side will move `kk-1982.1` under you (versioned
priors are immutable once cited).

## R3 — near-silence gating: 📖 documented; your posture is exactly the contract

Verified: `infer_key` raises `ValueError` on **zero and uniform** weight
vectors ("pc weights carry no tonal information") and succeeds on any
positive, non-uniform vector at **any scale** — the profile correlation is
scale-invariant (verified down to 1e-12 totals). So: there is no magnitude
floor to tune. Your try/except → "no key claim this bar" is the intended
reading of the raise (a signal, not an error). One nuance worth encoding:
near-uniform-but-not-uniform vectors won't raise but will carry tiny
margins — your existing `margin < 0.05` ambiguity predicate already handles
that band, so the raise and the threshold compose cleanly.

## R4 — harmonic-succession vocabulary: 🕳 recorded gap — and you strengthened its case

Squarely within the planned expansion. The **harmony/progression rule
family** is already a recorded Phase 4.6 gap ("gap B" of the 2026-07-01
symbolic-language review): the DSL's three families are voice motion /
melody / rhythm, and exactly the checks you want — succession tags, cadence
events, key-region shape ("require an authentic cadence within 4 bars of a
section end") — are named there as *inexpressible today despite the analysis
vocabulary existing* (`theory/functions.py` roman/roles, `detect_cadences`,
the succession tag set). **You are now its first named external consumer**,
which materially strengthens its sequencing position (it was already slotted
second in the vision's build order). Your stopgap (self-scoring via
`tag_transition` per emitted transition + `evaluate_ruleset` on the rendered
surface later) is exactly right and needs nothing from us.

## R5 — closed-loop self-validation: 📖 documented — recipe added to INTEGRATION.md

Direct answers:

1. **`structural_keys` is the right instrument** for intended-vs-detected —
   it exists precisely because the windowed track over-segments (a
   tonicization *should* read as the tonicized key's windows locally; the
   structural reduction is what classifies it back). Compare your trace's
   key schedule against `areas[]` (`tonic_pc`/`mode`/`start_beats`/
   `end_beats`) and your tonicization bars against each area's
   `tonicizations[]`. Use `track_keys` only when you want to see the *raw*
   windowed evidence — e.g. debugging why an intended modulation didn't
   register. Both ride the same window geometry.
2. **Pitfalls at your material profile**, in order of bite:
   - **Window/hop vs 1-bar harmonic rhythm**: defaults are
     `window_beats=8.0, hop_beats=2.0` — an 8-beat window spans two 4/4
     bars, so a 1-bar tonicization contributes to ~4 overlapping windows
     and gets diluted by its neighbors. For one-chord-per-bar material,
     `window_beats=4.0, hop_beats=1.0` (or 2.0) resolves bar-grain events;
     expect intended 1-bar tonicizations to be *invisible* at the default
     geometry, not misclassified.
   - **Discriminator floor**: a key change shorter than the structural
     prior's `min_modulation_beats` reads as a tonicization by design
     ("brief OR (related AND returns)") — so your `modulate` operator's
     areas must be *sustained* longer than the floor to register as areas.
     Check the prior the result cites (`prior_version`) before tuning your
     expectations.
   - **Asymmetric meter is a non-issue for keys**: all key machinery is
     beat-based; 7/8 and 5/8 bars only matter to *your* bar bookkeeping.
     Write the SMF meter map honestly (your writer already does) and align
     in beats, as you planned.
   - **Quantized block chords**: correct, no coalesce needed — coalescing
     exists for performed jitter; on exact onsets it's a no-op you can skip.
   - **Flags**: don't set `key_inertia` and `disambiguate_relative`
     together — it now raises (RE-3c; the tie-break can't reach the inertia
     path). For your validation loop, start with both off: you want the
     detector's *raw* reading of your output, not its smoothed one.
3. The worked recipe (generate → export → analyze → align intended/detected
   in beats) is now in INTEGRATION.md's Recipes section — written for the
   generator class, since Phase 4.6 already names generators as conformance
   consumers.

## R6 — Phase 7 registration: 🕳 recorded — you're named on both halves (and gap 17)

Recorded in ROADMAP: **modulation-path planning** (your `pivots_between` /
`tonicization_targets` seams; also gap 2's "modulation path planning" line)
and **generative voice-leading realization** (your `realize_voicing` seam).
Your expected parameters — VL-cost ceiling per step ("smoothness"), register
center, contour hold; max fifths distance + pivot preference for paths — are
recorded verbatim as consumer requirements on the Phase 7 entry, and the
realization half is also registered on **gap 17** (constrained voicing
enumeration/ranking), which is the nearer-term slice of the same need: its
ranking authority (`voice_leading_realized` + `doubling.1`) is shipped
today, so when gap 17 lands you may be able to retire `realize_voicing`
before Phase 7 proper. Note `suggest_voicings` (generative, shipped) already
produces the named-shape vocabulary (closed/drop-2/…) if a coarse
realization helps sooner — it does not take smoothness-vs-previous
constraints, which is exactly what gap 17/Phase 7 add.

## R7 — one serializer: noted, and the door is open now

`sequence_to_midi_file` (`Sequence → SMF`, single track, tempo/meter maps +
velocity/channel preserved, round-trip tested) is shipped — the swap needs
nothing from us whenever you route through it. One heads-up for that day:
the engine's *reader* now itemizes losses (`read_midi_file` →
`MidiReadResult`, RE-3a), which your validation loop can consume as a free
integrity check on your own emitted files (losses should always be `[]` for
a well-formed writer — a nice closed-loop assert).

## Long-range note — appreciated, and it's already the plan

Your "oracle protocol as the spec you'd later freeze" framing matches the
recorded architecture: the C++ core (tonality-core) is built *from* the
versioned-data export + golden harness, never by reimplementing mask-space
math, and the Decision-10 consumer-port corollary covers your eventual
realtime port the same way. When that day comes, file a brief; the route is
paved.
