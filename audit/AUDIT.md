# Tonality — Audit Charter

> Contract for the **audit thread**: a parallel loop that periodically checks the
> engine's current capabilities and surfaces bugs/inconsistencies. This file is the
> fence that keeps the audit and the main development loop from stepping on each
> other. Read it fully before running.

The audit's job is to **find and report**, not to fix. Fixes are the dev loop's job.

## 1. Isolation — run in your own git worktree (never the shared checkout)

Two agents in one working directory collide (uncommitted files get swept into the
other's commits — this already happened once). So the audit runs in a **separate
worktree**, sharing history but with its own files:

```bash
# from the main repo root, once:
git worktree add ../tonality-audit -b audit main      # new dir + new 'audit' branch
cd ../tonality-audit
# use the SAME interpreter (the venv lives at the main repo root):
/Users/machinepriest/Documents/Tonality/.venv/bin/python3.13 -m pytest audit/checks -q
# when done with a cycle:
#   git worktree remove ../tonality-audit     (from the main repo)
```

Notes:
- The worktree shares `.git`; **tracked** files come from the branch, **untracked**
  files are per-worktree (they do *not* leak into the dev checkout).
- One audit worktree at a time; rebase the `audit` branch onto `main` between cycles
  to audit current code.

## 2. Read-only / additive only

- **No edits to `mts/` (incl. `mts/data/`), `scripts/`, `tests/`, `ROADMAP.md`, `CLAUDE.md`.**
  Those belong to the dev loop. The audit only writes under `audit/` and files issues.
- No `git checkout`/`reset`/`pull`/`branch -d`/`push --force` on shared refs; never
  touch the dev loop's branches, open PRs, or `main`.
- Use an isolated, throwaway session path for anything stateful
  (`.tonality_session.json` is gitignored user state — point at a temp file).
- Ignore `build/` (stale generated copy) — never trust or report hits there.

## 3. Where things live (the fence)

| Thing | Location | Runs in dev Stop hook (`pytest tests/`)? |
|---|---|---|
| Dev regression suite | `tests/` | **yes** (must stay green) |
| Audit invariant checks | `audit/checks/` | **no** — fenced via `testpaths=["tests"]` |
| Audit charter (this file) | `audit/AUDIT.md` | n/a |

Because `audit/checks/` is **out of `tests/`**, a dev-loop fix can never redden the
audit's strict-xfails in the dev Stop hook, and vice versa. Run audit checks
explicitly: `pytest audit/checks`.

## 4. How to flag findings

**Bugs → GitHub issues** (primary, visible, triageable):

```bash
gh issue create --label audit --label "severity:high" \
  --title "Catalog: <one line>" \
  --body "Contract violated: <CLAUDE/ROADMAP rule>. Repro: <code>. Expected/Actual: ..."
```

Every finding must state **(a) severity** (`severity:high|med|low`), **(b) the
contract it violates** (cite CLAUDE.md / ROADMAP / a stated invariant), and
**(c) a minimal repro**. Labels: `audit`, `severity:*`, plus `bug` / `data` / `docs`.

**Optionally** back an issue with a strict-xfail check **in `audit/checks/` on the
audit branch** (never in `tests/`), referencing the issue number in its `reason`.
That auto-alerts (flips to a failure) when the bug is fixed. Keep the lifecycle on
the audit branch.

**Standing invariant checks** (not tied to a specific bug) live in `audit/checks/`.
When one proves its worth as permanent regression protection, **propose promoting it
into `tests/`** via a normal PR (the dev loop reviews + de-dupes against existing
tests). Don't add to `tests/` unilaterally.

## 5. Ground truth — what counts as a bug vs a known gap

- **`ROADMAP.md` = intended state.** Anything unchecked, "deferred", "parked", or
  "future" is a **known gap, not a bug** — don't file it. (E.g. functional harmony
  being major/minor-only; no `interpret_scale` yet; the parked CLI branch.)
- **`CLAUDE.md` = the contracts to audit against** (frozen/hashable core; mod-12
  identity; "analysis is numeric, display at the edge"; "reduce never invent / error
  don't guess"; typed results with `to_dict`).
- **`gh pr list` = in-flight.** Skip areas under open PRs (auditing half-merged work
  produces transient false positives). Rebase onto `main` to get merged state.

## 6. Prefer invariants over exact outputs

Assert on **behavioral contracts**, not exact strings/field shapes — otherwise every
dev refactor (e.g. the Phase 3 display cut moved ~90 fields) trips the audit with
false positives. High-value invariant families for this engine:

- **Catalog integrity** — every interval/degree ∈ 0–11; no *unexpected* mask
  collisions (see allowlist below); every alias resolves to its canonical object.
- **Reduction round-trips** — `Realization.reduce_to_key()` == `mask_from_pcs(distinct pcs)`; PCs↔mask round-trip; MIDI events → write SMF → ingest → equal events.
- **`interpret_chord`** — every interpretation's mask == input mask; symmetric-set
  interpretation counts match the symmetry order.
- **Display-free analysis** — `analyze_chord`/`analyze_scale` results contain no
  note-name strings (spelling is edge-only).
- **Transpose invariance** — interval vector / symmetry stable under transposition.
- **Determinism** — same input → identical output.
- **External ground truth (stretch)** — cross-check interval vectors / symmetry /
  Forte numbers against Ian Ring's "A Study of Scales" (ROADMAP reference).

## 7. Known limitations — do NOT file these as bugs

12-TET cannot faithfully represent every named scale, so distinct cultural/tuning
scales legitimately share a 12-TET footprint. Treat the following as **accepted
equivalences** (allowlist), and only flag *new/undocumented* footprint collisions:

- `Pelog Selisir` ≡ `Major Pentatonic` `[0,2,4,7,9]` — 12-TET approximation
  limitation; proper resolution is Phase 6 (beyond-12-TET). See ROADMAP Phase 6.

(Expand this allowlist as Phase 6 adds scales whose 12-TET footprints coincide.)

## 8. Quick "don'ts" recap
- Don't run in the dev checkout — use a worktree.
- Don't edit `mts/` (incl. `mts/data/`)/`tests/`/`scripts/`/docs — issues + `audit/checks/` only.
- Don't put audit checks in `tests/`.
- Don't file known gaps (ROADMAP) or in-flight-PR areas as bugs.
- Don't `git add -A` — scope every add.
