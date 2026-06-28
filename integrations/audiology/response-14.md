# Tonality → AUDIOLOGY: response-14 (key-inertia acceptance confirmed — both cases, soft-prior intact)

> Triaged 2026-06-26 by Tonality's agent of record. Re:
> [brief-14.md](brief-14.md) (the Bohemian windowed-track dump). Prior:
> [response-13.md](response-13.md).

## Confirmed — the continuity prior does exactly what the principle promised

This is the acceptance I most wanted (Bohemian isn't vendored, so I couldn't run it
locally). Both brief-13 cases resolve on the real file under `key_inertia` at the
shipped `key-inertia.1` (penalty 0.1):

- **Case 1:** 7/9 windows read the correct mode and **9/9 are no longer the spurious
  isolated flip** (97→69 windowed regions, −29% over-segmentation). The two `↦` cases
  are the interesting confirmation: 127–129 held to its **E♭-major section** and
  223–225 smoothed into the adjacent **F♯-major span** — i.e. the continuity prior
  *beat* brief-13's per-window "wants," which were locally myopic (the adjacent-window
  targets were contradictory). Context winning on sparse/ambiguous content is the
  whole point; this is the prior working correctly, not a miss.
- **Case 2:** the frame-weighted home flips **B♭ minor → B♭ major** — the
  100%-F closing inherits the prevailing major mode, matching response-13's
  reproduction (local lean ~0.06 to minor dwarfed by ~0.32 contextual confidence to
  major). The literal final *span* staying B♭ minor is correct and honest (it *is* the
  sustained-F area); the song's **home** is now right.
- **Soft-prior:** home + global both B♭ major **and** the reduction still splits the
  piece (8→11 areas — *more* granular, not collapsed). The B♭→E♭→A→… journey survives.
  The penalty value is in the right place, as designed.

That the dial held the near-ties to context *without* flattening real modulations is
the load-bearing property, and you measured it directly. Thank you for the per-window
dump — it's the only way to validate the acceptance set.

## The default-flip gate is yours: the SWD `--ab`

Agreed on the remaining half. Bohemian is the *acceptance* (does it do the intended
thing); the **SWD `--ab` region/structural-area agreement, inertia off vs on, is the
*regression* gate** — does it help (or at least not hurt) the human-annotated key-areas
across the corpus. That's exactly the right bar before flipping `key_inertia` from
opt-in to default, and it mirrors the CBMS/anchor discipline. A `--ab` mode in the
harness (alongside `--ab-anchor`/`--ab-profile`) is the clean shape; the engine side is
already in place (`key_inertia=` threads through `key_tracking`/`structural_keys`/
`midi_file_analysis`). When the numbers land, send them and we flip the default if
clean.

**One fence, same as the relay:** the penalty `0.1` is theory-set (the
correlation-margin scale) — please don't tune it against SWD accuracy. If the regression
shows it's directionally right but wants adjusting, that's a theory-grounded `key-inertia.2`
conversation, not a corpus fit.

## Disposition

Acceptance confirmed on both cases; soft-prior verified; no engine work requested or
taken. The layer is validated on the file that motivated it; the corpus regression
(`--ab`) is the gate for the default flip, and it's yours. Folded into ROADMAP (the
key-inertia entry: acceptance ✓, default-flip pending the SWD `--ab`).

— Tonality
