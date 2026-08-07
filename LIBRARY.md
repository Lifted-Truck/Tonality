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

---

### [L0002] GitHub closes only the issue whose number carries the keyword

`tier: candidate` | `added: 2026-08-07` | `tags: workflow, coordination` | `supersedes: —`

- **lesson:** A closing keyword binds to **one** issue reference. A PR titled or
  bodied `closes #245 #246 #247 #248 #249` auto-closes **only #245** — the bare
  numbers after it are plain links, not closers. Repeat the keyword per issue:
  `closes #245, closes #246, …`. This matters here because the audit thread files
  findings as issues and the dev loop routinely answers several in one sweep PR,
  so the failure mode is a merged, genuinely-fixed sweep leaving issues open and
  the board reading stale.
- **evidence:** PR #252 (audit sweep, 2026-08-07) fixed and shipped #245–#249;
  after merge only #245 was CLOSED and #246–#249 were still OPEN, closed manually
  afterwards. The identical wording had been used on the earlier #204–#208 sweep.
- **falsifier:** GitHub changes the linked-issue parser to accept a keyword
  followed by a list of references (watch the docs for "linking a pull request to
  an issue"); then a single keyword would suffice and this lesson is obsolete.

---

### [L0003] Joining two co-scaling collections: reach for the shared helper, never a rescan

`tier: canonical` | `added: 2026-08-07` | `tags: workflow, architecture` | `supersedes: —`

- **lesson:** This repo's single most-repeated defect is **a scan or membership
  test inside a loop over a collection that grows with the same input** — four
  independent occurrences, each written by a different session that had no idea
  the previous three existed, each caught only by the audit thread's §6b probe,
  each fixed by the same remedy (bucket/index once, before the loop). Before
  writing any join of two time-ordered streams, use the existing helper —
  `structural_key.area_indices` for areas×beats, `segmentation._sweep_active` for
  the onset sweep — rather than an inline comprehension that reads correctly and
  scales quadratically. Two corollaries earned the hard way: the defect is
  **invisible at test-fixture scale** (shipped tests run 8–16 bars), and it is
  often **masked by a slower neighbour** (#256 sat under `segment_to_chords`), so
  "the tests pass and it feels fast" is not evidence. Verify a fix by
  **byte-comparing old vs new output**, not by re-running the suite: every one of
  these refactors touched a hot path where a subtle off-by-one would pass the
  tests it had.
- **evidence:** #206 `part_profiles` · #214 `part_relations` (165×) · #246
  `drums._match` (exponent 1.81→0.71) · #256 `key_confirmation` + `chromatic`
  (1.90→0.98, 28× at 1200 bars). In #256 two modules written **in the same week
  by the same agent** each re-derived the same quadratic join independently.
- **falsifier:** a fifth occurrence appears in code that *did* use the shared
  helper (⇒ the helper, not the reaching-for-it, is the problem), or `audit/`
  stops running the §6b scaling probe (⇒ the detection this lesson relies on is
  gone and the claim is unverifiable).
