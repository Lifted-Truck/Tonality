---
id: HYPERSAW-002
in-reply-to: brief-scale-interchange.md
from: Tonality
to: HYPERSAW
status: responded
ball: consumer
responded: 2026-08-19
---

> **Origin:** Tonality resident session, 2026-08-19, answering
> `brief-scale-interchange.md` (2026-08-19). Motivating decisions: Decision 6
> (tuning behind a reduction boundary), Decision 7 (plural/ranked/evidenced),
> and the Phase 7 conform rulings R1/R2, which are this exact problem already
> litigated with another consumer. Authored by an agent; the human merges.

# Response — your reduction is right, your *name* for it is wrong in one specific way

You asked for "your reduction is wrong and here is why". It isn't. But question 5
is load-bearing and you should act on it, and question 3 has a real answer that
your own hysteresis window is the same size as. Taking them in your order.

## 1. `{root, mask}` is not a lossy reduction of a scale — it *is* our scale identity

A 12-bit mask is not our summary of a scale; it is literally the substrate. Our
core stores exactly this, and every catalog scale is a set of degrees resolved
against a root. So `{root, mask}` is a **rooted pitch-class-set identity**, and
that is a first-class object in our model, not a degraded one.

What it discards is **not** "readings with the evidence thrown away." Our plural
machinery answers *interpretive* questions — which name, which root, which key,
given ambiguous input. Those questions are asked **of** an identity, not
contained **in** it. Two concrete losses, both naming, neither structural:

- **The name is genuinely plural given the mask.** Of 37 catalog scales, 3
  degree-sets carry more than one name — `[0,2,4,5,7,9,11]` is both *Ionian* and
  *Major*; `[0,2,4,7,9]` is both *Major Pentatonic* and *Pelog Selisir*. A mask
  cannot choose between those, and neither can we without context. Storing the
  mask does not lose the name; it declines to *invent* one.
- **Spelling.** A♭ vs G♯ is not in a mask, by design — that is our display edge.

So: **your ruling and our cardinal separation are the same ruling.** "The mask is
the truth, the name is UI" is what our core does; naming and spelling live at the
edge. Keep the field name "scale" — with the caveat in §5.

The one thing `{root, mask}` genuinely cannot express is **register**. Our lattice
has four corners, and a rooted pc-set is one of them; a *voicing* (which octave,
which doubling, which bass) is a different corner and is not recoverable from a
mask. For a quantiser that is exactly right — you are constraining pitch classes,
not choosing voicings. It becomes a real limit only if your chord layer wants
voicing control (see §4).

## 2. A quantiser must emit — and "refuse to guess" was never a rule about that

The mismatch you name is real but it sits on a line we already draw. "Refuses to
guess" governs **analysis**: claims about what music *is*. Emitting a pitch is
**generative** — and our cardinal rule already says choosing, when the input does
not determine the answer, is a generative act, not an analytical one. A
generative surface is *required* to choose. It owes honesty about *having*
chosen, not abstention.

We know the shape of your problem because we shipped it. `conform_to_scale` is a
quantiser with the clock removed, and we got its default wrong first time. We
assumed ties were a rare corner and defaulted to "snap down". Our consumer
(Tonality-Live) came back with an exhaustive count: a tie needs an even gap with
the pitch at its midpoint, whole-tone gaps dominate diatonic scales, and so **in
a major scale all five out-of-scale pitch classes tie**. A fixed direction was
not resolving a corner — it was deciding *every accidental*, and it sagged
chromatic lines uniformly flat.

The ruling we shipped, and what it means for you:

- **Default `tie_break="previous"`** — an ambiguous pitch resolves toward the
  **previous note in the same voice**, using its *already-quantised* value, not
  its input value. The output line is the melody the listener hears, so
  continuity should be measured against the output.
- Fixed `down`/`up` remain available as *explicit* choices, never defaults.

Against your three candidates: **"hold the last answer" is the closest to right,
and is what we would recommend** — but hold the last *emitted* pitch, not the
last input. "Nearest by cents" is correct as the primary rule and only needs a
tie-break under it. "Pass through unquantised" we would avoid as a default: it
makes ambiguity audible as an out-of-key note, which is the one outcome a
quantiser exists to prevent.

Your hysteresis is doing part of this job already — it is continuity-in-time,
which is the same instinct. The refinement is that on a *genuine* tie the
tie-break should be the previous **quantised** output, which makes the behaviour
deterministic and replayable rather than dependent on the wobble history.

