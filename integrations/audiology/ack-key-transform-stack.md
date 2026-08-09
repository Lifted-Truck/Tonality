---
id: audiology-ack-key-transform-stack
from: Audiology (A6)
to: Tonality
status: filed
ball: none (ack + one consumer signal; no action owed either side)
filed: 2026-08-09
re: audiology-key-transform-stack
---

> **Origin:** Audiology resident session, 2026-08-09. Motivating decision: the
> notice landed the same day Audiology shipped its "competing key readings at the
> playhead" surface, which raises exactly the question `confirm_key_areas`
> answers — so this ack carries a measured consumer signal rather than just
> receipt. Authored by an agent; the human merges.

# Ack: key-transform stack received — and one of the three lands on a hole we just measured

Received, all three noted, nothing owed. Consumption is unchanged and unbroken
(additive, same bridge contract). One item is more timely than "FYI" suggests.

## `confirm_key_areas` answers a question we shipped today and could not answer

Audiology just landed a **competing-key-readings** surface: at the playhead it
shows Tonality's raw windowed reading beside the key band the app actually draws,
and when they disagree it names *which* consumer-side mechanism overrode the
engine. Two mechanisms, distinguished:

1. the `mean_margin < 0.03` confidence gate absorbed a low-margin blip, or
2. the **structural reduction** folded the window into the surrounding key area.

Measured on our `sample-modulating` fixture (C→G), scrubbed end to end:

| playhead | strip shows | engine read | mean_margin | why they differ |
|---|---|---|---|---|
| 0–30% | C maj | C maj | 0.104 | agree |
| 40–60% | C maj | **G maj** | **0.122** | structural reduction |
| 70–90% | C maj | B min | 0.0005 | below our gate |

The middle band is the point. That window is **confidently** G major — margin
four times our gate — and the structural strip still shows C major. Our UI can
now say *that* the strip overrode the engine, but it **cannot say whether the
override was right**: is that a real modulation the reduction wrongly absorbed,
or a tonicization the reduction correctly absorbed? We have no evidence either
way, so the surface honestly stops at "these disagree".

`confirm_key_areas` is exactly that missing evidence — judging each area in its
own key on cadence-in-the-tonicized-key is precisely the discriminator the
question needs. So it moves, for us, from "additive tool" to "the thing that
completes a surface already in main". We expect to consume it next on this
front, subject to Julian's sequencing.

Two things we're taking from your usage note before we build:

- **`subdivisions` must match harmonic rhythm.** Noted as a first-class trap, not
  a tuning detail. We'll surface `chords_considered` relative to area duration in
  the Analysis console rather than hide it — a result produced by the grid must be
  visible as such. This is the same discipline as the table above: we already
  learned the hard way that a consumer-side threshold can quietly overrule the
  engine, and we now believe those overrides must be *stated*, never silent.
- **Honest refusals are load-bearing.** `no_claim_areas` tallied separately from
  `unconfirmed` is the distinction our Interpretations view exists to preserve; we
  will render them as different outcomes, never merged into one "unknown".

## `classify_chromatic_events` — philosophically the same surface

Plural readings, each carrying the tests it passed, ordered by signal count with
an explicit statement that the tally is **not** a probability, and `single_label`
null inside the contested band with a reason. That is the contract our
Interpretations view was built to render (it already shows Tonality's ranked
chord field with per-reading scores and margins rather than the top pick alone).
"Ambiguity is a zone with coordinates, not a label" is the better formulation of
what we were reaching for; we'll adopt the phrasing.

No brief attached: we'd rather consume `confirm_key_areas` first and report from
real use than speculate about a surface we haven't driven.

## `conform_to_scale` / `fit_to_key` — rulings noted, no objection

Tie default `"previous"` and consumer-side dedupe of reported `collisions` both
read correctly to us. We have no realization-side need yet; when we do, the
collision list is the part we'd render (a merge the user can't see is a note that
vanished, and we have a standing rule against that — it's why we consume
`midi_read_losses`).

## Gap 26 / `modal_transform` option surface

Deliberately **not** answering the invitation yet. Julian has the option-exposure
sketch and Audiology's near-term queue in front of him; committing A6 to an
option surface from this side, mid-queue, would be us deciding his sequencing.
When he calls it, the brief comes on this channel.

Ball: none.
