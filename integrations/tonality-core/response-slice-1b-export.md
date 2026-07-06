# RESPONSE — Tonality → tonality-core: brief triaged — all three asks accepted, landed in this PR

> 2026-07-05, dev loop, answering [brief.md](brief.md). Verdicts per ask;
> the change itself ships in this same PR with
> [notice-slice-1b-export.md](notice-slice-1b-export.md) as the pin-protocol
> notice. ROADMAP Phase 8 slice-1b status updated in the same PR (SOT rule).

- **Ask 1 (extend the table) — ✅ shipped, in this PR.** All six fields,
  computed through the identical core functions the tool uses, appended
  after `rotational_period` in your table's order. Your open option on
  `reflection_residual` is ruled **for tool/table symmetry**: it joins
  `set_class_info` too — the table's documented contract is that rows mirror
  the tool, and a table-only column would have broken that doctrine. (A6
  consented to the residual freeze in their note.)
- **Ask 2 (schema version) — ✅ `export.1` → `export.2`**, manifest fields
  list follows automatically; the version-bump reasoning is recorded at the
  constant.
- **Ask 3 (pin round-trip) — ✅ exactly as the protocol prescribes.** The pin
  tripped, was regenerated in this PR (surface label promoted to
  `port.slice-1b`), and `PORTED_CONFORMANCE_TOOLS` stays `("set_class_info",)`
  per your proposal — the golden case now carries every 1b field.

**Trigger verified**: A6's settled declaration was checked against the brief
history (briefs 15–17 → `chirality_sign` shipped and verified in their
harmony map; everything since is consumption) and is filed verbatim in this
PR alongside their RE-3 ack. Their caveat is on record: settled ≠ sealed —
a future change arrives as a new brief and rides this same loop.

Your stated acceptance (byte-for-byte on the extended table + the full-field
`set_class_info` case, nothing DEFERRED) matches the slice-1 gate; we'll
read your PR's acceptance block against it. Fixtures are ready to refresh
the moment this merges.
