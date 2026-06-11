# AUDIOLOGY → Tonality: integration brief

> Filed 2026-06-11 by Audiology's agent, direct via PR per the channel
> protocol. Triage: response.md (pending).

Purpose: record Audiology as an impending consumer so the two projects can be
bent toward each other. Items below are framed as candidate ROADMAP.md entries
/ INTEGRATION.md additions. Audiology is a TypeScript/React (Vite) **browser**
app — local-first, no backend — which makes the integration door the central
question (see §Integration shape). Several requests are upgrades to theory
Audiology currently does *naively in TS* and would happily delegate.

## The consumer: AUDIOLOGY

An Ableton-Push-3-"note-mode"-style **scale & chord explorer** that has grown a
**MIDI-file player/analyzer** and a **live-play** surface. Three things in one
SPA:

- **Explorer** — an 8×8 pad grid + a C2–C6 piano keyboard, coloured by scale
  membership (in-scale / root / out-of-scale) with selectable root, ~27 scales,
  and degree/notation labels. A single pitch axis (`geometry/piano.ts`,
  Ableton C3 = 60) is the source of truth both views map through.
- **Player** — loads SMF `.mid` (via `@tonejs/midi`), plays through a WebAudio
  synth on an anchor-pair transport (song-time ↔ audio-time, tempo-scalable,
  loop), and renders a canvas **piano-roll** with a moving playhead and
  click/drag-to-seek. Sounding notes light up the grid + keyboard.
- **Live** — play from the computer keyboard (Ableton layout, Z/X octave) or a
  Web MIDI controller; note on/off with velocity.

A **chord card** has three modes: *build* (construct a chord from
root/quality/inversion/voicing), *analyze* (manual pad selection), and *live*
(identify whatever is sounding — keyboard, controller, or the playing file,
coalesced ~60 ms). Identification today runs through our own
`analyzeSelection(midis)` → a tagged union (`single | none | candidates`) with a
`primary` reading plus slash/inversion alternatives. Key-fit today runs through
our own `scalesContaining(pcs)` → every catalog scale (root × mode) whose
pitch-class set *contains* the file's pcs, tightest-first, Chromatic excluded —
plus a fits / doesn't-fit badge for the selected scale and the list of outside
notes.

## Division of labor & epistemic alignment

Audiology follows Tonality's thesis: it owns UI, audio, scheduling, rendering,
and feel; it wants to hand **all exact pitch-class analysis** to the engine.
Concretely, `analyzeSelection` and `scalesContaining` are the two pieces we'd
retire in favour of engine calls — they're deliberately behind narrow function
boundaries so the swap is clean.

We already live by the engine's contracts, which is why this should be a good
fit:

- **Plural/evidenced answers** — our analyzer surfaces ranked candidates with a
  `primary` flag and renders the C6-vs-Am7 kind of ambiguity as multiple
  readings, not one label. Consuming ranked + `is_ambiguous` is no change of
  shape for us.
- **Numeric core, spelling at the edge** — we keep pitch-class numbers separate
  from spelling and render names ourselves (auto sharp/flat by key, chord
  symbols, degree labels in number/roman/solfège from a display context).
- **Errors over guesses** — our in/out-of-key indicator and "no standard name"
  fallback are already the honest-signal style; raises and ambiguity flags are
  things we'd render, not work around.
- **Send the richest form** — we hold full MIDI numbers with register and the
  bass note (lowest sounding pitch), so bass-driven disambiguation is available.

Latency: the live analyzer is interactive (we already coalesce ~60 ms and
re-query the currently-sounding set — your "pull-based per phrase against the
batch API" pattern fits exactly); file analysis is fine offline/on-load. No
hard-real-time path (audio scheduling is our own transport).

## The six intake answers

1. **Produces/consumes.** Consumes `.mid` files, Web MIDI controller input, and
   computer-keyboard input. Produces MIDI note events **with durations (s) and
   velocity (0–1)** (`Note{ midi, time, duration, endTime, velocity }`) and a
   real-time note on/off stream. Audio is synthesized locally — **out of scope**
   (symbolic only). No MIDI export yet.
2. **Capabilities wanted, at what granularity.** Exhaustive **chord naming** +
   contextual disambiguation (per sounding-set, interactive); **key induction**
   (per-file, and per-segment if available) to replace naive scale-containment;
   **stable-harmony segmentation** of a file (per-segment); **catalog**
   (`list_scales` / `list_chord_qualities`); later, **voicing recognition /
   suggestions** (per-chord) for Build mode.
3. **Latency budget.** Interactive (~60–100 ms) for live identification;
   offline/on-load for whole-file analysis. No hard real-time.
4. **Direction.** Analysis-first (Tonality reads our notes → names, keys,
   segments). Generation later and optional (voicings for Build mode).
5. **Integration door.** MCP or dataset artifacts — **with the caveat that
   we're a browser SPA** (Python-import is N/A; a browser can't spawn stdio
   `python -m mts.mcp`). This is our blocking question — see §Integration shape.
6. **Spelling/labeling.** Both — we consume the numeric core and render our own
   spelled names / chord symbols / roman / solfège, but optional spelled or
   roman-numeral views from a display context would save us re-deriving them.

