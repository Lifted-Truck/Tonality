# Tonality → Audiology: response-19 (CHROMA — catalog contract confirmed, scorer confirmed, 12-TET confirmed)

> Triage of [brief-19-chroma.md](brief-19-chroma.md), 2026-07-04. Design
> handshake as requested — shapes confirmed here, build recorded as **gap 18**
> in ROADMAP (not yet scheduled, matching your "no urgency" gating). Your
> boundary carve-up (pitch arithmetic ours; rendering/selection yours) is
> accepted exactly as drawn.

## Ask 1 — the catalog contract: ✅ accepted, and it lands on machinery that now exists

You're the second consumer to ask for a compiled, versioned artifact this
month, and the framework decision is already on record: **Decision 11**
("contracts as object code — Tonality is the compiler for real-time
consumers", 2026-07-03, from the AURICLE harmony-contract RFC). Your catalog
contract is the second instance of that pattern; it will ride the same
versioning/emission discipline (canonical serialization, version stamps,
sha256 integrity — the `mts/io/export.py` machinery that already ships the
versioned-data manifest/bundle).

What exists today, verified in code:

- **Interval definitions are already data**: `mts/data/intervals.json` — all
  12 semitone values with `name` (P1/m2/M2/…), `verbal`, `diatonic_class`,
  `quality`, `inversion`, `cents`, `ratio`, `category`. Close to what Ask 1
  needs; the contract adds `interval_class` explicitly (it's derivable as
  `min(s, 12−s)` but your P4/P5 signature deserves a first-class field).
- **PC names/spellings are code, not yet data**: `core/enharmonics.py` owns
  `PC_TO_NAMES` + the spelling-preference logic. The contract lifts the
  12-row pc table (pc → canonical name + sharp/flat spellings) into the
  artifact.
- **The gap**: these catalogs are **unversioned** (the export manifest
  honestly records `versions: null` for them today). Gap 18's first slice is
  version strings on `intervals.json` / the pc table (then `scales.json` /
  `chord_qualities.json` for the sibling modules), so the contract can cite
  what it was compiled from.

Shape (yours to veto): one `catalog contract v1` JSON — `pitch_classes[]`
(pc, canonical_name, names) + `intervals[]` (semitones, interval_class, name,
verbal, quality, inversion, category), `meta.tonalityVersion` + per-catalog
version citations, canonical key order, published sha256. General enough for
functional-ear-training/interval-quality/chord-ID to extend rather than fork.

## Ask 2 — the scorer: ✅ accepted as specified, with one sweetener

`score(target_pc, response_pc)` as you wrote it — pure, deterministic,
identity-layer arithmetic (exactly the division of labor: the combinatorics
LLMs and app code get wrong live here):

- `correct: bool` — pc equality (mod 12).
- `error_magnitude: int` — interval class, `min(|d|, 12−|d|)` ∈ 0..6.
- `relationship` — read off the catalog's interval definitions per pair, both
  directed (`semitones_up`, i.e. `(response − target) mod 12`, with the
  catalog interval name) and undirected (`interval_class`, which collapses
  inversional pairs — your **P4/P5 contamination signature is one ic (5)** by
  construction, no special-casing).

The sweetener: since the input space is all of 144 ordered pairs, the
deliverable includes the **full 144-row test-vector table as a data artifact**
(same contract discipline). Vendored on your side, it *is* the scoring oracle
your CI blocks on — no cross-runtime calls, byte-diffable, regenerated only
with a version bump.

## Ask 2b — the aggregate confusion classifier: ✋ declined, boundary ruling

You offered us the option; keeping your original split. "Which relationship
dominates a session log" is behavioural aggregation over response data —
same side of the line as response-time capture and the anchoring index. The
same ruling as the confidence-thresholds-over-continuous-evidence precedent:
the per-pair relationship is theory and it's ours; what a *learner's* error
distribution means is yours. (If a future module needs a theory-side
primitive we haven't anticipated — e.g. expected-confusion geometry under a
null model — file that as its own ask.)

## Ask 3 — 12-TET: ✅ confirmed, explicitly

Tonality is 12-TET by design (mod-12 everywhere in the identity layer). The
contract artifacts carry an `edo` field fixed at 12 in v1 — reserved door,
zero microtonal/temperament work committed (same reservation as the AURICLE
harmony contract, Decision 11). Say "12-TET, per the engine contract" in the
product; that claim is safe.

## What to do with this

Shapes above are the handshake. Build is **gap 18** (recorded, not yet
scheduled) — sequenced when your module-contract sketch survives its second
module, per your own gating. If the proposed catalog-contract shape or the
directed+undirected relationship split needs adjusting, file a short brief-20
delta; otherwise the next artifact you see will be `catalog contract v1` + the
144-row scorer table.
