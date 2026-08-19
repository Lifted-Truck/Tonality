---
authoring-project: HYPERSAW (github.com/Lifted-Truck/HYPERSAW)
filed: 2026-08-19
motivating-decisions: HYPERSAW ruling "the mask is the truth, the name is UI"; the global scale surface (params 116-128, shipped 2026-08-19); the roadmapped scale-quantised chord layer
id: HYPERSAW-002
status: filed
ball: provider
respond-by: 2026-09-19
---

# HYPERSAW → Tonality — is `{root, 12-bit mask}` an honest interchange?

**No integration is wanted yet.** HYPERSAW has just shipped a global scale surface and a
scale-quantised pitch path, and has deliberately left a **seam** where a provider could sit.
This brief asks whether the shape we chose is one Tonality could ever fill without lying, and
what we would be throwing away if it did. Answer at your convenience; nothing of ours is
blocked.

## What we built, so the questions are concrete

A quantiser in the audio path (`glide_core.h`) that snaps pitch to a scale, fed by a global
surface of **thirteen CLAP parameters**: a root (0-11) and **twelve independent degree
toggles**. The mask, not a scale name, is what every consumer stores and transmits. Our
standing ruling:

> The mask is the truth, the name is UI. Consumers store and transmit `{root, mask}` only,
> never a scale ID.

That was chosen so the core carries **no scale table** — adding a named scale is a UI edit with
no core change and no parity surface — and so a hand-drawn set is first-class rather than a
degraded mode. The named-scale dropdown (18 names, borrowed from our own bench) lives in the
GUI, writes the toggles, and reads *custom* the moment one is edited by hand.

The seam is a single struct the consumers read:

```cpp
struct ScaleState { double root; int mask[12]; } scale;
```

Today thirteen parameters fill it. A provider filling it instead would change nothing
downstream — which is the point, and why we are asking before there is anything to unpick.

## The questions, in the order they cost us something

**1. Is a 12-bit mask an honest reduction, or a lossy one we should stop calling a scale?**
Your README says the engine *"returns every reading the theory admits (ranked, with
evidence)"*. A mask is exactly one reading with the evidence discarded. For a real-time
consumer that may be all we can use — but we would rather know **what we are destroying** than
discover later that we named it wrong. If `{root, mask}` is not a thing your model would call a
scale, we would rather rename our field than imply agreement we do not have.

**2. A real-time consumer cannot refuse to guess, and yours is designed to.**
That is the sharpest mismatch we can see. Tonality *"refuses to guess when it doesn't know"*;
a quantiser must emit a pitch on every grid tick — for us every 16 samples — and has no
"unknown" to return. So: when the theory is genuinely ambiguous, what is the **right degraded
behaviour** for a consumer that must answer? Nearest by cents, hold the last answer, or pass
through unquantised? We currently do nearest-by-cents with hysteresis, chosen for
implementability rather than for being right.

**3. Where does a boundary actually sit?**
We snap at the midpoint between admitted degrees, with 8 cents of hysteresis so a wobbling
pitch does not chatter across a step. Equal division is the naive answer. Is there a tonal
weighting under which the boundary between, say, degrees 3 and 4 of a major scale is *not* the
midpoint — and if so, is that a difference a listener could hear, or a difference only a
theorist can defend?

**4. Chord tones: scale degrees or semitone intervals?**
We have a scale-quantised chord layer roadmapped, where each chord note is a full copy of the
oscillator. Building chords from **degrees** keeps them in key under transposition; building
from **semitones** does not. That looks obvious from here, which usually means we are missing
the case that makes it not obvious. Is there one?

**5. Does the interchange assume 12-TET into a corner?**
`root` is 0-11 and the mask has twelve slots. If Tonality's model admits non-12-TET, then our
"scale" is really "12-TET scale" and should say so in its name before anything else consumes
it.

**6. If you ever filled our seam, what would you want to fill it WITH?**
The same `{root, mask}`, or something richer that we would reduce at the boundary? We would
rather design the reduction deliberately, on your terms, than have it happen by accident in
whichever of our modules gets there first.

## What we are not asking for

Code, a dependency, a schedule, or a commitment to integrate. The four consumers we can already
see — bend quantisation, the note-pitch lane, the chord layer, any arp — are all served by the
current surface. This is a design review of a boundary we have deliberately left open, and the
most useful possible answer is *"your reduction is wrong and here is why"*.

— HYPERSAW
