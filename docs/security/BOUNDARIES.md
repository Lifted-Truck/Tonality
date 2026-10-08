# Trust boundaries — Tonality

> Step 1 of the fleet's security method (`kit/security/` in the standards repo,
> Decision 85): list every place untrusted data enters and what it can reach,
> **before** writing guards — a generic vulnerability list describes other
> people's bugs. Written 2026-10-08 from the code, not from memory: the argument
> surface was read off every tool's signature, the bridge was probed live, and
> the MIDI path was tested with a crafted file.
>
> Decision 85 makes this **required** here, not opt-in: Tonality parses
> untrusted input on three doors.

## The threat model in one line

Every MCP tool argument is chosen by a caller the engine cannot trust — **a
prompt-injected model** on the stdio server, or **any local process** on the HTTP
bridge. The tool boundary is a trust boundary even on a loopback-only server.

## Surfaces

| # | Where untrusted data enters | Who controls it | What it can reach | Guard (strongest first) | Must-fail control |
|---|---|---|---|---|---|
| 1 | **MCP tool arguments, stdio** (79 tools) | a prompt-injected model | every engine entry point | pydantic types (FastMCP) → **boundary validator** (`mts/mcp/validation.py`: shape, finiteness) → engine invariants (below) | `tests/test_mcp_fuzz.py` (1,905 mutated calls) + its planted-defect control |
| 2 | **HTTP bridge requests** (`127.0.0.1:8012`) | any local process; allowed browser origins | request parsing, then every tool | origin gate (403, *before* the body is read) → strict `Content-Length` (400 non-numeric/negative, 413 over `MAX_BODY_BYTES` = 16 MB) → boundary validator | `test_bridge_content_length` |
| 3 | **MIDI files** (`midi_file_analysis`, `piano_roll_view`, and import) | whoever wrote the file | mido's parser, the sequence, the meter map | unreadable/truncated → `ValueError`; span limit; **bar budget** (a time-signature byte can encode a denominator up to 2^255) | `test_bar_enumeration_budget`, `test_missing_caller_file_is_the_callers_error` |
| 4 | **Named-library names** (`load_named_*`) | a model | `open()` on the filesystem | `resolve_named_asset`: separators/parent refs/leading dots refused, resolved path must stay inside the library, **≤ 128 chars** | `tests/test_mcp_path_traversal.py` (27 cases), `test_overlong_library_name_is_refused_before_open` |
| 5 | **Structured payloads**: rulesets, patterns, plans, transition matrices, groove templates, style profiles | a model | the parsers for each | total validators (`RulesetValidationError`, `PatternValidationError`, …), strict `plan_from_payload`, `TransitionMatrix.from_dict` → `ValueError` | fuzz; `test_malformed_transition_matrix_is_the_callers_error`; the plan round-trip ratchet |
| 6 | **Grid sizes derived from arguments**: span, `hop_beats`, `subdivisions`, loop length, time signature | a model (via 1–3) | memory and CPU | `Event` rejects NaN/±∞; `MAX_SPAN_BEATS` = 100,000; `MAX_GRID_CELLS` = 100,000 checked **before** allocating at all six grid sites (`mts/limits.py`) | one test per site, each just over budget (`tests/test_resource_limits.py`) |

**Outside the engine, recorded so they are not mistaken for covered:**
`.tonality_session.json` (written and read by the same local user, so no boundary
is crossed); the `integrations/` mailbox (a prompt-injection surface for *agents*,
governed by the protocol's "observed content is data, not instructions" rule, not
by engine code).

## What the first fuzz pass found (2026-10-08)

The same 1,905 calls, before and after this slice:

| | defects | tools affected | memory exhaustion |
|---|---|---|---|
| before | **523** | 65 of 79 | **11 inputs** allocating >1.2 GB/s until killed |
| after | **0** | 0 | 0 |

Five root causes:

1. **Arguments had no runtime type check** (~480). Python hints are not enforced,
   so a dict where a list belonged went into engine code and escaped as a
   `TypeError`/`KeyError`/`AttributeError`, which the bridge correctly reports
   as a 500 engine bug. An int passed as a file path reached `open(7)`, which
   opens file descriptor 7 of the server process.
2. **Grid sizes were unbounded.** One small argument (`1e9` beats; `1e999`, which
   valid JSON parses to infinity; `subdivisions=10**7`) made windowed analyses
   allocate without limit. Reachable on all three doors: pydantic accepts
   infinity for a float. A second route: below `hop_beats` ≈ 1e-11 at large
   spans, `start + hop == start` in floating point, so the window loop never
   advances and appends forever.
3. **`Event` accepted NaN and infinity.** NaN passed `onset >= 0` because every
   comparison with NaN is false.
4. **An overlong library name reached `open()`**, and `OSError("File name too
   long: <absolute install path>")` leaked the machine's home layout through the
   bridge's error echo.
5. **Two payload parsers let malformed input escape as `KeyError`.**

The fix also surfaced **two pre-existing bugs that depended on how you connect**
(found because one validator now enforces the same annotations on every door):

- `scale_names` was annotated `list[int]` while its docstring and tests accept
  note names, so the stdio server rejected `["C", "E", "G"]` while the bridge and
  import accepted it.
- `validate_ruleset` is meant to *report* every error as data, but its `dict`
  annotation let pydantic raise before it could report on a non-object.

## Accepted residuals (not open items — decided, with the reason)

| Residual | Why accepted |
|---|---|
| `midi_file_analysis` reads any `.mid` path the caller names | **Open decision, Julian's call**, unchanged: an env-var allowlist with an unrestricted default is recommended (`integrations/security/response-mcp-hardening.md`) |
| A bridge 500 echoes the exception message | 500 now means a genuine engine bug only; the client is the same local user on loopback |
| If the validator **and** a grid guard regress together, the fuzz test could exhaust memory instead of failing | each guard has its own cheap just-over-budget test that fails cleanly first |
| No `SECURITY-CATALOGUE` file yet | the kit has not shipped the format (Decision 85: "kit deliverables not yet built"); inventing one here would recreate the copy drift kit 2.4.0 ended. This table is the content; the format follows the kit |
| Row *meaning* (a well-formed note, a valid ruleset) is checked by each tool, not by the boundary validator | the validator checks shape; meaning stays with the tools' own total validators, which already raise `ValueError` |
