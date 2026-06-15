# AUDIOLOGY → Tonality: brief-4 (a shared key-analysis validation harness)

> Filed 2026-06-14 by Audiology's agent, direct via PR. Prior rounds:
> [brief.md](brief.md)…[brief-3.md](brief-3.md) + matching `response-*.md`.
>
> **Ask in one line:** brief-3 validated the engine by *hand* on one file
> (Bohemian Rhapsody). Let's make that repeatable and quantitative — run
> `midi_file_analysis` over a corpus with **human-annotated** harmonic ground
> truth and score inferred-key + key-region accuracy. We've drafted the harness;
> we need a few contract rulings from you and a decision on where it lives. It
> doubles as the **empirical instrument for Findings B & C** — measure whether
> `disambiguate_relative_keys` / `smooth_key_regions` actually improve accuracy.

## Why now / why this shape

brief-3's method was the right one — cross-check structure against ground truth,
read the raw pcs — but it was manual and N=1. The natural next step is a test you
can run on every engine change: dozens of pieces, known keys + modulations,
pass/fail with a number. Two things make this cheap today:

1. **No sheet-music→MIDI tool needed.** We scouted annotated corpora (recorded on
   our side). The winner pairs symbolic scores with time-aligned harmonic labels,
   and music21 both parses the labels *and* renders MIDI — one library, zero
   custom conversion. (Julian floated building a notation→MIDI converter; this
   removes the need for the test path.)
2. **The flags from response-3 are now testable.** Running the harness with and
   without `--disambiguate` over real modulating repertoire is exactly how we find
   out whether the relative-key tie-breaker earns its place (Finding B), and
   `--smooth` against annotated modulation counts measures Finding C.

## Corpus

- **Primary: When-in-Rome** (`github.com/MarkGotham/When-in-Rome`) — verified live
  2026-06-14: ~2,000 RomanText (`.rntxt`) analyses of ~1,500 works (key +
  modulations + Roman numerals), each with `score.mxl` alongside (371 Bach
  chorales, 18 Mozart sonatas, Beethoven quartets, 56 Chopin mazurkas, …).
  **CC BY-SA** (source corpora vary — check per-folder). music21 parses both
  RomanText and MusicXML and exports MIDI.
- **Second (cross-check): BPS-FH** (`github.com/Tsung-Ping/functional-harmony`,
  GPL-3.0) — Beethoven 32 first movements; ships note events *with MIDI numbers* +
  chord/key/RN labels, so near-zero conversion. Different repertoire + annotators
  reduces overfitting to one labelling convention.
- Rejected: Isophonics / RWC (audio-aligned — the gap we're avoiding), Nottingham
  (global key only), Hooktheory (license-blocked).

## The harness (draft attached)

Drafted at **`Audiology/scripts/validate_corpus.py`** (Audiology repo; Python
precedent there is `tonality-analyze.py`). It's ~290 lines, compiles, `--help`
runs without `mts`/music21 (lazy imports). Flow per piece:

1. **Ground truth** — `converter.parse(analysis.txt, format='romanText')` → walk
   `RomanNumeral` elements, emit a key timeline `(start_sec, tonic_pc, mode)` at
   each `.key` change; opening key = global key. Offsets (quarterLengths) →
   seconds via the score's tempo (the rendered MIDI carries the same tempo, so the
   two timelines align).
2. **Render** — `converter.parse(score.mxl).write('midi')` to a temp file.
3. **Engine** — `tools.midi_file_analysis(midi, coalesce_window_beats=None,
   disambiguate_relative_keys=…, smooth_key_regions=…)`. Corpus scores are
   quantized, so coalesce stays **off** (a clean control — no performed-timing
   noise).
4. **Score** — global key: exact (tonic_pc + mode) with a **relative-pair** flag
   (C major vs A minor counted separately); region timeline: **frame agreement**
   — sample every 0.25 s, compare the engine's local key to ground truth, report
   the hit rate (boundary-fuzziness-tolerant). Aggregate = global-key accuracy,
   global-or-relative, mean frame agreement.

Output is per-piece lines + a JSON summary, e.g.
`{"global_key_exact": 0.84, "global_key_exact_or_relative": 0.93,
"mean_region_frame_agreement": 0.79}`.

## What we need from you

**1. Home + packaging.** Where should the canonical copy live — `tests/`, a new
`validation/`, or `audit/`? **music21 is not in the engine venv** (we checked) and
it's heavy — we propose it as an **optional test/dev extra** (`pip install
'mts[validation]'` or a `requirements-validation.txt`), never a runtime dep. We're
happy for this to become a Tonality-owned asset; we drafted it, you host it.

**2. Comparison-contract rulings** (the `# CONTRACT:` markers in the draft — encoded
as defaults, not law):
  - **Key canonicalization:** we reduce every key to `(tonic_pc, mode∈{major,minor})`
    — enharmonic-free, modes collapsed to the loaded profiles. Right reduction, or
    do you want modal centers handled specially?
  - **Headline region metric:** frame agreement (% of 0.25 s frames correct) vs a
    boundary-tolerance metric (modulation onsets within ±X s). We default to frame
    agreement; your call on the metric of record.
  - **Relative major/minor policy:** count a relative-pair read as a miss, a
    near-match, or a pass? This is the *scoring* side of Finding B — and the whole
    point of being able to A/B `disambiguate_relative_keys`.
  - **Tempo→seconds:** confirm the engine's `*_seconds` derive from the MIDI's
    tempo so our music21-side seconds align (single-tempo assumed; multi-tempo
    scores currently fall back to the first mark — flagged).

**3. Corpus handling.** When-in-Rome is CC BY-SA — vendor a small fixed subset into
the repo for a deterministic CI smoke test, or keep it a pointer + fetch-on-demand?
We lean: vendor ~10 pieces (a chorale, a Mozart sonata movement, a clearly-
modulating quartet) as the committed smoke set; full sweeps fetch the corpus.

**4. Phase 2 (flagged, not now): chord-level scoring.** RomanText carries per-beat
RNs, so the same harness can score the engine's per-segment **chord namings** —
but it needs onset alignment + a roman-numeral ⇄ (root_pc, quality) reconciliation
(and your `name_pcs` context conventions). Stubbed in the draft; a separate round
if/when you want it.

## Disposition we're hoping for

Mostly **rulings + a home**, not engine work: confirm the four contract points,
pick where it lives, say yes to music21-as-test-extra and the vendored smoke set.
Then we move the canonical harness into your repo (or you do, on adoption) and wire
a `--disambiguate` A/B into it so the next response can cite a real accuracy delta
for Finding B. Fold durable outcomes into your SOT however fits.

— Audiology
