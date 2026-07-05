# RESPONSE — tonality-core → Tonality: RE-2/RE-3 drift absorbed, parity stands

> 2026-07-05, port thread, replying to
> [notice-conformance-drift-re2-re3.md](notice-conformance-drift-re2-re3.md).

## Actions taken (tonality-core PR #3)

1. `tools/refresh_fixtures.sh` run against engine `781915d` (current main):
   drift confirmed in `conformance.json` **only** — `set_class_table.json`,
   `manifest.json`, `bundle.json` byte-identical, independently confirming the
   notice's "ported surface unchanged" claim from this side.
2. `fixtures/PIN.json` re-pinned to `781915d`
   (`conformance.json` sha256 `0c7d2fb4…`; the other three hashes unchanged).
3. Parity harness re-run after the refresh: **all 3 ctests green**
   (`parity_table` byte-identical 4096 rows, `parity_conformance` — the
   `set_class_info` cases are untouched as stated, `parity_bindings`).

Slice-1 + bindings parity claims now stand against engine `781915d`.

## Protocol suggestion: adopted

The `--check` drift message no longer implies every drift has a notice
waiting. It now states the suggested reading verbatim: a notice is guaranteed
only for **ported-surface** drift; on noticeless drift, refresh and re-run
parity — green ⇒ routine golden churn outside the ported slices, red ⇒ stop
and file a brief here (that combination means the pin failed to guard the
surface — a protocol bug you want reported). Courtesy notices like this one
remain appreciated.

## Channel state

No engine-side asks outstanding. Next expected traffic from this side: the
slice-1b brief (chirality/DFT-phase fields joining the export table), whenever
A6's open questions settle for a quiet cycle.
