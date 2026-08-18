# Decisions on record (the "why", so we don't relitigate)

> **Append-only.** Entries are never altered or renumbered once written — a
> decision that turns out wrong is superseded by a NEW entry that says so, so
> the reasoning trail stays readable. The next number is **max + 1**, never
> "last + 1": the register need not stay in numeric order for the numbering to
> stay correct.
>
> Moved here verbatim from `ROADMAP.md` on 2026-08-18 (kit 2.4.1 retrofit,
> Decision 16). Numbering is unbroken, so every existing `Decision N` citation
> in the tree still resolves. **ROADMAP.md remains the single source of truth
> for *direction*** — phases, gaps, plans; this file is the immutable record of
> *why*, kept out of the blast radius of ROADMAP's restructures.

1. **Build on the existing engine, don't greenfield.** The bitmask PC substrate,
   immutable core objects, and the multi-notation parser are correct and tested.
   Greenfield would rebuild them nearly identically. The foundation has the right
   *substance*; we are correcting its *frame* (library/MCP, not standalone app).
2. **Time and timeless identity are layers, not opposites.** The identity layer is
   atemporal; the temporal layer sits above and *references* it. (See CLAUDE.md
   "core data model.")
3. **Identity key + optional realization**, with a two-axis lattice
   (transpositional × registral). Register is a *richer* representation that
   reduces to PC — not "secondary metadata." Voicing-sensitive analysis reads the
   realization; matching/naming reads the key.
4. **Reduce, never invent.** Inventing register = choosing a voicing = a generative
   act. Analysis declares the level it needs and errors when it's missing.
5. **The MCP layer is a thin adapter, not a subsystem.** Intelligence stays in the
   engine. MCP is the first *consumer* and a forcing function for clean APIs.
6. **Keep the tuning system behind a reduction boundary.** "The identity key *is* a
   12-bit bitmask" is a 12-TET-specific choice we accept for now (the substrate is
   correct and tested; a generalized identity type is premature). To keep the
   eventual multi-system generalization (see Phase 6) from being a teardown, the
   **lattice** (transpositional × registral) and the **Realization** API are
   deliberately tuning-agnostic — rooted-ness and register-ness are not 12-TET
   concepts. Only `reduce_to_key()` and `core/bitmask.py` know the substrate is 12.
   New code routes through the reduction rather than open-coding `mask` arithmetic,
   so swapping the substrate later is a localized change, not a rewrite.
7. **Disambiguation is ranked, explicit, and plural — never an opaque guess.** When a
   set or passage admits several names/analyses (the candidates `interpret_chord`
   enumerates), the engine selects the contextually-best reading *and* surfaces the
   competing alternatives with inspectable, data-derived weights and the evidence
   behind them. Statistical scoring stays **reproducible** (same input + same corpus
   → same ranking); it never collapses to a single black-box answer. This preserves
   the division of labor: transparent combinatorics + explicit statistics *here*,
   open-ended semantic leaps in the caller.
8. **Rulesets are declarative, serializable, versioned artifacts over the
   engine's own analytical vocabulary** (added 2026-06-11; see Phase 4.6). A
   compositional ruleset is a set of predicates over facts the typed results
   already expose — scoped (per-event / adjacent-pair / phrase / global), hard
   or soft-weighted, declaring the specification level each rule requires
   (cardinal rule applies: a parallel-fifths rule *errors* on voiceless
   material). Rulesets are versioned priors (the Phase 3.5 pattern; the naming
   weight table is the degenerate first instance). **Rule *proposal* is the
   caller's job; rule *verification and evaluation* are the engine's** — an
   LLM translates a treatise into candidate rules in the DSL, the engine
   validates and evaluates them exactly. Rule *induction* is exact
   version-space mining over a template vocabulary, scored against null
   models — statistics, never an in-engine learned black box. Corollary: the
   engine can only express, check, and induce what its analytical vocabulary
   can say — vocabulary expansion (voice, melody, rhythm) is therefore a
   first-class investment, not a side effect.
