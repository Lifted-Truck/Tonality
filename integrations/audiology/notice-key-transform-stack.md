---
id: audiology-key-transform-stack
from: Tonality
to: Audiology (A6)
status: filed
ball: consumer (FYI — no action owed)
filed: 2026-08-09
---

> **Origin:** Tonality resident session, 2026-08-09. Motivating decision:
> ROADMAP gap 26 names **Audiology as the first integration target** for the
> modal transform, and its three prerequisites shipped across the last two
> weeks — this notice is the "the ground you'll build on now exists" signal.
> Authored by an agent; the human merges.

# Notice: the key-transform analysis stack is live (gaps 25 + Phase 7 slice 0)

Three shipped surfaces, in dependency order — together they are the analysis
side of the "analyze a MIDI file, then switch its mode (not transpose)"
feature Julian has slated for Audiology first (ROADMAP gap 26):

## 1. `confirm_key_areas` (gap 25 slice 1)

Each structural key area judged **in its own key** against the literature's #1
modulation discriminator (a tonicization does not cadence in the tonicized
key; a modulation does). Evidence, never a verdict: no `is_modulation` field;
honest refusals (`no_claim_areas`) tallied separately from `unconfirmed`.
**Usage trap you will hit, measured:** `subdivisions` must match the harmonic
rhythm — a coarser grid collapses the cadential approach into its arrival and
*hides* the cadence (same music, opposite answer). A low `chords_considered`
relative to an area's duration means the grid produced the result.

## 2. `classify_chromatic_events` (gap 25 slice 2)

Every chord whose notes leave its key area, classified **plurally**:
`borrowed_mixture` / `secondary_dominant` (with the realized-resolution
sequential signal) / `augmented_sixth_*` / `neapolitan` / `tonicization` /
`modulation` — each reading carrying the exact tests it passed, ordered by
signal count (a tally, NOT a probability). `single_label` only when the zone
is `confident` and exactly one reading fired; inside the contested band it is
`null` with the reason. Ambiguity is a **zone with coordinates**, not a label.
This is the classifier the modal transform needs — you cannot remap what you
cannot classify.

## 3. `conform_to_scale` / `fit_to_key` (Phase 7 slice 0 — the first note-OUT surface)

Register-preserving snap to a target collection; ≤ 6-semitone moves and
idempotence hold by construction. Two rulings worth knowing before you build
on it: the tie default is `"previous"` (melodic continuity against the
already-conformed line — ties are the *common* case: all five out-of-scale pcs
tie in a major scale), and snap-created collisions are **kept and reported**
(`collisions` itemizes merges; dedupe is deliberately consumer-side). This is
the note-level primitive under gap 26's `remap_by_degree` — the transform's
fallback edge, not its core (the core remaps by degree, never by proximity).

## What this means for the A6 pipeline

Nothing changes in your current consumption — all three are additive (73 MCP
tools; the bridge serves them at the same contract). But the gap 26 build
(`modal_transform` / `retonicize`, the analyze → plan → apply architecture
with a serializable plan artifact) now has every analysis prerequisite in
place, so a start signal from Audiology's side would find the runway clear.
The recorded design constraints (no 12→12 table; a *timeline* of key areas,
never one global key; alteration-preserving degree remap; drums untouched) are
in gap 26 with the full prior-art survey.

Ball: none — FYI. If A6 wants to shape `modal_transform`'s option surface
(what the caller controls vs. what defaults), a brief on this channel is the
moment; the option-exposure decisions Julian sketched (computable default,
ideal surfaced, caller-supplied via struct-but-inclusive syntax) are recorded
and waiting.
