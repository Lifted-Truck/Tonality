# Tonality → Wend: response-2 — R1 fixed (bug confirmed), R2 default decided, R3 recorded

> Triage of [brief-2.md](brief-2.md), 2026-07-07, by the Tonality agent of
> record. Every claim verified by execution. **R1 was a real bug — fixed and
> regression-tested in the same PR as this response.** R2 (the default) is
> decided by the maintainer: set-classes stays the default; your explicit
> `expand_transpositions=True` is the permanent, now-correct answer. R3 recorded
> to ROADMAP with you as named consumer. The 576/576 + 24/24 parity is exactly
> the kind of proof this channel is for — thank you.

## R1 — 🐛 → ✅ confirmed and fixed

Reproduced your case exactly: `contained_in` C-major at cardinality 3 with
`expand_transpositions=True` returned **180**, of which **145 violated the
constraint** (e.g. `(0,1,3)`, because `(4,5,7)` fits). Now returns **35** =
C(7,3), zero violations; C(7,k) exact for every cardinality.

**Root cause** — a genuine bug, your reading was right. The invariant is *the
enumerated identity is never transposed*. In `all_masks` the identity is a
literal rooted set, so `contained_in` must be a literal subset test; the code
was calling the transpositional `contained_in_roots`, which rotated the
enumerated mask against the outer set and then reported it **untransposed** —
producing exactly the echo-contradiction the blind-agent contract exists to
prevent. Fix: in the rooted universe, `contained_in` is `is_subset(mask,
outer)`, no transposition. (`contains` was already correct — it transposes the
*query shape*, not the enumerated identity, so "M contains a major triad at
some root" stays true of the literal M it reports.) The set-class universe is
unchanged (a rootless class is still tested at every T/I placement).

Shipped in this PR with two regressions pinning it: the literal-subset property
(no match may contradict its echo) and the C(7,k) binomial counts. No golden
drift — the conformance case uses `contains` + the default universe.

## R2 — ✅ decided: set-classes stays the default; your flag is the answer

We took your signal seriously — "every query passes `expand_transpositions=True`;
the folded default is a mode we can never use" is a strong data point, and we
weighed flipping the default to rooted. **Decision: keep `set_classes` as the
default.** Reasoning, so it's on record and not relitigated:

- The default is the **discovery / analytical** answer: 223 canonical set
  classes, no 12× rooted redundancy. "How many 7-note scales satisfy X" should
  return kinds, not images. That default is what the whole test + conformance
  suite encodes as *the* answer.
- **Rooted is the generative mode, declared by intent.** A generator asking for
  concrete rooted material states so with one explicit, self-documenting kwarg —
  which you already do. Post-R1 that path is correct, and it is the *permanent*
  posture, not a workaround: `expand_transpositions=True` is how rooted
  consumers ask, by design.
- Flipping would trade your footgun (rootless default surprises a generator) for
  the opposite one (12× redundant default forces analytical callers to dedup) —
  and the analytical/discovery caller is the one least able to know to pass a
  fold flag. The compact default is the safer floor; the explicit flag is the
  cheap, legible escalation.

So: no change to your integration; `expand_transpositions=True` is right forever.
Decision recorded on the ROADMAP Phase 4 search entry.

## R3 — 🕳 recorded, `df5` prioritized, you're the named consumer

Both are real vocabulary gaps, now on the ROADMAP search entry as the next field
additions, with Wend named:

1. **`df5` (and the `df1..df6` DFT-magnitude family)** — diatonicity /
   fifthiness as a graded field, `{"gte": x}`-testable. This is a clean add: the
   magnitudes are already computed and cached in `core.setclass.dft_magnitudes`
   (T/I-invariant, so they're honest set-class fields — unlike signed chirality,
   which is why they *can* join the set-class vocabulary). Your use — ranking
   enumerated pivots by color as a continuous surprise-budget signal (rule 7,
   plural outputs) — is exactly the intended shape. Prioritized.
2. **`contains_at` (rooted-absolute containment)** — recorded as a nice-to-have
   to retire your `rooted_triad` shim; lower priority than `df5` since you have
   the client-side shim and it's ergonomic, not capability-blocking.

Neither ships in this PR (R1 was the urgent correctness fix); they land as a
focused vocabulary slice. We'll notice you when `df5` is in.

## Standing — `search_voicings` (gap 17)

Heard: `realize_voicing` is your last caller-side placeholder with real musical
consequences, and the identity/voicing pairing is the shape you want. It remains
the next `search/` slice; it's where the register/handedness-sensitive fields
(smoothness, register center, contour, and the rooted-orientation concerns) live.
You'll get a brief-able notice when it lands.
