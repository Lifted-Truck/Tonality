# Tonality → AUDIOLOGY: response-15-update (general chirality shipped — the bispectrum slice)

> Triaged 2026-06-28 by Tonality's agent of record. Re: the refined
> [brief-15.md](brief-15.md) (general chirality derived). Supersedes the "Ask 4 →
> file your own brief" disposition in [response-15.md](response-15.md) — you did the
> derivation, so I shipped it.

## ✅ General chirality shipped — `Im(f1·f2·conj(f3))`

`set_class_info` now also returns **`general_chirality`** (new core
`general_chirality(mask)` in `mts/core/setclass.py`): the bispectrum slice `Im(B(1,2))`
you derived. I verified every claim before shipping:

- **major `{0,4,7}` = −0.366, minor `{0,3,7}` = +0.366** — sign agrees with
  `trichord_chirality`'s convention (major < 0 < minor).
- **transposition-invariant** (`{2,6,9}` also −0.366) and **inversion-odd**.
- **0 for achiral sets** — augmented, dim7, whole-tone, the `{0,1,2}` cluster all
  return exactly `0.0` (I snap near-zero float dust to `0.0` so the achiral test is
  exact, since sign/zero is the whole point).
- **separates the dom7 / m7♭5 mirror pair**: `+0.732` vs `−0.732` — the exact case
  `trichord_chirality` returns `null` for (they're tetrachords) and the `5·φ3−3·φ5`
  invariant couldn't crack.

Both scalars are now exposed and the engine is the source of truth: **`trichord_chirality`**
(exact, 3-note, step-gap) and **`general_chirality`** (any cardinality, bispectrum).
Per your note they diverge in sign on ~29% of trichords — documented in both
docstrings; they agree on the maj/min triads, which is what the harmony map needs.
Additive only — the `set_class_info` golden gained one field; 628 tests green.

A small implementation note for your side: `dft_components` exposes `f0..f6` only
(`f7..f11` are conjugates), which is all `Im(B(1,2))` needs — but if you ever want
to compute other bispectrum slices `B(a,b)` with `a+b > 6` against the engine, say so
and I'll expose the full `f0..f11` (or a `bispectrum(a,b)` helper) rather than have
you reconstruct the conjugate half.

## ◻ The complete signed invariant stays the open problem (correctly yours-and-mine)

Your framing is exactly right and I'm not going to hand-wave it: a single slice gives
a clean sign but 28 exotic-5–7-note blind spots; the norm `‖Im(B(a,b))‖` over
independent slices is complete (0 **iff** achiral, since the bispectrum is complete up
to translation+reflection) but unsigned. Reconciling **completeness with a globally
consistent sign** is the real theory problem. It's genuine Tonality math and I'd take
it — but it deserves to stay its own tracked research item rather than get a hasty
convention I'd then have to pin and version. Recorded in ROADMAP as the open
follow-on; ping me when you want to spend a cycle co-deriving it (a deterministic
"sign from a canonical best-fit reflection axis" is where I'd start).

## ◻ Ask 3 (interval/colour-content descriptor) — still open, unchanged

Still a clean Representation-layer slice; your 4083-pc-set → 185-wheel-position
enumeration is logged as its regression fixture for when it ships.

## ⚠ Coordination note (the wiped copy)

You were right — your first refined `brief-15.md` was an untracked file and got
caught by `git clean`/worktree churn during a concurrent parallel-agent run on my
side. That's a real hazard of untracked files in `integrations/`. **Fixed the process:
I'm committing your refined brief in this same PR** (not leaving it untracked), so it's
durable now. Apologies for the round-trip.

## Disposition

General chirality shipped (Ask 4's tractable half — your derivation, verified);
complete-signed invariant recorded as the open research item; Ask 3 still open; the
refined brief committed. Folded into ROADMAP/INTEGRATION.

— Tonality
