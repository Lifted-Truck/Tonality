# mts/analysis — Enrichment engine

Turns identities into contextualized analysis. Pure functions over `core` objects;
no session state here (that lives in `workspace`/`SessionCatalog`).

- `specs.py` — the multi-notation parser (intervals, degrees, note names, MIDI,
  catalog names). This *is* the "various timeless notations" feature. Its
  `scope` literal (abstract/note/absolute) is the seed of the identity lattice —
  Phase 1 promotes it into `core`.
- `results.py` — **typed result dataclasses**. All analysis returns these, never
  raw dicts. Top-level results expose `to_dict()` (JSON/MCP output). Add new
  result fields here, not as ad-hoc dict keys.
- `scale_analysis.py`, `chord_analysis.py` — request in, typed result out. Private
  helpers return typed sub-objects, not dicts.
- `comparisons.py`, `summaries.py` — cross-object compatibility and compact briefs.
- `builders.py` — `SessionCatalog` + manual scale/chord registration. **No
  module-level mutable state** — sessions are instances.
- `timeline.py` — STUB (`NotImplementedError`). Phase 2 replaces it with the real
  temporal layer. Don't build around the current shape.

**When adding analysis:** declare the specification level it needs (PC-set vs.
realization). Register-dependent analysis must **error** on a register-less
identity, not guess a voicing. See root CLAUDE.md.
