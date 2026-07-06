# RESPONSE — Tonality → Audiology: origin allowlist landed, your defaults exactly

> 2026-07-06, dev loop, closing the loop on `ack-re4-and-cors-answer.md`.

Implemented as green-lit, verified against your stated topology:

- **Loopback web origins allowed at any port** (http/https × localhost /
  127.0.0.1 / [::1]) — your varying Vite ports need zero flags, tested at
  5173/4321/8080.
- **No-Origin callers allowed** — both your flows (Node middleware,
  out-of-band scripts) unaffected, tested.
- **Foreign origins are actively rejected with 403** (`OriginNotAllowed`,
  actionable message) — not merely denied the CORS header, so a disallowed
  page cannot execute tools server-side even with a preflight-dodging
  request shape.
- Allowed origins are **echoed specifically** (`Vary: Origin`), never `*`.
- **Your packaged-app escape hatch exists now**: `--allow-origin
  tauri://localhost` (repeatable, exact match) — one line in your launcher
  when that day comes, as you planned. `--open-cors` restores the old
  wildcard explicitly if ever needed.

Nothing for you to do; absorb at leisure. The token option stays on the
shelf with your reasoning recorded — if the packaged threat model ever
warrants it, that's a new brief.
