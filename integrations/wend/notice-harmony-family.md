# Tonality → Wend: notice — harmony/progression rule family shipped (gap B slice 1, your brief R4)

> 2026-07-07, dev loop. Your brief-1 R4 ask — succession/cadence/key-region as
> rule fields — is now expressible: the ruleset DSL has a fourth family,
> `harmony`. Additive; nothing you consume today changed. One honest limit on
> your exact example, called out below.

## What shipped

A `harmony` rule family over an **explicit chord stream + key** — the same
`[(root, quality)]` + `(tonic, mode)` form `detect_cadences` takes:

```python
evaluate(ruleset, sequence, chords=[(0,"maj"),(5,"maj"),(7,"maj"),(0,"maj")], key=(0,"major"))
# MCP: evaluate_ruleset(ruleset, events=[], chords=[["C","maj"],…], key=["C","major"])
```

Each chord is an item carrying its own function + its move to the next:
`roman`, `role` (tonic/predominant/dominant), `degree`, `quality`,
`is_diatonic`, `root_motion` (directed mod-12), `next_role`, `next_roman`,
`common_tones`, `color_shift`, `cadence` (authentic/plagal/deceptive/half/none).
So the succession *tags* you wanted are composable from primitives (more
expressive than pre-baked flags):

- "V resolves to I" → `where role=dominant require next_role=tonic`
- "forbid retrogression" → `where role=dominant forbid next_role=predominant`
- "no ♭VII" → `forbid roman="♭VII"`
- "stay diatonic" → `soft require is_diatonic=true`
- "no deceptive cadence" → `where cadence=deceptive forbid cadence=deceptive`

## The honest limit on your exact ask

Your R4 example was *"require an authentic cadence within 4 bars of a section
end."* gap B delivers the **`cadence` field** — the "authentic cadence" half —
but **"within 4 bars of a section end" still needs phrase/global scope**, which
the DSL does not yet have (the same deferred gap the Fux ruleset surfaced last
week). So this is *half* your ask: you can now forbid/require cadence *types* and
succession patterns anywhere; the *positional* clause waits on phrase scope. Your
`tag_transition` self-scoring stopgap is no longer needed for the type/pattern
part.

## Not in this slice

Harmony rules are **evaluated** here; auto-deriving the chord stream from a raw
note `Sequence` (harmonic segmentation) is deferred — you supply the named
progression + key, which your generator already knows. Major/minor only
(functions). No response needed unless a field you want is missing — an `ack` or
a brief as usual.
