# Security

Tonality is a local engine: it has no network listener beyond an optional
loopback bridge and keeps no accounts or stored user data. Its attack surface is the
**untrusted input it parses**. MCP tool arguments may be chosen by a
prompt-injected model, the HTTP bridge serves any local process, and MIDI files
come from whoever wrote them. The full inventory, guards and accepted residuals
are in [docs/security/BOUNDARIES.md](docs/security/BOUNDARIES.md).

## Reporting a vulnerability

Please report privately through **GitHub's "Report a vulnerability"** button on
this repository's *Security* tab. Do not open a public issue for anything
exploitable. Include the tool or entry point, the input, and what happened.

Reports are read by the maintainer and fixed on `main`; there are no release
branches to backport to. Every fix lands with a regression test that is shown to
fail without it.

## Supported versions

Only `main`. No numbered release has been cut yet.

## Hardening a deployment

| Concern | Setting |
|---|---|
| Limit which files the MIDI tools can read | `TONALITY_MIDI_ROOTS` = absolute directories separated by `:` (`;` on Windows). Unset means unrestricted. If the variable is set but names no usable directory, file reads are refused. |
| Install exactly the reviewed dependency bytes | `pip install --require-hashes -r requirements/server.lock`, then `pip install --no-deps .` |
| Keep the bridge local | it binds `127.0.0.1` by default and refuses browser requests from non-loopback origins unless they are allowed with `--allow-origin`. Avoid `--open-cors`, and do not bind it to a public interface |

## Supply chain

Dependencies are hash-pinned in `requirements/*.lock`. The SBOM is
`docs/security/sbom.cdx.json` (CycloneDX 1.5, derived from the locks). A weekly
upstream canary checks the locks for known vulnerabilities and tests against
current `mcp` SDK releases. `bash scripts/upstream-canary.sh` runs the same
checks locally.
