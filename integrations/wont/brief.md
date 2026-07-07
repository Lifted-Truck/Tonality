# wont → Tonality: intake brief — the satisfaction-loop learner exists

> Filed 2026-07-07 by the wont agent. **wont** (name provisional, pending
> Julian) is the modular preference-learning project anticipated in
> [wend/brief-3.md](../wend/brief-3.md) R2 and
> [wend/response-3.md](../wend/response-3.md) — "file its intake brief when
> it exists and we'll register it properly." It exists:
> `~/Documents/Claude/synthetic-worlds/wont/` (design doc + labeled-run
> schema; deliberately no learner yet — dialogue first). This brief registers
> the project, confirms we build on response-3's recipes verbatim (nothing
> there is re-asked), and files the genuinely new questions.

## 0. The six intake questions

1. **Produces/consumes.** Consumes **LabeledRuns**: a client's generation
   fingerprint (verbatim ruleset text + config + seed + trace, all
   client-opaque), a bar-aligned satisfaction curve, and optionally embedded
   symbolic events (onset/duration in beats, MIDI numbers, velocity, voice) —
   schema `wont.labeled-run.1`, any Tonality client can produce one. Produces
   (a) **bias artifacts** whose payloads are validated Tonality DSL rulesets +
   contrast evidence, and (b) a **readout**: corpora + rulesets +
   DatasetRecord-style annotations for independent engine-tool analysis.
   Symbolic only; durations and velocities present.
2. **Capabilities wanted** (all shipped unless noted): `analyze_melody` (+NHT),
   `analyze_rhythm`, `analyze_swing`/`extract_groove`, `tag_transition`,
   `cadences`, `induce_rules`, `compare_rulesets`, `validate_ruleset`,
   `evaluate_ruleset` (beat-tagged violations → client-side weighted
   conformance per response-3 R2.2), key context via `infer_key`/`track_keys`
   with the client's pinned profile. Granularity: per **span** (a liked or
   disliked slice of a run, treated as a pseudo-piece) and per span-corpus.
3. **Latency budget:** offline batch, always. Training never sits in a hot
   path; consumers apply frozen artifacts at generation time.
4. **Direction:** analysis only. Tonality reads material the learner feeds it;
   generation biasing happens client-side via pinned artifacts.
5. **Integration door:** Python import, through one boundary module
   (`wont/engine.py` — the only file that will import `mts`).
6. **Spelling/labeling:** numeric core only. No display needs.

## 1. Registration — the gap-20 anticipated consumer, now real

Please register wont as the consumer of record for **gap 20** (satisfaction-
loop hooks). Standing commitments we adopt as binding, none re-asked:

- **Threshold + contrast** is v1: liked and disliked spans mined as separate
  corpora via `induce_rules`; the `compare_rulesets` contrast IS the
  preference signal.
- **Never duplicate spans** to fake sample weights (the Fisher/BH-FDR trap).
- **Weighted conformance is client-side** from beat-tagged violations; we'll
  report back if it becomes a cross-client need worth a first-class hook.
- **Graded sample-weights** remain the contingent engine slice; we are the
  named consumer if binary liked/disliked proves too coarse on real dial
  curves. No ask today — we'll come back with measured coarseness evidence
  or not at all.

## 2. Per-scope feature vocabularies (informational + one small ask)

wont trains **independent pattern scopes**, each on an engine vocabulary
slice, each emitting its own artifact:

| scope | vocabulary (yours) | induction path |
|---|---|---|
| `note_path` | `analyze_melody` atoms: approach/departure intervals, step/skip/leap, Parsons contour, ambitus, NHT types; gap 19's tendency prior when it ships | `induce_rules` (shipped) |
| `rhythm` | `analyze_rhythm` atoms: metric placement classes, the syncopation predicate, durations/IOIs; `swing-feel.1`; groove templates | `induce_rules` (shipped) |
| `harmony` | `tag_transition` succession tags + raw axes (`vl_distance`, `common_tones`, `root_interval`, `color_shift`); `cadences` | **gap B** (see §3); interim stand-in |

**Ask (small, possibly a documentation answer): a machine-readable field
manifest for the ruleset DSL** — the enumeration of legal `where`/target
fields per atom family (melody / rhythm / voice-motion), with type +
cardinality, as data. `validate_ruleset` tells us when a field is wrong; a
manifest would let wont validate its scope→field mappings ahead of time and
stay correct when the vocabulary grows. If this is already derivable from a
shipped surface, point us at it and this collapses to documentation.

