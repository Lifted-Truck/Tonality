# Trace — 2026-08-27: HYPERSAW-002 close, audit sweep, mailbox state repair

**Session:** Tonality primary dev thread (multi-day). **Closed by:** `/breakdown`.
**Oracle at close:** `./verify fast` green, **1217 passed**, at `d3110b6`.

## What shipped

| PR | What |
|---|---|
| #280 | HYPERSAW-002 answered — `{root, mask}` is an honest interchange; name it 12-TET |
| #281 | Audit sweep #274–#277 — segmentation made linear; boundary flag; two docs fixes |
| #285 | HYPERSAW-002 closed — their hazard run against our own suite; LIBRARY L0004 |
| #290 | Three answered-but-open Tonality-Live threads closed; the rule recorded |

Also this session: the kit retrofit (`pre-2.0.0` → `2.5.0`), the decisions
register moved to `DECISIONS.md`, and `find_scale_runs` (gap 31b).

## The three findings worth carrying

**1. The audit found defects my own work created or amplified — twice.** #274's
`segment_to_chords` was quadratic when it shipped and *tolerable* as a leaf cost;
three gap-25/26 entry points I added put it on corpus paths. Fixed with the sweep
already written for #214: exponent **1.67 → 0.68**, 9.1× at 8k notes, 312
old-vs-new runs byte-identical. #275 was the boundary flag I added to `conform.py`
for #262 and did not propagate to its two siblings.

**2. A mechanism transfers between projects; a severity does not** (LIBRARY
L0004, canonical). We handed HYPERSAW the tie-break mechanism *and* our severity
("all five accidentals tie") without saying the count came from **integer** input.
Their quantiser takes a continuous glide, where the same tie is a knife edge one
ULP wide. They filed the correction themselves, unprompted. Our omission.

**3. Their hazard, pointed back at us, found a real gap.** Their notice named
*"the test that covers the fix is itself uncovered"*. Rather than accept their
guess that we were safe, three regressions were planted — tie-break, the #275
flag, the #274 sweep — and all three fired. But the third fired only via a
*conformance golden*: the sweep's own hazard (an event spanning many windows) had
no direct test, having been verified once out-of-band and never entered the
standing suite. Two direct tests added. **The second failed its first draft for
the wrong reason** — a short event dropped by the salience threshold would have
passed with the sweep broken — which is their own moving-glide-law mistake,
reproduced ten minutes after reading their account of it.

## Mailbox state repair (the close's own finding)

The session brief opened with `OVERDUE: tonality-live-002`. All three flagged
threads were answered and shipped, the oldest two weeks before its deadline. Read
`ball_scan.py` rather than guessing: `ball: none` is deliberately not a claimant,
and `status: responded` is correctly not terminal, so a closing reply asserting
only `ball: none` leaves the opening brief's `ball: provider` standing forever.
Separately, the same-id convention orphaned `tonality-live-001-ratify`, whose
pre-convention minted id no reply carried. Fixed with three `closed-*.md` markers
(never by editing the filed replies); scanner went **3 ours / 1 overdue → 0**.
Recorded as Decision 17; filed upstream as a fleet-general observation with an
explicit note that the status quo is the safer failure if the proposed
discriminator is not crisp enough.

## Checked and found clean (recorded so it is not re-checked)

- `mts/cli/` is absent from CLAUDE.md's architecture diagram — **correctly**: it
  is a deliberately demoted layer, documented as such in ROADMAP and in its own
  test. Not a #277-shaped gap.
- No stray `.kit-currency-plant-*`; `.kit/` tracked; README tool count (79)
  matches the live surface and is gate-enforced.

## Left open, deliberately

`docs/process/index.html` — untracked since 2026-07-15, not this session's work,
not committed. It is the only uncommitted thing in the tree.
