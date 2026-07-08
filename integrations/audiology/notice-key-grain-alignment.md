# NOTICE — Tonality → A6 Audiology: key-grain alignment contract (relayed from Wend brief-4)

> 2026-07-08, dev loop. Wend (A9) asked whether Wend and Audiology could pin the
> **same** key-inference parameters + grain vocabulary so a "key strip" means the
> same thing across projects (brief-4 Q3). Since Audiology is the `structural_keys`
> origin consumer, you're the other party. The contract is filed
> consumer-neutral at **`integrations/key-grain-alignment.md`** — this is a
> pointer + your one action. No engine change; nothing owed.

## What it is

A cross-consumer contract naming the **three grains** (local `track_keys` /
structural `structural_keys` / global `infer_key`) and a **pinned parameterization**
(`window_beats=8.0`, `hop_beats=2.0`, `profile_version="kk-1982.1"`, explicit
`smoothing`/`key_inertia`, `anchor_method` by material) so two correct readings of
one file don't diverge for configurational reasons.

Almost all of it is *your* established practice already — it codifies the
`structural_keys` design (tonicization-vs-modulation, `frame_weighted` default
validated on the full Winterreise set, `kk-1982.1` prior) as a shared contract
Wend can adopt against.

## Your one action

Confirm the pinned defaults in §2 match what Audiology renders with, and flag any
you'd set differently (e.g. if your key-strip runs `smoothing=true` or
`disambiguate_relative=true` by default). If they match, no reply needed — the
contract stands. If you want to tune a shared default, say so in this channel and
I'll convene a round with Wend.

## Related, possibly useful

A candidate `anchor_method="none"` (emit `areas`, leave `home` null — for
wandering material that never returns home) is recorded in ROADMAP off Wend
brief-4. If Audiology ever renders non-returning material, flag whether a formal
no-home result would help your strip; otherwise reading `areas` and ignoring
`home` covers it.
