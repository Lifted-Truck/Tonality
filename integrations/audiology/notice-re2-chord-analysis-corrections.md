# NOTICE — Tonality → Audiology: `chord_analysis` corrections (RE-2, 2026-07-03)

> From the rigor & efficiency review (ROADMAP "Standing review — rigor &
> efficiency", RE-2): three wrong-output fixes + one removed field on the
> `chord_analysis` tool, and one input-handling fix on `colour_content`.
> All verified by execution before and after. Conformance goldens regenerated
> in the same PR.

## What changed

1. **`inversions[].figured_bass` is now gated on tertian-ness** (stacked
   thirds), not cardinality alone. Non-tertian chords (maj6, add9, sus…) now
   report `figured_bass: null` instead of a **wrong** figure — a C6 in root
   position used to claim `"7"` (a seventh-chord figure), sus4 claimed
   `"5/3"`. Tertian triads/sevenths are unchanged. If you displayed figures,
   expect `null` where the figure was previously fabricated.

2. **`interval_summary` is now root-relative (transposition-invariant).** It
   was computed from absolute pcs, so the same chord shape reported different
   `span_semitones` / `interval_pairs` at different roots (C maj span 7,
   A maj span 8 — invented register inside a pure-identity analysis, a
   cardinal-rule violation). Now every root reports the shape's own summary.
   **C-rooted chords are byte-identical**; other roots change to the correct
   (C-equivalent) values.

3. **`inverted_interval_class_histogram` is removed.** The interval matrix is
   symmetric under negation mod 12, so this field was provably always
   identical to `interval_class_histogram` — it carried no information and
   never could. Read `interval_class_histogram`; `inverted_interval_matrix`
   (which is not redundant in the same way) stays.

4. **`colour_content` (engine-side `colour_content_descriptor`) input fix:**
   the pcs iterable was consumed twice, so a *generator* argument silently
   produced an all-zero interval vector beside correct mask fields. List/set
   inputs (the MCP path) were always correct — no output change for you;
   recorded for completeness.

## Action

Only if you consume the affected fields: drop any read of
`inverted_interval_class_histogram`, treat `figured_bass: null` as "no
conventional figure exists", and re-pin any cached `interval_summary` values
for non-C roots. No API/signature changes; no action needed otherwise.
