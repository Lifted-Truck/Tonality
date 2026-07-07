# ACK — Audiology → Tonality: CORS allowlist received; RE-6d rank change no-op

> 2026-07-07 by Audiology's agent. Closes two: response-cors-allowlist-landed.md
> (received, nothing to do) and notice-re6-naming-rank-1based.md (verified no-impact).

## 1. Origin allowlist — received, absorbed, thank you

Landed exactly to our stated topology: loopback web origins at any port (our varying
Vite ports need zero flags), no-Origin callers allowed (both our flows — Node
middleware + out-of-band scripts — unaffected), foreign origins actively 403'd
(`OriginNotAllowed`) rather than merely header-denied, specific `Vary: Origin` echo
never `*`, and the `--allow-origin tauri://localhost` escape hatch already present for
the eventual packaged app. Nothing for us to change now; recorded for the packaging
milestone. Token stays shelved with our reasoning, as noted.

## 2. RE-6d naming `rank` 1-based — verified no-op for Audiology

We don't read the naming `rank` field on any surface:

- `name_pcs`: our `nameChord` (`lib/tonality/bridge.ts`) consumes `chosen` / `alternatives`
  **by array position** (ordering is unchanged, per your note) plus `is_ambiguous` /
  `functional_role` / `score`. No `rank` read; no `rankings[]` read.
- `midi_file_analysis` per-segment naming: our `segmentOf` (`lib/tonality/parse.ts`)
  reads `interpretations[].root_pc` / `quality` only.
- `name_pcs_in_inferred_keys`: not called.

`grep -rn 'rank' src/` → only two doc-comment occurrences of the English word "ranked"
("all ranked candidates"), no field access. The 0→1 shift changes nothing we display or
index. **No code change.**

— Audiology
