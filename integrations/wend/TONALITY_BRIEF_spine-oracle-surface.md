# BRIEF — spine decoding jurisdiction + oracle surface for Wend harmonize mode

**Destination:** Tonality repo, `integrations/wend/` (asks 1–2) — ask 3
concerns port prioritization and may be cross-filed or referenced from
`integrations/tonality-core/` per house convention
**From:** Wend-side concept sessions, 2026-07-13
**ball:** tonality
**Context docs:** companion `WEND_BRIEF_harmonize.md`; Wend README oracle
seam table; tonality-core README parity contract.

---

## Context, briefly

Wend is adding a `harmonize` mode: MIDI file in → the oracle's hearing of it
("HarmonicSpine": per-segment ranked keys + chords with margins, smoothed by
a Viterbi-style DP decode) → complementary parts realized against that spine
→ harmony MIDI out. The spine becomes an on-disk, versioned artifact and the
seam for a future live device. Wend can build this today against the existing
seam with a defined stopgap; nothing below blocks it. Three asks, in
descending order of judgment required.

## Ask 1 — Jurisdiction: is spine decoding analysis or policy?

The decode selects a path through ranked hearings: emission costs from
windowed key induction + chord naming (unambiguously oracle territory);
transition costs penalize interpretation change via circle-of-fifths / VL
distance, scaled by a smoothing parameter λ; single deterministic DP pass.

The case that this is **upstream analysis**: `structural_keys` already
crosses from "score the window" to "commit to areas" — it segments. The DP
decode is arguably a generalized, principled `structural_keys` (explicit
transition model, tunable inertia, chord-level as well as key-level), and
the walk-validation finding that heard modulations lag / land a fifth flat
is exactly the kind of hearing-commitment problem such a decoder addresses.
If claimed: λ becomes an oracle argument with a versioned prior (the
kk-1982.1 pattern), the decode becomes portable spec for tonality-core, and
every downstream consumer (Wend, Audiology, the live device) inherits one
canonical hearing.

The case that this is **consumer policy**: choosing which hearing to commit
to is a decision, not a measurement; different consumers may legitimately
want different inertia (a harmonizer wants commitment; an analysis display
may want the raw flicker); and "reduce, never invent" arguably ends at
ranked candidates.

**Request:** claim or decline. Wend implements behind a `SpineDecoder`
interface either way; a claim later is a delegate swap, not a rewrite. If
claimed, please indicate target phase so Wend can plan the swap. Decline is
a complete answer; no shim will be built around it.

## Ask 2 — Surface confirmation: per-window chord naming

Does mts expose chord naming over a window's sounding pitch-class content in
a form suitable for per-cell emission costs (ranked candidates with
confidences), or is windowed hearing key-level only (`structural_keys`)?

If this is a gap: please register it (Wend as named consumer). Wend's
stopgap is a key-level decode with diatonic chord derivation per segment,
downgrade recorded in the spine's oracle badge — functional but strictly
worse for chromatic input.

## Ask 3 — Port demand signal (for Phase 8 / tonality-core prioritization)

The harmonize mode's complete oracle query surface, enumerated:

1. Windowed key estimate — ranked candidates + **margin** (kk-1982.1 pin
   assumed for margin-scale commensurability across FallbackOracle / mts /
   tonality-core)
2. Chord naming over pitch-class content — ranked, with pitch content
   (subject to Ask 2)
3. Voice-leading cost/map between voicings

This is also the *exact* slice set a native live harmonizer needs from
tonality-core. Requested action: record harmonize mode (and its planned live
successor) as a named external consumer of these slices in Phase 8
prioritization. No timeline pressure implied — the live device's
quantization ceiling is explicitly gated on measured slice availability, and
the Python path is the plan of record until then.

Additionally, FYI rather than ask: Wend will export deterministic spine
fixtures (`fixtures/spine/*.json` + producer PIN) from day one, following
the tonality-core golden-anchoring pattern, so any future native spine
deriver has its parity target ready-made.

## Response protocol

Per cross-project convention: respond in-place with answers to Asks 1–3 and
flip `ball:` back to wend. Ask 1 shapes Wend's internal structure but does
not gate its start; Ask 2's answer selects stopgap vs. native path before
Wend's H0 gate closes if possible.
