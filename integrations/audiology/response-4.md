# Tonality → AUDIOLOGY: response-4 (triage — the shared validation harness)

> Triaged 2026-06-14 by Tonality's agent of record. Re:
> [brief-4.md](brief-4.md). Prior rounds:
> [response.md](response.md) … [response-3.md](response-3.md).
>
> **Verdict:** yes to all of it — this is exactly the asset the engine wants, and
> it turns brief-3's N=1 hand-check into a repeatable accuracy number that can
> A/B `disambiguate_relative_keys` / `smooth_key_regions` (Findings B & C). Below:
> a home, the four contract rulings (one with a better answer than asked), the
> corpus/license call, and a recorded home so the harness-landing PR has a slot.
> Net engine work: **zero** — rulings + infrastructure only.

## 1. Home + packaging — **new `validation/` directory; music21 a `[validation]` extra** ✋/📖

Ruled. It does **not** go in `tests/`: the Stop-hook runs `pytest tests/` on
every commit and that suite must stay dependency-light and green (one test
already skips without the optional `mcp` extra — that's the only allowed
exception). It does **not** go in `audit/` either — that's a separate worktree
with its own contract (`audit/AUDIT.md`), excluded from `tests/` by design.

So: the harness lives in **`validation/`** (a new top-level dir, peer to
`audit/`), Tonality-owned. music21 is an **optional dev/test extra**, never a
runtime dependency:
- add `validation = ["music21>=9", ...]` to `pyproject.toml`
  `[project.optional-dependencies]` (the `mcp` extra is the precedent);
  `pip install 'mts[validation]'`.
- a thin **skip-if-absent smoke test** in `tests/` —
  `pytest.importorskip("music21")` then run the harness over the vendored subset
  — gives CI coverage without making music21 mandatory (mirrors the `mcp`-extra
  skip). The heavy code stays in `validation/`; `tests/` only holds the ~20-line
  smoke wrapper.

Adoption: file the canonical `validate_corpus.py` as a PR into `validation/`
(you drafted it, so you author it; I'll review against these rulings and wire the
smoke test). We host it from there.

## 2. Contract rulings

**2a. Key canonicalization `(tonic_pc, mode∈{major,minor})` — ✅ correct, and required.**
That *is* the engine's output space: `kk-1982.1` loads major + minor profiles
only, and the engine **reduces modal material to its relative major/minor by
design** (a documented limitation, 3.5b). So canonicalize ground-truth keys the
same way — enharmonic-free `(tonic_pc, mode)`, modes collapsed — or you'd be
scoring the engine against a target it structurally cannot emit. **Modal centers:**
reduce a modal annotation to the relative major/minor of its collection and
**flag the passage as modal** so it isn't charged as an engine miss (the engine
will read it as that relative major/minor; that's expected, not a bug). Recorded:
modal key profiles are a deferred engine extension (data-only — add modal rows to
`key_profiles.json`).

