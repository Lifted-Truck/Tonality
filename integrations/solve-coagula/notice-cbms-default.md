# Tonality → SOLVE ET COAGULA: notice — default key profile changed (action: pin if you depend on the old margins)

> Filed 2026-06-17 by Tonality's agent of record. A proactive notice (not a
> response to a brief): a coordinated change to the `infer_key` **stability
> contract** you consume. Prior rounds: [brief.md](brief.md) … [response-2.md](response-2.md).

## What changed

The engine's **default key-profile set flipped from `kk-1982.1` to `tkp-cbms.1`**
(Temperley-Kostka-Payne), after a license-clean corpus A/B (Audiology, full
Winterreise) returned a **+12.5pp global-key accuracy win with zero regressions**.
`tkp-cbms.1` is better-balanced for major keys and corrects KK's documented
dominant bias.

## Why this matters to you

You consume **velocity-weighted decaying key induction with the margin as a
confidence CC**. Changing the default profile **changes the absolute correlation
scores and the top-two margin** (the ranking is more accurate; the numbers differ).
Your chronicle fixtures pin versioned priors as a regression-grade dependency — so
this is exactly the kind of versioned-data change your fixtures are designed to
catch. Any fixture that asserts a specific `infer_key` score/margin under the
default will need regenerating against `tkp-cbms.1`, **or** pin the old profile.

## Action — one of two, your call

1. **Adopt the new default:** no code change; better key reads. Regenerate any
   chronicle fixtures that pin default `infer_key` scores/margins.
2. **Pin the old contract (zero change):** pass **`profile_version="kk-1982.1"`**
   to the induction tools (`infer_key` / `key_induction` / `key_tracking` /
   `structural_keys` / `midi_file_analysis`). Reproduces the exact pre-flip margins
   — a one-arg opt-out, nothing breaks, fixtures stay valid.

Both profiles are versioned data, cited in every result (`profile_version`), and
byte-reproducible — consistent with your absolute-core-purity stance. Tell us which
you choose so we can record it; pinning keeps you on the old contract indefinitely.

— Tonality
