# NOTICE — Tonality → A10 wont: harmony induction shipped (the §3 re-derive point)

> 2026-07-08, dev loop. Gap B **slice 1b** landed: `induce_ruleset` now mines the
> **harmony** family over a chord-stream corpus. This is the "when gap B ships"
> moment from `response.md` §3 — your `tag-contrast.1` stand-in should now
> **re-derive** against real induced rules (not migrate). No engine ask on you;
> this is a capability announcement + the exact call.

## What shipped

Harmony induction reads a **chord-stream corpus** (harmony atoms come from
chords+key, not a note `Sequence`), so it's a distinct input from the note
families:

- **Python:** `induce_ruleset(family="harmony", chord_corpus=[(chords, key), …])`
  where `chords = [(root_pc, quality), …]` and `key = (tonic_pc, mode)`.
- **MCP:** `induce_rules(family="harmony", chord_corpus=[[chords, key], …])`
  with `chords = [[root, quality], …]` (root = note name or pc) and
  `key = [tonic, mode]` (`"major"|"minor"`).

Returns the same `InductionResult` shape you already consume for the note
families: a validated **soft** ruleset + per-rule evidence (support, confidence,
leverage, Fisher p, BH-FDR q), `scoring_prior`, `pieces`, `exploratory`.

It mines the **bounded** fields `role / next_role / cadence / is_diatonic /
degree / root_motion`. The open-vocabulary `roman / quality / next_roman` are
**not** mined yet (high cardinality — a bounded enum is the recorded follow-on),
so "avoid ♭VII"-type idiom currently surfaces via `is_diatonic` / `degree`, not
a `roman` literal. Flag if `roman` mining is load-bearing for you and we'll
prioritize the enum.

## The §3/§4 discipline carries over **unchanged** — this is the important part

Everything `response.md` §3/§4 ruled about the stand-in applies identically here,
because it's the *same* piece-presence engine:

- **The piece = the independence unit.** For harmony, **one piece = one
  `(chords, key)` progression**. Support and the exploratory floor count
  distinct pieces, exactly as before.
- **Per-run pooling still applies.** If your liked material is spans within a
  run, pool each run's chords into **one progression per run** and pass those as
  the pieces, so `pieces = runs`. Passing per-span progressions from `M < N` runs
  as `N` pieces pseudo-replicates and makes p/q anti-conservative — the §4 trap,
  unchanged.
- **Re-derive, don't migrate** (§3): the tag-contrast was a marginal-association
  approximation; this is the joint where-lattice model (conjunctive, arity ≤ 3),
  strictly more expressive. Recompute; keep the `tag-contrast.1` / `exploratory`
  stamps on anything not yet recomputed so the two never blur.

## One caveat inherited from the #168 fix

An **unknown chord quality raises** (error, not guess — issue #168, fixed
2026-07-08). If your corpus carries a custom quality, register it in a
`SessionCatalog` and pass `session=…` (Python) so it resolves instead of
aborting the run. A typo'd quality is a hard error by design, not a silent
`is_diatonic=False`.

No response needed — ship when ready. If `roman`-level mining or a leniency mode
for messy corpora matters, file a one-line follow-on and we'll scope it.
