# NOTICE — Tonality → TERRANE: `cadences` corrections in minor keys (RE-2, 2026-07-03)

> From the rigor & efficiency review (ROADMAP "Standing review — rigor &
> efficiency", RE-2). You are the named external consumer of cadence detection
> (gap 7), so two minor-mode corrections are on record. Major-key behavior is
> unchanged (conformance golden untouched by these).

## What changed

1. **Deceptive cadences are now detected in minor.** Detection keyed on the
   *major* submediant (pc 9, arrival role `tonic`), which minor never
   satisfies (its submediant is pc 8, role `predominant`) — so V→VI in minor
   was silently invisible. It now keys on the mode's submediant *degree*:
   expect **new** `deceptive` events in minor progressions (evidence cites
   the arrival, e.g. "submediant (bVI)").

2. **bVII→i is no longer labeled an authentic cadence.** The subtonic carries
   the dominant *role* in the minor vocabulary, so G→Am in A minor was
   emitted as `authentic` with fabricated "leading-tone resolving to tonic"
   evidence (bVII contains no leading tone). Authentic now requires a true
   dominant degree — V (pc 7) or the leading tone (pc 11). The backdoor/
   subtonic shape emits **no cadence event**; the chords stay honestly
   annotated (`bVII`, role `dominant`). If you relied on that label for
   bVII→i, it was wrong — treat its disappearance as a correction, and tell
   us if you want the subtonic shape emitted as its own *named* type rather
   than silence (that's a vocabulary decision we'd take a brief on).

## Action

Re-run anything that cached minor-key cadence enrichment. No signature
changes; major-key outputs identical.
