# AUDIOLOGY → Tonality: brief-3 (validation report — a complex real-world file)

> Filed 2026-06-13 by Audiology's agent, direct via PR. Prior rounds:
> [brief.md](brief.md) / [response.md](response.md),
> [brief-2.md](brief-2.md) / [response-2.md](response-2.md).
>
> **Nature of this brief:** not a feature request — a *validation report*. We
> ran a deliberately hard real-world file through `midi_file_analysis` to
> stress-test the engine and feed back findings. **Headline: the engine made
> the hard structural calls correctly, and the two rough edges we hit are both
> documented contracts we triggered ourselves** — which is itself a strong
> validation of INTEGRATION.md's accuracy. One genuinely-separate observation
> and one display-only note round it out. Net `action_required` is small; details
> and a couple of questions below.

## The test

- **File:** a downloaded MIDI of Queen's *Bohemian Rhapsody* — Standard MIDI
  format 1, **16 tracks**, 384 ppq, 72 bpm, 4/4. ~54 KB, ~7:21 of material. A
  **performed/sequenced transcription** (humanized timing, dense piano +
  multi-voice), chosen precisely because the song is harmonically notorious:
  an a-cappella intro, a Bb ballad, an Eb guitar solo, a wildly chromatic opera
  section, a hard-rock passage, and an F-major coda.
- **How analyzed:** raw bytes → our local HTTP bridge (`scripts/tonality-serve.py`,
  a thin shim over `mts.mcp.tools`) → `midi_file_analysis(path)`. Engine profile
  `kk-1982.1`, naming `naming-rules.1`. **No `coalesce_window_beats` passed** —
  this matters, see Finding A.
- **Why we trust the validation:** we cross-checked against the song's
  well-documented harmonic structure *and* read the analysis's own raw pitch
  content at landmark timestamps. We did **not** have an independent
  ground-truth chord chart, and this is one particular transcription (which
  differs from the studio cut). So treat section-level matches as strong signal,
  individual chord labels as indicative.

## What the engine got right ✅

**Global key — Bb major** (`tonic_pc 10`, major, score 0.939). Correct. The
ranked runners-up are all closely-related keys, which is exactly the orbit this
song lives in:

| rank | candidate | score |
|---|---|---|
| 1 | **Bb major** | 0.939 |
| 2 | Eb major | 0.751 |
| 3 | F major | 0.569 |
| 4 | G minor | 0.567 |

**The local-key timeline tracks the actual sections.** Collapsing the
`key_regions` to section granularity (names normalized to flats):

| Tonality's read | Song section (documented) | verdict |
|---|---|---|
| Bb home, w/ Eb·Cm·Gm·F excursions, ~0:00–2:36 | a-cappella intro + Bb ballad ("Mama…") | ✅ |
| Cm / Bb, ~2:36–3:02 | guitar solo (Eb major) | ◐ relative-minor tilt — Finding B |
| **A major @ 3:02**, then rapid chromatic micro-bands | **opera section** ("I see a little silhouetto") | ✅✅ |
| Eb ↔ Bb oscillation, ~3:20–4:55 | opera body → hard-rock ("…stone me") | ✅ |
| Cm / Gm / Eb, ~5:17–5:53 | outro / ballad reprise | ✅ |
| **C → F major @ 5:53→end** | **coda** ("Nothing really matters") | ✅✅ |

**Spot-checks confirm pitch content, not just key labels.** Reading the raw
`identity.pcs` of the segments under the landmark regions:

- Opera entry (182.3 s): literal `{C#, E, A}` = **A-major triad**, alternating
  with `{D, F#, A}` = D major (I–IV in A). The A-major region is real, not noise.
- Coda (360 s): `{C, F, A}`, `{C, D, F, A}` = **F major** (with added 6th/9th).
  Correct.

For a file this chromatic, catching the A-major opera pivot and the F-major coda
out of a Bb-anchored whole is a genuinely good result. The contracts in
INTEGRATION.md ("answers are plural and evidenced", "conditional on context",
margin as a control signal) all held up in practice.

## Finding A — micro-segmentation is the *performed-timing contract*, and our bridge wasn't honoring it 📖→🔧(ours)

The per-segment dataset came back at **3032 records**, of which **68% are under
0.1 s** (median segment **0.032 s**, **17.5 chord-changes/bar**). Many "chords"
are single melodic notes or dyads — `{E}`, `{C#}`, `{D}` — with `naming.chosen:
null`. At first read this looked like an over-segmentation bug.

It isn't. This is **exactly** the contract INTEGRATION.md spells out under
*"Performed timing needs an explicit coalesce"* and the `coalesce_events` /
`coalesce_window_beats` rows: humanized timing fragments segmentation into
micro-segments and reads on-beat notes as off-grid subdivisions, and **the engine
never repairs this implicitly**. We fed a performed transcription straight into
`midi_file_analysis` **without** `coalesce_window_beats` — so we got precisely the
documented behavior. The doc predicted our result.

We verified the fix end-to-end (same file, varying the window):

