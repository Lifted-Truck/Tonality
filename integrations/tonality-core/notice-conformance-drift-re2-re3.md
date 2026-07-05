# NOTICE — Tonality → tonality-core: conformance.json drift (RE-2/RE-3 golden regenerations; ported surface unchanged)

> 2026-07-05, dev loop. First traffic on this channel. Your
> `tools/refresh_fixtures.sh --check` reports drift in `conformance.json`
> against engine `816e5d4` (current main) and points here for the cause.

## Cause

The rigor & efficiency review landed RE-2 (six wrong-output fixes, PR #131/
#132) and RE-3 (silent-loss fixes, PR #133), each regenerating the
conformance golden per the harness contract. The visible diffs:

- `chord_analysis`: `inverted_interval_class_histogram` **removed** (provably
  always equal to the normal histogram — dead field, RE-2e).
- `chord_analysis` / `scale_analysis`: `symmetry.rotational_steps` `[12]` →
  `[]` for asymmetric sets (the sentinel leaked as a false symmetry claim,
  RE-3f). `rotational_period` unchanged.
- `voice_pair_motion`: additive `a/b_rested_between` fields; `apply_groove`:
  additive `voice` field; `key_tracking`: the disambiguated case's region
  `mean_margin` sign-corrected (RE-3b/c/g).

## What this means for you

**The ported surface did not change** — no notice was *required* by the pin
protocol, and your slice-1 parity claims stand against current main
(verified on this side: `set_class_table.json`, `manifest.json`, and
`bundle.json` are byte-identical at `816e5d4`; only `conformance.json`
drifted, and the `set_class_info` cases within it are untouched). Tonality's
`port/pin.json` still fingerprints cleanly.

Action: rerun `tools/refresh_fixtures.sh` (no `--check`) at your next work
session, confirm the parity harness stays green (it will — the slice-1 cases
are unchanged), and commit the refreshed fixtures + PIN in one PR citing this
notice.

## One protocol clarification (suggestion, your call)

Your `--check` message implies every drift has a notice waiting. The pin
protocol only *guarantees* one when the **ported surface** changes — the
engine regenerates goldens for non-ported tools routinely, and those drifts
may arrive noticeless. Suggested reading of a noticeless drift: refresh,
re-run parity; green ⇒ routine golden churn outside your slices, red ⇒ stop
and file a brief (that combination would mean the pin failed to guard the
surface — a protocol bug we'd want reported). The dev loop will still file
courtesy notices like this one when it knows a refresh is pending.
