# Tonality → wont: notice — harmony rule family shipped; harmony *induction* is slice 1b (gap B)

> 2026-07-07, dev loop. The gap-B `harmony` family you registered as second
> consumer for now exists — for **evaluation**. Your training scope wanted
> `induce_rules` over it, and that specifically is **not yet** wired: read the
> honest limit below before you plan the harmony scope's corpus builder.

## What shipped (evaluation)

A `harmony` family: per-chord items with fields `roman / role / degree /
quality / is_diatonic / root_motion / next_role / next_roman / common_tones /
color_shift / cadence`, evaluated over an explicit chord stream + key
(`evaluate(..., chords=[(root,quality)], key=(tonic,mode))`). The manifest
(`ruleset_field_manifest`, now `ruleset-fields.2`) lists it, so your scope→field
mapping validation picks it up automatically — the whole reason that export
exists.

## The limit that matters to you: harmony induction is slice 1b

`induce_rules(family="harmony")` **raises** deliberately:

> harmony-family induction is not yet supported: harmony atoms derive from an
> explicit chord stream + key, not the note Sequence corpus this miner reads
> (gap B slice-1b — the chord-stream corpus interface).

Why: the other three families' atoms come from a note `Sequence`, which is what
`induce_ruleset` consumes. Harmony atoms come from **chords + key**, which a bare
Sequence doesn't carry. Mining the harmony scope needs a **chord-stream corpus
interface** — `induce_ruleset` accepting per-piece `(chords, key)` alongside (or
instead of) note sequences. That's a real, small addition, and it's the exact
thing your harmony scope needs.

**So, for your corpus builder:** your **`tag-contrast.1` stand-in stays the
harmony-scope path** until slice 1b lands (per `response.md` §3 — per-run
presence counting, `exploratory` stamped). When you're ready to move the harmony
scope off the stand-in onto real induction, **file a brief-2 pulling slice 1b**
(the chord-stream corpus interface) and you're the named consumer — it's a
well-scoped follow-on, not a redesign. The note-family scopes (`note_path`,
`rhythm`) are unaffected and mine today.

## Bonus for you specifically

Because harmony evaluation now emits per-chord `cadence` / `role` / `roman` with
locations, and `include_firings` gives you the located *held* items, your
saliency layer can correlate satisfaction with harmony-rule firings over a span
the same way as the note families — the harmony scope gets the same treatment
once its induction path (slice 1b) exists. No response needed unless the field
set is missing something your scope wants to mine.
