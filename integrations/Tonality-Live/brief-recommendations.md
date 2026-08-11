---
id: tonality-live-003
from: Tonality-Live
to: Tonality
status: filed
ball: provider
filed: 2026-08-10
respond-by: 2026-09-14
kind: early-signal
---

> **Origin:** Tonality-Live consumer session, 2026-08-10, filed at the human's
> request so the engine can anticipate this while shaping Phase 7+. Motivating
> decision: Tonality-Live ROADMAP **Q-006** (parked vision, deliberately not
> started). Authored by an agent; the human merges.
>
> **This is an early-signal brief, not a request for work.** Nothing in
> Tonality-Live is blocked on it and there is no deadline pressure — the long
> `respond-by` reflects that. We are telling you where the consumer is heading so
> that if Phase 7 is being designed anyway, it can be designed with this in view.
> A "noted, not now" is a complete and welcome answer.

# Brief: context-aware transformation *recommendations*

## The eventual shape

Today the consumer asks the engine to perform a transformation the **user**
chose. The direction is for the engine to *suggest* which transformation is worth
making, given what it already understands about the material — and for the user to
audition and accept a suggestion rather than specify one.

The human's words, verbatim, so nothing is lost in our paraphrase:

> "Tonality analysis uses smart context to recommend transformations based on
> established patterns (key transition, tonicization, re-voice, complexify or
> clean up harmony). Possibly even informed by genre/instrument(/part/song
> section/etc.) dropdowns."

## Why it comes to you rather than us

"This progression wants a secondary dominant here" is music-theoretic **judgment**,
which is yours under rule 3. We are not going to build a recommender behind your
back — the consumer's job is the dropdowns, the ranked presentation, and applying
whatever the user picks. Recording that division now so it doesn't get muddled
later.

## Where each named pattern already appears to stand (from your ROADMAP)

We read these before filing so we are not asking for things you have already
scoped. Corrections welcome:

| Pattern | Our reading of current status |
|---|---|
| key transition / modulation | "modulation path planning" named as a Phase 7 extension, generative-side |
| tonicization | pivots exist (`pivots_between`); the analysis already surfaces tonicization |
| re-voice | deferred to Phase 7 proper (your Ruling 6, brief-001) |
| complexify / clean up harmony | we found nothing scoped anywhere — genuinely new |

So roughly half of this already has a home; the ask is less "build a new layer"
than "consider whether these become a *recommendation surface* rather than N
separate callable transforms."

## The three things we think are actually hard

Flagging these because they are the parts that would make this expensive, and we
would rather name them than let them surface late:

1. **Genre / instrument / section context are priors, and rule 4 binds them.**
   "Jazz wants ♭9s" is an empirical claim with a provenance burden, not a
   preference toggle. Versioned, evidenced, and falsifiable — or the feature
   becomes taste laundered as analysis. This is the single biggest commitment in
   the whole idea, and it is entirely yours; we cannot help carry it.
2. **Recommendation is a judgment surface, so plurality matters (rule 7).** We
   want ranked candidates *with margins*, not one collapsed answer — the same way
   key induction gives us candidates and a margin today. A single "best"
   recommendation would hide exactly the ambiguity a musician needs to see. Our UI
   is already shaped for a ranked list.
3. **Where AI may and may not sit.** A recommender is *propose*, which we read as
   permitted. But nothing model-generated should end up inside the note pipeline —
   the transform that runs must remain deterministic and reproducible, as
   `conform_to_scale` is today. We are pinning this on our side; flagging so both
   sides pin it the same way.

## What we are NOT asking for

- Any code, this quarter or next.
- A commitment to genre priors. If the honest answer is "we will not ship genre
  priors without a corpus to back them", that is a good answer and we would
  rather have it early than have a plausible-feeling feature.
- Anything that would delay `revoice` or the Phase 6 fence.

## What would help us most, whenever you get to it

1. A **ruling on the shape**: does a recommendation surface belong in the engine
   at all, or should the engine expose richer analysis (pivots, weak spots,
   voice-leading costs) and leave "therefore suggest X" to consumers? We would
   take either; we just need to know which side owns it before we build UI for it.
2. If it does belong to you: whether recommendations arrive as their own endpoint
   or as an enrichment of the existing analysis result.

Ball: **provider** — acknowledge and rule when convenient; no consumer work is
blocked in the meantime.
