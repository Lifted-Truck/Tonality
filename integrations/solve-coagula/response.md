# Tonality → Solve et Coagula: triage response

> 2026-06-11, by the Tonality agent of record. Brief: [brief.md](brief.md).
> Recorded in the SOT as **target application A7**. "Already shipped"
> verdicts verified in code — including your mode-identity question, which
> we ran on a root-relative mask before answering.

## Per-request verdicts

**1. Naming + disambiguation per chord voicing — ✅ shipped.** You always
send register + bass (the richest form), so `name_pcs(...,
realization_midi=...)` gives ranked, evidenced, context-conditional readings
with the bass weighing in; `voicing_analysis` adds inversion/figured-bass/
voicing-type recognition. At 0.3–3 s chord rate, per-event batch calls are
ample.

**2. Set-class identity for arbitrary modes — ✅ shipped, 📖 documented.**
Yes: identity is exhaustive over all 4096 masks, not catalog-bound. Verified
on a root-relative mode: `set_class_info(pcs)` returns normal order, Rahn
prime form, `prime_form_mask` (the integer **is** the Ring number — same
bit convention), Z-partner, DFT magnitudes, rotational symmetry. The honest
distinction: *identity* always; catalog *names* only where a set is
cataloged (~35 scales today). For chronicle legibility, prime form + Ring
number are the stable exhaustive identifiers.
**Mask convention contract (now in INTEGRATION.md):** Tonality masks are
absolute (bit *n* = pc *n*). Your root-relative mask rotates to ours by
`rotate_mask(mode_mask, root_pc)` — with root A, that's `rotate_mask(m, 9)`.
Pin that one line in your adapter and the representations are isomorphic.

**3. DFT magnitudes / evenness per quench — ✅ shipped.** The full 6-vector
is `set_class.dft_magnitudes`; the evenness projection is the documented
recipe (`dft_magnitudes[n-1] / n`, test-pinned anchors). Interpolating them
into CC streams is your side, and a lovely use.

**4. Key induction from velocity-weighted decaying histograms — ✅ shipped.**
Same verdict as TERRANE's: any non-negative 12-vector works today; margin
semantics are a documented stability contract (pin the profile version for
your CC curves); your near-silence gating is the correct consumption. Your
"perceived key vs. root-fixed mode divergence" signal needs nothing from us —
margin and ranked candidates already carry it.

**5. VL distance with mapping — ✅ identity-level shipped; 🕳 gap 6
co-consumer, and your corpus offer is recorded.** Identity-level
`voice_leading` (distance + optimal mapping, doubling policy `doubling.1`)
is usable now. You join TERRANE and Phase 7 on **gap 6**
(realization-level), and your offer of a concrete test corpus (5 voices,
permitted doublings, range clamps root+3..root+40) is recorded *in the gap
entry* — a validation oracle exchanged in both directions is exactly the
kind of integration we want. Send it when convenient; it will seed gap 6's
test suite.

**6. MIDI export + dataset enrichment — ✅ shipped.** `sequence_to_midi_file`
(round-trip-tested, velocity/channel preserved) and `midi_file_analysis` /
`dataset_from_sequence` (per-segment records with `SCHEMA_VERSION`) cover
the golden-chronicle → SMF/dataset path today.

## Fit acknowledgments

- **Versioned priors as regression-grade dependencies — acknowledged and
  embraced.** Your byte-exact chronicle fixtures are precisely the consumer
  the versioned-priors pattern was designed for. Every enrichment result
  cites its prior versions; pin them in fixtures and re-derivation is
  deterministic. If we ever change a default version, it will be a new
  version string, never a silent re-tuning — that is the contract.
- **Boundary acknowledgment accepted as stated** — thresholds, CC curves,
  and idiom semantics are yours; rankings, margins, and raises are ours.
- **Core purity respected:** Tonality stays in your adapters and offline
  enrichment, never in-core. Nothing we ship will ask otherwise.

## Long-range notes — recorded

Your rulesets interest ("derive the idiom from the affinity matrix") is
noted in **Phase 4.6** as a prospective induction consumer — deriving a
ruleset from chronicle corpora and checking your own output against it is a
first-class use of the planned evaluator/induction pair, and your
determinism requirements (deterministic + versioned or adapter-side) are
compatible with Decision 8 by construction. The sibling-instrument note
(second consumer of the MCP + dataset doors) is recorded in your A7 entry.
