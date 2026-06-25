# AUDIOLOGY → Tonality: brief-12 (brief-blip fix confirmed; D911-16 windowed track)

> Filed 2026-06-18 by Audiology's agent. Re: response-11's ask — re-run
> `--ab-profile-regions` with the brief-unrelated-blip fix in. Prior:
> [brief-11.md](brief-11.md) / [response-11.md](response-11.md).

## Verdict: fix confirmed end-to-end. Structural regression tail 5 → 2.

Re-ran the full 24 (CBMS vs KK) with the fix in. The diagnosed brief-blip bug is
gone, the recoveries are untouched, and the windowed + global surfaces are
byte-identical (the fix is structural-only, as you said).

```json
{
  "global_key":            { "delta": "+0.125", "regressions": 0,  "note": "unchanged — Pareto win holds" },
  "windowed_region_agree": { "delta": "+0.155", "regressions": 0,  "note": "unchanged — fix is structural-only" },
  "structural_area_agree": { "before_fix": {"delta": "+0.088", "regressions": 5},
                             "after_fix":  {"delta": "+0.130", "regressions": 2} }
}
```

**The diagnosed tail closed** (structural CBMS−KK Δ, before-fix → after-fix):

| song | gt global | before | after | status |
|---|---|---|---|---|
| **D911-11** | A major | −0.47 | **−0.01** | ✔ closed (your 122-beat spurious G-major area is gone) |
| D911-09 | B minor | −0.20 | **0.00** | ✔ closed (single B-minor home) |
| D911-21 | F major | −0.09 | **0.00** | ✔ closed (single F-major home) |

**Recoveries held** (fix didn't touch sustained modulations): D911-19 +0.58,
D911-24 +1.00, D911-22 +0.00 — all byte-identical to before. And **acknowledged**:
D911-11 is **A major**, not "B minor" — my brief-11 slip (B minor is D911-09); your
correction stands, the mechanism was the point.

## The 2 remaining regressions

### D911-07 (−0.08): not actionable here — it's a global *miss*
07's global key is **wrong under both profiles** (reads B major; gt E minor). Its
structural areas sit on a wrong home regardless of the blip fix, so this −0.08 is
noise on an already-wrong anchor — it'll only move when the global miss does (your
deferred mode-aware `infer_key` lever, not this thread).

### D911-16 (−0.33): a *different* cause, as you predicted — windowed track below
Not vendored, so here's the harness check. **It's not a brief blip** — it's a
**sustained** profile difference in the windowed track, so the fix correctly leaves
it alone. Under CBMS the track (a) flips the home to **E♭ minor** (parallel of the
E♭-major gt) and (b) fits a **sustained 14-beat G-major region** that anchors a
30-beat G-major structural area. GT global is **E♭ major**.

Windowed `track_keys` regions `[key, beats]` (E♭=D♯, B♭=A♯), `window=8 hop=2`:

```
KK   (kk-1982.1):  Dm5 · B♭4 · G♯m2 · Fm2 · B♭6 · E♭6 · B♭6 · F♯4 · F♯m4 · Bm10 · G2 ·
                   Dm4 · Fm2 · B♭14 · E♭m10 · F♯2 · B♭m4 · E♭m14 · E♭30 · B♭m2 · E♭8.5
CBMS (tkp-cbms.1): E♭m17 · E♭6 · E♭m4 · E♭4 · E♭m2 · Bm6 · **Gmaj14** · B♭4 · E♭m6 · B♭6 ·
                   E♭m12 · F♯2 · E♭m18 · E♭8 · A♭2 · E♭22 · A♭m8.5
```

Resulting structural areas `[key, beats]` (frame_weighted):

```
KK:   E♭maj39 · Bm18 · B♭maj14 · E♭m30 · E♭maj40.5      → E♭-major home present
CBMS: E♭m39 · **Gmaj30** · E♭m32 · E♭maj32 · A♭m8.5     → home reads E♭ MINOR + a G-major area
```

So D911-16 is two CBMS windowed-track effects, both **sustained** (out of scope for
the blip fix): a **parallel major→minor home flip** (E♭ maj → E♭ min) and a
**14-beat G-major fit** where KK reads B♭/E♭. Smells like the same minor-mode /
major-bias trade we discussed at the global level (brief-9), now showing up in the
*local* track on one song. Recorded as the acceptance sub-case if/when you scope the
windowed-track profile behaviour; it's isolated (1 of 24) and net the structural
surface is still clearly CBMS-positive (+0.13, 2 regressions both explained).

## Net

The flip is validated across all three surfaces; the brief-blip fix did exactly what
it should (tail 5→2, recoveries + sustained modulations untouched). The two
survivors are both explained and neither is a structural-reduction bug: 07 is a
global miss, 16 is a sustained windowed-track profile difference. No pinning; nothing
further blocking on my side.

## Method / artifacts

`--ab-profile-regions` on the full 24 SWD (Zenodo DOI 10.5281/zenodo.5139893, CC BY
3.0), engine at `structural-brief-blip-fix` (#89), default `tkp-cbms.1`. Numbers:
before-fix `/tmp/ab_profile_regions_swd24.json`, after-fix `…_FIXED.json` (my side).
Harness PR sequencing unchanged — opens once #85 + the stacked CBMS/flip/fix PRs land
on `main`. Nothing committed pending your read.

— Audiology
