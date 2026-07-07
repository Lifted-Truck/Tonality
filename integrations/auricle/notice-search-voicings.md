# Tonality → AURICLE: notice — gap 17 slice 1 shipped (`search_voicings`)

> 2026-07-07, dev loop. Gap 17 (constrained voicing enumeration + ranking) was
> accepted from your RFC on 2026-07-03; its first slice is now on `main`.
> Additive — nothing you consume today changed, and gap 16 (compiled harmony
> contracts) is unaffected: hand-authored voicings remain valid contract input.

## What shipped vs. your recorded ask

`mts/search/voicings.py` — `search_voicings(pcs, root=, constraints=,
from_voicing=)`, MCP tool of the same name.

- **Enumeration (generative half):** exhaustive over a required
  `register: [lo, hi]` MIDI window — the engine never defaults a register (the
  cardinal rule expressed as API). Deterministic, no RNG. The raw space is
  computed upfront; an over-large window raises with advice rather than
  silently truncating, so `count` is always exact.
- **Ranking (analysis half):** with a `from_voicing` reference, every match
  carries `vl_from` — the exact `voice_leading_realized` cost under
  `doubling.1`, the ranking authority named in the gap — and matches return
  sorted by it. Margins are the continuous `vl_from` values; ties surface via
  a deterministic secondary order (spread, then pitch content), never hidden.
- **The voicing-template corner** (the gap's own framing) is operational:
  `root=None` searches registered+rootless templates.
- Constraint fields: `spread`, `bass_pc`, `top_pc`, `top_midi`, `center`,
  `voicing_type` (named-shape registry), `no_interval_over_bass` (directed
  pc-intervals, mod-12), `max_voice_leading`.

## What slice 1 does **not** cover (your resonator ask)

**Voice count N ≠ cardinality** — each pc is voiced exactly once in this
slice; doublings/omissions (the "N resonators over a pc set" form your RFC
implies) are the recorded slice 2, and your requirements would shape it. If
resonator voicing needs N-voice enumeration soon, file a brief with the N
semantics you want (doublings only? omissions? both, with priorities?) and it
moves up. Contour-hold curves are likewise slice 2 (v1 handle: `top_pc` /
`top_midi`).

No response needed; this is delivery notice + the slice-2 door.
