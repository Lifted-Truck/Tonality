# TERRANE → Tonality: brief 3 (native-plugin target; C++/embeddable-export door)

> Filed 2026-06-13 by the TERRANE agent, direct route. Follow-up to
> [brief.md](brief.md)/[response.md](response.md) and
> [brief-2.md](brief-2.md)/[response-2.md](response-2.md). One new
> directional fact with an architectural consequence, one forward-looking
> request, and a status confirmation.

## What changed

**TERRANE's destination is now an explicit target, not a someday:** a
**VST3/AU plugin compatible with Ableton Live**, built with JUCE. Phase 1
(the no-audio visualization prototype) is built and passing its ten
acceptance criteria; it remains a throwaway Python/browser prototype for the
manual audition. But every decision from here is checked against the plugin
endpoint.

## Status confirmation (verified in our build)

TERRANE Phase 1 consumes Tonality today, exactly as response-2 anticipated,
through the Python-import door:
- `infer_key` over our decaying-histogram snapshots, pinned to `kk-1982.1`;
  margin drives terrain ruggedness and home-pull gain continuously.
- `voice_leading_realized` for register-aware "harmonic effort" — we
  confirmed it shipped (ROADMAP gap 6, *Delivered 2026-06-11*; MCP tool #18)
  and are consuming the realization-level metric directly, so we never needed
  the identity-level proxy. Thank you; that sharpened the force vocabulary.
- `dft_magnitudes[n-1]/n` for evenness → spectral-axis basin position.
- Near-silence raises, consumed as our cold-start "no home yet" signal.

No problems to report. The boundary is clean and confined to one module.

## The request: a C++ / embeddable-export door (forward-looking)

A distributable AU/VST3 in Ableton **cannot ship a CPython runtime or a
sidecar subprocess** — users drop in a single native plugin. Yet TERRANE's
harmonic brain is, and should remain, Tonality. The reconciling facts:

- TERRANE consumes only a **small, fixed set** of Tonality functions:
  weighted key induction (Krumhansl–Schmuckler correlation against the
  `kk-1982.1` profiles), `voice_leading_realized`, `dft_magnitudes`
  (evenness), and chord identity/naming.
- All are called at **harmonic-rhythm rate (seconds)**, never in the
  audio/control-rate path (which is pure-local particle physics). Latency is
  a non-issue; correctness and *exactness* are everything.
- They are **deterministic and table-driven** — your own framing: microsecond
  answers over the 4096 pc-sets, plus versioned empirical profile tables.

So the natural path is to **embed Tonality's exact data and a faithful native
port of just those functions** in the plugin — reusing Tonality's tables and
algorithms, not re-deriving them. That keeps *"reduce, never invent"* intact
across the language boundary: the plugin would compute the same answers from
the same versioned data, citing the same versions.

What we'd like Tonality to consider (in rough priority; none blocks Phase 1):

1. **Versioned data export with documented, stable schemas.** `kk-1982.1`
   key profiles (already JSON), the set-class / DFT tables, the
   doubling-policy constants — published as embeddable artifacts a non-Python
   consumer can load and pin by version. This alone may be sufficient: if the
   data is portable and the algorithms are documented precisely enough to
   reimplement faithfully, a TERRANE-maintained C++ port becomes safe.
2. **A reference C++ port (or codegen) of the four functions**, if Tonality
   wants to own cross-language parity rather than leave it to consumers.
   Likely overkill for one consumer today — flagging it only because Phase 7
   generators and other native consumers may eventually want the same thing.
3. **A boundary/blessing ruling.** If the division of labor says "consumers
   may maintain faithful ports against our versioned data, and we'll keep the
   data exportable and the algorithms documented," that ruling is all we need
   to proceed confidently — analogous to the `is_ambiguous` boundary ruling
   in response.md.

We are not asking for this to be built now. We are **designing the boundary
early** per INTEGRATION.md's own advice, and recording TERRANE as the
motivating consumer so the native-export question is on the record before the
JUCE port begins.

## One open question on our side (does not affect the above)

Whether the plugin is a **MIDI-in / audio-out instrument** or a
**MIDI-driven audio effect** processing an external source is undecided —
we'll settle it after the audition. Either way TERRANE's Tonality consumer
profile is **identical**: analysis-only, harmonic-event rate, numeric core,
the same four functions. So the export question above is independent of that
choice; no need to wait on us to resolve it.

## Long-range, still live

The terrain-plasticity ↔ rulesets bridge (Phase 4.6) is unchanged and worth
keeping in view: if a plugin serializes terrain state, co-versioning it with
the ruleset active when carved remains the plausible bridge.
