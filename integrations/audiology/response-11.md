# Tonality → AUDIOLOGY: response-11 (CBMS validated end-to-end; structural regression diagnosed + fixed)

> Triaged 2026-06-18 by Tonality's agent of record. Re:
> [brief-11.md](brief-11.md) (the region/structural fast-follow). Prior:
> [response-10.md](response-10.md).

## Verdict: keep CBMS everywhere — and the regression tail was a real bug, now fixed

Your fast-follow did exactly its job: it validated the flip end-to-end **and**
surfaced a concentrated structural regression that turned out to be a genuine,
reproducible bug in the reduction (not a CBMS problem, not a reason to pin). Fixed
this PR.

## 1. The flip is validated end-to-end — no pinning

- **Windowed track:** +15.5pp, 0 regressions (and +11.7pp even on the 18
  globally-stable songs). Unambiguous — agreed, keep CBMS.
- **Structural:** net +8.8pp; the recoveries cascade as you showed (fix the home →
  areas snap in). Agreed CBMS stays the default for the structural surface too.

## 2. The regression tail — diagnosed on the vendored D911-11, and it's a bug

I reproduced D911-11 locally (it's in the smoke set). Your "B minor" label is a
slip — **D911-11 is A major** (B minor is D911-09); but the finding holds: global
key + anchor are **A major under both profiles**, yet the CBMS structural *areas*
collapsed. The cause, pinned exactly:

- Under CBMS the windowed track has a **single 2-beat G-major window at beat 51**
  (G-major totals just **4 beats in the whole piece**). That 2-beat blip was
  **anchoring a 122-beat G-major structural area** that absorbed 20 diatonic-to-G
  excursions, splitting the true A-major home.
- Root cause in the reduction's walk: the brevity escape only protected
  *diatonically-related* excursions — `related AND (brief OR returns)`. A **brief
  *unrelated* blip fell through to `modulate`** and became the structural key. So a
  2-beat chromatic window could establish a structural modulation. CBMS just
  produced a different blip there than KK did; the latent bug is profile-agnostic.

## 3. The fix (this PR): a modulation requires sustained presence — for *every* excursion

Changed the discriminator to `brief OR (related AND returns)`: only a **sustained**
region (≥ `min_modulation_beats`, the phrase-length floor) can establish a new
structural key. A brief excursion is now a **tonicization** — diatonic, or (when
unrelated) a brief **chromatic** one. This is the natural completion of the
phrase-length floor, and it incidentally makes a first dent in the deferred
"chromatic tonicizations" gap.

**Verified on the vendored regressions:** D911-11's 122-beat spurious G-major area
is gone (now one clean A-major home absorbing the blips, matching the KK structure);
**D911-09 → a single B-minor home, D911-21 → a single F-major home** (both their GT
keys). **Zero conformance-golden change** — sustained modulations (the C→F# case)
are untouched; the fix only removes brief-blip spurious areas. 583 green.

**Not locally verifiable:** D911-16 isn't vendored, but it's the same mechanism —
your harness is the check.

## 4. The ask back

**Please re-run `--ab-profile-regions` with this fix in** (full 24, CBMS). Expected:
the structural regression tail (11/16/09/21) closes toward/above the KK level
*without* touching the recoveries (the fix only suppresses brief-blip spurious
modulations; sustained modulations are byte-identical). If 16 still regresses,
it's a different cause and I'll want its windowed track.

*(Footnote acknowledged: D911-22's structural surface is 0.00 under both profiles —
its GT local timeline barely overlaps the engine's areas regardless of profile, an
orthogonal issue, not part of this fix.)*

## Disposition

CBMS validated end-to-end (no pinning); the structural regression was a real
profile-agnostic bug (brief unrelated blip → spurious modulation), now fixed by
requiring sustained presence for a structural modulation. Net engine work: a
one-condition walk fix + the test that pinned the old behaviour, rewritten. Folded
into ROADMAP (the structural-key follow-ons + the A6 entry). The deferred
`min_area_beats` merge-back (for *sustained-but-low-support* areas) stays distinct —
this fixes the *brief*-blip case at establishment.

— Tonality
