# NOTICE — Tonality → Audiology: naming `rank` is now 1-based (RE-6d)

> 2026-07-07, dev loop. One small consumer-visible change from the rigor &
> efficiency review's final workstream (RE-6d, API consistency).

## What changed

The `rank` field on **naming** results was **0-based** (top naming = `rank 0`)
while **succession**/`next_chord` was already **1-based** (top pick = `rank 1`).
That cross-surface inconsistency is resolved: naming is now **1-based too**, so
`rank` means the same thing everywhere — a human ordinal, `rank 1` = best.

Affected surfaces you consume:

- `name_pcs` → `chosen`/`rankings[].rank`
- `name_pcs_in_inferred_keys` → per-key `naming.rankings[].rank`
- `midi_file_analysis` → the per-segment dataset `naming` records

`next_chord` (succession) is **unchanged** — it was already 1-based.

## Impact

Only if you index or display the naming `rank`: add 1 to any hardcoded
expectation (the best naming is now `rank == 1`, not `0`). The **ordering is
identical** — only the integer label shifted. `is_ambiguous`, `score`, and the
chosen naming itself are untouched.

No base was pinned in any prior notice, so this breaks no standing contract —
it's the consistency fix flagged by the review. Ack when absorbed.
