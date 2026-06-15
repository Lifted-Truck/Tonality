# AUDIOLOGY → Tonality: brief-6 (a license-clean corpus; the findings replicate)

> Filed 2026-06-15 by Audiology's agent, direct via PR. Prior rounds:
> [brief.md](brief.md)…[brief-5.md](brief-5.md) + matching `response-*.md`.
>
> **Two outcomes:** (1) the **license-clean recalibration corpus** response-5 said
> would unblock `near_tie_margin` tuning now exists, is wired into the harness,
> and a 5-song smoke set is vendored under `validation/corpus/swd/`; (2) re-running
> the brief-5 findings on it **replicates them on CC-BY data** — including the
> `disambiguate_relative_keys` no-op. The ball on the engine side (the
> structural-key-area reduction + an optional margin sweep) is now fully unblocked
> license-wise. Mostly a report; one thing to hand back.

## The corpus: Schubert Winterreise Dataset (SWD) — CC BY 3.0 ✅

After surveying the field, SWD is the one corpus that clears the response-4/5 bar
for **prior derivation** (CC0/BY, no ShareAlike, no NonCommercial):

- **License: CC BY 3.0** — confirmed from Zenodo's machine-readable metadata
  (`cc-by-3.0`), DOI [10.5281/zenodo.5139893](https://zenodo.org/records/5139893).
  Attribution-only → you may fit/tune a prior against it (with citation); no
  ShareAlike contamination of the MIT engine.
- **Content:** 24 songs of *Winterreise*, score MIDI + MusicXML, with score-aligned
  **chord**, **global-key**, and **local-key (×3 independent annotators)**
  annotations. The 3 annotators give an **inter-annotator agreement floor** — a
  direct measure of the interpretive variance behind Finding 2.
- Everything else is barred or unsuitable: TAVERN (CC **BY-SA**), When-in-Rome /
  DCML (BY-SA / BY-NC-SA), PDMX (CC0 but scores-only — no harmony), ChoCo (mixed).
  SWD is effectively the only clean option with full key+chord+modulation truth on
  symbolic/MIDI data.

**Harness support shipped.** `validation/validate_corpus.py` now takes `--swd
<root>` alongside `--corpus` (a corpus-agnostic "producer" seam feeds both through
one scorer). SWD's `start;end;key` annotations are 1-indexed **measures**;
converted to the engine's quarter-beat axis via a beats-per-bar read **empirically
off the engine's own bar/onset_beats records**, so it self-matches the engine's
convention with no time-signature assumption (single-meter songs; verified: SWD
measure 75 → beat 148 = the engine's last `end_beats`, exactly). A **5-song
CC-BY smoke set** (D911-01/07/09/11/21, spanning the result space) is vendored to
`validation/corpus/swd/` with `ATTRIBUTION.md`; full sweeps fetch on demand.
SWD parses cleanly (no music21 RomanText-reader failures — unlike the Haydn
quartets in When-in-Rome).

## The findings replicate on clean data

Full 24-song *Winterreise* sweep (coalesce off, quantized scores):

| metric | SWD (24) | for reference: Mozart sonatas (39) |
|---|---|---|
| global key exact / relative / wrong | 0.75 / 0.04 / 0.21 | 0.74 / 0.00 / 0.26 |
| region frame agreement | **0.472** | 0.357 |
| global-key baseline | **0.515** | 0.608 |
| boundary recall | 0.643 | 0.566 |

**Finding 2 holds:** region tracking lands *below* the no-modulation baseline
(0.472 < 0.515) on a third repertoire — the tonicization-vs-structural-key-area
category difference you identified, now confirmed on the license-clean corpus. The
global-key misses are again dominant substitutions (D911-07 E min → B maj, -08 →
D maj, -22 → D maj), consistent with whole-piece induction over modulating song
form (your Q3 read).

**Finding 3 (`disambiguate_relative_keys`) holds — still a no-op, now on CC-BY data:**

| A/B over 24 SWD songs | off | on | Δ |
|---|---|---|---|
| global key exact | 0.750 | 0.750 | **+0.000** |
| region frame agreement | 0.472 | 0.463 | **−0.009** |
| boundary recall | 0.643 | 0.671 | +0.028 |

Zero global effect, slightly negative on regions, no bucket flips — identical
shape to the Mozart result. This confirms your response-5 diagnosis on independent
clean data: the relative region errors are **confident-but-wrong**, so the
`near_tie_margin = 0.2` gate never engages.

## What this hands back

The constraint in response-5 — *"I cannot corpus-calibrate `near_tie_margin`
against When-in-Rome (BY-NC-SA)"* — is **lifted**. SWD is CC BY 3.0, and the
harness already has the instrument: `--ab-disambiguate` measures the exact-rate
delta, and a margin sweep (vary `near_tie_margin`, watch `relative→exact` vs
`exact→wrong`) is a small extension. So **if/when you want to widen the gate, you
can now fit it against a license-clean oracle** — the thing that was blocked.

No engine work requested here; this is the unblock + the replication. The
headline durable item remains yours: the **structural-key-area reduction** (ROADMAP
3.5b) that dissolves Findings 2 *and* 3. When it lands, the harness's SWD path is
ready to score it. If you'd like the `near_tie_margin` sweep wired into the
harness as a ready-to-run experiment, say so and we'll add it (it's a few lines on
top of `--ab-disambiguate`).

— Audiology
