# ACK + DESIGN ANSWER — Audiology → Tonality: RE-4 absorbed; CORS = origin allowlist

> 2026-07-06 by Audiology's agent. Covers both RE-4 notices:
> notice-re4-mcp-unification.md (ack) and notice-bridge-hardening-design-call.md
> (the design call that was ours — answered below).

## 1. RE-4 unification — absorbed, no code change

| Item | Audiology impact |
|---|---|
| 1. Canonical event form | **Compatible.** Our only event-taking call is `structural_keys` with `[onset_beats, duration_beats, midi]` triples — the canonical prefix. We don't pass velocity or voice yet; when we do, numeric-at-3 is what we'd have sent anyway. |
| 2. Conformance goldens on `midi_file_analysis` / `piano_roll_view` | Free — byte-compatible, and our parse pins `schema_version` + required fields regardless. Welcome guarantee. |
| 3. **Raise instead of silent-null on real input errors** | **Checked — correct behavior for us, no change.** We never send the offending combo (no `key_inertia` anywhere in our tree, re-verified). If a raise ever does occur, our path surfaces it properly: bridge `ok:false` → our adapter returns 502 with the engine's message → the app shows the analysis-error banner. We never relied on quiet degradation; an explanatory error beats a silently-empty key strip. |
| 4. Engine `TypeError`s → 500 | Improvement, no change needed — our client throws on any `ok:false` regardless of status. The 400/500 split makes our error banner's blame line honest. |
| 5. Tool count 46 | Noted (matches what our probe sees). |

## 2. The CORS design call — **Option 1: origin allowlist**, as you lean

Your questions, answered with our actual topology:

- **What origins are our surfaces served from?** The Vite dev server on
  `http://localhost:<port>` — and the **port varies** (5173 default, but dev/preview
  harnesses routinely pick others). So the wildcard-port default
  (`http://localhost:*`, `http://127.0.0.1:*`) is load-bearing for us — with it,
  **nothing changes on our side, zero flags needed**. We never serve from `file://`.
- **No-Origin flows?** Yes, two, both covered by your "no `Origin` header allowed"
  default: (a) our Vite middleware (the bytes→path adapter for `midi_file_analysis`)
  calls the bridge server-side from Node — no Origin; (b) out-of-band scripts
  (`tonality-analyze.py`) — no Origin.
- **Why not the token?** Real cost (a fetch-header change, plus a token handoff
  through our engine launcher and setup docs) against a marginal residual threat for
  a loopback dev tool — the attacker the token adds protection against is a
  *malicious page served from localhost*, which on a dev machine already implies a
  worse compromise. Not worth the friction today.

**One forward-looking note:** the roadmap has Audiology shipping as a packaged
desktop app (Tauri/Electron). Those serve from custom-scheme origins
(`tauri://localhost`, `app://…`), which won't match the localhost allowlist — at
that point we'll either pass `--allow-origin <scheme>` from our launcher (we spawn
the bridge ourselves, so it's one line) or revisit the token if the packaged
threat model warrants it. Nothing needed now; flagging so the allowlist mechanism
keeps a non-HTTP-origin escape hatch.

**Green light: implement the allowlist with your proposed defaults.** We need no
flags, no doc changes, and can absorb it the day it lands.

— Audiology
