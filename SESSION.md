# SESSION — Tonality

> Hot state. The only prior-session context the next session should trust.
> Written at close; if it disagrees with the tree, **the tree wins** — re-run
> `./verify fast` and `python3 ~/Documents/Claude/autonomous/kit/session/state.py .`

**Last close:** 2026-08-27 · **branch** `main` · **oracle** `./verify fast`
**green, 1217 passed** · kit **2.5.0** (`currency.py`: CURRENT)

## Where the repo stands

79 MCP tools. Phase 7's generative layer (`mts/generate/`) is the newest: conform
(proximity), remap-by-degree (translation), the full `modal_transform`
analyze→plan→apply, and `retonicize`. Gap 25 (chromatic-event classification) and
gap 26 (modal transform) are both feature-complete; gap 31 is (a) adopted,
(b) shipped (`find_scale_runs`), (c) designed but unbuilt.

**Board is clean:** 0 open issues, 0 open PRs, **0 integration balls on us**
(verified with the real `ball_scan`, not by eye). Nothing is blocked on us
anywhere.

## First move next session

**Re-read the board and choose then** — Julian's call at close. Open with
`/wakeup`, read this file and the ROADMAP horizon cold, and pick with fresh eyes.
The candidates, ranked as they stood:

1. **Gap 31(c)** — grouped plan decisions for forced collapse. *Caveat recorded
   in REFLECTIONS: do not build it before gap 32 gives it a delivery shape, or it
   will guess at one.*
2. **Gap 32** — the recommendation surface (dedicated endpoint, proposals
   reference plan artifacts). Bigger; would shape 31(c).
3. **Recorded follow-ons** — chromatic-tolerant scale runs, two-bar drum clave,
   harmony-family repair (slice 2), the P0.2 per-tool fuzz set.

## Open threads

- **HYPERSAW's §3 listening test** — they owe it unprompted, no deadline, thread
  closed at `ball: none`. **No scanner will surface this.** See REFLECTIONS
  2026-08-27; if it is still outstanding, ask rather than assume it lapsed.
- **Upstream brief awaiting autonomous** —
  `autonomous/integrations/Tonality/brief-ball-scan-none.md` (uncommitted there;
  committing it is their resident's act). The `ball: none` blind spot is
  fleet-general.
- **Julian's outstanding calls** — `midi_file_analysis` path policy (recommended:
  allowlist roots via env var); public MCP registry listing; corpus-expansion
  license (recommended OpenScore CC0); branch protection on `tonality-core`
  **blocked** — classic protection and rulesets are both gated on a private repo
  under the free plan, so it needs GitHub Pro *or* making that repo public (which
  would also stop `macos-15` parity runs burning Actions minutes at 10×).
- **Gaps 30/31/32 converge on the plan artifact** and nobody has drawn that
  together in one place.

## Uncommitted / not ours

`docs/process/index.html` — untracked since 2026-07-15, unrelated to this
session, deliberately not committed.

## Traces

- `traces/2026-08-27-session-close.md` — this session (HYPERSAW-002, audit sweep
  #274–#277, mailbox state repair)
- `traces/2026-08-18-retrofit-kit-2.4.1.md` — the kit retrofit
