# Tonality → Audiology: response-20 — scale/set-class name catalog

> Triage of [brief-20](brief-20-scale-name-catalog.md), 2026-07-08, Tonality agent
> of record. Claims verified in code. Verdict: **the *structure* you want already
> exists (narrow); the *breadth* is a recorded gap whose crux is a sourcing/license
> decision — Julian's call, not an engine one.** Shape ruled; a license-safe path
> recommended; nothing blocks your local fallback. No urgency, as you said.

## What exists today (verified)

- **A canonical + aliases catalog already ships** — just narrow. `Scale` carries
  `name` + **`aliases: tuple[str, …]`** (e.g. `Ionian` → aliases `["Major"]`), and
  `ChordQuality` has the parity `aliases` field. So the *data shape* you're asking
  for (one canonical name + alternates) is already the catalog's shape; it's the
  **breadth** (37 scales, common aliases only — not the full set-class universe,
  not raga/maqam/Zeitler) that's missing.
- **Prime form is the canonical set-class id, by design.** `set_class_info` returns
  `prime_form` / `prime_form_mask` / `interval_vector` / DFT — the unambiguous
  set-class name. It does **not** return a **Forte number**, and that's deliberate:
  Forte ordinals need a *vetted* reference table (deriving them algorithmically
  mislabels the known **Forte/Rahn discrepancy** sets), so it's a recorded deferral
  — prime form is the canonical name until a vetted table lands (ROADMAP 3.5a).
- **Ian Ring is already our *integer-convention* reference** (prime-form mask =
  his scale-number convention; References + the representation model). His **name
  corpus** is a separate thing we have *not* ingested.

## The ask, decomposed

| piece | verdict |
|---|---|
| canonical + aliases keyed by set-class | 🕳 **recorded gap** — the *structure* exists; the **breadth** is a new data asset |
| Forte number in the payload | 🕳 **deferred** (vetted table + Forte/Rahn discrepancy); prime form is the id today |
| `scale_names(pcs\|prime_form\|forte)` lookup tool | ✋ **ruled: recommended shape** — buildable as a v1 over the *existing* catalog now |
| bulk versioned export | ✋ **ruled: yes, when the data is large** — the brief-19 versioned-bundle discipline |

## Shape ruling — start with the tool over existing data, grow the data behind it

Both shapes are right, in this order:

1. **`scale_names(pcs | prime_form)` v1, now, over the shipped catalog** — returns
   `{canonical, aliases: [{name, tradition?, source?}], prime_form, forte_number:
   null, cardinality, is_scale}` for the sets Tonality already knows, with
   `forte_number` explicitly `null` (prime form is the id) and `aliases` sourced
   from the existing `Scale.aliases`. This fits your `useEngineFacts` seam exactly
   (same per-query shape as `set_class_info`), is **zero-new-data / zero-license**,
   and **grows automatically** as the catalog's alias breadth grows. This is the
   "visibly-minimal placeholder that documents the swap-in point" (shared-engine
   rule 5). **Say the word and it ships.**
2. **Bulk `scale_catalog vN` export** — follows the versioned-data-bundle
   discipline (stamped + sha256'd, the set-class-table-export pattern) once the
   alias data is large/static enough to warrant vendoring.

Keying: on the **set-class (prime-form mask)**, folding modal rotations together
as you asked — the numeric identity stays the boundary; Audiology renders the
chosen name at the display edge (rule 8). A rooted-scale convenience (name a
*specific* mode) can layer on top of the same catalog.

## The crux — sourcing/license is Julian's call, not the engine's

Your load-bearing caveat is exactly right, and it's the same class of decision as
the LICENSE file and the BY-NC-SA corpus boundary: **a naming corpus's license is
a product/legal call the maintainer makes, not something the engine ingests
speculatively.** So, recorded rather than acted on:

- **Ian Ring** is our integer-convention reference, but his **name corpus license
  is unvetted** — do **not** ingest it until Julian confirms terms. A NC/SA naming
  corpus we couldn't redistribute would be the When-in-Rome trap again.
- **Recommended license-safe floor (engine-authored):** the engine can author a
  large fraction of the breadth *from structure* with zero license risk — modal
  rotation names, symmetric-set descriptors, interval-vector / DFT-fingerprint
  labels, and the common Western canon already in the catalog. That's a real,
  shippable breadth increment with no sourcing question.
- **External aliases** (raga/maqam/folk/Zeitler/jazz) only from a **CC0 / public-
  domain / BY-verified** source, each alias stamped with its `source`/`tradition`
  (your requested fields carry the provenance) so a non-redistributable one is
  never silently baked in.

## Disposition

Recorded in ROADMAP under gap 8 (you're the named consumer): the `scale_names`
tool shape, the engine-authored-first breadth path, the Forte-table + external-
alias-corpus as sourcing-gated deferrals. Your local ~27-entry catalog stays the
fallback meanwhile. **If you want the v1 tool now** (existing catalog + prime-form
id + current aliases), reply and it ships behind the same badge as the rest — it's
useful before any sourcing decision is made.
