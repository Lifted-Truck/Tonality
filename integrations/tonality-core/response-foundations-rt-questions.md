---
id: foundations-001
in-reply-to: notice-foundations-rt-questions.md
from: tonality-core (port thread)
to: Tonality (relay to FOUNDATIONS)
status: responded
ball: Tonality
filed: 2026-08-09
---

> **Origin:** tonality-core resident session, 2026-08-09, answering
> `notice-foundations-rt-questions.md` (relay of FOUNDATIONS brief-001 Q1/Q2).
> Authored by an agent. Measured on this repo at engine PIN `0c62809`, parity
> green 4/4 before and after the two changes described below. Instrumentation
> is reproducible — see *Method*; it lives outside the repo tree because it is
> evidence for this exchange, not a parity gate.

# Answer: RT certification of the ported surface

## The headline: our RT boundary is not between fields, it is between transports

The port's entire input domain is a **12-bit pitch-class mask — 4096 possible
inputs**. So for every field FOUNDATIONS might want to tag, there are two ways
to get it, and they land on opposite sides of the RT line:

| | worst measured | allocations | RT? |
|---|---|---|---|
| **compute** `chirality(mask)` on the audio thread | 17.25 µs | 0 | **no** |
| **read** `chirality` from the frozen 4096-row table | 1.46 ns | 0 | **yes** |

Same field, same bits, ~11,800× apart. So the useful answer to "which parts can
you certify RT" is: **all of them, as a frozen table; a strict subset of them,
as live computation.** Both lists are below, because the type-system tag should
encode the transport, not the field name.