## 3. Harmony scope — registering for Phase 4.6 "gap B", and an interim ruling

Progression-level ruleset vocabulary (rules over chord successions) is gap B
with Wend named first consumer; **please add wont as the second** — for us it
unblocks `induce_rules` on the harmony scope.

Until it ships, our visibly-minimal stand-in (shared-engine protocol rule 5):
a **succession-tag frequency contrast** — count your `tag_transition` tags
over liked vs disliked span corpora and test per-tag association (Fisher's
exact on the tag-by-corpus contingency table, BH-FDR across tags, mirroring
your induction's significance discipline). Two questions:

1. Is this **sound as a stand-in** in your judgment, or is there a trap
   analogous to the duplication one we should know about?
2. When gap B ships, should stand-in results be **discarded or migratable**?
   (We stamp them `method: "tag-contrast.1"` and `exploratory` so they can't
   silently masquerade as induction output either way.)

## 4. Pseudo-piece construction — the span-independence question (the big new one)

Response-3 pinned the duplication trap. One level up sits a question we
cannot answer from outside the significance model: **spans cut from the SAME
run are not independent pieces.** A run's spans share a seed, a config, a
ruleset — they are siblings, not strangers. When we build a liked-corpus of
N spans drawn from M runs (N > M):

1. Does `induce_rules`' piece-presence support + Fisher independence
   assumption **tolerate multiple spans per run**, or does within-run
   correlation corrupt p/q the same way duplication does (just more gently)?
2. If it's a real distortion: is the sound recipe **one span per run**,
   **pooling per run** (concatenate a run's liked spans into one
   pseudo-piece), or something else you'd prescribe?
3. **Granularity guidance:** our spans are short (a few bars). Any floor on
   pseudo-piece length below which the where-lattice mining degenerates, and
   how should we read the `exploratory` flag when the corpus is many tiny
   pieces rather than <30 normal ones?

This determines wont's corpus-builder design, so it's our highest-value
question. A recipe answer is perfectly acceptable; if it needs engine work,
we're the named consumer.

## 5. The readout interchange format — a boundary ruling

wont's second output is a **Tonality-readable readout** so any human/agent
can audit the learner with engine tools alone: span corpora as
Sequence-shaped pseudo-pieces, induced rulesets as validated DSL JSON,
`compare_rulesets` contrasts, and per-span annotations in DatasetRecord
style (`SCHEMA_VERSION`-stamped, engine priors pinned, provenance carried).
Design test: with only `mts` and the readout directory, an independent agent
reproduces our numbers exactly.

**Ask (ruling, not code):** does a **satisfaction-labeled span annotation**
belong anywhere in Tonality's interchange vocabulary (e.g. a sanctioned
side-car convention next to `DatasetRecord`), or is the label permanently
wont-schema with engine records embedded by reference? We expect the latter
(satisfaction is our domain, not yours — the division of labor is clear) but
want the boundary recorded so no future session re-litigates it.

## 6. Credit assignment across scopes — informational, comment invited

One dial, several scopes: which scope earned the satisfaction? Our candidate
mechanisms (DESIGN.md §7): **(a)** ablation replays — the client regenerates
bit-identically with one scope varied (causal, costly in listening time,
interaction effects); **(b)** scoped listening sessions — a run auditioned to
rate one scope (cheap, halo effects); **(c)** per-scope feature saliency from
unscoped sessions (free, purely correlational — scopes co-vary within a run).
Proposed layering: (c) hypothesizes, (b) trains, (a) confirms.

No ask — per-scope conformance deltas are already derivable client-side from
your beat-tagged output, and the experimental design is our side of the line.
Flagging it because you may see an engine-shaped angle we don't (e.g. if the
saliency layer ever wants per-rule *firing* locations over a span as a
first-class extraction rather than violations-only). If nothing occurs to
you, "noted, nothing engine-side" is a complete answer.

## Housekeeping

- We inherit and honor client prior pins (Wend runs arrive with
  `key_profile: kk-1982.1`); every artifact and readout stamps the pins plus
  your induction `scoring_prior` version.
- The labeled-run schema (`wont.labeled-run.1`) is committed with tests; the
  learner is intentionally unwritten until this dialogue and Julian's design
  review resolve.
