---
id: tonality-live-002
from: Tonality-Live
to: Tonality
status: filed
ball: provider
filed: 2026-08-10
respond-by: 2026-08-24
---

> **Origin:** Tonality-Live consumer session, 2026-08-10, found while building a
> before/after preview for the workshop GUI (Tonality-Live ROADMAP Q-004).
> Motivating decision: the preview needs reliable note pairing. Authored by an
> agent; the human merges.

# Brief: `conform_to_scale` docstring says input order, output is onset-sorted

## The mismatch

`mts/generate/conform.py` documents `ConformResult.events` as:

> "``events`` is the full piece in canonical event form
> ``[onset_beats, duration_beats, midi, velocity, voice]``, **in the input's
> note order** — count, timing, velocity and voices preserved; pitch is the
> only field that may differ."

The output is **sorted by onset**, not in input order. Reproduced against a
20-note clip (block chords entered first, melody second — i.e. deliberately not
onset-ordered):

```
input  onsets: 0,0,0,2,2,2,4,4,4,6,6,6,0,1,2,3,4,5,6,7
output onsets: 0,0,0,0,1,2,2,2,2,3,4,4,4,4,5,6,6,6,6,7
```

Likely mechanism (reading the source, not asserted): the walk is driven by
`order = sorted(range(len(events)), key=lambda i: (onset, i))` for the
melodic-continuity tie-break, and `out_events` is built in that walk order
rather than being written back by original index — the loop that computes
`new_midis[i]` does index correctly, so this looks like the assembly step only.

## Why it matters to a consumer

Nothing user-visible is broken in Tonality-Live today: we hand `events` straight
to `clip.notes`, and note order is irrelevant inside a MIDI clip. Our collision
dedupe keys on (pitch, onset, duration), so it is order-independent too.

The cost is a **silent trap for anything that pairs input to output**, which is
exactly what a before/after diff view does. `output[i]` is not `input[i]`, so a
positional comparison reports the wrong notes as changed — for our test clip it
claimed 17 notes moved where you had correctly snapped 10. The docstring
actively invites that assumption, which is what makes it worth a report rather
than a shrug.

It also makes accepted contract test 3 ("preserves note count / startTime /
duration; pitch is the only field it may change") ambiguous: true of the
multiset, false position-by-position. Whichever you intend should be pinned.

## What we did on our side (no upstream dependency)

We now reconstruct the "after" set as `before + report.edits`, matching on
`(onset, from_midi)`. That pairs exactly — paired-moved equals your
`notes_snapped` for all four transforms we exercised (2, 8, 10, 3), with zero
unmatched edits. So we are unblocked either way.

## The ask (either is fine — we just need it pinned)

1. **Make the code match the doc** — assemble `out_events` by original index so
   input order is preserved. Cheap, and keeps the documented promise.
2. **Make the doc match the code** — state that events come back onset-sorted,
   and that consumers must pair via `edits` rather than by position. Then please
   also disambiguate contract test 3 as a multiset claim.

We'd mildly prefer (1), because "same order in, same order out" is the less
surprising contract and it keeps `edits[].index` meaningful against the input.
But (2) costs us nothing now that we pair via `edits`.

Ball: **provider**.
