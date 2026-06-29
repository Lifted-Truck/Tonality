# AUDIOLOGY → Tonality: brief-17 (a pitch-space canonical orientation — for a voicing-continuous hue)

> Filed 2026-06-29 by Audiology's agent. A **research/design rider on [brief-16.md](brief-16.md)**
> (the complete signed chirality via a canonical reflection axis). Same primitive — a *continuous
> geometric orientation angle* — but lifted from pitch-class space into **pitch space**, so it
> varies with **voicing**. Exploratory (the maintainer wants to *test* a hue that responds to
> voicing); not urgent. The colour encoding stays Audiology's; the orientation is the engine ask.

## The need

Audiology's chord hue is `arg(f5)` of the **pitch classes**. The DFT folds octaves, so it is
**octave- and voicing-invariant**: every inversion / register / spacing of a chord gets the
*identical* hue. We'd like to test a hue that **varies continuously with voicing** — so inversions
and registral spread read as distinct, continuously-shifting colours (a chord gliding through
register sweeps hue smoothly, no quantization).

That requires a continuous orientation defined on the **actual pitches**, not the pc-set.

## The principled object (and why it's brief-16's cousin)

This is **Chew's spiral array** "center of effect": place each sounding pitch on a fifths **helix**
(angle = circle-of-fifths position, height = register); the (optionally register-weighted) centroid
projects to a **continuous angle** that moves as the voicing moves. That angle is the same *kind* of
object as brief-16's **canonical reflection-axis frame** — a continuous geometric orientation rather
than a discrete ± — just computed in pitch space on a register-weighted point set instead of in
pc-space. The two likely share machinery: a "canonical frame" routine parameterized by
(pc-space, unit-weighted) for chirality vs (pitch-space, register-weighted) for voicing hue.

## The ask

Expose a **pitch-space tonal orientation angle** for a voicing — input = the sounding MIDI pitches
(a `realization`), output = a continuous angle (radians) that:
- is rotation-stable in the musically-meaningful sense (transposing the whole voicing rotates it
  predictably; the *relative* result across voicings is what we map to hue),
- varies **continuously** with register / inversion / spread,
- reduces to (or stays consistent with) the pc-space `arg(f5)` orientation for a neutral
  closed-root voicing.

A spiral-array center-of-effect angle is the natural candidate; if you already have spiral-array
machinery (or want to build it alongside the brief-16 canonical frame), this rides along.

## Division of labor

| Piece | Owner |
|---|---|
| The pitch-space orientation **angle** (spiral-array / canonical-frame, register-weighted) | **Tonality** |
| Mapping angle → **hue** (OKLCH), the voiced-colour rendering + any toggle | **Audiology** |

## Status on our side

We have a working **proxy** for prototyping now — a register/bass-weighted fifth-space resultant
(`arg(Σ_notes w(register)·e^{i·cof(pc)})`, `w` decaying with height) — which already gives the
voicing-continuous behaviour (bass tints the chord; the sweep is smooth). It's a heuristic stand-in;
we'd switch to consuming the engine's principled orientation when available. No rush — this is a
"test the idea" item, gated on nothing.

— Audiology
