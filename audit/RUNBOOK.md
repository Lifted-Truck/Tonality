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
