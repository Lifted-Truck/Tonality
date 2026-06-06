# mts/core — Identity layer

The atemporal foundation. Everything here answers *"what is this set of pitches?"*
in mod-12 pitch-class space. No clock, no register semantics (register is carried
by `Pitch` but identity reduces to pitch-classes).

- `bitmask.py` — 12-bit PC-set ops (membership, subset, rotation). The substrate;
  keep it allocation-light and correct. This is the hot path.
- `pitch.py` — `Pitch` (PC + octave/MIDI) and token parsing. The one place register
  lives in `core`.
- `scale.py`, `chord.py`, `quality.py` — `@dataclass(frozen=True)` identities built
  on the bitmask. Immutable and hashable — keep them that way.
- `enharmonics.py` — spelling preference / PC ↔ name. Presentation-adjacent; callers
  pass preferences in, don't hardcode.
- `symmetry.py` — rotational/reflective symmetry over masks.

**Rules:** frozen + hashable; mod-12 only; no I/O, no session state, no upward
imports (`core` depends on nothing else in `mts`). See root CLAUDE.md for the
identity-key vs. realization model before adding types.
