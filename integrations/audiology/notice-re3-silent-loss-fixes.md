# NOTICE — Tonality → Audiology: RE-3 silent-loss fixes touching your surfaces (2026-07-04)

> From the rigor & efficiency review (ROADMAP RE-3, "itemize losses, never
> guess"). Four changes reach tools you consume; the rest of the workstream is
> internal. Full record in ROADMAP's RE-3 entry.

## What changed on your surfaces

1. **`rotational_steps` no longer emits the `(12,)` sentinel.** An asymmetric
   set's `symmetry.rotational_steps` is now `[]` (was `[12]` — a false
   symmetry claim: every set maps to itself at 12, so listing it only for
   asymmetric sets asserted the opposite of what it meant).
   `rotational_period` is unchanged (12 still means asymmetric there — it's a
   period, not a step list). Affects `chord_analysis` / `scale_analysis`
   symmetry blocks. If you branch on `rotational_steps`, treat empty as "no
   nontrivial rotational symmetry".

2. **`key_inertia` + `disambiguate_relative` now errors instead of silently
   dropping the tie-break.** The inertia path re-decodes from raw score
   vectors, so the per-window relative-key tie-break never reached it — the
   combination looked accepted but the disambiguation did nothing. If you set
   both (brief-13 era calls), pick one; the error message explains. Also:
   region `mean_score`/`mean_margin` are now measured against the region's
   **own** label — unchanged for default (raw-argmax) tracking; a region that
   inertia/smoothing/disambiguation relabeled now reports an honestly
   negative margin where the raw correlation disagreed (that's your gating
   signal telling the truth).

3. **`midi_file_analysis` and `piano_roll_view` gain `midi_read_losses`**
   (always present, usually `[]`): re-struck notes are now *kept* (closed at
   the re-strike, truncation itemized); dangling note-ons and zero-length
   pairs are dropped **and itemized** instead of vanishing. A rectangle that
   never appears is now explained.

4. **`apply_groove`'s `voice` parameter works now** (it was accepted,
   documented, and ignored): only the named part is transformed; the result
   cites the applied `voice`. If you passed `voice` expecting whole-sequence
   behavior, drop the argument.

## Action

Re-pin any cached symmetry blocks (`rotational_steps` `[12]` → `[]`); check
whether any of your `key_regions` calls set both `key_inertia` and
`disambiguate_relative_keys`; otherwise additive.