9. **Audio stays outside — permanently.** (Decided 2026-06-11 after evaluating
   Magenta DDSP for inclusion.) Audio synthesis and audio-domain DSP — neural
   (DDSP/RAVE-class) or otherwise — are consumer-side, full stop. Reasons on
   record: the division of labor *is* the product (exact combinatorics here;
   a learned controls→audio mapping is the opposite kind of object, and
   Decision 8 just barred in-engine learned components); three consumer
   briefs (A5–A7) signed contracts that depend on the symbolic-only boundary;
   neural synthesis is not byte-reproducible in the versioned-priors sense;
   and the dependency footprint is incompatible with a `mido`-sized engine.
   The engine's audio-facing contribution is **descriptor tracks** (typed
   continuous harmonic control signals — see Phase 5), never sound. Which
   synthesis stack a consumer uses (DDSP, RAVE, analog modeling, …) is a
   per-project choice made in *their* repo.
10. **C++ is the performance home — dual implementation, golden-anchored.**
    (Decided 2026-06-12; **revised 2026-06-29 with Julian** — see the revision
    note.) A C++ core becomes the engine's **performance / generative / embedded
    main**, while the **Python implementation stays a fully-functional peer** (not
    a binding shim). Both are held to one language-neutral spec — the conformance
    golden. Motivations on record: A4's plugin/device frame cannot ship a CPython
    runtime (the one consumer the Python engine structurally cannot serve
    in-process); an embedded profile (below) needs it; a C++ core compiles to WASM
    nearly for free, incidentally reopening the declined browser-door commitment as
    a side effect rather than a promise. Sequencing fence: port **after** the 12-TET
    surface is frozen — Phase 6 renegotiates "the mask is the key", so porting
    before it means porting the substrate twice (and **port by stability** — only
    the frozen subset is ever dual; see Phase 8 / [CPP_PORT.md](CPP_PORT.md)). The
    migration's spec anchor is the **golden-file conformance harness** (delivered
    2026-06-12, `tests/test_conformance.py` + `tests/golden/conformance.json`): one
    deterministic call per MCP tool, full-JSON comparison with float tolerances
    (rel 1e-9), language-neutral by construction — a C++ engine reproducing the
    goldens is conformant. The harness doubles today as regression armor: any output
    change fails it; intended changes regenerate goldens in the same PR, making
    output drift reviewable. Versioned priors and catalogs are JSON and ship to both
    implementations verbatim. See Phase 8.

    **Revision note (2026-06-29):** the original decision said "**not** a second
    parallel implementation (two implementations drift; a fork is the failure
    mode)" and that "the Python package becomes a shim." Reversed deliberately:
    some consumers are better served by **pure-Python** Tonality (no native
    toolchain — agents, notebooks, scriptability, and the MCP live-signature
    introspection a pure C++ port would *lose*), so Python is kept first-class. The
    drift fear that motivated "not parallel" is now mitigated by machinery that
    didn't exist in June: (a) the **conformance golden is CI for both** — neither
    can ship a parity-breaking change, so a golden-anchored pair can't drift
    silently (the failure mode was an *unanchored* fork); (b) **port-by-stability**
    bounds the dual surface to the frozen core — the churning analysis layer lives
    in Python only until it freezes, so no two copies of moving code; (c) **Python
    remains the spec's source of truth** (the golden is generated from it), so a
    disagreement has a defined arbiter, not a fork.
    *Consumer-port corollary (2026-06-13, ruled from TERRANE brief-3 —
    its VST3/AU JUCE plugin can ship neither CPython nor a sidecar):*
    **a consumer MAY maintain a faithful native port of the subset it
    uses, in the interim before the Phase 8 shared core exists** — bounded
    by two contracts so it is sanctioned interim, not a drift-prone fork.
    (1) *Versioned data + documented algorithm:* the port computes the same
    answers from the same versioned data, citing the same version strings.
    Key profiles (`kk-1982.1`) are already portable JSON; the table-driven
    functions (DFT/set-class/prime-form, the `doubling.1` pairing) are
    deterministic algorithms over the 4096 mask-space, documented in their
    docstrings — ported by reimplementation, optionally against a generated
    precomputed-table artifact if a consumer wants pure data. (2) *Parity
    is mechanically checkable, not trust-based:* the **golden conformance
    harness is the oracle for consumer ports too** — a port is faithful iff
    it reproduces the relevant golden cases (within the same tolerances).
    The *destination* still removes the fork entirely: when the Phase 8 C++
    core lands, consumers **link it** rather than maintaining a port. TERRANE
    is the recorded motivating native consumer (four functions: weighted key
    induction, `voice_leading_realized`, `dft_magnitudes` evenness, chord
    identity/naming; all at harmonic-event rate, never audio-rate). A
    **stable-schema versioned-data export** (priors + a generated set-class/
    DFT table artifact) is the concrete deliverable this implies — recorded
    in Phase 8.
