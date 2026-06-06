# mts/core — Identity layer

The atemporal foundation. Everything here answers *"what is this set of pitches?"*
in mod-12 pitch-class space. No clock, no register semantics (register is carried
by `Pitch` but identity reduces to pitch-classes).

- `bitmask.py` — 12-bit PC-set ops (membership, subset, rotation). The substrate;
  keep it allocation-light and correct. This is the hot path.
- `pitch.py` — `Pitch` (PC + octave/MIDI) and token parsing. The one place register
  lives in `core`.
- `spec_level.py` — the identity lattice: `Transpositional {ROOTED, SHAPE}` ×
  `Registral {REGISTERED, PC_SET}` and the four named corners (`VOICING`,
  `NAMED_CHORD`, `INTERVAL_SHAPE`, `VOICING_TEMPLATE`). **Tuning-agnostic** — knows
  nothing about 12 (Decision 6); imports nothing from `mts`.
- `realization.py` — `Realization`: ordered `Pitch` list with optional `root_pc`,
  the register-bearing sibling of the identity key. `reduce_to_key()` is the *only*
  12-TET reduction boundary in new code. A rootless realization (`root_pc=None`) is
  a voicing template — the registered+rootless corner `scope` could never reach.
- `scale.py`, `chord.py`, `quality.py` — `@dataclass(frozen=True)` identities built
  on the bitmask. Immutable and hashable — keep them that way.
- `enharmonics.py` — spelling preference / PC ↔ name. Presentation-adjacent; callers
  pass preferences in, don't hardcode.
- `symmetry.py` — rotational/reflective symmetry over masks.

**Rules:** frozen + hashable; mod-12 only; no I/O, no session state, no upward
imports (`core` depends on nothing else in `mts`). See root CLAUDE.md for the
identity-key vs. realization model before adding types.
