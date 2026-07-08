# benchmarks — the computational efficiency audit (Layer-E)

The **efficiency audit**: a periodic, non-blocking measurement of the engine's
computational fitness. Sibling to the capability audit loop (`audit/`), but about
*speed and freezability* rather than *correctness*.

## The standard it holds

Per ROADMAP **Decisions 10 & 11**, the engine is **never on a consumer's audio
thread**. A real-time consumer either reads a **frozen contract artifact** or
embeds the **C++ core**; Tonality itself targets **offline / interactive**
latency. So "realtime-fitness" here means the outputs are **freezable,
reproducible, small, and fast to load** — not "fast on the audio callback."

## Layer-E, not Layer-0

These are **measured, non-blocking** (Layer-E) — they are *not* in `tests/` and
never gate CI. Timing is machine-specific and noisy; treat the numbers as a
**relative / regression** signal, not an absolute threshold. (The one exception
is `freezability.py`, which is deterministic and a **candidate to promote** into
`tests/` as a guaranteed invariant — see below.)

## The checks

| Script | What it measures | Blocking-worthy? |
|---|---|---|
| `freezability.py` | static scan: no wall-clock / unseeded RNG in the pure layers (the invariant that makes outputs freezable + reproducible) | **promoted 2026-07-08 → CI gate** at `tests/test_freezability.py`; this script is now a report that reuses the test's scan |
| `latency.py` | per-MCP-tool call latency over the conformance workload, slowest-first | no (machine-specific) |
| `artifacts.py` | contract-artifact serialized size + load round-trip cost | no (machine-specific) |

## Running

```bash
.venv/bin/python3.13 benchmarks/freezability.py     # exit != 0 on a finding
.venv/bin/python3.13 benchmarks/latency.py [runs]   # default 9 runs, min-of-N
.venv/bin/python3.13 benchmarks/artifacts.py
```

`latency.py` reuses the conformance `CASES` as its workload — the same
representative, deterministic tool inputs the golden pins, so the benchmark set
stays maintained for free and matches what consumers actually call.

## Baselines

Each pass is recorded as `baseline-YYYY-MM-DD.md` (machine-stamped). Compare a new
run against the latest baseline to spot regressions; write a fresh baseline when
the surface changes materially.

## Where parallelism fits (recorded in ROADMAP)

Determinism-preserving **map + canonical-order reduce**, **offline/batch only**:
the per-piece corpus map (`induce_ruleset` / `build_transition_matrix` /
`segment_to_chords` / ingestion) and the exhaustive search enumeration. **Not**
in the microsecond identity cores (vectorization + the C++ port are the lever),
**not** on any realtime thread. The GIL means true CPU parallelism needs
multiprocessing or the C++ port. **Measure here before building it.**
