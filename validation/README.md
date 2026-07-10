# validation/ — corpus accuracy harness

Quantitative, repeatable validation of the engine against **human-annotated**
harmonic ground truth — the instrument that turns the brief-3 N=1 hand-check
(Audiology, *Bohemian Rhapsody*) into an accuracy number you can A/B across
engine changes. Drafted by Audiology (brief-4); adopted as a Tonality-owned
asset (response-4). This directory is the home for that harness.

It is **not** part of the dev test suite. `pytest tests/` (the Stop hook) stays
dependency-light and green; this harness needs **music21** (heavy), which is an
**optional dev/test extra** — `pip install 'mts[validation]'` — never a runtime
dependency. A thin skip-if-absent smoke test in `tests/`
(`pytest.importorskip("music21")`) runs it over the vendored subset for CI; the
heavy logic lives here. (Same shape as the optional `mcp` extra.)

## Contract of record (response-4 rulings)

The harness measures inferred-key + key-region accuracy against ground truth.
The comparison contract — encoded as defaults, frozen here so it doesn't drift:

- **Key canonicalization:** every key reduces to `(tonic_pc, mode ∈ {major,
  minor})`. This is the engine's output space (`kk-1982.1` is major+minor only;
  modal material reads as its relative major/minor by design). Modal annotations
  reduce to the relative major/minor of their collection and the passage is
  **flagged modal** (not charged as an engine miss). Modal key profiles are a
  deferred engine extension.
- **Region metric of record:** **frame agreement** (% of 0.25 s frames whose
  engine local key matches ground truth) — holistic and boundary-fuzziness-
  tolerant, matching that engine region boundaries sit on the window/hop grid,
  not sample-exact. A ±X-second **boundary-tolerance** metric is reported
  *alongside* as secondary (it measures change-point accuracy — the instrument
  for the future local-meter / change-point work).
- **Relative major/minor:** scored into three buckets — `exact`, `relative`
  (right diatonic collection, wrong member), `wrong`. **Never collapsed.** The
  headline for Finding B is the **exact-rate delta with vs without
  `--disambiguate`** (`disambiguate_relative_keys`): the tie-breaker earns its
  place iff it converts `relative → exact` without regressing `exact → wrong`.
- **Temporal comparison axis: beats, not seconds.** Engine regions/placements
  carry beats alongside seconds, and RomanText offsets are quarterLengths
  (beats). Comparing in beats removes tempo conversion from both sides → exact
  alignment, no multi-tempo caveat. (The engine itself is multi-tempo and
  multi-meter correct — it builds a piecewise `TempoMap`/`MeterMap` from every
  `set_tempo`/`time_signature`.) Seconds are for human-readable output only.

## Corpus

Primary: **When-in-Rome** (RomanText analyses + scores). Cross-check: **BPS-FH**
(Beethoven, note events with MIDI numbers + labels). The committed **smoke set**
(~10 pieces, fetched into `validation/corpus/`) is the deterministic CI fixture;
full sweeps fetch on demand.

**Licensing (load-bearing):** the *scores* are public-domain works (Bach,
Mozart, Beethoven, Chopin); only the RomanText *annotations* are **CC BY-SA**.
Vendor the PD scores freely; keep the BY-SA annotation files under
`validation/corpus/<piece>/` with `ATTRIBUTION`/`LICENSE` (per-folder check). The
annotations may be **read by the harness to score, never derived into an engine
prior or shipped data asset** — ShareAlike would otherwise contaminate the MIT
engine (the same rule that ruled out DCML's BY-NC-SA corpora for gap-14 priors).

See ROADMAP **A6** and integrations/audiology/response-4.md for the full triage.
Phase 2 (chord-level scoring against per-beat Roman numerals) is recorded as a
separate round.

## Corpus exercise harness — rulesets + patterns (added 2026-07-09)

`exercise_rules_patterns.py` runs the whole Phase 4.6 stack over a MIDI corpus
directory (default: the vendored SWD smoke set) — per piece: ingest →
`segment_chords` → every named ruleset evaluated (harmony rules fed the
segmented chords+key) → every named pattern matched; corpus level: rule
induction per family (pieces = files), harmony induction over the segmented
chord corpus, and a degree-transition matrix scored on a held-out piece by
cross-entropy (**split by piece** — same music never straddles the split).
Layer-E: measured, non-blocking. The Layer-0 invariants CI can gate (no-crash,
honest refusals, occurrence contract, induced-output validity, determinism)
live in `tests/test_corpus_smoke.py` over the same vendored set.

```bash
.venv/bin/python3.13 validation/exercise_rules_patterns.py [--corpus DIR] [--out report.json]
```

Corpus expansion is license-gated (the standing rule): candidates + the
sign-off live in ROADMAP (Phase 4.6 corpus-exercise entry).