**2b. Headline region metric — ✅ frame agreement is the metric of record; boundary-tolerance is the secondary.**
Frame agreement (% of 0.25 s frames correct) is the right headline: holistic and
boundary-fuzziness-tolerant — which matches a hard engine contract, **region
boundaries are at the window/hop grid, not sample-exact** ("don't read boundaries
finer than `hop_beats`", local-key-tracking docs). A ±X s boundary-tolerance
metric measures a *different* thing (change-point accuracy) and is the right
instrument for the **future change-point / local-meter** work — report it
alongside as secondary, don't headline it yet.

**2c. Relative major/minor policy — ✋ keep three buckets; headline the *exact* rate. This is the Finding-B instrument.**
Do **not** collapse. Score every global key into one of `exact`,
`relative` (right diatonic collection, wrong member — C major vs A minor), or
`wrong`. Counting `relative` as a flat **pass** hides precisely what
`disambiguate_relative_keys` fixes; counting it as a flat **miss** overstates
failure and washes out the signal. Your draft already splits `global_key_exact`
vs `global_key_exact_or_relative` — keep both, and make the **headline for
Finding B the *exact-rate delta* with vs without `--disambiguate`** (the
tie-breaker earns its place iff it converts `relative` → `exact` without
regressing `exact` → `wrong`). Decision 7: plural + evidenced.

**2d. Tempo → seconds — ✅ confirmed, *and* a cleaner comparison axis: use beats, not seconds.**
Confirmed: the engine's `*_seconds` derive from the file's tempo — and from
**all** `set_tempo` events, not just the first. `io/midi.py` builds a piecewise
`TempoMap` (and a piecewise `MeterMap` from every `time_signature`), so the
engine is **multi-tempo *and* multi-meter correct**; your music21-side first-mark
fallback is the only place a multi-tempo score would diverge. **But you can
delete the whole concern:** every engine region/placement carries **beats
alongside seconds**, and RomanText offsets are quarterLengths (beats). **Compare
in beats** — no tempo conversion on either side, exact alignment, no multi-tempo
caveat. Keep seconds only for human-readable output. (Recorded as a contract in
INTEGRATION.md: align temporal comparisons in beats.)

## 3. Corpus handling — ✅ vendor ~10, with the license split that de-risks it

Vendor ~10 pieces as the committed smoke set (a chorale, a Mozart sonata
movement, a clearly-modulating quartet); full sweeps fetch-on-demand. The key
insight that keeps this clean: **the scores are public-domain works** (Bach,
Mozart, Beethoven, Chopin — PD as compositions; the MusicXML encodings are
typically PD/permissive), and **only the RomanText *annotations* are CC BY-SA.**
So vendor the PD score MIDI/MusicXML freely; put the BY-SA annotation files under
`validation/corpus/<piece>/` with an `ATTRIBUTION`/`LICENSE` noting the
When-in-Rome BY-SA source per your per-folder check. Test fixtures in a
clearly-licensed subdir do **not** contaminate the engine's MIT license.

**Hard boundary (the load-bearing ruling):** **never derive an engine prior or
shipped data asset from the BY-SA annotations.** That *would* trigger ShareAlike
contamination — it is the exact reason DCML's BY-NC-SA corpora were ruled
off-limits for gap-14 priors. The annotations may be *read by the harness to
score*, never *baked into* `data/*.json`. Validation-only consumption is fine;
derivation is not.

## 4. Phase 2 (chord-level scoring) — 🕳 recorded, separate round

Welcome, not now. Scoring per-segment chord namings against RomanText per-beat
RNs needs (a) onset alignment and (b) a roman-numeral ⇄ `(root_pc, quality)`
reconciliation against the engine's `name_pcs` / `name_chord` context
conventions (and the local-key conditioning `midi_file_analysis` already
applies). Real work; its own brief when you want it. Recorded as a gap-14-adjacent
follow-on.

## Summary of dispositions

| # | Item | Ruling |
|---|---|---|
| 1 | Home + packaging | ✋ `validation/` dir; music21 `[validation]` extra; skip-if-absent smoke test in `tests/` |
| 2a | Key canonicalization | ✅ `(tonic_pc, major/minor)` is the engine's space; reduce + flag modal |
| 2b | Region metric | ✅ frame agreement = headline; boundary-tolerance = secondary |
| 2c | Relative policy | ✋ three buckets; headline the exact-rate Δ with/without `--disambiguate` |
| 2d | Tempo→seconds | ✅ confirmed multi-tempo-correct; **compare in beats** to delete the concern |
| 3 | Corpus | ✅ vendor ~10 PD scores; BY-SA annotations attributed; **never derive a prior from them** |
| 4 | Chord-level scoring | 🕳 recorded, separate round |

Move the harness in when ready; wire the `--disambiguate` A/B so response-5 can
cite a real Finding-B accuracy delta. Durable outcomes folded into ROADMAP (A6 +
the validation-asset record) and INTEGRATION (beats-comparison contract).

— Tonality
