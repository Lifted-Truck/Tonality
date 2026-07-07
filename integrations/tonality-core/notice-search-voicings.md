# NOTICE — Tonality → tonality-core: `search_voicings` landed (promised follow-up to notice-search-layer)

> 2026-07-07, dev loop. notice-search-layer.md promised "you'll get a notice
> when search_voicings lands" — this is it. Your `refresh_fixtures.sh --check`
> will report `conformance.json` drift against current main: **one new,
> purely-additive tool case** (`search_voicings`, +155/-0). The set-class
> export table and every pinned case are byte-identical; `port/pin.json`
> unmoved, `test_port_pin.py` green. **Action: re-baseline `--check`; nothing
> else.**

## Port-relevant shape (for when you take the `search/` slice)

`mts/search/voicings.py` — the first `search/` piece that leaves pure mask
space. Still fully port-friendly:

- **Deterministic, no RNG, no wall-clock.** Output order is total: with a
  `from_voicing` reference, `(vl_from, spread, midi)`; without, `(spread,
  midi)`. A conformant engine must reproduce the ordering, not just the set.
- **Bounded by construction:** raw space = ∏ per-pc candidate counts in the
  required `register` window, computed *before* enumeration; > 200_000 raises
  (constant `_MAX_RAW_SPACE` — pin it if you vendor fixtures). `count` is
  always the true match total; `truncated` refers only to `limit`.
- **Dependencies:** `voice_leading_realized` (`doubling.1` — bijection +
  two-sided surjection over sorted MIDI; already spec'd by the existing
  goldens), the `voicing_shapes` fingerprint registry (labels are exact
  root-position spacing matches in slice 1; inversions label as null), and the
  same `Condition` predicate as identity search (one new value kind: `str`,
  with a closed label vocabulary).
- **Semantics to reproduce exactly:** `register` inclusive both ends;
  `no_interval_over_bass` is directed pc-intervals (1..11, mod-12) above the
  lowest voice; each pc voiced exactly once (slice 1); `root=None` → template
  search (no shape labels); `center` = mean MIDI (float).

The new conformance case (Cmaj9, C3–C6, spread ≤ 19, no ♭9-over-bass,
`from_voicing` + ceiling, limit 10) exercises ranking, labeling, and the echo
block in one row — a good single fixture when you vendor. No response needed.
