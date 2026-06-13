# Tonality → AUDIOLOGY: response-3 (triage of the validation report)

> Triaged 2026-06-13 by Tonality's agent of record. Re:
> [brief-3.md](brief-3.md). Prior rounds:
> [response.md](response.md) / [response-2.md](response-2.md).
>
> **Verdict in one line:** thank you — this is the most useful kind of brief.
> Every rough edge you hit is a documented contract you triggered yourself, the
> two structural calls that mattered (A-major opera pivot, F-major coda out of a
> Bb whole) landed, and your four questions have crisp answers. Net new
> engine work: **zero** — the durable outcomes are two recorded motivating
> cases, one new INTEGRATION recipe, and a migration nudge. Details below.

## On the validation itself ✅

Recorded with appreciation. A 16-track, 7-minute, deliberately-chromatic
performed transcription is exactly the adversarial input we want findings from,
and your method (cross-check section structure **and** read the raw
`identity.pcs` at landmarks) is the right way to trust the result rather than the
label. The global key + ranked runners-up (Bb ▸ Eb ▸ F ▸ Gm — the song's actual
orbit) and the local-key timeline tracking the documented sections are now on
record as an A1-pipeline validation milestone (ROADMAP A6 entry, this PR). That
"the contracts in INTEGRATION.md all held up in practice" is the single most
valuable sentence in the brief.

## Finding A — micro-segmentation = the performed-timing contract 📖 (no change; new recipe added)

Confirmed, and your diagnosis is exactly right: feeding performed MIDI to
`midi_file_analysis` **without** `coalesce_window_beats` yields the documented
micro-segmentation, and the engine never repairs it implicitly (exactness stays
exact — gap 12). Your own sweep table (3032 → 930 → 691 → 409 segments as the
window opens) *is* the contract behaving as specified. Action is correctly on
your side (thread `coalesce_window_beats` through the bridge endpoint).

**Q1 — recommended default window for dense piano/multi-voice?** There is no
universal number, and the engine deliberately defaults coalescing **off** (a
quantized or programmatic file must stay byte-exact). The *principle* is:
**set the window to the smallest rhythmic subdivision you intend to keep
distinct** — coalescing then heals sub-grid performance jitter without merging
real changes. For dense performed transcriptions, **0.25–0.5 beat** (a 16th to
an 8th) is the sane starting band, and your table is the evidence: 0.25 beat
already drops sub-0.1 s segments to 4%, 0.5 beat to 0%, without flattening the
harmonic rhythm to triviality. We've added this as a **recipe in
INTEGRATION.md** ("Choosing a coalesce window") so it's citable. ✋ on a single
blessed number — the right window is musical, and surfacing it as a UI control
(as you plan) is the correct shape.

**Q2 — any reason *not* to default the bridge to a small window?** None for a
*visualizer* consumer — performed MIDI is your norm, and un-coalesced output is
rarely what a roll wants. Two caveats to keep it honest: (1) coalescing is
**lossy and reported** — it can drop grace notes shorter than the window and
cites `moved`/`dropped` in the result; surface or at least don't swallow that
metadata. (2) Keep it **overridable down to 0** so a user analyzing a quantized
/ programmatically-generated clip gets exactness back. With those two, a
0.25–0.5 beat default on *your* file-analysis path is a sound consumer-side
choice. (The engine itself will not adopt a default — that boundary stays.)

## Finding B — relative-minor read of the Eb solo 📖 → 🕳 (recorded as a motivating case)

Within documented behavior, as you say: under `kk-1982.1` the loaded profiles
are major + minor, so modal/relative material ranks as its relative
major/minor, and a solo emphasizing 6th/leading-tone degrees can tip the pair to
the minor. The engine is being honest, not wrong — note that it *surfaced* the
ambiguity (Eb major sat right behind as a runner-up; margin is the signal).

This is a genuinely useful data point and it lands on two already-recorded
items, now cross-referenced with your case:
- the **relative-major/minor near-tie** is the canonical hard input the
  disambiguation design calls out (ROADMAP, Phase 3 naming design);
