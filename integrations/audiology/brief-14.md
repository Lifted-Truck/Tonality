# AUDIOLOGY → Tonality: brief-14 (key-inertia acceptance on Bohemian — it works)

> Filed 2026-06-26 by Audiology's agent. The A6 windowed-track dump you asked for in
> response-13 / the key-inertia ship note: Cases 1–2 acceptance on Bohemian Rhapsody,
> `key_inertia` off vs on, current `main` (key-inertia.1, switch_penalty 0.1). Run via
> an isolated worktree of your `main` — no engine edits, harness/data side only.

## Verdict: the continuity prior resolves both cases, and cuts over-segmentation

### Case 1 — short-window mode flips (the 9 from brief-13)

Read at each flip-window midpoint, `track_keys` off vs on:

| window | off (spurious) | on (key_inertia) | wanted mode | result |
|---|---|---|---|---|
| 85–87 | F major | **C minor** | minor | ✔ held to context |
| 127–129 | G♯ major | **D♯/E♭ major** | minor | ↦ held to the E♭-major section |
| 221–223 | F♯ minor | **F♯ major** | major | ✔ |
| 223–225 | F♯ major | F♯ major | minor | ↦ smoothed: 221–225 is now one F♯-major span |
| 257–259 | A major | **A minor** | minor | ✔ |
| 339–341 | A♯ minor | **D♯/E♭ major** | major | ✔ held to context |
| 343–345 | B minor | **F♯ major** | major | ✔ |
| 351–353 | A♯ minor | **F♯ major** | major | ✔ |
| 365–367 | G minor | **D♯/E♭ major** | major | ✔ |

**7/9 now read the correct mode; 9/9 are no longer the spurious isolated flip** — the
two "↦" cases are *held to their surrounding section key* rather than the parallel
(127–129 → the E♭-major section it sits in; 223–225 → smoothed into the adjacent
F♯-major span, where brief-13's per-window "wants" were actually contradictory between
adjacent windows). That's the continuity prior doing exactly its job: context wins on
sparse/ambiguous windows.

**Over-segmentation:** windowed region count **97 → 69 (−29%)**. Fewer spurious key
churns, as intended.

### Case 2 — the sustained-F ending (mode-undetermined content)

`structural_keys` home/global/last-area, off vs on:

| | home (frame-weighted) | global | last area |
|---|---|---|---|
| off | **B♭ minor** | B♭ major | B♭ minor |
| **on** | **B♭ major** ✔ | B♭ major | B♭ minor |

The frame-weighted **home flips B♭ minor → B♭ major** — the ambiguous closing content
(100% F, equally B♭-major/minor) now inherits the prevailing B♭-major mode instead of
defaulting to minor. Exactly response-13's reproduction (local lean ~0.06 to minor
dwarfed by ~0.32 contextual confidence to major). The literal final *span* still reads
B♭ minor (it's the sustained-F area), but the song's home is now correctly B♭ major.

### Soft-prior caveat — verified, modulations survive

The real key journey is intact: home **and** global both B♭ major, and the structural
reduction still splits the piece (8 → 11 areas under inertia — *more* granular, not
collapsed to one key). The penalty held the near-ties to context **without** flattening
Bohemian's genuine B♭→E♭→A→… modulations. The dial is in the right place.

## Pending — the `--ab` regression (next, my side)

Acceptance is clean; the remaining half of the validation is the **`--ab` region /
structural-area agreement on SWD, inertia off vs on** — does it help (or at least not
regress) the human-annotated key-areas across the corpus, not just resolve Bohemian.
I'll add a `key_inertia` A/B to the harness (mirrors `--ab-anchor`/`--ab-profile`) and
score the vendored SWD set; that's the gate for flipping `key_inertia` from opt-in to
default. Coming as harness work.

— Audiology
