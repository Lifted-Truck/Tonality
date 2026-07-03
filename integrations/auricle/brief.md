# AURICLE → Tonality: brief (RFC — compiled harmony contracts as a Tonality export format)

> Relayed 2026-07-03 by Julian (the AURICLE agent was not yet spun up; filed by
> Tonality's agent of record per the relay route in [../README.md](../README.md)).
> Original filename in the AURICLE repo: `PROPOSAL-TONALITY-HARMONY-CONTRACT.md`
> (kept there as their copy of record). Verbatim below the rule.

---

# PROPOSAL-TONALITY-HARMONY-CONTRACT.md
## RFC: Compiled Harmony Contracts as a Tonality Export Format

**From:** AURICLE (grain manipulator VST, first external consumer)
**To:** Tonality ROADMAP.md, via standard branch/PR process
**Status:** Draft for reconciliation against Tonality's integrations protocol
**Depends on:** nothing in Tonality's runtime; adds surface only

> **Protocol caveat:** The Tonality repo was not readable from this session, so
> this document is structured against Tonality's known conventions (ROADMAP.md as
> single source of truth; agent-led branches/PRs; outputs plural, ranked, and
> evidenced; "reduce, never invent"). Before submission: reconcile section
> numbering, proposal format, and naming against the repo's actual integrations
> protocol doc, and verify §4's "current capability" assumptions against
> ROADMAP.md — items assumed missing may already exist or be planned.

---

## 1. Summary

Tonality should own a **compiled harmony contract** format: a versioned,
schema-validated JSON artifact that freezes theory decisions (pitch-class sets,
concrete voicings, voice-leading transition maps, quantization policy) into a
deterministic document that real-time clients consume without any runtime
dependency on Tonality.

Three deliverables:

1. **The schema** (`contracts/harmony.schema.json` in Tonality, versioned) +
   a contract validator (`tonality.contracts.validate`).
2. **`voice_leading_map(voicingA, voicingB) → (assignment_pairs, cost)`** —
   the optimal voice assignment itself, not only the distance scalar.
3. **Constrained voicing generation/ranking** — N-note voicings of a pc set
   under register/polyphony constraints, ranked with margins.

A draft schema, a golden contract, and a validator with semantic checks already
exist in the AURICLE repo (provisional, marked for upstream migration per
AURICLE D-11) and are attached as the starting point, to be adapted — not
adopted verbatim.

## 2. Motivation: compiler, not library

Tonality's stated role is infrastructure and coherence layer for downstream
products. The contract format is the missing link for *real-time* downstream
products, which cannot call Python and must be deterministic:

- **AURICLE** needs pc sets + voicings + voice-leading maps to drive grain
  quantization, a modal resonator bank with voice-leading glides, and a chroma
  mask — all from one authority.
- **TERRANE**'s harmonic state reshaping the timbre terrain is the same shape of
  consumer: discrete harmonic states + transition behavior.
- **wend** already serializes harmonic decisions with full traces; a shared
  contract format would let wend *emit* contracts other clients play through.

Without a Tonality-owned format, each client grows its own dialect — the
Audiology divergence, repeated three times. The model that prevents it:
**Tonality as compiler, contracts as object code, N clients as targets.**
Analysis/authoring stays in Tonality where it belongs; clients get a frozen,
diffable, version-controlled artifact. Text as truth, applied to harmony.

## 3. The contract format (proposed shape)

See attached `harmony.schema.json` (draft 2020-12). Core:

- `states[]`: id, `pcs` (pitch classes, mod `edo`), `voicing` (root + concrete
  MIDI notes for client voices), optional `evidence` block — **this is where
  Tonality's plural/ranked/evidenced discipline lands in the artifact**: rankings,
  margins, and derivations travel with the contract as provenance, ignored by
  runtimes, preserved for audit.
- `transitions[]`: from/to, `voiceMap` ([fromIdx, toIdx] pairs — the serialized
  output of deliverable 2), optional `glideMs`, optional `cost` (provenance).
