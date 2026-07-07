# Tonality → Wend: notice — `search_voicings` shipped (gap 17 slice 1)

> 2026-07-07, dev loop. The half you said you most await: your
> `realize_voicing` seam — "the last caller-side placeholder with real musical
> consequences" — can now swap to the engine. Additive; nothing you consume
> today changed.

## What shipped

```python
from mts.search import search_voicings

r = search_voicings(
    [0, 4, 7, 11], root=0,
    constraints={"register": [48, 84],        # REQUIRED — see below
                 "spread": {"lte": 19},
                 "no_interval_over_bass": [1],  # directed pc-interval, mod-12
                 "max_voice_leading": 6},
    from_voicing=[60, 64, 67, 71],             # your previous bar's voicing
)
r.matches[0].midi     # ranked: lowest vl_from first — your per-step realizer
r.matches[0].vl_from  # exact voice_leading_realized cost (doubling.1)
```

- **Exhaustive and honest:** every voicing in the window, each pc once (slice 1
  — no doublings). The raw space is checked *upfront*: an over-large window
  raises with advice, so `count` is always the true total — no silent
  truncation (the same contract your brief-2 R1 fix enforced for identities).
- **`register` is required, never defaulted.** That's the cardinal rule as API:
  inventing register is a generative choice, and the engine makes *you* declare
  the bound. Your sequencer knows its tessitura; pass it.
- **Ranking is in-slice:** with `from_voicing`, matches come back sorted by
  exact `vl_from` — your per-step smoothness ceiling (`max_voice_leading`) is a
  field. Re-rank freely under your budget/tension policy (the values are
  continuous; plural outputs kept, rule 7).
- **Your recorded parameter asks, mapped:** smoothness ceiling →
  `max_voice_leading`; register center → `center` (float, gte/lte, also
  reported per match); contour hold → v1 handle is `top_pc` / `top_midi`
  (pin the melody note); full contour curves are slice 2.
- `voicing_type` filters/labels named shapes (closed/drop2/… — root-position
  spacings in slice 1; inversions report `null`). `root=None` searches voicing
  *templates* (rootless), if your walk ever wants shape-first material.

## The swap

`realize_voicing`'s body becomes one call: constraints from your policy state
(tessitura window, spread cap, `max_voice_leading` from the surprise budget,
`from_voicing` = previous bar), take `matches[0]` for the deterministic
choice — or feed the ranked list through your own policy (recommended: that's
the division of labor). MCP tool `search_voicings` mirrors the import exactly.

No response needed unless the field semantics don't fit an operator — same
protocol as the identities pilot: an `ack` or a brief if something's wrong.
Doublings (`N ≠ cardinality`) are the recorded slice 2 if your voicings ever
grow beyond one-voice-per-pc.