11. **Contracts as object code — Tonality is the compiler for real-time
    consumers.** (Decided 2026-07-03 with Julian, from the A8 AURICLE RFC.)
    Real-time clients (VST/JUCE class) cannot call Python and must be
    deterministic; without a Tonality-owned artifact format each grows its own
    dialect — the Audiology divergence repeated per consumer. So Tonality owns
    **compiled contract formats**: versioned, schema-validated, deterministic
    JSON artifacts that freeze theory decisions for consumption without any
    runtime dependency (first instance: the harmony contract, gap 16).
    Analysis/authoring stays in Tonality; clients get a frozen, diffable,
    version-controlled document; the plural/ranked/evidenced discipline
    travels in the artifact as a provenance block runtimes ignore. This
    *complements* Decision 10, not competes: contracts serve consumers whose
    harmonic material is decided ahead of time; the C++ core serves consumers
    who need the engine live.
    **Scope rule (recorded with this decision, Julian 2026-07-03):** add to
    Tonality anything that may benefit **multiple clients** in the future,
    provided it doesn't break the cardinal rules. Generative capabilities are
    in scope under this rule *as* generative — explicitly labeled, never
    disguised as analysis (the groove-apply precedent; applied first to
    voicing enumeration, gap 17).

*Efficiency & realtime-fitness — planned audit + the multithreading frame (added
2026-07-08 with Julian; **first pass shipped same day** — `benchmarks/`,
`baseline-2026-07-08.md`: freezability CLEAN, slowest tool 6.3 ms, contract
artifacts sub-KB / µs-load — all green, nothing to act on).* The realtime contract
is already **Decisions 10 + 11**:
a real-time consumer never calls the engine on its hot path — it either reads a
**frozen contract artifact** (Decision 11) or embeds the **C++ core** (Decision
10). So the engine's own target is **offline / interactive** latency, not the
audio thread; "realtime-safe" here means *freezable, small, fast to load, cheap
to read* — not "fast on the audio callback." A periodic **computational
efficiency audit** (a group effort, sibling to the capability audit loop) is
planned to hold that standard: measure (a) no core reads wall-clock or hides
global mutable state that would bar freezing/reproducibility, (b) contract-artifact
freeze size + load cost (e.g. the 2–6 KB transition-matrix target), (c) per-tool
interactive latency, (d) allocation on the read/`sample` path. Division of labor:
the dev loop keeps hot paths engine-free and results freezable; the **tonality-core
port** owns low-latency in-process throughput (GIL-free, vectorizable); each
consumer owns its own audio thread. The RE-5 series (caching, single-sweep,
branchless mask ops) is the existing lineage this audit extends.
  **Multithreading — where it fits, and where it doesn't.** *Determinism is the
  hard constraint:* any parallelism must yield byte-identical output regardless of
  thread scheduling (the conformance golden + reproducibility), so only
  **embarrassingly-parallel map + canonical-order reduce** — no shared mutable
  state, no race-ordered output. *CPython reality:* the GIL bars CPU-bound thread
  speedup, so true parallelism needs **multiprocessing** or the **C++ port
  releasing the GIL**; pure-Python threads help only I/O-bound concurrency (the
  MCP/bridge serving concurrent requests). *Where it pays (offline/batch only):*
  the **per-piece corpus map** — `induce_ruleset`, `build_transition_matrix`,
  `segment_to_chords`, and dataset ingestion all loop independently over pieces, so
  corpus-scale processing parallelizes cleanly behind a deterministic reduce; and
  the **exhaustive search enumeration** (`search_identities` / `search_voicings`
  over the 4096-identity universe / bounded register windows). *Where it does NOT
  belong:* the identity-layer cores (bitmask / DFT / prime-form ops are
  microseconds — thread dispatch dominates; **vectorization + the C++ port** are
  the lever there), and any realtime consumer thread (barred by Decisions 10/11
  regardless). Net: multithreading is a **batch-harness** concern (offline corpus
  throughput), not a core or realtime one — and the audit should **measure before
  building** (a parallel map pays only when per-piece work ≫ dispatch overhead).