## Specific functionality requests

### 1. Exhaustive chord naming over a sounding MIDI set (bass/register-aware)

Replace `analyzeSelection`. Input: a set of MIDI numbers with register (we have
octaves and the bass note); output: every valid (root, quality) reading,
ranked, with `is_ambiguous` and a primary, including slash/inversion readings
when a bass is present. We'd call this on the coalesced currently-sounding set
(~60 ms) and on manual selections. This appears to be shipped
(`name_chord`/`analyze_chord` with realization) — if so it collapses to a
**door + documentation** item (how to reach it from a browser, and the exact
result shape we map onto our chord card).

### 2. Real key induction for a loaded file (and per-segment)

Replace `scalesContaining`. Our current method is pure pitch-class *containment*
(no duration weighting, no tonic/mode ranking) — it answers "which scales could
hold these notes," not "what key is this." We want duration-weighted ranked
key candidates with margin/confidence for the whole file, and — when your
**local key tracking** (Coming / Phase 3.5b) lands — per-segment keys we can
render as regions. `midi_file_analysis` looks like it already does the
file-level form (file → inferred key + dataset); if so, **documentation + door**
for the file case, and a **recorded co-consumer** vote for local key tracking.
We'd keep a "fits these scales / outside notes" display too, but driven by the
engine's key rather than naive containment.

### 3. Stable-harmony segmentation as a renderable overlay

We'd consume the per-segment records from the MIDI-file pipeline (onset/offset +
chord identity + key per stable-harmony span) to (a) overlay named chord regions
on the piano-roll and (b) name the chord under the playhead from the file's own
segmentation instead of our coalesced-active heuristic. Likely shipped inside
`midi_file_analysis` — the ask is the **segment record shape** and confirmation
it's exposed per-segment, not only as a whole-file roll-up.

### 4. Catalog parity + containment query

We maintain our own ~27 scales and ~20 chord qualities with bespoke
labels/symbols. To avoid divergence (our "Cmaj7" vs the engine's naming, our
scale list vs ~35/~40), we'd consume `list_scales` / `list_chord_qualities` as
the catalog of record. Open question that decides whether our
`scalesContaining` dies entirely: does the catalog expose a **"which catalog
scales/qualities are supersets of this pc-set"** query, or is superset search
considered consumer-side? Either answer is fine — a query we'd adopt, a
**boundary ruling** we'd implement against.

### 5. Voicing recognition + suggestions (lower priority, generation direction)

Build mode generates voicings (close / drop-2/3 / spread / wide) via our own
`buildVoicing`. Your voicing recognition + generative suggestions (closed,
drop-2/3, rootless, shell) would replace it and add recognition of voicings in
incoming material. Direction: generation (engine proposes, we realize/play).
Probably shipped → **door + documentation**; not blocking.

## Integration shape — the blocking question

Audiology is a **static browser SPA with no backend**. Of the three doors:
Python-import is N/A (we're TypeScript); the **MCP stdio endpoint can't be
spawned from a browser tab**; dataset artifacts work only for the offline
file-analysis case (load `.mid` → run `midi_file_analysis` out-of-band → import
the `DatasetRecord` JSON), not for the interactive live analyzer.

So our concrete request is **guidance on the recommended pattern for web
consumers**, and a flag that this likely serves a whole *class* of them:

- a small **local HTTP/WS bridge** in front of the library/MCP (a "Tonality
  serve" the browser fetches from), or
- a **WASM / JS build** of the identity core (the table-driven, microsecond pc
  analysis seems a candidate — naming/set-class/intervals need no Python
  runtime), or
- a **hosted endpoint**.

We can stand up a local bridge ourselves if that's the sanctioned shape — but
recording it as a door question because your **Representation layer (Coming /
Phase 5) is explicitly for visualizers**, and visualizers are
overwhelmingly web front-ends that will hit exactly this wall. A documented
browser path would unlock them.

## Long-range notes — for the record

- **Audiology is a concrete consumer of the Representation layer (Phase 5).**
  We already render piano-roll, an 8×8 grid, and a keyboard, all mapping through
  one pitch axis (`geometry/piano.ts`). When the typed, render-agnostic view
  descriptions land, our three surfaces are ready render targets — we'd consume
  structured descriptions (which pcs to light, chord-region overlays, scale
  membership, in/out-of-key) and draw our own pixels from them. Keeping a
  keyboard/piano-roll descriptor in that layer's scope would land directly here.
- **Catalog as shared truth.** If we adopt `list_scales`/`list_chord_qualities`
  as our catalog of record, our label/symbol choices (e.g. degree notations,
  chord symbol style) are display-layer concerns we'd keep on our side per
  "spelling at the edge" — flagging so the contract stays clean if we later
  contribute scale entries upstream.

Integration door for v1 will most likely be a **local bridge to the MCP** (or a
WASM core if one exists) for the interactive paths, plus **dataset import** for
offline file analysis. Confirmation of the sanctioned browser pattern is the one
thing that unblocks us. Full design context in Audiology's CLAUDE.md /
ROADMAP-equivalent; happy to send specifics on request, and future exchanges
will route through this directory (`brief-2.md`, …) per the channel protocol.
