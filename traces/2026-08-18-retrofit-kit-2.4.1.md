# Trace — 2026-08-18: retrofit to kit 2.4.1

**Session:** Tonality primary dev thread. **Trigger:** `/retrofit`.
**Opening state:** `declared: pre-2.0.0 — BEHIND by 5 entries`.
**Closing state:** `declared: 2.4.1 — CURRENT, nothing to do`.

## What was done

- **Vendored the kit mechanism** (2.4.0): `.kit/kit-gates.sh` + `.kit/MANIFEST`
  via `kit_sync.py`. No gate code copied into the repo; `leak_gate` is defined
  once, in the vendored file, and `./verify` sources it. This closed 2.2.0 and
  2.3.0 at the same time — a vendored repo answers the gate questions by
  checksum, so no probe is planted in this tree at all.
- **Created `./verify`** (project-owned) wrapping what already worked rather
  than inventing an oracle: `fast` = kit gates + `plant_not_tracked` + the dev
  suite (which carries the conformance golden, the tool-manifest pin, the
  port-pin fingerprint and the repo's own identity test); `full` = + the audit
  invariants (fenced out of the dev suite by `testpaths`) + `scripts/ci-local.sh`.
  Nothing was quarantined: the suite was green at 1212 before and after.
- **Migrated the decisions register** to `DECISIONS.md` (Decision 16) — see below.
- **`project.manifest.json`**: survey answers, architecture rung **2** (ratified
  by the human, not defaulted).
- **`## Mailbox`** appended to CLAUDE.md, marker-delimited (2.1.0). None existed.

## Two corrections to my own analysis, both caught by measuring

1. **I claimed the register held "53 decisions."** It holds **15**. The 53 was
   `^[0-9]+\. \*\*` across the *whole* 4710-line ROADMAP — mostly the 33-entry
   gap list. I used that inflated number to argue the migration was risky, and
   it was the main reason I recommended against it.
2. **My citation survey returned "0 bare `Decision N` references,"** which is
   absurd on its face and I nearly acted on it. Cause: `git grep -E "\bDecision"`
   — POSIX ERE has no `\b`, so the pattern silently matched nothing. The real
   count is 176. This is the exact trap `/retrofit`'s own gotcha list warns
   about, hit within ten minutes of reading it, and the reason a gate must be
   watched to FIRE rather than trusted to exist (LIBRARY L0002).

The `autonomous` resident's numbers were closer than mine on both counts. Their
"3 citations name ROADMAP" was low (the true figure is ~19), which strengthened
rather than weakened their case: 15 of the 19 are in live files and were
mechanically rewritable, and the other 4 are in `integrations/` — a historical
record this repo does not retro-edit, so they correctly stay as filed.

## The move, verified rather than asserted

Per the resident's prescription, executed as a **move, not a copy-paste**:

| Check | Result |
|---|---|
| `diff` of the section that left ROADMAP vs the body that landed in DECISIONS | **empty** |
| entry count, both sides | **15 = 15** |
| numbering | unbroken 1..15, so all 176 `Decision N` citations still resolve |
| ROADMAP | dated stub left at the old location |
| live citations naming ROADMAP as the home | 15 rewritten to the repo's dominant bare `(Decision N)` form |
| `integrations/` citations | **untouched** — correct as of their date |

One rewrite touched a *runtime* string (`chromatic.py`'s `no_label_reason`), so
the conformance golden was checked explicitly: unchanged, because that case's
events are all `confident` and the field is null there. Worth knowing that the
reason string is therefore **not** golden-pinned.

## Gate behaviour proven, not assumed

`./verify` sources `.kit/kit-gates.sh` (a checksum-perfect copy nothing sources
is an ungated repo); a planted **POSIX** identity path fires and names the file;
a planted **Windows** identity path fires and names the file; a **tracked**
`.kit-currency-plant-*` fires `plant_not_tracked`; an **untracked** one stays
invisible to a concurrent run (2.3.0), and it is deliberately NOT gitignored —
`git grep --untracked` skips ignored files, which would blind the owning probe.

## Not done, deliberately

Nothing. Every `[ ]` in the opening delta is `[x]`; the manifest declares
`2.4.1` only because the closing `currency.py` agrees.
