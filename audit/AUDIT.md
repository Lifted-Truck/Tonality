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
~/Documents/Tonality/.venv/bin/python3.13 -m pytest audit/checks -q
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

> **CI runs `audit/checks/` too (added 2026-07-08, `.github/workflows/ci.yml`).**
> A *committed* audit check is now **enforced on every PR** — a strict-xfail that
> flips to a failure (a fixed bug, or a new regression) is loud at PR time, not
> only in a manual run. This sharpens the split: the audit thread's job is to
> **find what isn't yet covered** and add checks; the checks it commits are then
> guarded by CI automatically. The repeatable per-cycle procedure is in
> **[RUNBOOK.md](RUNBOOK.md)**.

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

### 6a. Semantic coherence — the judgment-layer check (run every cycle)

The families above are **numerical / behavioral** — a machine can assert them. This
one is **semantic**: does the system still *make coherent sense* — do its concepts,
claims, and vocabulary agree across code, docs, decisions, and consumer rulings?
Drift here doesn't crash a test; it quietly rots the project. It is exactly what an
LLM-driven audit can catch and a `pytest` cannot, so **probe it every cycle** by
*reading across* sources, not by running code. A finding is the **two contradicting
locations** + which claim/contract they violate (still the §4 format). Sub-checks:

- **Doctrine actually upheld in code.** The epistemic claims the README / CLAUDE.md
  make must be *true*: register-dependent analysis **errors, doesn't guess**; a
  result documented as *plural/ranked/evidenced* isn't silently collapsed to one; a
  **versioned prior** the doctrine says is "cited in the result" really is stamped
  there; a **generative** act is labeled generative and lives generative-side (not
  disguised as analysis). A new function that guesses, invents register, or drops
  the evidence is a coherence break even if every number is right.
- **Docs ↔ code truth.** Docstrings, per-layer `CLAUDE.md` rules, `README.md`,
  `INTEGRATION.md` describe what the code *actually* does now — signature, fields,
  behavior. Flag: a ROADMAP/README "shipped" claim that raises or is absent; a tool
  docstring naming result fields that aren't there; a layer rule an import violates.
- **Vocabulary consistency.** A term of art means one thing everywhere — `identity`
  vs `realization`, `piece` vs `run` vs `span`, `prime form` vs `set class`,
  `hard`/`soft`, `scope`. A silent redefinition across code ↔ docs ↔ an
  `integrations/` response is a finding.
- **Decision & ruling non-contradiction.** ROADMAP decisions don't contradict each
  other or the code; a boundary ruling or contract in an `integrations/` response is
  still honored (e.g. "satisfaction stays wont-schema", a pinned prior version, a
  by-reference embedding) and not quietly reversed by later code or a later notice.
- **Provenance / versioning coherence.** A schema or prior **version is bumped when
  its content changed** (a frozen `x.1` that silently changed is the worst drift);
  every "stamped/cited" promise is kept on the artifact it names.

### 6b. Efficiency & complexity — the scaling check (run every cycle)

The families above guard **correctness**; this one guards **cost**. It has its
own section because the engine's stated direction is corpus scale (ROADMAP:
OpenScore / full-SWD / Mutopia — real scores, thousands of notes per part), and a
quadratic that is invisible on a 20-note fixture becomes minutes on a symphony.
Two real quadratics (#206 `part_profiles`, #214 `part_relations`) were caught by
*eyeballing loop shape*, not by any charter check — this codifies that instinct so
it runs every cycle, not by luck. Two complementary probes:

- **Structural read (primary — deterministic, no timing).** A *reading* pass, like
  §6a, over the newest and most-scalable code. Flag these anti-patterns in any
  path that grows with input size (events, corpus pieces, the 4096-mask space,
  search spaces):
  - a **scan or membership test inside a loop over the same or a co-scaling
    collection** — `for x: if any(… for y in growing)`, or a helper like
    `_sounds_at(events, beat)` called once per beat (the exact #206/#214 shape);
  - **re-deriving a memoizable value** inside a loop instead of hoisting/caching it;
  - **materializing an O(n²) (or worse) structure** where a single onset-sorted /
    mask-sorted sweep would do (the `segmentation._sweep_active` pattern, RE-5d);
  - an **unbounded cache** on an input space that is not 4096-bounded (Phase 6
    makes 2^N > 4096 — see ROADMAP), or a bound silently exceeded.
  The question to ask of each hot function: *does its work grow linearly with the
  input the ROADMAP plans to feed it?* If not, and it is not documented as an
  accepted bound, that is a finding (§4 format; contract = "must scale to the
  corpus regime", ROADMAP).
- **Empirical scaling probe (secondary — exponent, never wall-clock).** Use
  `audit/checks/scaling_probe.py` (`report(name, make_input, run)`): it times a
  path at geometric sizes and fits the **growth exponent** — O(n) ≈ 1.0, O(n²) ≈
  2.0. Exponents are **machine-independent** (the shape transfers even though the
  milliseconds do not), so assert on the exponent, **never on an absolute
  millisecond threshold**. Each cycle, point it at the newest scalable entry
  points; the must-stay-~linear set today: `part_profiles`, `part_relations`,
  `segment_to_chords` / segmentation, MIDI ingestion, and corpus-level induction /
  transition-matrix building. A fitted exponent above ~1.4 on a "should be linear"
  path is a finding.

**The one hard rule for this family: never commit a wall-clock assertion into
`audit/checks/` as a collected test.** CI runs `audit/checks/`, and a timing gate
flakes — the very anti-pattern the audit exists to prevent. The probe harness is
therefore a **hand-run cycle utility** (no `test_` prefix, uncollected); its output
becomes an **issue** (superlinear → §4 finding) or a **cycle-log line** (clean),
not a red build. Correctness invariants gate; cost probes report.

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
