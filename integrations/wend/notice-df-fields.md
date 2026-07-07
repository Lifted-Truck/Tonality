# Tonality → Wend: notice — `df1..df6` DFT-magnitude fields shipped (R3)

> 2026-07-07, dev loop. Follows [response-2.md](response-2.md) R3 ("we'll notice
> you when df5 is in"). Additive — nothing you consume today changed; your R1
> fix and the set-class default posture are unaffected.

## What shipped

The `df1..df6` interval-content fields you asked for, plus the full spectrum on
every match so you can **rank**, not just filter:

- **Query fields `df1..df6`** — the DFT magnitudes `|f1..f6|`, **float, range-only**
  (`{"gte": x}` / `{"lte": x}`). `df5` = diatonicity/fifthiness (your ask), `df6`
  = whole-tone-ness, `df4` = octatonicity, `df3` = hexatonicity, `df2` =
  quartal/whole-tone-cluster balance, `df1` = chromatic clustering. Equality and
  `in` are rejected with an actionable error (an exact-value test on an
  irrational magnitude is a footgun).
- **`dft_magnitudes` on every match** — the full `[|f1|,…,|f6|]` vector, always
  present, so an enumerated pivot carries its own color and you can price it in
  the surprise budget without a second call.

They're honest set-class fields (T/I-invariant), so they compose with the folded
default *and* with `expand_transpositions=True` — your rooted pivot queries get
the spectrum on each rooted match.

## The shape you described, now runnable

```python
# rooted pivots into a key, ranked by fifthiness (your "price pivot color")
r = search_identities(
    {"cardinality": 3, "contained_in": key_pcs, "df5": {"gte": 2.0}},
    expand_transpositions=True,
)
ranked = sorted(r.matches, key=lambda m: m.dft_magnitudes[4], reverse=True)
# m.dft_magnitudes[4] is |f5| — a continuous control signal, plural outputs kept
```

Two orientation values to calibrate thresholds against: the whole-tone scale is
the unique set with `df6 == 6.0` (perfectly whole-tone), and the diatonic scale
maximizes `df5` among 7-note sets at `2 + √3 ≈ 3.732`.

## Not in this drop

`contains_at` (rooted-absolute containment, to retire your `rooted_triad` shim)
is recorded as the lower-priority ergonomic add, per your own ranking — it's a
convenience, not capability-blocking, so it waits. `search_voicings` (gap 17,
your `realize_voicing`) remains the larger next slice. No response needed unless
the field semantics don't fit an operator you had in mind.
