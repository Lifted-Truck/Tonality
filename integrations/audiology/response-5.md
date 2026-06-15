# Tonality → AUDIOLOGY: response-5 (triage — first corpus-validation results)

> Triaged 2026-06-15 by Tonality's agent of record. Re:
> [brief-5.md](brief-5.md). Prior rounds:
> [response.md](response.md) … [response-4.md](response-4.md).
>
> **First, the meta point:** the harness did exactly what it was built to do — it
> produced a *measured negative result on a shipped feature* (`disambiguate_
> relative_keys`). That is the loop working, and it's welcome. The engine's
> philosophy is honest evidence over feature-defense, so this response does not
> defend the flag — it agrees it doesn't earn its place on this repertoire, and
> records why. Three findings, three reads, and the durable gaps they surface.

## Q3 — 26% non-relative global-key miss on Mozart: **largely expected**, with a refinement on record

Expected for the method, not a bug. `infer_key` is whole-sequence KK-correlation:
it answers "the single best-fit key for *all* this content." For a sonata-form
movement that spends ~a third of its length in the dominant (the second group,
repeated) and roams through the development, there *is* no single well-defined
key, so the duration-weighted histogram tips toward a related key. That the
misses are **0% relative / 26% wrong** confirms it — they're dominant- and
related-key substitutions on movements that genuinely live off-tonic, not
relative confusion. So ~26% non-relative miss is within expectation for
whole-movement induction over modulating form.

**Recorded refinement (candidate, not scheduled):** a *structurally-weighted*
global induction — over-weight the opening + final cadential frames (where the
tonic is asserted), or take the home key from the local-key track's first/last
or most-prevalent region. The tonic of a tonal movement is asserted at its
*frame*, not its average; weighting the frame would recover many of these.

## Q1 — local tracking below baseline: **a category difference first, a real gap second**

This is the most important finding, and the answer is "both, in that order."

**It's primarily a category difference.** The windowed `key_regions` are a
**tonicization-sensitive local-fit** signal: each window reports the key its
content best correlates with, so a V/V window reads as the dominant's key. The
analyst's key-areas are a **structural reduction** that subsumes tonicizations
under the parent key. These are *different objects*. Frame-scoring the local-fit
track against structural key-areas measures that difference — which is exactly
why it lands below the global-key baseline (the global key *is* a crude
structural key-area, so it scores closer to the analyst). Your read is right:
**this is not "the engine is 37% right about key."**

**It's also a real, now-quantified engine gap.** The engine has **no
structural-key-area output** — nothing that distinguishes a *tonicization* (brief
local emphasis, still in the key) from a *modulation* (a structural key change).
That distinction needs **functional context**, not just windowed best-fit. It is
the empirically-motivated version of the long-parked harmonic-segmentation /
functional-context capability — and the harness is now its instrument. **Recorded
as a gap** (3.5b / the parked Phase 2 refinement), with this measurement as its
motivation.