- `quantize`: mode + strength policy.
- `meta`: name, author, **`tonalityVersion`** stamp (which compiler produced it).
- `version`, `edo` (12 fixed in v1; field exists so 12-TET is an instance, not
  an assumption — aligned with Tonality's exact-arithmetic trajectory).

**One semantic rule requiring documentation in the schema itself**, because it
reads as arbitrary otherwise: `voicing ⊆ pcs` per state. This is a
*contract-coherence* constraint, not a theory claim — clients may drive multiple
subsystems (masks, quantizers, resonators) from `pcs` simultaneously, so a
voicing tone outside `pcs` makes the artifact self-contradictory (e.g. a spectral
mask attenuating the client's own resonators). Musically richer voicings are
expressed by extending `pcs`. The validator enforces it; the schema comment
explains it.

Namespace and field names are Tonality's call; AURICLE will conform.

## 4. Requested capabilities

### 4.1 `voice_leading_map` (assignment, not just distance)
Given two concrete voicings, return the cost-minimal voice assignment (bijection
where cardinalities match; policy for mismatch to be defined — octave-wrap or
explicit birth/death of voices) under Tonality's existing voice-leading distance.
This *selects among given material* — squarely inside "reduce, never invent."
Output: pairs + total cost + (per discipline) alternatives within margin, if any.

*Assumption to verify:* Tonality computes voice-leading distance today but not
the assignment map. If the map already exists, this item reduces to "expose it
in contract serialization."

### 4.2 Constrained voicing generation/ranking
Given a pc set, a voice count N, and register constraints (range, optional
spacing rules), return ranked candidate voicings with margins. If generation is
judged to cross the "never invent" line, an acceptable reduction: rank
*client-supplied* candidate voicings, with generation as a thin enumeration
layer clearly separated from the ranking authority.

### 4.3 Contract validator + emitter
`tonality.contracts`: `validate(doc)` (schema + semantic checks: voicing⊆pcs,
transition endpoint resolution, voiceMap index bounds, sequence resolution) and
`emit(states, transitions, policy) → doc` (canonical serialization, sorted keys,
stamped `tonalityVersion`). MCP tool wrappers for both, consistent with the
existing 17-tool surface.

## 5. Division of labor (explicit boundary)

| Concern | Owner |
|---|---|
| Theory: sets, voicings, voice-leading, ranking, evidence | Tonality |
| Contract schema, validator, canonical emitter | Tonality |
| Contract *consumption*: glides, quantization application, masks | Clients |
| Trivial mod-arithmetic fallbacks (greedy assignment when voiceMap absent; pcs-from-held-MIDI) | Clients, documented as degraded, instrumented (AURICLE oracle O-H1), never grown |
| Authoring orchestration (`author_contract.py` etc.) | Client repos, zero theory logic |

Client fallbacks are the one sanctioned duplication: real-time threads cannot
call Tonality, and the duplicates are bounded to ~15 lines of arithmetic each,
required to be *visibly inferior* (diagnostics fire when engaged).

## 6. Non-goals

- No runtime/network coupling: clients never call Tonality during audio.
- No client-specific fields in the schema (AURICLE's bank polyphony etc. stay in
  client presets; contracts describe harmony, not instruments).
- No EDO generalization work now — only the `edo` field reserving the door.
- No obligation on Tonality to know contracts' consumers exist.

## 7. Acceptance criteria (proposed, for Tonality's oracle style)

- Schema versioned in-repo; validator rejects a malformed-contract corpus with
  documented error classes; golden contracts round-trip byte-identically
  (canonical emission).
- `voice_leading_map`: on golden voicing pairs, returned cost equals the
  independently computed voice-leading distance of the returned assignment;
  exhaustive check vs. brute force for N ≤ 8.
- Voicing ranking: deterministic order with explicit margins; ties surfaced,
  not hidden (plural outputs discipline).
- One end-to-end fixture: chord list in → contract out → AURICLE's vendored
  validator passes it unmodified (cross-repo integration check, runnable in
  either CI).

## 8. Migration plan

1. Tonality adopts/adapts the schema; assigns its own `$id`; publishes v1.
2. AURICLE moves its copy to `schemas/vendor/`, pins the version, deletes local
   authority (D-11 executed).
3. `author_contract.py` implemented as pure orchestration once §4.1/§4.3 land
   (§4.2 can lag; hand-authored voicings remain valid contracts).
4. TERRANE/wend adopt the format when their harmonic-state work next surfaces —
   no action now; the point of doing this in Tonality is that no action is
   needed then.

## 9. Attachments

- `harmony.schema.json` (AURICLE provisional draft)
- `tests/contracts/golden-cmaj7-fmin9.json` (golden contract; nb: its voiceMaps
  are hand-written identity maps, exactly the thing §4.1 replaces)
- `tools/validate_docs.py` (semantic checks §3 refers to — the voicing⊆pcs check
  caught a real authoring error (B♭ for A♭ in an Fmin9 voicing) on first run,
  which is both the case for the validator and the case for never authoring
  contracts by hand)
