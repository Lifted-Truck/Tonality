# INDEX — knowledge retrieval map

The retrieval layer for the [Self-Improving Knowledge Loop](CLAUDE.md#self-improving-knowledge-loop).
**Read this file in full at the start of each session** (it is kept deliberately
small), then pull ONLY the matching entries from [LIBRARY.md](LIBRARY.md) into
context — never load all of LIBRARY by default.

Each line: `[Lxxxx] tags — one-line hook → resolves to the LIBRARY anchor`.
`†` marks a `candidate` (unpromoted) lesson; canonical lessons carry no mark.

## Tags
`workflow` · `architecture` · `contracts` · `coordination` · `theory-traps`

## Entries
- [L0001]† `workflow,contracts` — a new MCP tool needs a conformance CASE or the total ratchet fails; regenerate goldens additively in the same PR.

<!--
Scope reminder (full rules in CLAUDE.md § Scope boundary): LIBRARY holds only
repo-shared agent-PROCESS lessons. Decisions/plans → ROADMAP.md; code-structure
facts → per-layer CLAUDE.md; user-private machine-local state → ~/.claude memory.
Never edit INDEX without LIBRARY, or vice versa.
-->
