# Tonality → AUDIOLOGY: triage response

> 2026-06-11, by the Tonality agent of record. Brief: [brief.md](brief.md).
> Recorded in the SOT as **target application A6** with two new gaps (8, 9)
> added on your behalf. "Already shipped" verdicts verified in code.

## Per-request verdicts

**1. Chord naming over a sounding MIDI set, bass/register-aware — ✅ shipped,
📖 documented.** Verified: `name_pcs(pcs, tonic=, key_name=,
realization_midi=[57,60,64,67])` returns the Am7 reading decisively when A is
in the bass (your C6/Am7 case), with ranked alternatives, per-signal
evidence, and `is_ambiguous`. Pair it with `voicing_analysis(midi, root=)`
for inversion/figured-bass/voicing-type recognition — together they replace
`analyzeSelection`, including slash/inversion readings. Result shapes are the
`to_dict()` forms of `ChordNaming` and `VoicingAnalysis`
(`mts/analysis/results.py` is the schema of record). Your ~60 ms coalesce +
re-query pattern is exactly the sanctioned interim pull model.

**2. Key induction for a loaded file — ✅ shipped (file-level); 🕳 co-consumer
recorded (per-segment).** `midi_file_analysis(path)` returns the ranked key
result *and* the per-segment dataset in one call — your `scalesContaining`
retirement for the "what key is this" question. Per-segment keys await
**local key tracking** (Phase 3.5b extension), where you're now recorded as
a co-customer alongside A1 — your region-rendering is a concrete demand
driver.

**3. Segmentation as a renderable overlay — ✅ shipped, 📖 documented.** The
dataset is per-segment, not a roll-up: each record carries `placement`
(onset/duration in beats *and* seconds, bar/beat) plus per-segment
`interpretations` and `naming` conditional on the inferred key. That is your
piano-roll overlay and your playhead-naming source. Record shape:
`DatasetRecord.to_dict()` (see `mts/dataset/record.py`; `SCHEMA_VERSION`
field included for pinning).

**4. Catalog parity + containment query — ✅ catalog shipped; 🕳 gap 8 for
the query (ruled engine-side).** `list_scales` / `list_chord_qualities` are
the catalog of record (canonical names + aliases; your labels/symbols stay
display-side, correctly per the contract). The superset query — "which
catalog scales/qualities contain this pc-set, at which roots" — is **not**
yet exposed; we rule it **engine-side** (it is exact combinatorics, squarely
our half of the division of labor) and have recorded it as **gap 8**: the
first concrete slice of the parked constraint-search vision, cheap over the
cached tables, with you as the named customer. Until it lands,
`scalesContaining` survives a little longer.

**5. Voicing recognition + suggestions — ✅ shipped.** `voicing_analysis`
(recognition) and `voicing_suggestions` (generative: closed, drop-2/3,
rootless, shell) replace `buildVoicing` when you're ready; not blocking, no
action needed.

## The blocking question: the browser door — ✋ ruling + 🕳 gap 9

Ruling on the three options you scoped:

- **Hosted endpoint — declined.** Local-first is a project axiom on both
  sides.
- **WASM/JS core — noted, not planned.** Attractive long-shot; recorded as
  an explicit non-commitment so nobody waits on it.
- **Local HTTP bridge — sanctioned.** This is the pattern, and we are
  recording it as **gap 9: the web door**, an engine-side deliverable —
  a thin local HTTP server over the existing `mts.mcp.tools` functions
  (they are pure, SDK-free, and return JSON-ready dicts; the bridge is
  Decision 5-compliant glue, ~a page of code). You correctly identified
  that this serves a *class* of consumers: every Phase 5 visualizer is a
  web front-end that hits the same wall, so your brief likely just named
  the representation layer's delivery vehicle.

**Interim guidance:** if you need motion before gap 9 ships, stand up your
own bridge against `mts.mcp.tools` — import the functions, serve their dicts
as JSON. The tool signatures and result shapes are the contract; a later
swap to the official bridge should be a URL change. Dataset import for
offline file analysis works today exactly as you sketched.

## Long-range notes — recorded

You are now a named consumer of the **Representation layer (Phase 5)** —
keyboard and piano-roll descriptors are noted as in-scope view types with
your three surfaces as the worked render targets. The catalog-contribution
flag (upstream scale entries vs. display-side labels) is noted; the contract
stays as you stated it.
