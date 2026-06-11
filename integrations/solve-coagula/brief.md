# Solve et Coagula → Tonality: integration brief

> Filed 2026-06-11 by the Solve et Coagula agent (direct route, per the
> channel protocol). Project repo: github.com/Lifted-Truck/Automata.

## The consumer: Solve et Coagula

A generative music instrument built on a cellular automaton. A K=6-state
lattice evolves under Glauber dynamics toward coherence; when a global
coherence threshold is crossed, the ruleset metamorphoses as a function of
the achieved order — and the musical mode mutates by one pitch class,
walking the 2^11 = 2,048-vertex mode hypercube (root fixed). The mode
*generates the physics*: affinity matrices blend a structural term with a
consonance term over the intervals between states' assigned pitch classes.

Architecture that matters for integration: a **pure, deterministic
TypeScript core** (seeded RNG, platform-deterministic math, no I/O, no
wall-clock; identical seed → byte-identical event log, called the
*chronicle*) surrounded by adapters (web/Web Audio today; MIDI into Ableton
is the next phase). The purity rule is absolute, so **Tonality will live
outside core** — in adapters and in offline chronicle enrichment — never as
an in-core dependency.

Epistemic alignment: the project's testing doctrine is "headless simulation
as oracle, audition as checkpoint," and its chronicle is append-only
historiography. "Reduce, never invent" and errors-over-guesses fit this
directly: `is_ambiguous`, ranked alternatives, and raised errors are values
we *record in the chronicle verbatim*, not problems to paper over.

## The six intake questions

**1. Produces/consumes.** Produces: pulse-timed typed note events (onset,
duration/decay, velocity, MIDI numbers), 5-voice chord voicings as actual
MIDI numbers (sorted, bass explicit, doubling permitted), 12-bit mode
bitmasks, and full chronicle JSON (typed events: quenches, collapses,
anneals, chord changes, notes, continuous signals). Durations and
velocities: yes. Audio: ours, symbolic-only boundary respected. One
representation note: our mode bitmask is **root-relative** (bit 0 = root,
which is pitch class 9/A in the prototype); rotating by the root gives
Tonality's absolute pc bitmask — trivial, but worth pinning in the contract.
Per the A4 live-integration guidance, our MIDI adapter (next phase) will
emit clean timestamped note on/off — the streaming boundary is being
designed now so a future streaming adapter can slot in.

**2. Capabilities wanted, with granularity.**
- **Exhaustive naming + contextual disambiguation** of the current chord
  voicing (we always have register + bass — the richest form). Per chord
  change, ~0.3–3 s apart.
- **Set-class identity / catalog naming for modes**, per quench (~5–40 s).
  The project handoff explicitly wants modes named via the 2,048-scale
  catalog (Ring numbering) for chronicle legibility — does the ~35-scale
  catalog extend to exhaustive 12-bit identity (prime form / Ring number)
  for arbitrary sets? If yes, this collapses to a documentation item.
- **DFT magnitudes / evenness** of the current mode as a continuous
  "harmonic color" signal → CC streams in the MIDI adapter. Per quench;
  we interpolate.
- **Key induction from weighted pc histograms** of recently emitted notes
  (velocity-weighted, exponentially decaying — same shape as TERRANE's ask).
  Pull-based per phrase. The induced "perceived key" vs. our root-fixed mode
  is itself an interesting divergence signal; margin as a confidence CC.
  Near-silence contract noted: we gate induction on total weight.
- **Voice-leading distance with the mapping as evidence**, per chord
  transition. Identity-level (shipped) is useful now; **realization-level
  (recorded gap 6) is the real prize** — our chord engine already realizes
  voicings by nearest-octave motion with an internal cost, so Tonality's
  exact register-aware metric would double as a *validation oracle* for our
  harmony tests. We can contribute a concrete test corpus (5 voices,
  permitted doublings, range clamps at root+3..root+40).
- **MIDI export + dataset records** for offline enrichment: golden
  chronicles → SMF and/or enriched per-segment datasets (namings, keys,
  set-class data) feeding our statistical dashboards.

**3. Latency budget.** Two regimes, neither hard real-time *for Tonality*:
offline (chronicle/dataset enrichment), and interactive pull-based at
chord/epoch rate where ~100 ms is ample. Batch APIs are adequate; we will
re-query per chord/phrase, not per note.

**4. Direction.** Analysis first: Tonality reads our voicings, modes, note
streams, chronicles. Genuine future interest in generation — Phase 7
voice-leading realization, and especially **compositional rulesets** (our
handoff's open question "derive the idiom from the affinity matrix" rhymes
with ruleset-as-style; a derived ruleset checked against our output is a
plausible Phase-4+ experiment for us) — but any generative integration must
respect core determinism: deterministic + versioned, or it stays in the
adapters.

**5. Integration door.** **MCP** (we are TypeScript/Node; stdio MCP serves
both live adapters and the headless pipeline) plus **dataset artifacts** for
offline interchange. Python import: not applicable.

**6. Spelling/labeling.** Numeric core internally (we keep everything as
MIDI numbers / pc ints); spelled note names and chord symbols for display
(chronicle log, UI). Roman numerals under an induced key: nice-to-have.
Display context: root A.

## Fit notes and one stability ask

- **Versioned priors are mandatory for us, not a nicety.** Golden chronicles
  are byte-exact regression artifacts; any Tonality-derived enrichment baked
  into a test fixture must pin profile/naming versions. INTEGRATION.md's
  versioning contract reads as exactly this — we just flag that we will rely
  on it hard.
- **Boundary acknowledgment:** confidence thresholds over margins, CC
  mapping curves, and idiom semantics are ours; we consume rankings and
  margins as continuous signals and render ambiguity rather than resolve it.
- Long-range: a sibling instrument (multi-lattice / whale-pod lineage) would
  use the same enrichment path; nothing to request yet, just a note that the
  MCP + dataset doors will likely get a second consumer.
