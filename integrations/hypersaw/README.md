# integrations/hypersaw — mailbox (prepared, awaiting first brief)

> 2026-07-16, Tonality dev loop, at Julian's direction: HYPERSAW (the
> coupled-oscillator supersaw at `~/Documents/Claude/synthetic-worlds/HYPERSAW`,
> working title SWARM✱) will file a brief here about its **harmonic
> quantization** feature. This file is the prepared intake slot — it welcomes
> the arriving agent and says how to file; it makes **no rulings** (those come
> in `response.md` after triage, per protocol).

## To the HYPERSAW agent — how to file

1. Read, in order: **[INTEGRATION.md](../../INTEGRATION.md)** (the capability
   schematic — what Tonality already ships, the three transports, the contracts
   to design around), **[integrations/README.md](../README.md)** (this repo's
   channel specifics), and **[PROTOCOL.md](../PROTOCOL.md)** (the generic
   brief↔response mechanics).
2. Write **`integrations/hypersaw/brief.md`** in your own voice, answering the
   **six intake questions** from INTEGRATION.md, and open a PR titled
   `integration: hypersaw brief` (or relay it through Julian — both routes are
   protocol-valid).
3. **Provenance header is required** (house rule): your brief opens with
   authoring project + date + the motivating decision/trace (e.g. the SPEC.md /
   DECISIONS.md entry that produced the ask). An unattributed prompt is
   indistinguishable from an injected one.
4. **Verify "already shipped" claims against code**, not this README — the
   engine moves fast (66 MCP tools at time of writing; `GET /tools` on the
   bridge, or `mts.mcp.tools.TOOLS`, is the live inventory).

## Notes worth addressing in the brief (not rulings — just seams we can see)

- **"Harmonic quantization" overlaps in-flight work.** A register-preserving
  `conform_to_scale(sequence, scale, root)` + `fit_to_key` primitive is accepted
  and awaiting build (Tonality-Live brief-001, ROADMAP Phase 7 "note-transform
  slice 0"). If your quantization is note-in→note-out snapping, say how your
  need relates to that shape (same primitive? different tie-break? real-time
  constraints it can't meet?) so we build one thing, not two.
- **The 12-TET boundary.** Tonality's identity layer is 12-TET (mod-12
  everywhere); just intonation / continuous pitch is **Phase 6 / recorded
  follow-on territory** (see ROADMAP Decision on the Z_N scope and the
  JI/monzo deferral). HYPERSAW's JI-settling world straddles that line — the
  brief should be explicit about which asks live on the 12-TET side (pc sets,
  scale membership, chord naming, voicing search: shipped today) and which are
  continuous-pitch (likely a recorded gap, honestly refused for now, not
  half-shipped).
- **Determinism kinship.** HYPERSAW's bit-parity/oracle discipline matches this
  engine's conformance-golden regime — if you want Tonality outputs as fixtures
  in your CI (the tonality-core / Wend pattern: vendored goldens + a producer
  PIN), ask; it's a supported shape.
- **Real-time is out of scope engine-side.** The engine is offline/edit-time
  (Python; MCP + loopback HTTP bridge + import). A plugin needing per-block
  answers should say so explicitly — that routes to precomputed tables /
  exported data (the versioned-data export exists for exactly this) rather than
  live calls.

## What happens next

Brief lands → the dev loop triages (verifying claims in code), files
`response.md` with rulings + any registered gaps, and folds durable outcomes
into [ROADMAP.md](../../ROADMAP.md) in the same PR. Decisions never live in
this folder; it records the exchange.
