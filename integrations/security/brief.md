# BRIEF — MCP Security Hardening (Tonality + all MCP-exposing repos)

**ball:** receiving agent
**Scope:** Tonality's MCP server (primary), plus any repo exposing or planning MCP tools (JUCE-RAG retrieval tools, Audiology integration surface). Doctrine applies: reduce-never-invent, gates never weakened, done = green + acceptance criteria + trace.

**Context:** MCP's documented threat record (30+ CVEs in ~12 months) clusters in four classes: shell/command injection (~43%), tooling-infrastructure attacks (~20%), auth bypass (~13%), path traversal (~10%). The distinctive MCP-specific surface: **tool metadata is executable intent** — descriptions and schemas are read by an LLM and shape its behavior, enabling tool poisoning, shadowing, and rug pulls. A public registry listing raises stakes on all of the below.

---

## P0 — Before any public listing (CI-blocking, Layer-0 style)

**1. Freeze and lint tool metadata.**
Tool names, descriptions, and schemas are a trust surface, not documentation.
- No dynamically generated descriptions. All tool metadata lives in version-controlled source.
- Add a `./verify` check: hash the full tool manifest (names + descriptions + schemas); fail on unreviewed drift. A description change gets the same review weight as a code change (rug-pull prevention).
- Lint descriptions for instruction-like language ("ignore," "always," "instead of," imperative phrasing aimed at the model rather than at the human). Descriptions describe; they never direct.

**2. Strict schema validation on every tool input.**
- Reject-by-default: unknown fields rejected, types enforced, enums closed, string lengths bounded.
- Validation happens in deterministic code before any tool logic runs — this is the AI/deterministic boundary doing security work. The model proposes arguments; the schema decides admissibility.

**3. Injection-class audit.**
- Grep audit for any subprocess, shell, eval/exec, or filesystem path constructed from tool arguments. Tonality should be near-zero here (pure-function theory engine) — **verify that assumption rather than relying on it**; the audit result goes in the trace.
- Any legitimate file access: canonicalize paths, allowlist roots, no traversal (`..`) survival after canonicalization.
- JUCE-RAG note: retrieval tools (grep/read-section) are *exactly* the high-risk shape — path and pattern arguments touching the filesystem. Allowlist the docs mirror root; treat patterns as literals unless explicitly regex-validated.

**4. Transport hygiene.**
- Local/stdio servers: no network listener, which is the win — don't add one without cause.
- Any HTTP transport: bind localhost unless remote is intended; validate `Origin` (DNS-rebinding class — cf. the MCP Inspector RCE); TLS for anything non-local.

## P1 — Spec currency + remote readiness

**5. Auth to current spec** (only if/when remote): OAuth 2.1 with PKCE, short token lifetimes, scopes per tool group (read-theory vs. anything stateful), no long-lived static bearer tokens.

**6. Session model:** stateless or explicitly resumable per the 2026 roadmap direction; no in-memory session state that a restart or LB reroute invalidates silently.

**7. Server Card:** publish `.well-known` metadata; sign it if the registry supports signing. The card claims only what the manifest hash covers — card and manifest drift together or not at all.

## P2 — Supply chain + ongoing

**8. Pin dependencies; add SBOM generation and dependency scanning to `./verify full`.** MCP's active supply-chain campaign makes "install popular server/SDK" the current infection vector — the same caution applies to any third-party MCP servers *consumed* by agents, not just served.

**9. Rate limiting + audit log** on any public endpoint: per-client limits, append-only request log (fits DECISIONS.md/trace discipline).

**10. Trace requirement:** each item above closes with a trace entry — what was audited, what was found, what gate now enforces it. "Passing ≠ done."

---

## Acceptance criteria

- [ ] `./verify fast` fails on tool-manifest drift and on schema-validation gaps (fuzz a malformed-input set per tool)
- [ ] Injection-class audit complete with written findings in traces/ (including the "Tonality is pure" verification)
- [ ] Transport posture documented per repo: stdio-only, or hardened HTTP checklist complete
- [ ] Server Card published only after P0 fully green
- [ ] SBOM + dep scan in `./verify full`; pins committed
- [ ] Cross-repo: this brief propagated to every MCP-exposing repo via standard brief→response exchange; each returns a response file with its audit findings

## Explicit non-goals

- No A2A adoption or interop work (decision stands; revisit trigger unchanged)
- No auth infrastructure for stdio-only servers — don't build for a listener that doesn't exist
- No weakening of any existing gate to accommodate the new checks