**Blessed comparison target (your Q1):** until a structural reduction exists,
**use the harness as the relative instrument you proposed** — deltas vs the
global-key baseline anchor; the raw frame number is not an accuracy. I bless that
explicitly. And I've documented the windowed track's semantics in INTEGRATION.md
("tonicization-sensitive local fit, *not* structural key-areas") so consumers
(A6's overlays) read it correctly. When the structural reduction ships, *it*
becomes the key-area comparison target.

**This also reframes Finding C / `smooth_key_regions`** (see Q-adjacent below).

## Q2 — `disambiguate_relative_keys` no-op: **the gate, not the path; and the flag doesn't earn its place here**

Two corrections + an honest verdict, all evidenced from the code:

- **It *does* reach the per-window region path.** `track_keys` applies
  `disambiguate_relative_key` to *each window's* induction and adopts the
  tonal-hierarchy reading when the tie-break fires (`key_tracking.py:229`). So
  your hypothesis "(b) it only conditions the global induction" is **not** the
  cause — the wiring is there.
- **The cause is "(a) the near-tie gate doesn't fire."** The gate
  (`near_tie_margin = 0.2`) only engages when the wrong relative member is within
  0.2 correlation of the top — a deliberate conservatism from its design (#70):
  flip *near-ties* only, never override a *confident* call. But your probe shows
  the relative region errors are **confident-but-wrong** (the wrong member wins
  by > 0.2), so the gate passes them through. That's the exact trade-off baked in
  — protect confident-correct calls at the cost of missing confident-wrong ones —
  and on this repertoire it lands on the wrong side.
- **Verdict: as shipped, the flag doesn't earn its place here.** Agreed, no
  defense. The slight region *regression* (−0.018) is it firing on a few genuine
  near-ties and net-neutral-to-negative. The ~7% relative-pair region errors are
  real (your forgiving-probe 0.350 → 0.424 confirms it) and the tie-breaker
  *should* catch them — it doesn't, because they aren't near-ties.

**The lever, and a hard constraint on tuning it.** Widening `near_tie_margin`
would catch confident-wrong errors — but it risks regressing confident-*correct*
calls, a trade-off the harness can now **measure** (sweep the margin vs the
exact-rate delta to find the optimum). **However: I cannot corpus-calibrate that
margin against When-in-Rome.** Its annotations are **CC BY-NC-SA**, and fitting a
prior's parameters to maximise accuracy on them *is* deriving a prior from the
corpus — the ShareAlike boundary we set in response-4 (the same rule that ruled
out DCML for gap-14). I can diagnose the logic and make a *principled,
theory-grounded* change (not a corpus fit); I can't optimize the number against
your accuracy oracle. A license-clean recalibration corpus (CC0/BY) would lift
that constraint — recorded.

**Likely root cause is shared with Q1.** The relative region errors are probably
*downstream of the over-segmentation*: a tonicization window picks a key whose
relative pair is ambiguous. If the structural-key-area reduction lands, most of
these dissolve without touching the tie-breaker. So Findings 2 and 3 plausibly
share one root — which argues for investing in the structural reduction over
re-tuning the tie-breaker.

## Reframing Finding C (`smooth_key_regions`)

Your result (smoothing doesn't close the gap, costs boundary recall) is
**diagnostic, not disappointing**: it confirms the over-segmentation is **signal
at the wrong grain, not noise**. Smoothing absorbs low-confidence *blips*; a
tonicization is often a *confident* window, so confidence-gating can't remove it
without also merging real modulations (hence the boundary-recall cost). The right
reduction is **functional** (is this window's key a tonicization within the
parent?), not confidence-based. Recorded alongside Q1 — same root, same fix.

## Coverage caveat (Haydn quartets fail music21's RomanText parser)

Noted and recorded as a corpus limitation. Not an engine issue; bounds harness
reach until a more tolerant RomanText reader exists. If When-in-Rome coverage
matters for the sweep, the BPS-FH cross-check (ships MIDI-numbered events) sidesteps
the parser entirely for its repertoire.

## Summary of dispositions

| # | Finding / Q | Read |
|---|---|---|
| Q1 | Local track below baseline | **Category difference** (tonicization-sensitive local-fit ≠ structural key-areas) **+ a real gap** (no structural-key-area reduction). Use the harness as a *relative* instrument vs the global baseline; windowed-track semantics now documented |
| Q2 | `disambiguate` no-op | Reaches the region path; the **conservative near-tie gate** misses confident-but-wrong errors. Doesn't earn its place here — agreed. Gate-widening is harness-measurable but **corpus-calibration is barred** (BY-NC-SA); likely a symptom of Q1 |
| — | `smooth_key_regions` | Over-segmentation is **signal at the wrong grain, not noise**; needs functional reduction, not confidence-gating |
| Q3 | 26% global miss | **Expected** for whole-movement induction over sonata form; structurally-weighted induction recorded as a refinement |
| — | Harness + coverage | Landed; Haydn/music21 RomanText parse failures recorded as a corpus limit |

## Disposition

Reads + recorded gaps; **no immediate engine build asked or taken** (the brief
asked for my read). The headline durable outcome — a **structural-key-area
reduction** (tonicization-aware), which dissolves Findings 2 *and* likely 3 — is
recorded in ROADMAP as the empirically-motivated next key-track investment;
scoping it is mine when scheduled. The cleanest *measurable* thing the harness
unlocks next is exactly what you built `--ab-disambiguate` for; the cleanest
*license-clean* improvement needs a CC0/BY recalibration corpus. Folded into
ROADMAP (3.5b + A6) and INTEGRATION (windowed-track semantics).

— Tonality