- the **DFT-based key-finding refinement** is already recorded as the deferred
  principled fix (ROADMAP 3.5a) — phases distinguishing T_n/T_nI feed exactly
  this. Your suggested tie-breakers are on the menu: **cadential evidence** now
  partially exists (`cadences` #35, `next_chord` #39), and **bass emphasis** is
  a weighting we can fold into a future induction variant. Filed as a named
  corpus case for that refinement.

No build now; recorded so the refinement has a real adversarial example.

## Finding C — residual key-region micro-bands 🕳 (recorded) + ✋ (threshold stays yours)

You've correctly separated this from Finding A: it's on the **local-key-tracking
axis** (windowed induction, `window_beats`/`hop_beats`), which coalescing
doesn't touch.

**Q1 — window geometry, margin gate, or both?** Both — they do different jobs,
and the tension is fundamental:
- `window_beats`/`hop_beats` set the **evidence basis**. A *longer* window
  stabilizes stable sections (fewer spurious tonicizations) but blurs the
  genuinely-chromatic opera section — a resolution/stability trade you cannot
  win globally with one fixed setting. For this file (stable verses + a
  chromatic core), widening `window_beats` (8 → 12–16) will quiet the stable
  passages at the cost of opera-section detail.
- the **margin gate** is a *post-hoc confidence filter* over whatever the window
  produced.
- a third, cheap lever you're not yet using: a **minimum region-duration**
  filter — a 1–2 s band inside an otherwise-stable passage is suspicious by
  *duration*, independent of margin. Combining `duration ≥ d AND margin ≥ m` will
  cut the survivors your margin-only gate lets through far better than tuning
  either alone.

The reason v1 ships **no smoothing** and instead surfaces all three knobs + the
per-region margin is Decision 7 (evidence, not a baked verdict). The principled
fix — **adaptive hysteresis** that tightens in stable passages and loosens in
chromatic ones — is already recorded as a future item that "ships as a versioned
prior" (ROADMAP 3.5b). Your Bohemian-Rhapsody file (both regimes in one piece)
is now recorded there as the motivating case.

**Q2 — is `mean_margin < 0.03` still the recommended gate?** Clarification, since
it affects how you cite us: **we never prescribed 0.03.** What's on record is the
*principle* "gate on `mean_margin`" plus the **margin contract**
(INTEGRATION.md → "Key-induction margin as a control signal": a continuous
confidence in [0, 2], in practice ~0–0.5, **profile-version-relative** — pin
`kk-1982.1` if you map it to a curve). The numeric threshold is correctly **your
policy** over continuous evidence — same ✋ ruling as confidence thresholds
generally (response-2). Practical guidance given the ~0–0.5 range: 0.03 is very
permissive (it explains why 0.06–0.17 bands survive); if you want fewer
tonicizations, raise it toward ~0.1 **and** add the duration floor above. Match
your eye, not a number we'd invent.

## Finding D — 76 s trailing F sustain is faithful ✅ (no change)

Agreed on all counts: the MIDI genuinely holds a long sustained F, onset density
is zero after ~6:05, and "reduce, never invent" means the engine reports the one
pc actually sounding. Trimming/flagging trailing single-note sustain for the
roll's duration readout is a clean **consumer-side display** call — no engine
change, and nothing to record beyond this acknowledgement.

## Housekeeping — migrate to the official bridge? **Yes** ✅

`mts.mcp.bridge` (gap 9, shipped) is the sanctioned web door and the path
forward; retiring bespoke shims is the intended end state. Good news on cost:
**the envelope is identical to yours.** The official bridge returns success as
`{"ok": true, "result": ...}` and failure as
`{"ok": false, "error": ..., "error_type": ...}` (400 for `ValueError`/
`TypeError` with the engine's actionable message, 404 unknown tool, 500
otherwise) — so for `src/lib/tonality/bridge.ts` it really is a **base-URL +
path change** (`POST /call/<tool>` with a JSON kwargs body; `GET /tools`
introspects live signatures, so new tools — `next_chord` #39, the groove pair —
appear automatically with **no client change**). It binds loopback
`127.0.0.1:8012` by default. Recommend you plan the swap; ping us if any tool's
kwargs shape surprises the client and we'll align.

## Summary of dispositions

| # | Finding | Verdict | Where |
|---|---|---|---|
| — | Validation milestone | ✅ recorded | ROADMAP A6 |
| A | Micro-segmentation = performed-timing contract | 📖 (no change) + new recipe | INTEGRATION "Choosing a coalesce window" |
| A.Q1 | Default window | ✋ caller's call; 0.25–0.5 beat principle | INTEGRATION recipe |
| A.Q2 | Bridge default window | consumer's call; affirmed w/ 2 caveats | — |
| B | Relative-minor tilt | 📖 documented → 🕳 motivating case | ROADMAP 3.5a (DFT refinement) + A6 |
| C.Q1 | Which knob | both + a duration floor; ✋ | response (here) |
| C.Q2 | `0.03` gate | ✋ threshold is yours; we set principle only | INTEGRATION margin recipe |
| C | Micro-bands | 🕳 motivating case | ROADMAP 3.5b (hysteresis) + A6 |
| D | 76 s sustain | ✅ faithful, no change | — |
| — | Bridge migration | ✅ yes, migrate (same envelope) | A6 |

— Tonality
