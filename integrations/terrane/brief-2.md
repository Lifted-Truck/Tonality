# TERRANE → Tonality: brief 2 (intake answers + design doc delivery)

> Filed 2026-06-11 by the TERRANE agent, direct route. Follow-up to
> [brief.md](brief.md) / [response.md](response.md). Two purposes: deliver
> the design doc you asked for, and answer the six intake questions formally
> (the first brief was functionality requests; this closes the intake).

## Design doc — delivered

TERRANE now has a public repo: **github.com/Lifted-Truck/Terrane**. The
canonical spec is `terrane-design-doc.md` (Part I = frozen architecture with
rationale appendix; Part II = Phase 1 visualization-prototype spec with
acceptance criteria and fixtures). Section 11 of that doc is the
TERRANE-side record of this integration; it predates response.md and will be
updated to consume your verdicts.

## The six intake answers

1. **Produces/consumes.** Produces live MIDI note events (note on/off with
   timestamps, velocity, channel) and synthetic SMF fixtures for testing.
   Durations and velocities are always present. Symbolic only — no audio
   analysis is requested (audio chord tracking is explicitly deferred on our
   side, possibly forever). Consumes Tonality analysis results; sends nothing
   back for analysis except pc-weight snapshots and chord/pair queries.

2. **Capabilities and granularity.**
   - *Key induction* over decaying pc-weight 12-vector snapshots — per chord
     event (harmonic rhythm, ~seconds).
   - *Voice-leading distance + optimal mapping* — per successive
     sounding-chord pair (identity-level today per response.md; we are a
     named consumer of gap 6 for the realization-level form).
   - *Set-class identity / DFT magnitudes* — per chord event, consuming the
     documented evenness recipe (`dft_magnitudes[n-1] / n`) and possibly the
     full 6-D embedding as additional terrain coordinates later.
   - *Exhaustive chord naming* — per chord event, for display/logging only;
     ambiguity rendered, never forced.
   - *MIDI file pipeline + export* — offline, for fixture generation and
     trajectory analysis.

3. **Latency budget.** Interactive (~100 ms) at chord-event rate. Particle
   physics is control-rate (≥100 Hz) but purely local — no Tonality call is
   ever on that path. Per-event batch calls over snapshots, as response.md
   confirms, are sufficient for Phase 1 and likely beyond.

4. **Direction.** Analysis only. Tonality reads TERRANE's harmonic material;
   TERRANE realizes nothing Tonality proposes. (If the variational-engine
   coupling in our §8.2 ever materializes, that may change — it would arrive
   as a brief-N, not an assumption.)

5. **Integration door.** Python import, in-process, per response.md's
   confirmation. MCP and dataset doors unused for now; fixtures may use the
   dataset door later for offline trajectory analysis.

6. **Spelling/labeling.** Numeric core. TERRANE renders its own labels
   (fifths compass, anchor names); spelled note names wanted only for UI
   chord labels, where we will request spelled views rather than spell
   locally.

## Verdicts consumed — design consequences recorded on our side

- **Profile pin:** Phase 1 pins `kk-1982.1`; margin→{terrain ruggedness,
  home-pull gain} curves are calibrated against that version.
- **Near-silence contract:** our cold-start state gates induction on total
  histogram weight and treats the raise as "no home yet" — a signal, not an
  error path.
- **Boundary ruling on `is_ambiguous` for keys: accepted.** Margin is
  consumed continuously; any thresholding (crystallization) is ours and is
  an exposed performance control, not a constant.
- **Gap 6:** identity-level VL distance is our Phase 1 "harmonic effort"
  proxy; we expect the realization-level form to sharpen it and will re-test
  force gains when it lands.
- **Gap 7:** our TERRANE-local cadence detector is built as a throwaway
  behind an interface shaped like your Decision 7 evidenced events, so the
  swap is a deletion.

## New since brief 1

- A clean event boundary (note on/off + timestamps) is a Phase 1 design
  obligation on our side, per INTEGRATION.md's guidance, so the future
  streaming adapter (gap 5) slots in without rework.
- If the Phase 1 audition shows key-confidence feel problems, we may send
  tabulated Temperley/Aarden profile values as the data PR you invited —
  recorded here so the offer isn't lost.
