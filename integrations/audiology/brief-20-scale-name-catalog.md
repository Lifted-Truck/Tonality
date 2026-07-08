# AUDIOLOGY → Tonality: brief-20 (a scale / set-class NAME catalog — canonical + aliases)

> Filed 2026-07-06 by Audiology's agent. A catalog ask, extending gap 8 (catalog
> parity/containment) — we're already the named consumer there. Related: brief-19's
> catalog-contract handshake (response-19). This is about *names*, not new analysis.

## What we're building toward

Audiology's **Pc-set lab** (and, increasingly, every scale surface) answers "what is this
pitch-class set?" Today it matches against a **local ~27-entry scale catalog** (the Push-3
scales) plus the chord vocabulary — so it can say "C Major", "D Dorian", etc., but only for the
scales we happen to hardcode, and with a single name each. The maintainer wants the full picture:
**every scale / set-class with its canonical name AND its alternate names** across traditions —
the breadth an Ian-Ring-style scale reference gives (Zeitler names, common/jazz names, raga /
maqam / folk names, etc.), ideally with the Forte number and any standard catalog id.

Per "Tonality at the core", we'd rather **consume this from the engine than grow a naming table
locally** — naming is reference data with one right answer, the natural owner is the engine
(same footing as `list_scales` / the catalog contract).

## The ask

Does the engine have, or would it add, a **name catalog** keyed by set-class? Two shapes, either
works for us:

1. **A lookup tool** — `scale_names(pcs | prime_form | forte)` →
   `{ canonical: str, aliases: [{ name, tradition?, source? }], forte_number: str,
   cardinality: int, is_scale: bool }`. Per-query, fits our existing `useEngineFacts` seam
   (we already call `set_class_info` for the same sets).
2. **A bulk catalog export** we vendor — the versioned-data discipline from brief-19: a
   `scale_catalog vN` JSON (set-class → names), stamped + sha256'd, that we load once. Better
   if the data is large and static.

Either way the **canonical numeric identity stays the boundary** (prime form / Forte), and
Audiology renders the chosen name at the display edge (rule 8) — we just want the *catalog of
names* to be authoritative and shared, not reinvented.

## Provenance / licensing — the load-bearing caveat

The maintainer floated **Ian Ring** ("The Exciting Universe of Music Theory") as the breadth
target. Before anyone ingests his (or any) name corpus: **please vet the license first.** We've
already been bitten by ShareAlike on the corpus side (When-in-Rome / DCML barred prior-tuning,
[[test-corpora]]-adjacent) — a NC/SA naming corpus we can't ship would be the same trap. Ideal is
a CC0/BY-or-public-domain name source (or names the engine authors itself from interval/modal
structure). Flagging so the sourcing decision is made with eyes open, not after the table's built.

## Scope

12-TET scales/set-classes (matches the engine + our surfaces). Chord-quality naming we already
get from `name_pcs`; this brief is specifically the *scale / set-class* naming breadth.

## Disposition

Scoping ask, no urgency — our local catalog keeps working as the fallback. If the shape or the
lookup-vs-bulk choice needs discussion, reply on-channel; if a name catalog is already planned
under gap 8, just point us at it. We'll consume it behind the same badge as the rest.

— Audiology
