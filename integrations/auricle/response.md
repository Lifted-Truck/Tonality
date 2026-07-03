# Tonality → AURICLE: response (harmony-contract RFC triage)

> Triage of [brief.md](brief.md), 2026-07-03, by the Tonality agent of record.
> Every "already exists" claim below was verified in code, per protocol. The
> durable decisions live in ROADMAP.md — **Decision 11** (contracts as object
> code + the multi-client scope rule), **gap 16** (the contract format), and
> **gap 17** (voicing enumeration/ranking); **A8** is your target-application
> entry. This file is the routing map between your brief and those anchors.

## Headline

The RFC is accepted in substance: **Tonality will own the compiled
harmony-contract format** (Decision 11). And your one flagged assumption is
wrong in your favor — **deliverable 2 already ships**. Details per section:

## §4.1 `voice_leading_map` — ✅ shipped (2026-06-11), better-verified than you asked

Your assumption ("Tonality computes voice-leading distance today but not the
assignment map") is false at *both* specification levels:

- **`voice_leading_realized(source_midi, target_midi)`** (`analysis/voice_leading.py`,
  MCP tool #18) is your §4.1, already: concrete MIDI voicings in → **optimal
  assignment pairs + total cost** out (`RealizedVoiceLeading.mapping` +
  `.distance`). Octaves cost 12; register is required (raises on `None` — the
  cardinal rule).
- The identity-level `voice_leading(source_mask, target_mask)` *also* returns
  its optimal pc-pair `mapping`, not just the scalar.
- **Cardinality mismatch is already policied**: doubling/omission under the
  **`doubling.1`** policy — which is *exported as data* (id + description) in the
  versioned-data manifest/bundle (`mts/io/export.py`), so a contract can cite it.
  Your proposed alternative (explicit voice birth/death) is **not** implemented;
  if AURICLE's resonator glides need births/deaths rather than doublings, that
  is a round-2 ask — say so with a concrete case, and it becomes a second named
  policy beside `doubling.1`, never a silent change.
- Your §7 acceptance criterion (returned cost == independently computed cost of
  the returned assignment; exhaustive vs. brute force) is already effectively
  pinned: the optimal pairing is **brute-force-verified** in tests, and an
  independent 286-case five-voice corpus from another consumer agrees 285/285
  (`tests/test_vl_corpus.py`; gap 6 has the full record).

So deliverable 2 reduces to exactly what your fallback clause anticipated:
**serialize the existing result into the contract's `voiceMap`** — part of
gap 16, not new theory.

One caveat your schema should absorb: `mapping` pairs are **(source_midi,
target_midi) values**, not (fromIdx, toIdx) indices. The contract emitter will
translate to your index convention; if you consume the analysis surface
directly in the meantime, translate accordingly.

## §3 `voicing ⊆ pcs` — ✅ endorsed, and stronger than you claim

You frame it as a pragmatic contract-coherence constraint. It is more than
that: it is Tonality's **cardinal rule**. A voicing is a *realization*; a
realization must **reduce to** its identity key (`event → realization →
identity key`). A voicing tone outside `pcs` means the state's realization
does not reduce to its stated identity — the artifact isn't merely
self-contradictory for your mask/resonator plumbing, it is *theoretically
malformed*. The validator will enforce it as a first-class invariant, and the
schema comment can cite the doctrine instead of apologizing for arbitrariness.

## §4.2 constrained voicing generation/ranking — ✅ accepted, with the boundary drawn (gap 17)

Ruled under the scope rule recorded with Decision 11 (Julian, 2026-07-03):
*anything that may benefit multiple clients in the future and doesn't break
the cardinal rules belongs in Tonality.* Voicing enumeration/ranking clears
both tests — you, TERRANE, and the registered+rootless "voicing template"
corner of the identity lattice all want it — so Tonality takes **both halves**,
split exactly along the line your own fallback drew:

- **Ranking** (analytical): rank candidate voicings of a pc set under register/
  spacing constraints, with margins and ties surfaced. The ranking authority
  already has its metric (`voice_leading_realized` + `doubling.1`).
- **Enumeration** (generative): a thin, **explicitly generative** layer — same
  precedent as groove *apply* (gap 10) and the gap-2 transformations. Choosing
  register from an identity is a generative act; it is in scope *as* one,
  clearly labeled, never disguised as analysis. Deterministic:
  same-input-same-output, any randomness seed-explicit.

Hand-authored or client-supplied voicings remain valid contract input
regardless — §4.2 gates nothing in gap 16.

## §4.3 validator + emitter — 🕳 recorded gap (gap 16), accepted

New surface, cleanly in scope. Shape notes that are Tonality's call (you
offered; we're taking you up on it):

- **Versioning rides the existing discipline**, not a new one:
  `mts/io/export.py` already stamps `EXPORT_SCHEMA_VERSION` and version-cites
  every data asset and policy. The contract emitter reuses that machinery —
  `meta.tonalityVersion` + a contract schema version, canonical serialization
  (sorted keys), same pattern as the manifest/bundle.
- **Semantic checks** (voicing⊆pcs, transition endpoint resolution, voiceMap
  index bounds, sequence resolution) are pure functions → a `contracts` module
  below the MCP line, with thin MCP wrappers per Decision 5. Your attached
  draft schema/validator are the *starting point, adapted not adopted* — as
  your own brief specifies. Namespace and field names will be settled when
  gap 16 is scheduled; your "Tonality's call; AURICLE will conform" is
  recorded.
- Your §7 acceptance criteria are adopted nearly verbatim into gap 16,
  including the cross-repo end-to-end fixture (chord list in → contract out →
  AURICLE's vendored validator passes it unmodified).

## §5 division of labor — ✅ endorsed as written

Your table matches Tonality's thesis exactly, and your sanctioned-degraded
client fallbacks (~15 lines of visibly-inferior arithmetic, diagnostics when
engaged, never grown) are the same shape as the **consumer-port corollary**
already on record under Decision 10: bounded duplication, mechanically
checkable, destination is linking the shared core. No friction.

## §6/§8 non-goals + migration — ✅ agreed

- No runtime coupling; no client-specific schema fields; `edo` reserved, no
  EDO work now — all consistent with existing rulings.
- Migration order stands: Tonality adapts the schema and assigns its own `$id`
  at v1; AURICLE then vendors and pins (your D-11). §4.2 lags §4.1/§4.3
  without blocking anything, exactly as your step 3 anticipates.

## What to do with this

Everything committed-to is in ROADMAP.md (Decision 11, gaps 16–17, A8);
everything usable **today** is `voice_leading_realized` (MCP #18, HTTP bridge
`POST /call/voice_leading_realized`) and the versioned-data export. When the
AURICLE agent spins up, its first brief can be the birth/death-policy question
and the concrete register/spacing constraint vocabulary for gap 17.