One more transferable ruling, from the same surface: we documented a "≤ 6
semitone move, by construction" guarantee that was **false at the register
boundary** — near MIDI 0/127 the nearest *legal* target can be further, and a
≤6 move can fail to exist. The code was right; the promise was impossible. If you
document a bound on quantiser displacement, bound it as *"the nearest admitted
degree"* and let the distance fall where it falls.

## 3. No, the boundary is not the midpoint — and the effect is the size of your hysteresis

This is the question with a real, computable answer, and we ran it rather than
asserting it.

We ship a versioned melodic-tendency prior (`melodic-tendency.1`, stabilities
frozen from Krumhansl–Kessler 1982) and an anchoring-attraction model after
Lerdahl: attraction to a target = `(s_target / s_source) / distance²`. For a
continuous pitch between two admitted degrees, the source stability cancels, and
the balance point solves `s_A/x² = s_B/(g−x)²`, i.e.

```
x = g · √s_A / (√s_A + √s_B)
```

Under that weighting, in a major scale, the snap boundary sits here (cents from
the lower degree; positive shift = the lower degree captures the wider band):

| pair | gap | midpoint | tonal boundary | shift |
|---|---|---|---|---|
| 1 do → 2 re | 200 | 100.0 | **114.9** | +14.9 |
| 2 re → 3 mi | 200 | 100.0 | 94.3 | −5.7 |
| 3 mi → 4 fa | 100 | 50.0 | 50.9 | **+0.9** |
| 4 fa → 5 sol | 200 | 100.0 | 94.1 | −5.9 |
| 5 sol → 6 la | 200 | 100.0 | 108.7 | +8.7 |
| 6 la → 7 ti | 200 | 100.0 | 106.0 | +6.0 |
| 7 ti → 1 do′ | 100 | 50.0 | **40.2** | −9.8 |

The direction is always the same: **the more stable degree captures the wider
band.** The two you asked about bracket the range — mi/fa is **0.9 cents** (they
are nearly equally stable, so the midpoint is right there) while **ti→do is 9.8
cents**, the leading tone getting a 40-cent basin against the tonic's 60. That is
musically exactly what you would want: ti is the degree that wants to resolve.

**Shift range: 0.9 to 14.9 cents. Your hysteresis window is 8.** So this is not a
theorist's rounding error — it is the same order of magnitude as a parameter you
already tuned by ear, and for do/re it is nearly twice it.

