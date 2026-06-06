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
  register from an identity; kept out of the analysis path deliberately.
- `results.py` — **typed result dataclasses**. All analysis returns these, never
  raw dicts. Top-level results expose `to_dict()` (JSON/MCP output). Add new
  result fields here, not as ad-hoc dict keys.
- `scale_analysis.py`, `chord_analysis.py` — request in, typed result out. Private
  helpers return typed sub-objects, not dicts. `analyze_chord` is **pure-identity**
  (PC-set only, invents no register); `analyze_voicing` is the register-required
  sibling that reads a `Realization` and errors without one.
- `comparisons.py`, `summaries.py` — cross-object compatibility and compact briefs.
- `builders.py` — `SessionCatalog` + manual scale/chord registration. **No
  module-level mutable state** — sessions are instances.
- `timeline.py` — STUB (`NotImplementedError`). Phase 2 replaces it with the real
  temporal layer. Don't build around the current shape.

**When adding analysis:** declare the specification level it needs (PC-set vs.
realization). Register-dependent analysis must **error** on a register-less
identity, not guess a voicing. See root CLAUDE.md.
