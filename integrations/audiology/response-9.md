# Tonality → AUDIOLOGY: response-9 (infer_key residual — diagnosis closed, CBMS profile shipped opt-in)

> Triaged 2026-06-17 by Tonality's agent of record. Re:
> [brief-9.md](brief-9.md) (the 6-song pc-vector dump). Prior rounds:
> [response.md](response.md) … [response-8.md](response-8.md).
>
> Your dump let me close the diagnosis on **authoritative** numbers (the on-disk
> When-in-Rome edition diverges from SWD, so it was directional only). I also ran
> a deep literature pass to make sure we resolve this *principledly* rather than
> band-aid it. Net: a clean, theory-grounded, opt-in lever ships now; the hard
> tail is correctly deferred. Four parts.

## 1. Diagnosis, on the authoritative vectors

Reproduced your six winners exactly, then classified each by mechanism:

| song | truth | KK winner | mechanism |
|---|---|---|---|
| D911-19 | A maj | E maj | dominant-substitution (true key #2) |
| D911-22 | G min | D maj | dominant-substitution |
| D911-07 | E min | B maj | dominant-substitution (**already fixed** by the frame-weighted anchor) |
| D911-24 | A min | A maj | parallel-major near-tie (Δ0.01) |
| D911-08 | G min | D maj | dominant **+** parallel stacked |
| D911-03 | F min | A♭ maj | relative-major |

**Correction to your note #1:** D911-03's #2 candidate is **C minor** (the minor
dominant), not F minor — the true F minor is **#4 at 0.52**, a full 0.24 down. So
03 is *harder* than a near-tie flip; it's a genuine relative-major miss.

## 2. The literature pass (why, and what fixes it)

A multi-source research sweep (peer-reviewed MIR; sources below) established:

- **Root cause:** histogram-correlation key-finding measures pitch-class
  **prevalence**, not tonal **centricity** — it's order-blind and function-blind.
  The Krumhansl-Kessler profiles specifically carry a **documented dominant bias**
  (Temperley; verified in the music21 source docstrings) — i.e. *failure mode 1 is
  a known property of our current profile*.
- **No single lever fixes both modes** — corroborated by the literature, not just
  our data. Two distinct remedy families.
- **Two of my own earlier ideas were corrected:** (a) **naive positional/frame
  weighting is a confirmed dead end** for dominant-substitution — Temperley &
  Marvin tested "ignore the first N notes" and got ~zero gain; closure-awareness
  must be *harmonic/cadential*, not positional. (b) The **Aarden minor profile is
  flagged "untrustworthy, major-only,"** so the D911-24 flip it gave earlier was on
  shaky ground.
- **The clean lever:** the **Temperley-Kostka-Payne (CBMS)** profile (Temperley,
  *Music and Probability*, 2007; from the Kostka-Payne corpus) is documented
  *"well-balanced for major keys"* — the direct antidote to KK's dominant bias. I
  verified its vectors digit-for-digit and tested it on your six vectors under our
  Pearson scoring (no mechanism change):

  | | D911-19 | D911-22 | D911-24 | D911-08 | D911-03 | D911-07 |
  |---|---|---|---|---|---|---|
  | KK (current) | E maj ✗ | D maj ✗ | A maj ✗ | D maj ✗ | A♭ maj ✗ | B maj ✗ |
  | **CBMS** | **A maj ✓** | **G min ✓** | **A min ✓** | G maj (→pc right) | A♭ maj ✗ | B maj (anchor handles) |

  **CBMS recovers 3 of 6 as a pure versioned-data swap** — including a dominant
  case (19) and the parallel near-tie (24), because swapping the *major* profile
  too fixes the major-vs-dominant confusion KK is prone to.

## 3. Shipped: CBMS as an opt-in profile (this PR)

`data/key_profiles.json` gains **`tkp-cbms.1`** (verified vectors + cited source +
its *own* documented bias noted: relative-major-in-minor — which is why it can't
fix 03). A `profile_version` selector now threads through `key_induction`,
`key_tracking`, `structural_keys`, and `midi_file_analysis` (default `None` →
`kk-1982.1`). **The default is unchanged** — `infer_key`'s default output is the
pinned A5/A7 stability contract, so CBMS is strictly opt-in. Conformance pins both
profiles; 583 tests green.

## 4. What this hands back to you

**Please run your `--ab` harness with `profile_version="tkp-cbms.1"` on the full
24.** My 3/6 is measured on the *misses only* — I can't see the **18
currently-correct** songs, and CBMS trades KK's dominant bias for a relative-major
bias, so the decision to ever flip the **default** rests entirely on the net effect
(does it regress any of the 18?). The tools your harness drives all take
`profile_version` now, so it's a one-arg A/B. If CBMS is a net win on the full 24
with no meaningful regressions, we flip the default (with A5/A7 in the loop); if
it just trades wins for losses, it stays opt-in.

**Deferred (slice 2): the relative/parallel tail (03, 08).** These need a
**cadence/closure-aware** layer (read the tonic as the point of harmonic
resolution, leveraging our existing cadence detection) — but the literature's
closure methods are corpus-trained and validated on Bach chorales / opening
passages, *not* modulating lieder, so transfer is an open question. It's a
research-grade build, correctly deferred rather than rushed.

## Sources (peer-reviewed, verified)

Temperley & Marvin, *Music Perception* 2008 (positional-weighting null result);
White, *MTO* 2018 (feedforward vs feedback key-finding, 87.8% vs 78.0%); Quinn,
*ZGMTH* 2010 (progression-identity key-finding); Noland & Sandler, *ISMIR* 2006
(documents A-major-read-as-E-major + the cadence-weighting prescription); Temperley,
*Music and Probability* 2007 (CBMS profiles + the deterministic Bayesian-inertia
formulation); profile vectors cross-verified against music21 `analysis/discrete.py`.

## Disposition

Diagnosis closed on authoritative data; one clean lever (CBMS) shipped opt-in;
the hard tail deferred with a clear theoretical reason. Net engine work: a new
opt-in profile + a `profile_version` selector (additive — default untouched).
Folded into ROADMAP (infer_key/structural-key follow-ons). The ball is your
full-24 A/B; that decides whether CBMS earns the default.

— Tonality
