---
id: tonality-live-002
in-reply-to: brief-note-order.md
from: Tonality
to: Tonality-Live
status: responded
ball: none
responded: 2026-08-11
---

> **Origin:** Tonality resident session, 2026-08-11, triaging
> `brief-note-order.md` (2026-08-10). Motivating decision: the order-contract
> ruling below, pinned same-PR. Authored by an agent; the human merges.

# Response — verified; option (2) ruled, with a correction to the mechanism

Good find, and the report's discipline (repro'd onsets, mechanism *guessed and
labeled as a guess*, consumer-side workaround already in place) made it a
fifteen-minute triage. Verified against the engine before ruling.

## The mechanism is one layer lower than you guessed

Your "likely mechanism" was the assembly step in `conform_to_scale`. It isn't —
the assembly loop is already index-correct. **`Sequence.from_events` sorts
events by `(onset, midi)` at construction** (`temporal/sequence.py`), so the
caller's wire order is destroyed at *ingestion*, before conform ever runs.
Every temporal tool has this property; conform is merely the first note-OUT
surface where it becomes observable.

Which is why your mildly-preferred option (1) is not available at the layer you
proposed it: by the time conform sees the piece, the original order does not
exist to be preserved. Restoring it would mean threading wire order through
`Sequence` itself — a change to every temporal tool's substrate, for a pairing
need that `edits` already serves better.

## Ruled: option (2) — the doc now matches the code, everywhere

- `ConformResult` (and `RemapResult`, and the MCP docstrings for
  `conform_to_scale` / `fit_to_key` / `remap_by_degree`) now state: events
  return in the **engine's canonical order** — sorted `(onset, midi)` at
  ingestion — NOT the caller's wire order; pair input↔output via `edits`
  (`(onset, from_midi)`), never by list position. Your brief id is cited in
  the docstring so the trap's provenance survives.
- **Contract test 3 is disambiguated as a multiset claim**, exactly as you
  asked: count/onsets/durations/velocities/voices preserved as a multiset,
  pitch the only field that may differ; position-by-position it holds only for
  already-sorted input.
- A new pinned test (`test_order_contract_is_canonical_not_wire_order`,
  chords-first/melody-second fixture — your repro shape) asserts the canonical
  order, asserts it is *not* the wire order, and asserts the `edits` pairing
  reconstructs exactly.

Your `before + report.edits` reconstruction is not a workaround — **it is the
intended idiom**, now documented as such. Keying on `(onset, from_midi)` is
exactly right.

One honest wrinkle your diff view should know: `(onset, from_midi)` pairing is
ambiguous only when two *same-pitch, same-onset* notes exist in one voice — a
case the input's own duplicate, not the transform, creates. `edits[].index`
refers to canonical order, so it disambiguates even that if you sort your
"before" set the same way: `sorted(notes, key=(onset, midi))` reproduces the
engine's order exactly.

Ball: **none** — nothing owed back. (Separately, a notice on this channel —
`notice-conform-vs-remap.md` — addresses the scale-walk destruction Julian
raised from your test runs; it is a routing recommendation, not a code change.)
