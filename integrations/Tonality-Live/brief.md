---
id: tonality-live-001
from: Tonality-Live
to: Tonality
status: filed
ball: provider
filed: 2026-07-13
respond-by: 2026-07-27
---

# Brief: theory-driven note transforms for the /transform seam

## Need

Tonality-Live is an Ableton Live extension that reads a MIDI clip's notes,
sends them to the Tonality engine via a local bridge (`bridge/server.py`
wrapping `mts.mcp.tools.midi_file_analysis`), and writes altered notes back.

Analysis ships end-to-end. The next "alter" features — **fit-to-key**,
**scale-conform**, and **revoice / voice-leading** — are deliberately NOT
implemented in the consumer: per INTEGRATIONS rule 3 the harmonic
combinatorics stay in the engine. The bridge already exposes a `/transform`
endpoint that returns `501 Not Implemented` as the documented seam
(`bridge/README.md#the-transform-seam`). It stays a visible 501 (rule 2,
degraded-not-silent) until `mts` ships transform functions to call.

Today `mts` analyzes and has only a couple of generative hooks
(`suggest_voicings`, `apply_groove`); there is no note-in → note-out
transform surface. That gap is what blocks Tonality-Live ROADMAP Q-003.

## Proposed interface delta

Transform functions in `mts` that take a note sequence + parameters and
return a new note sequence, callable from the bridge without the consumer
knowing any theory. Proposed shapes (provider owns the final design):

1. `fit_to_key(sequence, key) -> sequence` — snap out-of-key pitches to the
   nearest in-key pitch (tie-break rule the engine's call).
2. `scale_conform(sequence, scale, root) -> sequence` — conform to an
   arbitrary scale/mode, not just major/minor.
3. `revoice(sequence, options) -> sequence` — voice-leading-aware
   re-voicing (minimize total motion; keep or drop the bass — engine's call).

Boundary stays canonical (rule 8): pitch-class / MIDI integers in and out,
same `NoteDescription` shape (`{pitch, startTime, duration, velocity?}`,
quarter-note beats) that `/analyze` already consumes. Spelling/labels remain
display-layer in the consumer.

## Contract tests offered (executably: "what I rely on")

Tonality-Live proposes these to be reviewed and, if accepted, committed into
`mts` CI so a future change that breaks the consumer fails the provider's
build:

- `fit_to_key` is idempotent on already-in-key input and never moves a pitch
  by more than 6 semitones.
- `scale_conform` output contains only scale-member pitch-classes.
- Every transform preserves note count, `startTime`, and `duration` (pitch is
  the only field it may change) unless an option explicitly says otherwise.
- Output pitches stay in MIDI 0–127.

## Not asking for

- A new transport or wire format — the existing bridge import path is fine.
- Real-time / per-sample processing — these run at edit time, offline.

## Consumer state while this is open

Tonality-Live proceeds unblocked: `/transform` stays a visible 501, transpose
(pure arithmetic) ships locally, and Q-003 is marked `blocked (upstream)`
pending this brief's response. No consumer-side reimplementation of the
theory will happen (that would violate the core invariant).
