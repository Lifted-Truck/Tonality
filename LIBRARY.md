# LIBRARY — durable, evidence-backed lessons

Long-term memory for the [Self-Improving Knowledge Loop](CLAUDE.md#self-improving-knowledge-loop).
**Repo-shared agent-process lessons only** — the hard-won, evidenced "how to work
in this repo without re-tripping a wire." Not decisions/plans (→ ROADMAP.md), not
code-structure facts (→ per-layer CLAUDE.md), not user-private machine-local state
(→ `~/.claude` auto-memory). See CLAUDE.md § Scope boundary before adding.

Entries are retrieved via [INDEX.md](INDEX.md); every entry has an `[Lxxxx]` anchor
that INDEX points to. New lessons enter as `tier: candidate` and are promoted to
`canonical` on a second independent occurrence or human review. Each entry states
its own **falsifier** — the observation that would retire it (trust present
evidence over any stored lesson).

**Entry template**

```
[Lxxxx] <title> | tier | added: YYYY-MM-DD | tags: … | lesson: … | evidence: … | falsifier: … | supersedes: …
```

---

### [L0001] A new MCP tool requires a conformance case

`tier: candidate` | `added: 2026-07-07` | `tags: workflow, contracts` | `supersedes: —`

- **lesson:** The conformance harness (`tests/test_conformance.py`) enforces
  **total** tool coverage (no exclusions since RE-4b): any function added to
  `mts/mcp/tools.py`'s `TOOLS` tuple without a matching entry in `CASES` fails
  `test_every_tool_has_a_conformance_case`. Add the `CASES` entry and regenerate
  the golden in the **same** PR — `PYTHONPATH=. .venv/bin/python3.13
  tests/test_conformance.py --regenerate` — where a brand-new tool's diff is
  **purely additive** (new lines, zero deletions); any deletion/modification means
  you changed existing output and must justify it.
- **evidence:** Adding `search_identities` (PR #147) tripped exactly this failure;
  adding its `CASES` entry + regenerating produced a `+148 / -0` golden diff,
  confirming no existing behavior moved.
- **falsifier:** `test_conformance.py` stops asserting total tool coverage (e.g.
  `EXCLUDED_TOOLS` is reintroduced), or the golden stops being the tool oracle.
