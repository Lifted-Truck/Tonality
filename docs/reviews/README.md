# Review archive

Durable copies of the **visual-first review documents** produced alongside major
changes — the "evaluate the change without reading the diff" reports (per the
development doctrine: lead a review with a self-contained visual). Each is a
standalone HTML file (inline CSS/SVG/JS, no external dependencies) — open it
directly in a browser.

These are **evidence for posterity**, not living docs: each is a snapshot tied to
the PR/phase named below. Decisions they informed live in
[ROADMAP.md](../../ROADMAP.md); this folder preserves the reasoning-at-the-time.

| File | Date | Tied to | What it shows |
|---|---|---|---|
| [2026-07_re6-decisions.html](2026-07_re6-decisions.html) | 2026-07 | RE-6 (PRs #143–#145) | The three RE-6 decisions put to review: rank base (1-based), list→tuple on frozen dataclasses, and the RE-6b session/import-cycle plan. |
| [2026-07_re6b-plan.html](2026-07_re6b-plan.html) | 2026-07 | RE-6b (PR #146) | The module-relayering plan (notation/session below `io/`) and the retire-vs-keep-the-default-session fork. |
| [2026-07_next-frontier.html](2026-07_next-frontier.html) | 2026-07-07 | Post rigor-&-efficiency review | The four open build frontiers after RE-1→RE-6, with the recommendation that led to picking Phase 4 constraint search. |
| [2026-07_search-identities-review.html](2026-07_search-identities-review.html) | 2026-07-07 | Phase 4 · `search_identities` (PR #147) | The build review with live engine output — the marquee query, exact set-class oracles, strict validation, and Decision 12. |
| [2026-07_search-voicings-design.html](2026-07_search-voicings-design.html) | 2026-07-07 | gap 17 · design brief (pre-PR #157) | The `search_voicings` design: the bounded register space, reused primitives, and the four design forks (A–D) put to review. |
| [2026-07_search-voicings-review.html](2026-07_search-voicings-review.html) | 2026-07-07 | gap 17 slice 1 · `search_voicings` (PR #157) | The build review — live ranked-voicing evidence, the Fable-pass design deltas, and the honesty guarantees. |
| [2026-07_rhythm-search-assessment.html](2026-07_rhythm-search-assessment.html) | 2026-07-07 | gap 21 (recorded, unscheduled) | The rhythmic-constraint-search assessment — the pitch/rhythm isomorphism (diatonic = bembé), field mapping, and the three design realities behind gap 21. |
| [2026-07_melodic-tendency-design.html](2026-07_melodic-tendency-design.html) | 2026-07-07 | gap 19 · design brief (pre-build) | The `melodic_tendency` design: Lerdahl attraction over frozen KK stabilities with live-computed evidence, and the three forks (stability source, target policy, chord anchoring). Minor-mode oracle corrected post-review. |

Also published as claude.ai artifacts at build time; these committed copies are the
version-controlled record that travels with the repo.
