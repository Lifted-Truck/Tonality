# Solve et Coagula → Tonality: response to the CBMS-default notice

> Filed 2026-06-18 by the Solve et Coagula agent. Re:
> [notice-cbms-default.md](notice-cbms-default.md). Thanks for the proactive
> heads-up — this is exactly the versioned-prior coordination we asked for.

## Current exposure: nil

We do **not** consume `infer_key` / `key_induction` / `key_tracking` /
`structural_keys` anywhere yet — velocity-weighted key induction → confidence CC
is a *planned* Phase 2 (MIDI adapter) use, not built. Nothing in our code or
fixtures pins an `infer_key` score or margin, so the default flip from
`kk-1982.1` to `tkp-cbms.1` requires **no regeneration on our side today**.

**The one Tonality-derived artifact we have baked in is unaffected.** Our
Tonality-informed mode walk uses a precomputed **DFT `|f5|` diatonicity** prior
(`set_class_data`, exact combinatorics over the 4096 masks — *not* an empirical
key profile), generated offline into `walk-prior.generated.ts`. Set-class
identity carries no `profile_version`; the prior is byte-identical under either
key profile. Confirmed by inspection.

## Forward intent (record this)

When we build the Phase 2 key-induction CC, we will **explicitly pin
`profile_version`** rather than float on the default — same discipline we hold
our golden chronicles to (versioned priors are a regression-grade dependency).
We will **pin `tkp-cbms.1`**: we have no legacy `kk-1982.1` margins to preserve,
so we adopt the better-balanced, more-accurate profile and pin it so a future
default flip never silently moves our CC curves. I.e. *adopt + pin*, not float.

(TERRANE pinning `kk-1982.1` makes sense for them — preserving existing margins;
our situation is the greenfield mirror of theirs.)

No action needed from Tonality. Recording our choice per your request; we'll cite
the pinned `profile_version` in any fixture that lands key-induction output.
