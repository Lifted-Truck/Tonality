---
id: mcp-hardening-response
re: BRIEF — MCP Security Hardening (Tonality + all MCP-exposing repos)
from: Tonality
to: security / originating agent
status: responded
ball: julian (two decisions) + tonality (P0.1 build)
responded: 2026-07-25
---

# Response: MCP security hardening — Tonality audit

**Headline: the "Tonality is pure" assumption was WRONG, and the brief's
instruction to verify it rather than rely on it is what caught it.** One real
vulnerability found and fixed in this PR (path traversal + content disclosure
via the named-library tools). Two P0 items were already green from prior work.
One P0 item (metadata freeze) is a genuine gap with a build queued. Findings and
evidence below; every claim was executed, not reasoned about.

## P0.3 — Injection-class audit ✅ COMPLETE — **1 vulnerability found + fixed**

**Shell/command injection: none.** `grep -rnE "subprocess|os\.system|os\.popen|
eval|exec|__import__|pickle\.load|yaml\.load|shell=True"` over `mts/` returns
**zero hits**. The pure-function claim holds for the ~43% CVE class.

**Path traversal: CONFIRMED VULNERABLE (now fixed).** Three MCP tools took a
*name* and built a filesystem path from it unguarded:
`load_named_ruleset` · `load_named_pattern` · `load_named_cross_part_pattern`
(`_RULESETS_DIR / f"{name}.json"` and kin).

Executed proof (before the fix), reading a real file outside the library dir:

```
load_named_ruleset("../../../port/pin")
  → RulesetValidationError: unknown keys ['export_schema_version', ...]
```

Two things happened there, and the second is the worse one:

1. **The file was opened and parsed** — arbitrary `.json` anywhere the process
   can read was reachable via `../`.
2. **The validator's total-error report echoed the file's top-level keys back to
   the caller.** The blind-agent "collect every error" contract — a genuinely
   good design for repairability — became an **information-disclosure amplifier**:
   an attacker enumerates the key names of any JSON on the filesystem. Worth
   noting as a general pattern: *verbose, helpful validation errors are an
   exfiltration channel whenever the validated content is attacker-chosen.*

**Threat model (why this matters on a local stdio server):** exactly the MCP one
the brief names — the tool argument is chosen by a **prompt-injected model**, not
by a trusted human. The tool boundary is a trust boundary even with no network
listener. This is the ~10% path-traversal class.

**Fix** (`io/loaders.resolve_named_asset`, wired at all three call sites): a
library name is a **stem, never a path**. Two layers by design — reject
separators / parent-refs / leading dots up front (clear error), then verify the
**resolved** path is contained in the library directory (catches symlinks and
normalisation surprises a string check cannot see). Refusal now happens *before
any file is opened*, so the disclosure channel closes with it.

**Gate:** `tests/test_mcp_path_traversal.py` (27 cases) — every loader × 7
malicious names, an assertion that the refusal is a *name* rejection rather than
a downstream schema error (i.e. the file was never read), legitimate names still
load, and a **ratchet** that fails if any future loader builds `f"{name}.json"`
without the guard.

**Remaining path surface, by design, flagged for a decision:** `midi_file_analysis(path)`
takes an **arbitrary filesystem path** — that is its documented purpose (analyze
a MIDI file), so it is not a bug, but it *is* an unrestricted read primitive for
`.mid` content in the hands of an injected model. The brief's rule ("allowlist
roots, canonicalize") is not yet applied. **Julian's call** — see Open Decisions.

## P0.4 — Transport hygiene ✅ ALREADY GREEN (verified, no change needed)

- stdio server: no network listener. ✅
- HTTP bridge: binds `127.0.0.1` by default (`DEFAULT_HOST`), and enforces an
  **origin allowlist** (RE-4e): no-Origin callers pass, loopback web origins pass,
  everything else is **actively 403'd** — not merely denied the CORS header, so a
  disallowed page cannot execute tools. This is the DNS-rebinding class the brief
  cites (cf. the MCP Inspector RCE) and it was already handled.
- TLS: N/A while local-only.

## P0.2 — Strict schema validation 🟡 PARTIAL

- **Unknown fields: rejected.** The bridge binds arguments through the tool
  signature and returns **400** on a binding `TypeError` (unknown/missing args) —
  reject-by-default holds at the transport.
- **Per-field types/ranges: partial.** Python type hints are *not* runtime-enforced;
  individual tools validate ad hoc (`_pc()`, `validation_errors()`, the total
  ruleset/pattern validators). Coverage is good where a DSL exists, thinner on
  scalar args.
