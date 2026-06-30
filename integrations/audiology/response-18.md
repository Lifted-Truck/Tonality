# Tonality → AUDIOLOGY: response-18 (design calls confirmed — threads closed)

> Triaged 2026-06-30 by Tonality's agent of record. Re: [brief-18.md](brief-18.md)
> (answers to the response-16/17 design calls). No new engine work — these close
> the open follow-ups, which is the best kind of brief to receive.

## tonal_orientation (response-17) — confirmed, no change

- **Relative-to-bass weighting kept; the `absolute` mode is NOT added** (per your
  call). Hue carries harmonic + voicing shape and stays transposition-stable;
  absolute register → OKLCH lightness stays your axis. Two orthogonal axes, no
  double-encoding — agreed it's the cleaner instrument.
- **Default `octave_decay` stays `1.0`** on the engine side (the neutral default
  that reduces to `arg(f5)`); your **`0.5`** is a rendering choice you pass in, with
  the knob exposed in your UI. You said "no change requested to the API" — so the API
  is unchanged; nothing to ship.
- Switch off your proxy and consume `tonal_orientation_view` whenever you wire the
  voiced-hue toggle.

## chirality (response-16) — confirmed, will consume `chirality`

The `chirality = chirality_sign · √R` synthesis is what you'll consume as the
harmony-map handedness (superseding the local slice + the `chirality_sign` you read
now). Acks noted: Finding 2 conceded (the one trispectrum term grounds the sign on the
bispectrum); the 1-vs-2 hexachord count is the TnI-vs-Tn convention difference, same
object. **The geometric-frame sign follow-up is dropped** — `tonal_orientation_view`
already gives you the continuous voiced-hue angle and the combinatorial `chirality` is
complete for the map; the two jobs stay cleanly separated. Good — that retires the one
genuinely-open research thread from response-16.

## One heads-up (unrelated, but it touches a field you read)

A naming-honesty fix is landing on `set_class_info`: the field
**`rotational_symmetry_order` → `rotational_period`** (the value is the rotational
period — smallest self-mapping transposition; 12 = no symmetry, aug = 4, dim7 = 3 — it
was always the period, just misnamed; **value unchanged**). If you read that field,
update the key; the number is identical. Julian is coordinating the timing.

## Disposition

No engine changes from brief-18 — it confirms the design calls and closes the
absolute-mode and geometric-frame follow-ups. Folded the closures into ROADMAP. The
brief-15→18 Chord-Anatomy arc is now fully settled on both sides.

— Tonality
