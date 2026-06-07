# mts/analysis — Enrichment engine

Turns identities into contextualized analysis. Pure functions over `core` objects;
no session state here (that lives in `workspace`/`SessionCatalog`).

- `specs.py` — the multi-notation parser (intervals, degrees, note names, MIDI,
  catalog names). This *is* the "various timeless notations" feature. Its
  `scope` literal (abstract/note/absolute) is now an additive compat alias over
  the `core/spec_level.py` lattice: `from_scope`/`to_scope` bridge the two, and
  `ChordSpec.spec_level` / `ChordParseResult.to_realization()` expose the lattice
  view. `scope` is a *diagonal* — it cannot express the registered+rootless cell.
- `errors.py` — `SpecificationError` + `require_realization`, the guard for the
  cardinal rule. Register-dependent analysis calls the guard and **errors** when
  handed a register-less identity instead of inventing a voicing.
- `voicings.py` — `suggest_voicings`: **generative**, not analysis. It invents
  register from an identity; kept out of the analysis path deliberately. An
  extensible registry (`_VOICING_BUILDERS`) produces a named vocabulary
  (closed, drop-2/3, rootless, shell, …); `voicing_shapes` exposes those spacings
  as the single source of truth shared with recognition.
- `equivalence.py` — `interpret_chord`: identity-level analysis enumerating every
  valid `(root, quality)` naming of a PC set (symmetric chords name at several
  roots; ambiguous sets name as several qualities, e.g. C6 = Am7).
- `analytical_context.py` — `AnalyticalContext` (tonal center + optional key) and
  `contextualize_chord` → `ChordInKey` (scale-degree placement, diatonic vs
  chromatic). The **analytical** frame; the counterpart to the display-edge
  `DisplayContext` in `mts/context/`. Numeric only; foundation for context-sensitive
  naming + dataset records.
- `results.py` — **typed result dataclasses**. All analysis returns these, never
  raw dicts. Top-level results expose `to_dict()` (JSON/MCP output). Add new
  result fields here, not as ad-hoc dict keys. **Numeric/PC only** — no spelled
  `note_names`, no styled interval labels, no enharmonic spellings (those are a
  display concern; render at the edge via `mts/context/result_format.py` from a
  `DisplayContext`). Litmus test: if a value changes when you flip sharps↔flats
  or numeric↔classical, it's display and does **not** belong here.
- `scale_analysis.py`, `chord_analysis.py` — request in, typed result out. Private
  helpers return typed sub-objects, not dicts. Requests carry **no display params**
  (spelling/key-signature/label-style live on the `DisplayContext`). `analyze_chord`
  is **pure-identity** (numeric only; `Inversion`s carry figured-bass — structural,
  not spelling); `analyze_voicing` is the register-required sibling that reads a
  `Realization`, errors without one, and *recognizes* the actual bass inversion +
  voicing type (matched against `voicing_shapes`).
- `mts/context/result_format.py` (display edge, not this layer) — renders numeric
  results into spelled/labeled views from a `DisplayContext`
  (`format_chord_analysis`, `format_scale_analysis`, `name_interpretations`,
  `spell_voicing`). Display imports analysis; analysis never imports display.
- `comparisons.py`, `summaries.py` — cross-object compatibility and compact briefs.
- `builders.py` — `SessionCatalog` + manual scale/chord registration. **No
  module-level mutable state** — sessions are instances.
- `timeline.py` — **DEPRECATED stub**, superseded by the `mts/temporal/` package
  (Phase 2). Kept only for the legacy `workspace.analyze_timeline` path pending
  migration. Build temporal code in `mts/temporal/`, not here.

**When adding analysis:** declare the specification level it needs (PC-set vs.
realization). Register-dependent analysis must **error** on a register-less
identity, not guess a voicing. See root CLAUDE.md.