12. **Containment granularity follows universe granularity (constraint search).**
    (Decided 2026-07-07 building `search_identities`.) In the default
    **set-class** universe, `contains`/`contained_in` fold inversions — a shape
    and its mirror are the same set class, so a rooted-shape test against Rahn's
    (arbitrarily-handed) prime form would be ill-posed for chiral sets. In the
    **rooted** universe (`expand_transpositions`/`all_masks`) they are strictly
    transpositional: `[0,4,7]` means the major triad, not the minor. Corollary:
    *signed* chirality is not a set-class field — only `is_achiral` (a genuine
    T/I-invariant) is; handedness-sensitive search awaits the register-aware
    `search_voicings` slice. The rule is teachable and keeps every field a true
    invariant of the universe it is queried in.
13. **`ScaleAnalysisResult.step_pattern` is a transposition-invariant SHAPE
    descriptor, not a tonic-relative field.** (Decided 2026-07-13 resolving audit
    issue #205; the field was buggy — anchored at the numerically-smallest pc, so
    neither invariant nor tonic-anchored.) It is the lexicographically-minimal
    rotation of the cyclic ascending-step sequence — identical across all 12
    transpositions, a sibling of `interval_vector`. The supplied `tonic_pc` does
    **not** rotate it; the tonic-relative reading is `degrees`, and each mode's
    root-anchored ascending pattern lives in the `modes` list. Chosen over
    anchoring at `tonic_pc` because it is robust for the common no-tonic call,
    avoids the tonic-not-in-scale edge case, and matches the field's placement
    beside `interval_vector`. (`_ascending_steps` stays the root-anchored helper
    the modal rotations use.)
14. **Spine decoding (Viterbi-style DP over ranked hearings) is engine-owned
    analysis — CLAIMED.** (Decided 2026-07-13 answering Wend harmonize-mode brief
    `spine-oracle-surface`, ask 1.) The apparent "analysis vs. consumer policy"
    dichotomy is false: the **exact optimal path under a stated cost model is a
    measurement** (a Viterbi DP has one answer), while the **inertia λ that shapes
    the cost model is a policy knob**. So the engine owns the *mechanism* (the
    deterministic DP + emission costs from windowed key/chord hearing + transition
    costs from circle-of-fifths / voice-leading distance it already computes),
    **λ is a caller argument with a versioned default** (`spine_decode.1`-class,
    the kk-1982.1 pattern), and the decode is **plural-preserving** — it returns
    the committed path *and* the per-cell ranked alternatives + margins (rule 7),
    so one primitive serves both a harmonizer (high λ, read the path) and an
    analysis display (low λ, read the flicker). Engine-owned because it is the hard
    combinatorics (rule 3) and because a per-consumer decode would give Wend /
    Audiology / the live device three *different* hearings — engine-owned means one
    canonical hearing all inherit, and one port parity target. Precedent:
    `reduce_to_structural_keys` already commits to key areas, so committing-to-a-
    hearing is already within remit; the DP decode is its principled generalization
    (explicit transition model, tunable inertia, chord- as well as key-level). It is
    a temporal-analysis primitive on the Phase 3.5 induction stack (registered
    below), not yet scheduled; Wend builds behind a `SpineDecoder` seam and swaps
    the delegate when the engine ships the canonical decode.