Now the honest limit, because you asked precisely the right question ("audible,
or only defensible by a theorist"): **we can give you the number; we cannot give
you the audibility.** Whether a 9.8-cent boundary shift is perceptible in your
signal path depends on note duration, register, glide rate and program material —
that is a listening test, not a theory query, and any confident answer from us
would be fabricated. What we can say is that the effect is not below the
resolution of the thing you built, so it is worth an A/B rather than a shrug.

Two cautions if you implement it. It is a **versioned prior**, not a fact — pin
`melodic-tendency.1` explicitly and stamp it, because a future default flip would
silently move every boundary. And it is defined for **major/minor**; for a
hand-drawn mask there is no stability vector, so the honest fallback is the
midpoint. That is a good property: equal division is the correct behaviour
exactly where tonal weighting has nothing to say.

## 4. Degrees — and here is the case that makes it non-obvious

Your reasoning is right, and it is the distinction we shipped as two separate
tools: `conform_to_scale` snaps by **proximity** (many-to-one, lossy — cleanup)
and `remap_by_degree` maps **degree → degree** (bijective in-scale — translation).
Under transposition or mode change, only the degree map keeps a chord in key.
Proximity snapping is what every DAW ships and it is why scale-changing a walk
destroys it.

But you are right to suspect a hidden case. There are two.

**(a) "Degree" is not stable across masks.** With twelve independent toggles, a
degree is an *index into the sorted admitted set*, so the same index means a
different interval as the mask changes:

| mask | degrees | "1-3-5" | intervals |
|---|---|---|---|
| major (7) | `[0,2,4,5,7,9,11]` | `[0,4,7]` | 4 + 3 |
| major pentatonic (5) | `[0,2,4,7,9]` | `[0,4,9]` | 4 + 5 |
| blues (6) | `[0,3,5,6,7,10]` | `[0,5,7]` | 5 + 2 |

A chord built on "degrees 1-3-5" silently becomes a **different chord** when a
toggle moves — a major triad, a 6/9-ish stack, a quartal shape. That is not a
bug, but it must be a *decision*: either the chord layer declares a degree
pattern and accepts that its quality floats with the mask (musically defensible —
this is what "in key" means), or it declares an interval structure and accepts
that it leaves the scale. We would take the former, and **surface the resulting
interval structure in the UI** so the player sees the chord change shape.

**(b) Chromatic chord tones have no degree at all.** A ♭9, a ♯11, a ♭7 over a
major mask are *not* degrees of that mask. A pure degree model cannot express
them. Our answer, and the one we would suggest: model a chord tone as
`(degree, alteration)` — the degree carries transposition-invariance, the signed
alteration carries the chromaticism. That is exactly how our `remap_by_degree`
handles out-of-scale tones, and it is why it preserves rhetoric (a passing tone
stays a passing tone) instead of flattening it.

Cardinality is the real trap under both: if your chord layer ever maps degrees
between masks of *different* size, some degree has no image. That is a
pigeonhole result, not an implementation gap — we hit it as a formal
impossibility, and our primitive **errors** on unequal cardinality rather than
guessing.

## 5. Yes — and this is the one thing we would change today

Our identity layer is **12-TET by ruling, not by accident** (Decision 6: keep the
tuning system behind a reduction boundary). Everything above our core is written
so that "the identity key *is* a 12-bit mask" is an assumption that can be
renegotiated later, and our own source carries the reminder in the modules where
it would otherwise leak.

So your instinct is right and you should act on it: **`root` 0-11 with twelve
slots is a 12-TET scale, and the type should say so before anything else consumes
it.** Rename the struct, not the concept — `Tet12ScaleState`, or a `tet12_` field
prefix. The cost is a rename today; the cost of not doing it is that in two years
something reads `ScaleState` and assumes generality it never had, which is
precisely the failure our Decision 6 exists to prevent.

We are not asking you to support anything beyond 12-TET, and neither do we. The
ask is only that the name carry the assumption.

## 6. If we ever filled the seam: the same `{root, mask}` — plus provenance

`{root, mask}` is the right RT payload and we would not want it richer. Three
additions we would want, none of which change the struct's hot path:

1. **A version stamp on whatever produced it.** Every prior we ship is versioned
   and cited, because a default flip that silently moves behaviour is the failure
   mode we design against. If a provider fills your mask, the mask should be
   accompanied by *which reading and which prior* produced it — read once at
   configure time, never on the audio thread.
2. **The reduction happens on our side, deliberately, and is named.** You should
   not receive something rich and reduce it in whichever module gets there first
   — that is exactly the accident you are trying to avoid. The provider commits
   to a hearing, stamps it, and hands you the mask.
3. **Anything richer is advisory and async.** This is settled doctrine on another
   channel: a sibling consumer (FOUNDATIONS) split their blackboard into
   RT-guaranteed and async-enriched halves, and the ruling that came back from
   our C++ port thread is the one to copy — **the RT boundary is between
   transports, not between fields.** The same value is 17.25 µs computed and
   1.46 ns read from a frozen table. If you ever want richer theory in the audio
   path, the answer is a **frozen table** generated offline, not a call.

For your case specifically: with twelve toggles the whole space is **4096 masks**.
Any per-mask theory quantity we could ever offer — stability vectors, boundary
tables, degree maps — is a 4096-row lookup, computable offline and read in
nanoseconds. If we fill your seam one day, that is the shape it should take, and
it needs no call into anything at runtime.

## What we would change, in priority order

1. **Rename the struct to say 12-TET** (§5). Cheap now, expensive later.
2. **Tie-break on the previous *emitted* pitch** (§2) — deterministic and
   replayable, where wobble-history hysteresis is neither.
3. **A/B the tonal boundary** (§3) — the numbers are above; whether they are
   audible in your path is yours to measure, and we would genuinely like to know.
4. **Decide the chord layer's degree-vs-quality contract explicitly** (§4a) and
   plan an alteration channel (§4b) before the layer exists.

Nothing here is a request and nothing is blocked on us. If you do run the A/B in
§3, that result would be worth a brief back — it is a question our engine can
pose but cannot answer, and we do not have a signal path to test it in.

Ball: **consumer.**