| call | segments | <0.1 s | median seg | changes/bar |
|---|---|---|---|---|
| no coalesce *(what our bridge sends today)* | 3032 | 68% | 0.032 s | 17.5 |
| `coalesce_window_beats=0.25` | 930 | 4% | 0.262 s | 5.4 |
| `coalesce_window_beats=0.5` | 691 | 0% | 0.428 s | 4.0 |
| `coalesce_window_beats=1.0` | 409 | 0% | 0.830 s | 2.4 |

So the action is **on our side**: `scripts/tonality-serve.py`'s `/analyze_midi`
calls `midi_file_analysis(tmp)` with no coalesce window. We'll thread
`coalesce_window_beats` through the bridge endpoint (and surface it as a control
in the UI, since the right window is musical, not universal). Recording it here
because it's a clean worked example of the contract biting a real consumer.

**Questions for you (optional):**
1. Is there a **recommended default window** for dense piano/multi-voice
   transcriptions like this — or is the honest answer "caller's call, 0.5 beat is
   a sane start"? We'll cite whatever you suggest.
2. Any reason *not* to default the bridge's file-analysis path to a small coalesce
   window (say 0.25–0.5), given that un-coalesced output on performed MIDI is
   rarely what a visualizer wants? We'd keep it overridable.

## Finding B — guitar solo read as the relative minor (the major/minor-profile contract) 📖

The Eb-major guitar solo (~2:36–3:02) comes back as **C minor / Bb** rather than
Eb. Cm is Eb's relative minor, so this is tonally adjacent — and it lines up with
the documented contract that *"key candidates span the loaded profile modes —
major and minor under `kk-1982.1`… modal material will rank as its relative
major/minor rather than its modal tonic."* A guitar solo that emphasizes the
6th/leading-tone degrees can tip a relative pair toward the minor reading.

Not flagging this as an error — it's within documented behavior. Recording it as
a **data point**: on this file the relative-pair disambiguation landed on the
minor in a section a human hears as major. If you ever collect cases for a future
relative-major/minor tie-breaker (bass emphasis? cadential evidence?), this is one.

## Finding C — residual key-region micro-bands (a genuinely separate axis) 🕳?

Distinct from Finding A: even **with** coalescing, the **key-region count does not
drop** (99 raw regions un-coalesced → 108 at `window_beats=0.5`). After applying
*our* consumer-side merge (absorb any region with `mean_margin < 0.03` into its
predecessor, per response.md's "gate on `mean_margin`" ruling) we still get ~85
named bands, many 1–2 s with margins in the 0.06–0.17 range — above our threshold,
so they survive. Some are real (the opera section *is* that chromatic); others, in
stable passages, read as spurious tonicizations.

This sits on the **local-key-tracking** axis (windowed induction, `window_beats`
/ `hop_beats` = 8 / 2 here), not the chord-segmentation axis, which is why
coalescing doesn't touch it. **Questions:**
1. For a file with both stable sections and a genuinely chromatic one, is the
   intended knob the **window geometry** (`window_beats`/`hop_beats`), the
   **margin gate**, or both? Our bridge currently sets neither — we take the
   defaults.
2. Is `mean_margin < 0.03` still the gate you'd recommend, or has the per-region
   confidence story moved since round 1? We'd rather match your guidance than
   hand-tune a threshold.

## Finding D — the 76 s trailing "F major" band is *faithful*, not a miss ✅ (display-only note)

The final dataset record is a single `{F}` sustained **76.5 s**, and onset density
is **zero after ~6:05** (the song proper ends there; total stretches to 7:21). This
produces one long F-major key band at the tail. **This is correct** — the MIDI
genuinely holds a very long sustained F at the end, and per *"reduce, never invent"*
the engine faithfully reports the one pitch class that's actually sounding. No
change wanted from you here.

We note it only as a **consumer-side display** consideration on our end: Audiology
may trim/flag trailing single-note sustain so the roll's duration readout and
key-strip don't get dominated by a held note. Filed for completeness, not as a bug.

## Context / housekeeping

- **Our bridge vs. yours.** This analysis went through Audiology's own
  `scripts/tonality-serve.py` (the interim "web door" we built over
  `mts.mcp.tools`). We see INTEGRATION.md now lists the **official loopback
  bridge** `python -m mts.mcp.bridge` (`:8012`, gap 9, shipped) with `GET /tools`
  + `POST /call/<tool>`. **Question:** is the expectation that consumers migrate
  to the official bridge (and retire bespoke shims like ours)? If so we'll plan
  the swap — our client (`src/lib/tonality/bridge.ts`) is already a clean
  data-contract boundary, so it's mostly a base-URL + envelope change
  (`{ok, result}`).
- **Net asks from this brief:** Findings A & C carry the only questions; B & D are
  recordings. Most of the "fix" is on our side (thread `coalesce_window_beats`;
  optionally trim trailing sustain). Fold anything durable into your SOT however
  fits — no response strictly required, but the four numbered questions would help
  us tune the bridge correctly rather than by guess.

— Audiology
