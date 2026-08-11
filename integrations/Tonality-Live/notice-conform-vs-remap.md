---
id: tonality-live-conform-routing
from: Tonality
to: Tonality-Live
status: filed
ball: consumer (routing recommendation — adopt or push back)
filed: 2026-08-11
---

> **Origin:** Tonality resident session, 2026-08-11, from Julian's report of a
> destroyed scale-walk during Tonality-Live test runs. Motivating decision:
> ROADMAP gap 31(a). Authored by an agent; the human merges.

# Notice: scale-CHANGE operations should route through `remap_by_degree`, not `conform_to_scale`

## The observed failure, explained

A topline walking down the scale (G–F–E–D–C) fitted to another scale via
`conform_to_scale` can come back with the walk destroyed (G–E–E–D–C into C
pentatonic: F and E merge). This is not a bug in conform — it is what a
proximity map *is*. Conform snaps each note independently by nearest-member
distance and never sees degrees, so "one scale step per note" is invisible to
it. Ableton's Scale MIDI tool fails identically, for the identical reason.

## The tool you want shipped last week

`remap_by_degree` (MCP tool of the same name; `modal_transform` for the
timeline-aware version) maps **degree → degree**: for any equal-cardinality
target, a scale walk survives **exactly, by construction** — consecutive
degrees stay consecutive, the map is bijective on in-scale tones, collisions
cannot occur. Step *sizes* change (that is what a mode change is); walk-ness
cannot.

The two tools answer different questions, and the UI should say so:

| | question it answers | character |
|---|---|---|
| `conform_to_scale` | "make these notes **legal** in scale S" | proximity, many-to-one, lossy — cleanup |
| `remap_by_degree` | "**translate** this music into scale S" | degree-preserving, bijective in-scale — translation |

**Recommendation:** route "change scale/mode" operations through remap (or
`modal_transform` when the clip may contain key changes — it builds per-area
maps and leaves channel-10 drums untouched); keep conform for its real jobs —
constraining new/incoming material to a key, cleaning stray accidentals.
Labeling matters: a user who asks "make this Dorian" means translate, and a
proximity snap silently gives them something else.

## The honest limit (so the UI can be honest too)

For **unequal cardinality** (7-note walk into a pentatonic) no map can keep
the walk intact — pigeonhole, the same totality/locality impossibility that
defines the modal transform. Preserving the walk's *character* there means
span-level choices (wider span vs. chord collision vs. repetition vs.
compression) that are policy, not computation. That is ROADMAP gap 31(b)/(c)
— pattern-detected scale runs as grouped plan decisions with policy knobs —
recorded and awaiting your related brief before final scoping. Until it
ships, an unequal-cardinality remap request is refused by the engine
(equal cardinality is a stated precondition), which is the correct interim
behaviour: a refusal you can surface beats a silently broken walk.

Ball: consumer — adopt the routing (or push back on this channel if your
`/transform` semantics want something different). No engine change is needed
for the equal-cardinality case; it works today.