15. **The learned-manifold engine is a SIBLING, not a Tonality layer — Tonality is
    its featurizer, instrument, and oracle.** (Decided 2026-07-14, from Julian's
    question: *are rules probability-gated — can I say "parallel fifths ≤ 5% of the
    time"?* — and the correct intuition behind it, that real style is a web of
    interdependent soft constraints too nuanced to enumerate prescriptively, whose
    right tool is a system that **derives** them in a high-dimensional space.)
    - **The line is an epistemic KIND, not a topic.** Tonality exists to be exact,
      inspectable, reproducible (the arithmetic LLMs are bad at; deterministic
      cores; seeded RNG; versioned priors you can read). A trained high-dimensional
      model is the opposite kind — **opaque, continuous, non-reproducible across
      training runs, non-inspectable.** Hosting one *inside* Tonality would dissolve
      the very property that makes it trustworthy as a foundation, and would couple
      a fast-churning research artifact to a stable library.
    - **The boundary is NOT learned-vs-not-learned.** Tonality *already learns* —
      `induce_ruleset` mines rules from a corpus, `build_transition_matrix` fits
      distributions, `build_style_profile` bundles them. Every one produces a
      **transparent, versioned, deterministic artifact** (a rule you can read, a
      matrix you can sample). **Transparent learned artifacts stay here; opaque
      learned manifolds go to the sibling.** That is the whole rule.
    - **They are complementary, not competing** (the payoff): a learned model cannot
      learn "avoid parallel fifths at rate X" without an exact parallel-fifth
      detector to compute the feature. Tonality supplies the **coordinates of the
      high-dimensional space** — interval vectors, VL distances, conformance rates,
      transition probabilities, texture atoms, pattern occurrences — and the sibling
      learns the manifold *in those coordinates*. So Tonality is that engine's
      **featurizer** (its inputs), **measurement instrument** (what did the model
      actually do? — measure it against explicit rules), **ground-truth oracle**
      (deterministic gates it is graded against), and **stimulus generator**
      (rule-conforming vs violating material for preference testing).
    - **Integration** is the normal boundary protocol (INTEGRATIONS): the sibling
      consumes Tonality's exact outputs as features; anything it returns comes back
      as a **versioned learned prior / a plural, ranked, evidenced signal** — never
      silently collapsed, never a hidden default (Decision 7 discipline applies to a
      learned prior exactly as to `kk-1982.1`). Precedent: **Wont** is already the
      statistical/preference sibling of this shape.
    - **What this decision does NOT do:** it does not bar statistical work here.
      Induction, distributions, style profiles, and the budget rule (gap 23) all
      stay — they are the transparent end of learning. Seeded as
      `integrations/style-manifold/seed.md` (name provisional); the engine's
      architecture and feasibility remain **open research**, and only its
      *placement* is decided here.
16. **The decisions register lives in `DECISIONS.md`, not inside ROADMAP.**
    (Decided 2026-08-18, kit 2.4.1 retrofit; the `autonomous` resident argued
    it and the human ratified.) An append-only record housed inside the
    most-edited file in the repo sits in the blast radius of every restructure
    of that file — ROADMAP is 4710 lines of phase state, standing reviews and
    parked work, and the register is immutable by contract. Splitting them puts
    the immutable thing somewhere immutable. "Single source of truth" in
    CLAUDE.md was always a claim about *plans* (ROADMAP outranks other docs on
    direction), never a claim that ROADMAP contains every artifact — the
    doctrine tenet it derives from names ROADMAP and DECISIONS in one breath.
    Rejected alternatives: a pointer file that satisfies the kit's presence
    check while the discipline lives elsewhere (the declared-vs-effective
    failure the kit exists to end — if the check were wrong, the honest move
    would be to change the check); and pointer-plus-append-going-forward, which
    reads as a transition but is a permanent split-brain — every future lookup
    would need to know the cutoff number before knowing which file to open, and
    the reader this repo optimizes for is a fresh-context agent who does not.
    The move was executed as a **verified move, not a copy-paste**: the
    extracted body was diffed byte-for-byte against what left ROADMAP, and the
    entry count was checked identical on both sides.
