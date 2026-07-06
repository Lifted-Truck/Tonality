# NOTICE + DESIGN CALL — Tonality → Audiology: bridge auth (you coordinate), and one error-code fix

> 2026-07-06, dev loop, from the rigor & efficiency review (RE-4e). One
> already-landed behavior fix, and one design call that is **yours to make**
> because you are the web door's consumer of record (gap 9).

## Landed now (no action): engine TypeErrors are 500s

`POST /call/<tool>` used to report *every* `TypeError` as HTTP 400 — blaming
your client for engine bugs. The bridge now binds the kwargs against the
tool signature first: unknown/missing arguments are still 400 with the
actionable message; a `TypeError` raised *inside* the engine reports as 500.
If you alert on 500s, they now mean what they should: our bug, not yours.

## The design call: tightening the wide-open CORS

Current state: the bridge binds loopback and sends
`Access-Control-Allow-Origin: *` + preflight approval. The recorded finding:
**any web page you happen to visit can invoke the bridge on
127.0.0.1:8012** — including path-taking tools (`midi_file_analysis`) that
read files the browser page names. Loopback bounds *who can listen*, not
*which origin can call*.

Two candidate mechanisms (pick one, or argue for neither):

1. **Origin allowlist (our lean).** Default: allow requests with **no
   `Origin` header** (curl, CLIs, native apps — unaffected) plus origins on
   an allowlist defaulting to localhost (`http://localhost:*`,
   `http://127.0.0.1:*`). `--allow-origin <origin>` extends it;
   `--open-cors` restores today's behavior explicitly. Cost to you: if your
   visualizer is served from a localhost dev server, **nothing changes**;
   if it's served from `file://` (Origin `null`) or a non-localhost host,
   you'd add one flag to your launch instructions.
2. **Shared token.** Bridge starts with `--token <t>` (or auto-generates and
   prints one); calls carry `X-Tonality-Token`. Stronger (defeats even a
   malicious localhost page), but costs you a fetch-header change and a
   token-handoff step in your setup docs.

Questions for you: which mechanism; what origin(s) your surfaces are
actually served from (localhost dev server? `file://`? packaged app?); and
whether any of your flows call the bridge from a context that sends no
`Origin` header. Reply as an ack/brief on this channel; we implement to
your answer. **No behavior changes until then** — today's wide-open CORS
stands, documented as awaiting this call.
