# SEED — the corpus workbench (a new consumer project; hand this to its agent)

> 2026-07-09, Tonality dev loop, approved by Julian. This is a **seed packet**,
> not an intake brief: the project does not exist yet, so Tonality states the
> mission and the boundaries from its vantage. The new agent's FIRST protocol act
> is to read this + [INTEGRATION.md](../../INTEGRATION.md) +
> [integrations/README.md](../README.md), set up its repo, and file its OWN
> `brief.md` here (its voice, the six intake questions) — this seed then becomes
> historical context, and the brief↔response exchange takes over. Name
> "corpus-workbench" is provisional; the project may rename itself (its channel
> directory follows the final name).

## Mission

A **batch corpus-exploration surface** for Tonality's ruleset + pattern +
style-profile stack: point it at a corpus report and browse what the engine
found — across *many* pieces at once. It is the visualization/orchestration half
of the corpus exercise regime (ROADMAP Phase 4.6, corpus-exercise entry);
deliberately **not** part of Audiology, which stays the per-piece / live
instrument surface (right-size: one product shape per project).

## Division of labor (the non-negotiables)

- **Rule 3 — never reimplement the engine's domain core.** The workbench does
  **zero** music analysis: no key inference, no matching, no statistics of its
  own. It renders and orchestrates what the engine computed. If a view seems to
  need new analysis, that is a **brief to Tonality**, not workbench code.
- **Rule 1 — one boundary module.** A single seam file is the only code that
  talks to the engine; everything downstream consumes normalized JSON.
- **Rule 8 — canonical numeric at the boundary, presentation at the edge.**
  Pitch classes and MIDI ints arrive; note spelling/labels are the workbench's
  display concern.
- **Rule 2 — degrade visibly.** If the bridge is down, say so; never silently
  show stale data.

## What it consumes (all shipped today)

1. **The exercise-harness report** — `validation/exercise_rules_patterns.py
   --out report.json` (lands with Tonality PR #197): per-piece segmentation
   (key, chords, unnameable spans), per-piece results for every named ruleset
   (hard/soft + itemized refusals) and pattern (counts + occurrence beats),
   corpus-level induction summaries, and the by-piece held-out cross-entropy.
   The report is the workbench's primary input — static JSON, no live engine
   needed for a first version.
2. **Live per-piece descriptors** (optional, second step) via the **HTTP
   bridge** (`python -m mts.mcp.bridge` → `127.0.0.1:8012`, `GET /tools`,
   `POST /call/<name>`): `piano_roll_view`, `find_pattern`, `evaluate_ruleset`,
   `segment_chords`, `transition_matrix`, `transition_cross_entropy`. Same
   contract as MCP; CORS allowlist already admits loopback web origins.

## The first three views (the acceptance targets)

1. **Pattern-occurrence heatmap** — pieces × named patterns, cell = occurrence
   count; click a cell → the occurrence list (beats, voices) rendered over a
   `piano_roll_view` strip.
2. **Conformance distribution** — per named ruleset: hard hold/fail per piece +
   the soft-score distribution across the corpus; refusals shown as refusals
   (never as zeros — the engine's honesty must survive rendering).
3. **Induced-rule browser** — the induction summaries with their evidence
   (support/leverage/q, the `exploratory` flag rendered prominently — an
   exploratory result must LOOK exploratory).

## Practical notes for the new agent

- **Stack is yours** (likely web/TS). If you build in TS against the bridge,
  you are the **first web consumer** — you may file for the typed TS bridge
  client recorded as Horizon H2 (types generatable from the engine's manifest);
  that ask goes in your brief, and its trigger condition is literally you.
- **Pins**: stamp the engine version + any prior versions (`kk-1982.1`,
  `distribution.1`, `scoring prior`) shown in a report; a dashboard that mixes
  reports from two engine versions must say so.
- **Local-first**: the bridge is loopback-only by design. No cloud endpoint
  exists or is planned.
- File your brief **direct** (a PR adding `integrations/corpus-workbench/brief.md`
  in the Tonality repo) or by relay through Julian — both are protocol-valid.

## What Tonality owes this seed

Nothing yet — everything referenced is shipped or in #197. Rulings, gaps, and
any engine asks the brief raises get the normal `response.md` treatment.
