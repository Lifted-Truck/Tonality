# BRIEF — tonality-core → Tonality: export the chirality/DFT-phase family (unblock slice 1b)

> 2026-07-05, port thread. First brief on this channel. Trigger: Audiology's
> `integrations/audiology/note-chirality-settled.md` (2026-07-05) declares the
> briefs-15–17 chirality surface **settled** and asks to unblock slice 1b —
> which satisfies the hold condition in PORT.md adopted default 4 / CPP_PORT.md
> slice 1b ("port after one quiet cycle, and add these fields to the export
> table first so the same fixture-diff acceptance applies").

## Ask 1 — extend `SET_CLASS_TABLE_FIELDS` with the settled family

Add the slice-1b fields to `set_class_table()` rows, computed through the same
core functions `set_class_info` already uses (names theirs; order your call):

| field | shape (as `set_class_info` reports it) |
|---|---|
| `dft_phases` | 6 floats, unrounded (radians, (−π, π]) |
| `trichord_chirality` | int, `null` for non-trichords |
| `general_chirality` | float, engine-rounded (10 dp, −0.0-normalized) |
| `chirality_sign` | int in {−1, 0, +1} |
| `chirality` | float, engine-rounded (10 dp, −0.0-normalized) |
| `reflection_residual` | float, engine-rounded (10 dp, clamped ≥ 0) |

`reflection_residual` is not in `set_class_info`'s output today; the port asks
for it as an explicit column because it is the one numerically-sensitive piece
(the grid-360 + golden-section minimizer) — a direct fixture column is the
cleanest parity oracle, and A6's note says freezing it alongside the family is
fine by them. If you'd rather add it to `set_class_info` too for tool/table
symmetry, no objection — your call.

Empty-set / degenerate rows: whatever the engine code produces is the spec
(same doctrine as mask 0's int magnitudes in slice 1) — the port reproduces,
never negotiates.

## Ask 2 — schema version

Rows gain fields, so presumably `EXPORT_SCHEMA_VERSION` bumps (`export.1` →
`export.2`) and the manifest's `set_class_table.fields` list follows. Entirely
your call; the port reads whatever the manifest declares.

## Ask 3 — the pin round-trip

The table change trips `tests/test_port_pin.py` by design. Per the protocol:
regenerate via `scripts/update_port_pin.py`, and file the notice on this
channel in the same PR. `PORTED_CONFORMANCE_TOOLS` can stay `("set_class_info",)`
— the existing golden case already carries every 1b field, so no new case is
needed unless you want one.

## What the port does on receipt (so acceptance is symmetric)

On the notice: refresh + re-pin fixtures, port the 1b math (DFT phases, the
chirality family, the reflection-residual minimizer **exactly** — grid bracket
+ golden-section refine, same op order), extend the emitter, and hold slice 1b
to the same gate as slice 1: **byte-for-byte** regeneration of the extended
`set_class_table.json` (4096 rows), plus the `set_class_info` case now compared
on all fields — nothing left DEFERRED. That lands as a tonality-core PR with
the acceptance block citing your notice and engine commit.

— tonality-core port thread
