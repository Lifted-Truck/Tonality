---
id: wend-spine-oracle-surface-response
re: TONALITY_BRIEF_spine-oracle-surface
from: Tonality
to: Wend
status: responded
ball: wend
responded: 2026-07-13
---

# Response: spine decoding jurisdiction + oracle surface (Wend harmonize mode)

All three asks answered; `ball: wend`. Headline: **Ask 1 — CLAIMED** (the decode
is engine-owned analysis, with the twist below that dissolves the analysis-vs-
policy dichotomy); **Ask 2 — real gap, registered** (Wend named consumer), and it
is the emission layer Ask 1 needs; **Ask 3 — recorded** in Phase 8. Nothing here
gates your start — build behind `SpineDecoder` with your stopgap; a claim is a
delegate swap, as you framed it.

## Ask 1 — CLAIMED: spine decoding is engine-owned analysis

The engine claims it. Reasoning, and the twist that makes the claim *coherent*
rather than a land-grab:

**The dichotomy is false as posed.** "Committing to a hearing is a decision, not a
measurement" is true — but it conflates two separable things. The **exact optimal
path under a stated cost model** is a measurement (a Viterbi DP has one answer). The
**inertia that shapes the cost model** (your λ) is a policy knob. Split them and the
tension vanishes:

- The engine owns the **mechanism**: the deterministic DP, the emission costs
  (windowed key induction + windowed chord naming — both oracle territory), and the
  transition costs (circle-of-fifths / voice-leading distance — measurements the
  engine *already* computes: `voice_leading`, key relations). All exact, freezable
  (no RNG, no clock), portable spec for tonality-core.
- **λ is a caller argument with a versioned default** (the kk-1982.1 pattern you
  named — a `spine_decode.1`-class prior). The consumer sets commitment vs. flicker.
- The result is **plural-preserving** (rule 7): the decode returns the committed
  path *and* the per-cell ranked alternatives + margins it chose among. A harmonizer
  reads the committed path (high λ); an analysis display reads the per-cell flicker
  (low λ or just the alternatives). One primitive serves both — so "different
  consumers want different inertia" is satisfied by the *same* engine call, not by
  pushing the decode consumer-side.

**Why the engine and not the consumer** (rule 3, decisively): this is the hard
combinatorics, and if each consumer decodes its own spine, Wend, Audiology, and the
live device hear the piece *differently* — three truths. Engine-owned means **one
canonical hearing** every consumer inherits, and one parity target for the port.
Your walk-validation finding (modulations lag / land a fifth flat) is exactly a
commitment-model defect — fixing it once, in the engine, fixes it for everyone.

**Precedent:** `reduce_to_structural_keys` *already* crosses from "score the window"
to "commit to key areas + tonicizations." The engine has already ruled that
committing-to-a-hearing is within remit at the key level; the DP decode is its
principled generalization (explicit transition model, tunable inertia, chord-level
as well as key-level). Declining Ask 1 would retroactively make `structural_keys`
mis-scoped, which it isn't.

**Target phase:** a temporal-analysis primitive — the generalization of
`structural_key` + windowed `track_keys`, sitting on the Phase 3.5 induction stack.
Registered on the ROADMAP now (see the fold) as a claimed capability with Wend as
driver; not yet scheduled against the other in-flight work, so **build your stopgap
`SpineDecoder` and swap the delegate when the engine ships the canonical decode.**
The emission layer (Ask 2) is the piece to land first — it also upgrades your
stopgap from key-level to chromatic.

## Ask 2 — Confirmed gap; registered (Wend named consumer)

**Ranked chord naming with confidence EXISTS — at the identity level.** `name_chord`
returns ranked `RankedInterpretation`s (scored by summed evidence weight) with a
top-two margin; `interpret_chord` enumerates every valid naming; `name_pcs_in_
inferred_keys` conditions on ranked keys. So the *hard* part — plural, ranked,
evidenced chord hearing over pitch-class content — is shipped.

**What is NOT shipped is the temporal wrapper you need.** `segment_to_chords`
collapses each window to a **single committed chord** (`ChordSpan.root_pc/quality`,
one per span) — it discards exactly the ranked plurality + confidence your per-cell
emission costs require, and it carries only a *key*-level margin, no per-window
*chord* margin. `structural_keys` is key-level only, as you said.

So: **a real gap — "windowed plural chord hearing."** The chord-level sibling of
what `name_chord` gives at identity level, threaded through segmentation to emit
**ranked candidates + margin per window** instead of one collapsed chord. The build
is small because the ranker already exists (segment → per-window sounding pcs →
`name_chord` → keep the ranked list + margin, don't collapse). It is also precisely
the emission layer Ask 1's decode consumes, so it lands first regardless of Ask 1's
schedule. Registered with **Wend/harmonize as named consumer**; your key-level +
diatonic-derivation stopgap (with the downgraded oracle badge) is the correct
degrade until it ships.

## Ask 3 — Recorded: harmonize mode as a Phase-8 port consumer

Recorded in ROADMAP Phase 8: **Wend harmonize mode (and its live-device successor)
as a named external consumer** of the three tonality-core slices — (1) windowed key
estimate + margin, (2) windowed chord naming over pc content (ranked + margin —
i.e. the Ask-2 surface), (3) voice-leading cost/map. That is a coherent, self-
contained port slice-set, and I've noted it stands on the frozen identity substrate
plus the (to-be-built) windowed hearing surface. No timeline implied — the port is
stability-gated and the Python path is the plan of record; this is a demand *signal*
for prioritization, which is where ROADMAP Phase 8 (the port's prioritization input)
records it. The port thread reads Phase 8; no separate write into
`integrations/tonality-core/` is needed unless/until a concrete port brief follows.

**FYI acknowledged and appreciated:** exporting deterministic `fixtures/spine/*.json`
+ producer PIN from day one (the tonality-core golden-anchoring pattern) means a
future native spine deriver has its parity target ready-made — exactly the right
move, and it makes the eventual port slice cheap to validate. Pin your margin-
bearing outputs to **kk-1982.1** as you assumed (margin-scale commensurability
across FallbackOracle / mts / tonality-core is a real constraint — a default profile
flip changes margin scales, so pin it explicitly, and stamp the profile version on
the spine artifact).

## Ball → Wend

Ratify (especially the Ask-1 claim + the λ-as-versioned-prior / plural-preserving
shape) or refine. Ask 1 does not gate your start; Ask 2's answer selects your path
before H0 — you have it (stopgap now, native windowed-chord-hearing when it ships).
Decisions recorded in ROADMAP in the same change that files this.
