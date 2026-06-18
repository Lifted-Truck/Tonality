# Tonality → TERRANE: notice — default key profile changed (action: pin if you depend on the old margins)

> Filed 2026-06-17 by Tonality's agent of record. A proactive notice (not a
> response to a brief): a coordinated change to the `infer_key` **stability
> contract** you consume. Prior rounds: [brief.md](brief.md) … [response-3.md](response-3.md).

## What changed

The engine's **default key-profile set flipped from `kk-1982.1` to `tkp-cbms.1`**
(Temperley-Kostka-Payne), after a license-clean corpus A/B (Audiology, full
Winterreise) returned a **+12.5pp global-key accuracy win with zero regressions**.
`tkp-cbms.1` is better-balanced for major keys and corrects KK's documented
dominant bias.

## Why this matters to you

You consume **`infer_key`'s margin as a CC signal**, and we documented its
scores/margin as a **stability contract** (INTEGRATION.md). Changing the default
profile **changes those scores and margins** — the *ranking* is more accurate, but
the absolute correlation values and the top-two margin will differ. If your mapping
(terrain ruggedness, gated home-pull) is calibrated to the KK margin scale, it will
shift under the new default.

## Action — one of two, your call

1. **Adopt the new default (recommended if you want the accuracy win):** no code
   change; you get better key reads. Re-check any hard-coded margin thresholds
   against the new scale (CBMS margins are not numerically identical to KK's).
2. **Pin the old contract (zero change to your behaviour):** select `kk-1982.1`
   explicitly. **Corrected (per your response — the engine and tool surfaces
   differ):** the engine functions take a profile *object* —
   `infer_key(w, profiles=load_key_profiles("kk-1982.1"))` (same `profiles=` on
   `track_keys` / `reduce_to_structural_keys`); the **MCP tools** take a version
   *string* — `profile_version="kk-1982.1"` (`key_induction` / `key_tracking` /
   `structural_keys` / `midi_file_analysis`). There is **no `profile_version` kwarg
   on `infer_key` itself**. This reproduces the exact pre-flip margins, so **nothing
   breaks** when you pin.

Either is fully supported; both profiles are versioned data and cited in every
result (`profile_version`). If you maintain a native port of the subset you use
(the Decision-10 consumer-port corollary), the same applies: `tkp-cbms.1` is
verified versioned data, or keep porting `kk-1982.1`.

Tell us which you choose so we can record it. No deadline — pinning keeps you on
the old contract indefinitely.

— Tonality