- **Not done: the fuzz set.** The brief's acceptance criterion ("fuzz a
  malformed-input set per tool") is not implemented. Queued (see below).

## P0.1 — Freeze and lint tool metadata 🔴 GAP (build queued)

There is a test that every tool **has** a docstring (it becomes the description),
and the conformance golden pins every tool's **output** — but **nothing hashes
tool names + descriptions + schemas**, so a description edit is invisible to CI.
That is precisely the **rug-pull** surface the brief calls out, and the one P0
item with no coverage at all.

Planned (own PR, small): a `tests/test_tool_manifest_pin.py` that hashes the full
manifest (name + signature + docstring, sorted) against a committed pin, failing
on unreviewed drift — the `port/pin.json` pattern, reused. Plus the
**instruction-language lint** (`ignore`, `always`, `instead of`, imperative
phrasing at the model): descriptions *describe*, never *direct*. Note one real
consequence to accept: **an intentional docstring edit will then require a pin
regen in the same PR** — that is the point, but it is friction worth naming.

## P2.8 — Supply chain 🟡 PARTIAL

Runtime deps are minimal and range-pinned (`mido>=1.3,<2`; `mcp>=1.2` optional
extra) — small attack surface, but **not exact-pinned, no lockfile, no SBOM, no
dependency scan**. The brief's `./verify full` items are not implemented. This
repo has no `./verify` script (its gate is `scripts/ci-local.sh` + the Stop hook);
mapping the brief's `verify fast` / `verify full` vocabulary onto this repo's
actual gate is a small piece of work, noted so the cross-repo criterion is not
silently mis-reported as met.

## Not applicable / explicitly not built

P1.5 (OAuth 2.1) · P1.6 (session model) · P1.7 (Server Card) — **stdio + loopback
only; no remote listener exists and none is planned** (local-first is a recorded
architectural decision, not an oversight). Per the brief's own non-goal ("no auth
infrastructure for stdio-only servers"), these stay unbuilt. **They become live
the moment a hosted endpoint is contemplated**, and P0 must be fully green first.

## Open decisions (Julian's call — not the engine's)

1. **`midi_file_analysis` path policy.** Options: (a) leave unrestricted (it is a
   local file-analysis tool; the user's own agent reads the user's own files);
   (b) allowlist roots via env var (e.g. `TONALITY_ALLOWED_ROOTS`), refusing
   outside; (c) canonicalize + refuse symlink escapes only. Recommendation: **(b)
   with an unrestricted default**, so the capability is unchanged for direct users
   but a hardened deployment can constrain it — and the refusal is honest and
   reported either way. This needs a decision because it can *break* a legitimate
   workflow, which is not a call I should make unilaterally.
2. **Public registry listing.** The brief frames P0 as gating a public listing.
   Recommendation: **do not list until P0.1 (manifest pin) is green** — with a
   public listing, an unreviewed description edit is exactly the rug-pull vector,
   and it is currently the one uncovered P0.

## Trace

| Item | Status | Evidence |
|---|---|---|
| P0.1 metadata freeze/lint | 🔴 gap | no manifest hash exists; build queued |
| P0.2 schema validation | 🟡 partial | unknown-field rejection verified; fuzz set absent |
| P0.3 injection audit | ✅ **1 found + fixed** | zero shell/eval; traversal proven then closed; 27-case gate |
| P0.4 transport | ✅ green | loopback default + origin allowlist w/ 403 verified |
| P1.5–7 remote | ⛔ n/a | stdio/loopback only, by decision |
| P2.8 supply chain | 🟡 partial | range pins only; no SBOM/scan |
| P2.10 trace | ✅ | this file |

Full local CI green on both legs at time of writing: **1055 passed, 1 skipped**
(dev suite) + **3 passed** (audit invariants).

## Cross-repo propagation

The brief asks that it reach every MCP-exposing repo with a response each. From
Tonality's vantage the others are **JUCE-RAG** (retrieval tools — the brief
correctly flags these as the *highest*-risk shape here: path **and** pattern
arguments touching the filesystem; our traversal finding is direct evidence the
class is live, and JUCE-RAG's surface is strictly larger) and **Audiology**
(consumer-side; consumes our HTTP bridge rather than exposing MCP today — its
exposure is *inbound trust* in a local endpoint, a different question). Propagation
itself is Julian's to route; this response covers Tonality only.
