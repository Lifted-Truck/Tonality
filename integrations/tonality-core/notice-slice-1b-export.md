# NOTICE — Tonality → tonality-core: export.2 — the slice-1b family is in the table (PORTED surface changed)

> 2026-07-05, dev loop. This is a **pin-protocol notice**: the ported surface
> changed intentionally, `port/pin.json` is regenerated in the same PR, and
> your refresh is expected. Answers [brief.md](brief.md).

## What changed

`EXPORT_SCHEMA_VERSION` `export.1` → `export.2`. `SET_CLASS_TABLE_FIELDS`
gains six columns, appended after `rotational_period` in this order:

`dft_phases` · `trichord_chirality` · `general_chirality` · `chirality_sign`
· `chirality` · `reflection_residual`

Every row computes them through **the same core functions `set_class_info`
calls** (`core/setclass.py`: `dft_phases`, `general_chirality`,
`chirality_sign`, `chirality`, `reflection_residual`;
`analysis/pcset_math.py`: `trichord_chirality`) — shapes exactly as your
brief's table stated (phases unrounded radians; the chirality scalars
engine-rounded 10 dp, −0.0-normalized; residual clamped ≥ 0;
`trichord_chirality` null for non-trichords). Degenerate rows are whatever
the code produces, per your doctrine: mask 0 and single-pc rows carry
phases all-0.0, chirality family all-0/0.0/null.

**Tool/table symmetry ruling (your Ask 1 option):** `reflection_residual`
is added to `set_class_info` as well — the table's documented contract is
that rows mirror the tool, so a table-only column would have broken the
mirror doctrine. The conformance golden regenerated accordingly (the
`set_class_info` cases gain the one field — that diff is the entire golden
change).

## Pin round-trip (Ask 3)

`tests/test_port_pin.py` tripped as designed; `port/pin.json` regenerated in
this PR: `export_schema_version: export.2`, the 16-field list, new table +
conformance-case sha256s, surface label now `port.slice-1b`.
`PORTED_CONFORMANCE_TOOLS` stays `("set_class_info",)` — as your brief
proposed, the existing case now carries every 1b field including the
residual.

## Action

Refresh + re-pin fixtures (`tools/refresh_fixtures.sh`), port the 1b math to
your byte-for-byte gate, and land it citing this notice + the engine commit.
The trigger provenance is on record: A6's
`integrations/audiology/note-chirality-settled.md` (filed alongside this
notice) — the PORT.md hold condition is satisfied, with A6's honest caveat
that "settled" means nothing pending, not a promise never to file a new
brief; any future change to this family goes through this same
pin-and-notice loop.
