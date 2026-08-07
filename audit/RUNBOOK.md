# Audit loop — runbook (the executable cycle)

> The **[AUDIT.md](AUDIT.md) charter is binding** — read it first every cycle;
> this file is only the repeatable *procedure* that runs it. One cycle = one
> pass of the steps below. The audit **finds and reports; it never fixes**
> (fixes are the dev loop's job) and it **only writes under `audit/` or as
> GitHub issues** — never `mts/` `tests/` `scripts/` `docs/` `ROADMAP.md`
> `CLAUDE.md`.

## 0. Preconditions (one of two isolation modes)

The audit must never share a working directory with the dev loop (uncommitted
files collide — it has happened). Pick the mode that matches how the loop runs:

**Mode A — cloud / fresh clone (recommended for a scheduled routine).** A fresh
`git clone` is self-isolating; no worktree needed.
```bash
git clone <repo> tonality-audit && cd tonality-audit
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev,mcp]'          # mcp so the full tool surface imports
```

**Mode B — local worktree (this Mac).** Share history, isolate files; use the
main repo's venv.
```bash
git worktree add ../tonality-audit -b audit-cycle origin/main   # fresh per cycle
cd ../tonality-audit
PY=~/Documents/Tonality/.venv/bin/python3.13
# cleanup at cycle end (from the main repo): git worktree remove ../tonality-audit
```

Either way: **audit `origin/main`'s current tip.** Rebase/re-clone each cycle so
you audit merged code, not a stale branch.

## 1. Scope the cycle (avoid false positives)

- `gh pr list --state open` → **skip areas under open PRs** (auditing
  half-merged work produces transient noise). Note which subsystems are in-flight.
- Skim `ROADMAP.md` for what's **intended-but-unbuilt** — anything unchecked /
  "deferred" / "parked" / "future" is a **known gap, not a bug** (charter §5).
  Recent deltas to know: harmony rule family shipped (gap B); CI enforces
  `pytest tests/` + `pytest audit/checks/` on every PR; port pin fingerprints
  only integer fields (floats are tolerance-checked).
- Note the commit you're auditing: `git rev-parse --short HEAD`.

## 2. Run the committed checks (regression floor)

```bash
$PY -m pytest audit/checks -q          # the standing invariants
```
These now also run in CI — so a *committed* audit check that fails is already
loud on PRs. Your value this cycle is **finding what isn't yet covered.**

## 3. Explore for new findings (the actual audit)

Pick 1–3 invariant families from charter §6 that the current diff/subsystems most
stress, and probe them **as behavioral invariants, not exact outputs** (§6 —
exact-output asserts trip on every refactor). High-value families:
identity/reduction round-trips · `interpret_chord` mask consistency ·
display-free analysis (no note-name strings in `analyze_*`) · transpose
invariance · determinism (same input → identical output) · catalog integrity ·
(stretch) external ground truth vs Ian Ring.
Bias toward subsystems that changed since the last cycle (check `git log` since
the last audit tag/issue) and toward the newest surface (e.g. the `search/` and
`harmony`-family code, `melodic_tendency`, the style-profile pieces).

**Then run the efficiency & complexity pass (charter §6b) — every cycle.** Two
parts: (1) a **structural read** of the newest/most-scalable code for the
scan-inside-a-loop / re-derivation / O(n²)-structure / unbounded-cache
anti-patterns (this is how #206 and #214 were both caught — by loop shape, not
timing); and (2) the **empirical probe**:
```bash
$PY audit/checks/scaling_probe.py     # exponents for the temporal entry points
```
Add the cycle's newest scalable surface to that file's `__main__` (a probe is
three lines: `make_input(n)`, the callable, one `report(...)`). A fitted exponent
> ~1.4 on a should-be-linear path is a §4 finding. **Never** commit a wall-clock
assertion as a collected `audit/checks/test_*` — CI runs those and timing flakes;
the probe stays a hand-run utility whose output is an issue or a cycle-log line.

**Then run the semantic-coherence pass (charter §6a) — every cycle, not optional.**
Unlike the families above, this is a *reading* pass, not a code run: check that the
system still makes coherent sense across code + docs + decisions + `integrations/`
rulings. Concretely each cycle: (a) does the doctrine actually hold in the changed
code (error-don't-guess, plural/evidenced, priors cited, generative-labeled)? (b)
do docstrings / per-layer `CLAUDE.md` / `README` / `INTEGRATION.md` / ROADMAP
"shipped" claims match what the code now does? (c) is any term of art redefined
between code and docs? (d) is any ROADMAP decision or `integrations/` response
ruling contradicted by newer code or a newer notice? (e) did any frozen schema/prior
version change without a bump? File contradictions as §4 findings (the two
locations + the violated claim); a clean pass is logged, not silent.

## 4. File findings (charter §4 format — every finding needs all three)

```bash
gh issue create --label audit --label "severity:high|med|low" \
  --title "<subsystem>: <one line>" \
  --body "Contract violated: <cite CLAUDE.md / ROADMAP / stated invariant>.
Repro: <minimal code>.
Expected vs Actual: <...>.
Audited at: <commit>."
```
Optionally back a bug with a **strict-xfail check in `audit/checks/`** (never
`tests/`) referencing the issue number in its `reason` — it flips to a failure
(auto-alert) when the dev loop fixes it. A standing invariant that earns its keep
gets **proposed for promotion into `tests/` via a normal PR** — never added there
unilaterally.

## 5. Close the cycle

- If you added checks, commit them on the audit branch only (`git add audit/…`,
  never `-A`).
- Mode B: `git worktree remove ../tonality-audit` from the main repo.
- **Append one line to the cycle log below** (date · commit · #issues filed ·
  families probed) so the next cycle sees coverage history and doesn't re-till
  the same ground.

## Cycle log

| Date | Commit | Issues filed | Families probed | Notes |
|---|---|---|---|---|
| _(seed)_ | — | — | — | Loop (re)prepared 2026-07-08; awaiting first scheduled cycle. |
| 2026-08-03 | `5c55f58` | #245 (high, mcp packaging), #246 (med, efficiency), #247 (med, semantic/RE-3d recurrence), #248 (low, docs), #249 (low, docs) | catalog integrity, reduction round-trips, determinism, display-free analysis (drum patterns) · efficiency §6b structural read + scaling probe (drums/parts/relations/rules/repair/mcp tools) · semantic coherence §6a (README tool count, ROADMAP repair contract, tool-manifest-pin, vocabulary) · MCP security fixes re-attacked (tool-manifest pin, path traversal) | #245: `mcp>=1.2` unbounded breaks `build_server()` against current PyPI `mcp==2.0.0` (FastMCP removed), invisible to CI (`.[dev]`-only install). #246: `drums.py _match()` rescans onsets per bar per pattern, exponent≈1.81 (same class as #206/#214). #247: `repair_sequence.already_conformant` reintroduces the RE-3d "held vs never-tested" conflation one layer above the evaluator. #248/#249: doc drift (tool count 57→69; repair contract missing budget-gating post-#230). Both MCP security hardenings (tool-manifest pin, path-traversal fix) re-attacked and held. All five closed by PR #252 (`8bcd3d2`). |
| 2026-08-07 | `c54ada8` | #254 (low, docs), #255 (low, docs), #256 (med, efficiency) | **Fix verification** of #245–#249 · determinism, display-free analysis, error-don't-guess, transpose invariance on the new gap-25 surface · efficiency §6b (committed probe + structural read of the new modules) · semantic coherence §6a (gap-25 ROADMAP↔code, tool-manifest pin, LIBRARY/INDEX scope boundary) | **Procedural note for future cycles: this run began against a stale checkout (`5c55f58`) and re-derived all five findings that the 2026-08-03 cycle had already filed — RUNBOOK §0's "audit `origin/main`'s current tip, re-fetch each cycle" is load-bearing; `git fetch origin main` BEFORE probing, not after.** Rebased to `c54ada8` and verified every 2026-08-03 finding is genuinely fixed, by execution not by reading the fix commit: #245 `build_server()` constructs (pyproject now pins `mcp>=1.2,<2` with the 2.0.0 rationale in-comment; venv resolves 1.29.0); #246 `drums._match` now takes a caller-bucketed `{role: {bar: {beat}}}` — O(1) per-bar lookup, no rescan; #247 `already_conformant` is now tri-state, returning `None` + an explicit "conformance was never tested … 'Held' and 'never tested' are different answers" reason; #248 README says 71, live `len(TOOLS)`==71, golden `tool_count`==71; #249 ROADMAP now states "**Two polarities gate: hard must hold AND every budget rule must be back within its ceiling**". New surface probed: `temporal/key_confirmation.py` + `temporal/chromatic.py` (gap 25 slices 1–2, ~620 lines) and their 2 new MCP tools — **clean** on determinism (byte-identical `to_dict()` across `PYTHONHASHSEED` 0/1/42/12345 in separate processes), display-free analysis (0 note-name hits over all result strings; pcs are integers), error-don't-guess (empty seq / bad `subdivisions` → `ValueError`; all-12-pc → `InsufficientInformation`; one nameable chord → `claim_possible=False` tallied in `no_claim_areas`, never a modulation verdict), and transpose invariance (12 transpositions × 2 entry points, key-relative fields move, shape fields don't). **Findings: #256** — both new modules join areas↔spans by linear scan (`key_confirmation.py:135-139`; `chromatic.py:241`→`_area_of:285`, plus a per-secdom `spans[index+1:]` copy at `:337`), isolated exponents **1.87 / 1.89**, `confirm_key_areas` entry point **1.43** on an areas-dense fixture — the 4th instance of the #206/#214/#246 shape. **#254/#255** from the §6a pass: `INTEGRATION.md:203` still says "46 tools" (the #248 sweep fixed README only, leaving the *consumer-facing* door doc stale), and `INDEX.md:16` omits L0002's `†` so the loop's own ORIENT surface renders a same-day `tier: candidate` lesson as canonical. Observed, deliberately **not** filed: `classify_chromatic_events(confirmation=…)` keys `confirmed_by_span` on `(start_beats, end_beats)` floats, so a confirmation computed from a *different* sequence silently misses and drops the cadence-confirmed signal — but that is caller misuse of a documented reuse hook (docstring: "reuse an existing `KeyAreaConfirmationResult` instead of recomputing"), and in correct usage the areas come from the same object; revisit if the param ever becomes public-facing. Green at HEAD: `pytest tests/` 1124 passed, `audit/checks` 3 passed, `test_tool_manifest_pin` 14 passed; committed scaling probe `part_profiles` exp≈1.03, `part_relations` exp≈1.13 (both ≤1.4). |