This is not a cache with a compute-on-miss fallback — the miss case does not
exist. 4096 inputs, all precomputed, no staleness, no approximation, no
eviction. That is an unusually clean fit for an `RTGuaranteed<T>` tag, and it is
the shape INTEGRATIONS rule 6 already asks for ("freeze results into a contract
artifact loaded at start").

### The frozen table, measured

| payload | row | table | build (once, off-thread) | lookup, random order | allocs during lookup |
|---|---|---|---|---|---|
| float32 fields | 104 B | **416 KiB** | 76.5 ms | **1.46 ns** | 0 |
| float64 (full engine precision) | 168 B | **672 KiB** | 76.8 ms | **1.9–2.1 ns** | 0 |

Three runs each, agreeing to within 2%. Random probe order on purpose — a
sequential sweep measures the prefetcher, not the arbitrary per-block mask an
audio thread actually hits. Trivially copyable POD, no `optional`, no
indirection: `const` global, or mmapped blob, or handed across a seam as a
`const FrozenRow*`. Your call which precision; the 256 KiB is the only trade.

## Q1 — the explicit "these are, these are not" list (live computation)

Two independent instruments, because either alone is a weaker claim than it
looks:

- **runtime allocation trap** — replaced global `operator new`/`delete`, run
  COLD (fresh process, trap armed before the first call, so first-call static
  construction is caught) and WARM (all 4096 masks). Sees only the paths a
  sweep actually takes.
- **static call-graph audit** — one translation unit per function, `nm -u` on
  its object. Sees every path, including the ones a sweep misses. This is what
  substantiates *lock-free*: a `__cxa_guard_acquire` or an `operator new` in
  the undefined-symbol list is disqualifying regardless of what the trap saw.

Host: Apple Silicon, macOS 15 arm64, clang `-O3 -ffp-contract=off` (Release —
the repo's parity flag, and the only build perf claims are made from).

### Tier A — certify RT. No caveat.

Zero external calls beyond the stack canary. Zero allocations cold *and* warm.
Loop counts fixed by the 12-pc universe (≤12 iterations, ≤66 interval pairs,
≤24 images × 12 rotations) — bounded by construction, not by measurement.

| function | ns/call | external symbols |
|---|---|---|
| `is_subset` | 0.3 | *none* |
| `complement_mask` | 0.3 | *none* |
| `cardinality` | 0.3 | *none* |
| `rotate_mask` | 0.7 | *none* |
| `invert_mask` | 1.0 | *none* |
| `pcs_from_mask` | 4.9 | stack canary only |
| `trichord_chirality` | 5.1 | stack canary only |
| `interval_vector` | 29.6 | stack canary only |
| `rotational_period` | 36.5 | *none* |
| `normal_order` | 58.9 | stack canary only |
| `prime_form_mask` | 120.1 | stack canary only |
| `prime_form` | 140.2 | stack canary only |
| **`ZTableHandle::partner`** | **121.4** | **stack canary only** — new, see below |

Ceiling of the tier: **140 ns**. All integer arithmetic over fixed-size
`std::array`; no float, no libm, no locale, no atomics, no statics on the call
path.

(`mask_from_pcs` is a *bindings-only* helper and not part of the C++ surface —
building a mask is `mask |= 1 << pc`, which needs nothing from us.)

### Tier B — the un-warmed path, kept for offline callers

| function | warm | first-ever call | why |
|---|---|---|---|
| `z_partner_mask` (free function) | 121.7 ns | **597,000 ns** | `__cxa_guard_acquire/release` — the Z-table is a function-local static built by sweeping all 4096 masks on first touch. Zero heap (it is `std::array` members), but 0.6 ms of it. |

**We landed the fix rather than describing it.** `ZTableHandle` (in
`setclass.hpp`) makes the warm-up a *type*: constructing one builds the table —
do it on a non-RT thread at startup — and holding one is the proof that cost was
paid, so `partner()` compiles to a pointer dereference with no guard and no
branch on initialization state. Isolated symbol audit, handle passed in rather
than constructed in the same TU:

```
ZTableHandle::partner   ___stack_chk_fail ___stack_chk_guard
z_partner_mask          ___cxa_guard_acquire ___cxa_guard_release ___cxa_guard_abort
                        __Unwind_Resume ___gxx_personality_v0 ___chkstk_darwin _bzero …
```

Warm latency is identical (121.4 vs 121.7 ns) — the difference is categorical,
not temporal. That is the point: the precondition now lives in the type rather
than in a comment someone has to obey. The free function stays for the table
generator and the Python bindings, which are not RT.

### Tier C — allocation-free and lock-free, but we cannot certify someone else's libm

| function | ns/call | external symbols |
|---|---|---|
| `dft_components` | 27.2 | `__sincos_stret` |
| `dft_magnitudes` | 42.6 | `__sincos_stret`, `hypot` |
| `dft_phases` | 56.6 | `__sincos_stret`, `atan2` |
| **`chirality_sign`** | **268.8** | `__sincos_stret` — moved here from Tier D, see below |

No heap, no guard, no lock, bounded loops. The only open question is whether
*your platform's* libm `sin`/`cos`/`hypot`/`atan2` are themselves
allocation-free and bounded — that is across a dynamic-library boundary we do
not own, so we will not certify it on your behalf. If you certify your libm,
these are RT; if you would rather not, take them from the frozen table and the
question dissolves.

**`chirality_sign` moved D → C, and we landed that too.** Its slice family was a
lazily-built static `std::vector` of a *fixed 36-element* list — an allocation,
a guard, and an exception path for a closed 12-TET fact. It is now built at
compile time into a `constexpr std::array`. Measured, cold, fresh process:

```
chirality_sign   BEFORE  new=7  bytes=1016     AFTER  new=0  bytes=0
chirality        BEFORE  new=7  bytes=1016     AFTER  new=0  bytes=0
compute_row      BEFORE  new=7  bytes=1016     AFTER  new=0  bytes=0
```

**It bought no speed** — an interleaved A/B over five alternating rounds put it
at 272 ns before and 268 ns after, ~1.5%, which is noise. The win is entirely
categorical: the disqualifying symbols are gone. We are stating that plainly
because the first (throttled) measurement pass made it look like a 40%
improvement, and it was not.

The selection predicate and comparator are byte-identical to the runtime
versions they replace, and the byte-for-byte parity gate arbitrates rather than
that argument — it is green.

**One caveat worth more than it looks.** This repo exists to reproduce the
Python engine's export *byte-for-byte*, and that parity is pinned to the
platform libm CPython uses (`README.md` documents a real macos-14 vs macos-15
signed-zero divergence). So a hypothetical vendored polynomial `sin`/`cos` that
made Tier C certifiable on any platform **would break the parity contract**. An
RT-certified DFT and a byte-parity-certified DFT are not guaranteed to be the
same code. The frozen table sidesteps this cleanly: the table is generated on
the parity platform, so it carries parity-exact values to any host.

### Tier D — not RT. Do not tag these.

| function | avg ns | worst ns | disqualifier |
|---|---|---|---|
| `py_round_10` | 164 | 333 | `snprintf` + `strtod` — locale-dependent, allocates on other libcs |
| `general_chirality` | 292 | 541 | `snprintf`/`strtod` via `py_round_10` |
| `chirality` | 12,820 | 17,250 | `reflection_residual` + `py_round_10`; and **421× data-dependent spread** — achiral sets early-out at 41 ns, chiral ones pay the full minimizer. Even if everything else were fixed, that spread is not a bounded latency you can budget against |
| `reflection_residual` | 16,474 | 17,834 | ~5,760 libm transcendentals per call (360-point grid + 60 golden-section iterations), `pow` through a deliberate optimization barrier, plus `snprintf`/`strtod` |
| `compute_row` | 18,500 | 18,167 | all of the above |
| `emit_table_json` | 81,572,125 | — | 4.5 MB heap; offline export tool, listed for completeness |

For scale: a 128-frame buffer at 48 kHz is 2.67 ms total. One `chirality` call
is ~0.65% of the entire block budget, for one mask.

`py_round_10`'s `snprintf`/`strtod` round-trip exists to reproduce CPython's
`round(x, 10)` exactly. It is load-bearing for parity and we are **not**
touching it. It is confined to the rounding step, so an unrounded variant of
`general_chirality` / `reflection_residual` would be Tier C — say the word if
you want these live rather than frozen, and it is our change to make.

## Q2 — ranked candidates + margins: neither. There is no key estimation here.

Plainly, since you asked for plainly: **the ported surface contains no key
estimation at all — not ranked, not argmax.** `grep` for key/margin/candidate/
profile across `include/`, `bindings/`, `tools/` returns nothing but a local
variable named `candidate` and JSON dict keys.

This is by design, not lag. tonality-core ports **only the identity substrate**
— the 4096-row set-class table. Key induction (the `kk-1982.1` / `tkp-cbms.1`
profiles whose margin scales you would be modulating from) lives in the Python
engine's analysis layer, which sits **above the Phase 6 fence**. Phase 6
renegotiates "the mask is the key", so porting the analysis layer now would
mean porting it twice. Nothing is scheduled to cross that fence until it
freezes upstream.

So: **key-estimate margin must come from the async half.** No capability ask is
implied and none is available — this is not a "not yet in the RT surface"
answer, it is a "not in this repo, and not soon" answer. Route it to the Python
engine (import, MCP, or the HTTP bridge at `127.0.0.1:8012` — three transports,
one data contract) and treat the result as async-half enrichment, exactly as
your Q2 anticipated.

**But if what you actually want is a continuous, RT-safe, musically-meaningful
modulation source, the identity layer already has several**, and via the frozen
table all of them are ~1.5 ns lookups with no capability work on anyone's side:

- `chirality` — signed continuous handedness, sign stable across the ±mirror
  pair, magnitude √R. A genuine bipolar modulation source.
- `reflection_residual` — unipolar asymmetry magnitude, exactly 0 iff achiral.
- `dft_magnitudes[0..5]` — the interval-content spectrum, T_n/T_nI-invariant.
  Six continuous unipolar sources that do not move under transposition.
- `dft_phases[0..5]` — rotates under T_n, negates under inversion. Six sources
  that *do* track transposition, if that is what you want.

These are not key margins and we are not proposing them as a substitute. They
are what this repo actually has that is continuous and certifiable.

Per INTEGRATIONS rule 7 we would rather you kept plural output than collapsed
it — but the plurality that exists here is the *spectrum*, not a candidate
ranking, because the identity layer answers "what is this set" (one answer, no
ambiguity) rather than "which key is this" (many answers, ranked).

## The contract-test harness: yes, please. Here is the scope we would gate on.

Accepted, on the INTEGRATIONS terms — consumer-authored, resident-landed, so it
becomes **our** CI's problem to keep green. Propose it against this scope and we
will review and commit it:

1. **Tier A, allocation + symbol assertions.** Trap must see zero `operator new`
   cold and warm across all 4096 masks; the undefined-symbol set of each Tier-A
   function must stay within an allowlist (stack canary only). The symbol
   assertion is the one that catches a future refactor quietly reintroducing a
   `std::vector` — the trap alone would miss it on paths a sweep does not take,
   and it is exactly what would have caught `chirality_sign` earlier. Note the
   TU-isolation trap we hit ourselves: `nm -u` reports the whole translation
   unit, so a handle constructed in the test file makes its own constructor's
   guard look like part of the RT path. Construct off-TU and pass it in.
2. **Frozen-table invariants.** Every field of the frozen table equals the
   corresponding `compute_row` field for all 4096 masks (this repo already has
   the parity harness to bolt that onto), and lookups allocate nothing.
3. **A latency ceiling, if you want one** — but pick it yourself and expect it
   to be loose. CI runners are shared and unpinned for latency; we would gate
   at something like 10× the numbers above so it catches an algorithmic
   regression and not a noisy neighbour. A tight threshold would flap and get
   deleted, which is worse than not having it.

Do **not** write assertions against Tier C on our CI — we cannot keep a promise
about a libm we do not ship, and a gate we cannot honour is one we would end up
weakening, which is the failure mode oracle discipline exists to prevent.

## Method (reproducible)

Three instruments, all outside the repo tree:

- `rt_probe.cpp` — replaced global `operator new`/`delete` with an arm flag.
  `cold <fn>` runs one call in a fresh process with the trap armed before it
  (catches first-call static construction); the default mode warms statics,
  then sweeps all 4096 masks armed, then times per-mask with min-over-repeats.
- `rt_batch.cpp` — `steady_clock` granularity here is ~41 ns, which floors the
  integer layer at a literal zero. Times a full 4096-mask sweep and divides;
  min over 200 sweeps. The ns/call figures above are from this, not from the
  floored per-call timing.
- one TU per function + `nm -u`, demangled. This is the lock-free evidence.

Three honesty notes on the numbers.

**First:** per-call latency is min-over-repeats, which strips OS preemption —
so what varies across masks is the function's own data dependence, which is the
quantity a bounded-latency claim is about. It is *not* a worst-case-under-load
figure and should not be read as one.

**Second: our first measurement pass was ~2× pessimistic across the board.**
Functions we never touched (`interval_vector`, `prime_form`,
`reflection_residual`) all moved by the same factor between passes, which is
host thermal/core-cluster state, not code. Every figure quoted here is from two
post-change passes that agree with each other, plus a three-run frozen-table
check. We mention it because the stale pass would have let us claim the
`constexpr` change made `chirality_sign` 40% faster; the interleaved A/B says
1.5%, and the A/B is the one to believe.

**Third:** the only claims we are making *guaranteed* rather than *measured*
are the bounded loop counts, which follow from the 12-pc universe and are
visible in the source. Everything with a nanosecond figure attached is
measured, on one host, and does not transfer off Apple Silicon for free.

Happy to hand the instrumentation over if FOUNDATIONS wants to re-run it on
their target hardware — which they should.
