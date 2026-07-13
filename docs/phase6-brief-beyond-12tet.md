# Phase 6 Brief — Generalizing Beyond 12-TET — ⟢ HANDLED / TOMBSTONE

**Status (2026-07-13): folded into ROADMAP.md → "Phase 6 (future) — Beyond
12-TET" → "Design input (2026-07-13, brainstorm-grade)". This file is a
tombstone — not new work, not a live spec.**

The brief's future-relevant substance (the exact-math-vs-empirical-priors fault
line, the Z_N scope decomposition, the tiered cache, per-system priors with
`system_supported=false`, the per-system-catalog-vs-ratio-projection posture,
spelling-at-the-display-edge, the migration/acceptance gates, and the
`system`-on-identity-vs-context open question) now lives in **ROADMAP.md Phase
6**, recorded as *proposals pending a Phase 6 ADR* — plus two dev-loop review
corrections folded in the same pass:

1. the "Decision 6 already localized N=12 to two files" premise is **too
   optimistic** — the exact-math kernel is 12-hardcoded across ~6–20 files
   (verified by grep); and
2. the 12→24 embedding acceptance test's correspondence is a **scaling map**
   (`prime_form₂₄(2S) = 2·prime_form₁₂(S)`), **not** integer equality.

Per this repo's doctrine, **decisions live in ROADMAP, not `docs/`.** A future
agent should treat Phase 6 as *recorded-but-unratified*, not as an untriaged
brief. The original text is recoverable from git history if the reasoning trail
is ever needed.
