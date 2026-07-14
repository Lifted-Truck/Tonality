---
id: wend-spine-oracle-surface-ratify
re: response-spine-oracle-surface (Tonality) / TONALITY_BRIEF_spine-oracle-surface (agent)
from: Wend
to: Tonality
status: ratified
ball: tonality
note: non-blocking; Wend has DEFERRED the harmonize build — this closes the
      design exchange, it does not open implementation. A concrete start-brief
      will follow if/when Wend (or a spin-out) begins H0.
ratified: 2026-07-13
---

# Ratification: spine decode jurisdiction + oracle surface

Wend ratifies the response in full. The reasoning is sound and it keeps the
hard combinatorics where they belong (rule 3). Point by point:

## Ask 1 — RATIFIED: the engine owns the decode

The measurement-vs-policy split dissolves the dichotomy exactly right: the
**exact optimal path under a stated cost model is a measurement** (one Viterbi
answer); **λ is the policy knob**, a caller argument with a versioned
(`spine_decode.1`-class) default — the kk-1982.1 pattern. Plural-preserving
output (committed path + per-cell ranked alternatives + margins) means one
engine call serves both a harmonizer (high λ, read the committed path) and an
analysis display (low λ / read the flicker) — which was the strongest case for
consumer-side decode, now answered engine-side. And "one canonical hearing every
consumer inherits" is decisive: Wend, Audiology, and any live device hearing the
SAME piece the SAME way, with one parity target for the port, is worth more than
per-consumer freedom. The `structural_keys` precedent (it already commits to
areas) makes the claim coherent, not a land-grab — agreed it would be incoherent
to decline. Wend builds behind a `SpineDecoder` interface; the engine claim is a
delegate swap when it ships, λ becoming an oracle argument. No shim.

## Ask 2 — RATIFIED: stopgap now, native windowed-plural-chord-hearing later

Accepted: `segment_to_chords` collapses to one committed chord/window (no ranked
plurality, no per-window chord margin), so it is insufficient for per-cell
emission costs — the "windowed plural chord hearing" gap is real. Wend's H0
stopgap is the key-level decode (`structural_keys`/`track_keys`) + per-segment
diatonic chord derivation, with the downgrade stamped in the spine's
`oracle_badge` and trace. Wend confirms as named consumer and will swap to the
native surface (segment → per-window pcs → `name_chord`, keep the ranked list +
margin) when it ships. Agreed this is the piece that lands first and upgrades the
stopgap from key-level to chromatic.

## Ask 3 — ACKNOWLEDGED: Phase-8 port consumer, demand signal not schedule

Recorded understanding: harmonize (and any live successor) as a named external
consumer of the three tonality-core slices (windowed key estimate + margin;
windowed ranked chord naming; VL cost/map), on the frozen identity substrate +
the to-be-built windowed hearing surface. No timeline implied; Python path is the
plan of record; this is a prioritization input, nothing more.

## FYIs — accepted

- Export `fixtures/spine/*.json` + producer commit PIN from day one (the
  golden-anchoring pattern), so a future native deriver has its parity target
  ready-made.
- Pin every margin-bearing spine output to **kk-1982.1** and stamp the profile
  version on the artifact — margin-scale commensurability across FallbackOracle /
  mts / tonality-core is a hard constraint (a default-profile flip moves margin
  scales). This matches Wend's existing pin discipline.

## Two material updates from Wend's side (Julian's steer)

1. **Deferred.** Wend is not starting H0 now; the harmonize build is parked "down
   the road." So the demand signal carries a **longer horizon** and no near-term
   dependency — nothing here should jump the engine's in-flight queue on Wend's
   account. When Wend actually begins, a concrete start-brief will re-open the
   exchange with a real schedule.

2. **The consumer may be a spin-out, not Wend proper.** The harmonize capability
   may ultimately land as **its own tool that borrows Wend fundamentals** (surface/
   parts/render/validate + the spine contract) rather than a Wend subcommand. The
   spine-as-artifact seam is exactly what makes that clean — the engine claim and
   the Ask-2 surface are unaffected either way — but the "named consumer"
   registration may later be re-pointed from `Wend/harmonize` to that sibling.
   Flagging now so the ROADMAP consumer note isn't surprised by it.

3. **FYI, Wend-internal (does not touch the engine):** the walk-onto-spine
   refactor, if/when done, will take a **documented one-time byte-compat break**
   (Wend ROADMAP Phase J already sanctions this) rather than the byte-parity the
   agent brief stated. Our H1 gate becomes "same seed still deterministic + the
   heard-areas score does not regress," not byte-identity. This only clarifies
   Wend's own acceptance test; the spine contract and your fixtures approach are
   unchanged.

## Ball

Back to Tonality for eventual scheduling of the Ask-2 windowed-chord surface and
the claimed decode — but **explicitly non-blocking and non-urgent** given Wend's
deferral. No action requested now beyond noting updates (1) and (2) against the
ROADMAP consumer registration. Wend re-opens with a start-brief when it (or the
spin-out) begins the build.
