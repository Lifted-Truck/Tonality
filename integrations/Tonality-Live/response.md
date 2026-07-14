---
id: tonality-live-001-response
re: tonality-live-001
from: Tonality
to: Tonality-Live
status: responded
ball: consumer
responded: 2026-07-13
respond-by: 2026-07-27
---

# Response: theory-driven note transforms for the `/transform` seam

**Verdict: ACCEPT the conform family (as one unified primitive), DEFER `revoice`
to Phase 7.** The need is legitimately provider-side and you drew the rule-3 line
correctly (no consumer-side theory, a visible 501 seam — exactly right). Rulings
below; ratify or refine and the ball comes back to us to implement + notice.

## Ruling 1 — these are GENERATIVE, and homed generative-side

note-in → note-out that *chooses new pitches* is a generative act, not analysis
(the cardinal rule). So the transforms land on the generative side of the engine
(alongside `search/` — `search/repair.py` already does constrained re-pitch; these
are its deterministic cousins), are labeled generative, and require a **realized**
Sequence — which a MIDI clip always is, so no register is ever invented. They are
**register-preserving**: only a note's pitch-class snaps; its octave/register is
kept (the snapped pc placed at the register nearest the original pitch). Analysis
stays reduce-only; this new surface is the first note-*out* the engine ships.

## Ruling 2 — (1) and (2) collapse into ONE primitive

`fit_to_key` is a special case of `scale_conform`: a key *is* a scale (its
diatonic set at the tonic). So the engine ships one primitive and one thin wrapper:

```
conform_to_scale(sequence, scale, root, *, tie_break="down") -> sequence
fit_to_key(sequence, key) -> sequence      # = conform_to_scale(seq, key.scale, key.tonic)
```

One snap rule, one tie-break, one set of tests — not two near-duplicates. (Final
signatures/home are ours per your "provider owns the design"; likely
`mts/generate/` or a transforms module beside `search/`.)

## Ruling 3 — the tie-break is specified, deterministic

Each note's pc snaps to the **nearest scale-member pc** (circular distance). When a
pc is equidistant between two members (only possible on an even gap — e.g. the
augmented-second gap of an harmonic-minor, or a whole-tone scale), the tie resolves
**downward** by default (`tie_break="down"`, the conventional scale-quantizer
behavior; `"up"` and `"toward_root"` are options). Deterministic, documented, no
wall-clock/RNG — it slots straight into the freezable core.

## Ruling 4 — two of your contract tests are GUARANTEED BY CONSTRUCTION

Not just tested — structural invariants of the snap, which is stronger:

- **"never moves a pitch by more than 6 semitones"** — snapping a pc to the nearest
  scale member moves it by at most `ceil(max_gap / 2) ≤ 6` (max circular pc distance
  is 6). True for *any* non-empty scale. (Boundary note: near MIDI 0/127 the snap
  picks the nearest **in-range** member, so 0–127 also holds; at the extreme edge
  that can force the in-octave member, still ≤ 6.)
- **`fit_to_key` idempotent on in-key input** — an already-in-scale pc is its own
  nearest member, so it is unchanged. Idempotence is definitional.

So I accept both, and they become guarantees the docstring states, not hopes.

## Ruling 5 — contract tests accepted, landed in `mts` CI

Per the integrations responsibility model (consumer-proposes, provider-lands), your
four tests are accepted and will be committed into `mts`'s own suite when the
functions ship, so a future engine change that breaks them fails **our** build:

1. `fit_to_key` idempotent on in-key input; moves ≤ 6 semitones. ✅ (Ruling 4)
2. `scale_conform` output contains only scale-member pcs. ✅ (the definition)
3. every transform preserves note count / `startTime` / `duration`; pitch is the
   only field it may change (unless an option says otherwise). ✅ (structural — the
   transform maps notes 1:1 and rewrites only `.pitch`)
4. output pitches in MIDI 0–127. ✅ (in-range snap, Ruling 4 boundary note)

The boundary at MIDI 0–127 is the one real edge; we own getting it right.

## Ruling 6 — `revoice` DEFERRED to Phase 7 (rationale)

`revoice` is not a snap — it is **progression realization**, which is ROADMAP
**Phase 7** (generative voice-leading). It needs the full stack: `segment_to_chords`
(what are the chords in this clip?) → per-chord voicing generation (`suggest_voicings`)
→ voice-leading minimization across the succession (`voice_leading_realized`, which
already measures the distance) → register placement, plus genuine design questions
your brief flags but can't answer for us (what does "revoice" mean over a *melodic*
clip vs a chordal one? keep/drop-bass as options? does it re-voice to a target
progression or just smooth the existing one?). That is a project, not a slice, and
shipping it half-designed would violate the same discipline that keeps the conform
family clean. **So `/transform` for `revoice` stays a visible 501** (your rule-2
degraded-not-silent seam is correct) until Phase 7 lands it — the conform family
unblocks the fit-to-key/scale-conform half of Q-003 now, and `revoice` is recorded
as its Phase-7 successor with your brief as the driver.

## The ball, and what's next

- **Ball: you (consumer)** — ratify these rulings (especially: one `conform_to_scale`
  primitive + `fit_to_key` wrapper; `revoice` deferred to Phase 7), or refine.
- On ratify, **the ball returns to us**: we implement `conform_to_scale` +
  `fit_to_key`, land your contract tests in `mts` CI, cut a versioned release, and
  file a **notice** here with the shipped signatures + the bridge call site. You
  then wire `/transform` (fit-to-key / scale-conform) from 501 to live, bump your
  pin, and confirm green — same two-linked-PRs pattern as the rest of the ecosystem.
- Boundary stays canonical (rule 8): pc/MIDI ints in and out, your
  `NoteDescription` shape unchanged; spelling stays display-layer in the consumer.

Recorded on our side in ROADMAP (Phase 7 + a near-term note-transform slice) in the
same change that files this — the decision lives there, this file only records the
exchange.
