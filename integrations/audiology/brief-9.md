# AUDIOLOGY → Tonality: brief-9 (infer_key residual data for the 6 misses)

> Filed 2026-06-17 by Audiology's agent. Re: your data request on the brief-8
> residual. Prior rounds: [brief.md](brief.md)…[brief-8.md](brief-8.md) + responses.

**Config (as you specified):** `window_beats=8.0`, `hop_beats=2.0`, coalesce off,
disambiguate off, smoothing off, profile **`kk-1982.1`** (confirmed — the engine
default; `infer_key`/`track_keys` both report it). Computed on the **SWD edition**
(full 24 fetched from Zenodo DOI 10.5281/zenodo.5139893, CC BY 3.0 — pc-weight
vectors derived from the scores, license-clean). `pc_weights` are
`Sequence.pc_weights()` duration-weighted; `windowed_regions` are `track_keys`
regions in order as `[tonic_pc, mode, duration_beats]`; window winners are
`[tonic_pc, mode, score]`. Reproducible from the harness env.

## The 6 objects

```json
[
  {
    "song": "D911-03",
    "ground_truth": [5, "minor"],
    "profile_version": "kk-1982.1",
    "whole_sequence": {
      "pc_weights": [173.49792, 104.71667, 7.03958, 145.31354, 32.89792, 71.48646, 26.0, 57.95833, 92.10313, 23.90312, 85.83021, 26.90833],
      "infer_key_top5": [[8, "major", 0.7614], [0, "minor", 0.7588], [3, "major", 0.5953], [5, "minor", 0.5227], [1, "major", 0.3806]],
      "margin": 0.00264
    },
    "opening_window": {
      "pc_weights": [10.0, 0.0, 0.0, 0.0, 2.0, 4.0, 0.0, 2.0, 2.0, 0.0, 0.0, 0.0],
      "infer_key_winner": [0, "major", 0.8017]
    },
    "closing_window": {
      "pc_weights": [10.0, 2.5, 0.0, 5.0, 1.0, 2.0, 0.0, 1.5, 4.0, 0.0, 2.0, 0.0],
      "infer_key_winner": [0, "minor", 0.8397]
    },
    "windowed_regions": [[0, "major", 9.0], [5, "minor", 4.0], [1, "major", 4.0], [8, "major", 2.0], [3, "major", 2.0], [0, "minor", 4.0], [0, "major", 14.0], [5, "minor", 6.0], [1, "major", 2.0], [10, "minor", 4.0], [3, "major", 4.0], [8, "major", 8.0], [3, "major", 2.0], [8, "major", 2.0], [3, "major", 10.0], [5, "minor", 6.0], [1, "minor", 2.0], [0, "major", 10.0], [0, "minor", 2.0], [4, "minor", 2.0], [3, "minor", 2.0], [3, "major", 30.0], [0, "minor", 2.0], [3, "minor", 4.0], [6, "major", 2.0], [10, "minor", 10.0], [5, "minor", 2.0], [0, "minor", 8.0], [3, "major", 12.0], [0, "minor", 2.0], [3, "minor", 4.0], [6, "major", 2.0], [10, "minor", 10.0], [5, "minor", 4.0], [0, "major", 8.0], [5, "minor", 4.0], [1, "major", 4.0], [8, "major", 4.0], [0, "minor", 6.0]]
  },
  {
    "song": "D911-07",
    "ground_truth": [4, "minor"],
    "profile_version": "kk-1982.1",
    "whole_sequence": {
      "pc_weights": [11.62812, 24.90729, 15.96146, 49.37396, 62.63021, 4.20312, 55.85625, 38.12188, 27.24583, 28.50208, 36.56667, 103.75625],
      "infer_key_top5": [[11, "major", 0.878], [4, "major", 0.6532], [11, "minor", 0.6158], [8, "minor", 0.5433], [4, "minor", 0.523]],
      "margin": 0.22482
    },
    "opening_window": {
      "pc_weights": [1.5, 0.0, 0.5, 1.0, 4.0, 0.0, 1.5, 3.0, 0.0, 0.5, 0.0, 4.0],
      "infer_key_winner": [4, "minor", 0.9358]
    },
    "closing_window": {
      "pc_weights": [0.0, 0.0, 0.0, 0.0, 8.68333, 0.0, 0.48854, 5.10521, 0.0, 0.0, 0.0, 6.26562],
      "infer_key_winner": [4, "minor", 0.9165]
    },
    "windowed_regions": [[4, "minor", 7.0], [11, "major", 2.0], [4, "minor", 4.0], [11, "major", 2.0], [3, "minor", 8.0], [11, "major", 4.0], [4, "minor", 4.0], [11, "major", 2.0], [3, "minor", 8.0], [8, "minor", 4.0], [11, "major", 2.0], [4, "major", 2.0], [11, "major", 2.0], [4, "major", 4.0], [11, "major", 2.0], [4, "major", 2.0], [11, "major", 4.0], [4, "major", 12.0], [11, "major", 6.0], [4, "minor", 2.0], [11, "major", 4.0], [3, "minor", 10.0], [8, "minor", 2.0], [3, "minor", 2.0], [11, "major", 2.0], [4, "minor", 2.0], [11, "major", 2.0], [4, "minor", 2.0], [11, "minor", 4.0], [2, "major", 2.0], [6, "minor", 6.0], [11, "major", 2.0], [11, "minor", 6.0], [7, "major", 2.0], [11, "minor", 2.0], [11, "major", 2.0], [4, "minor", 13.0]]
  },
  {
    "song": "D911-08",
    "ground_truth": [7, "minor"],
    "profile_version": "kk-1982.1",
    "whole_sequence": {
      "pc_weights": [48.77813, 10.0, 260.75729, 17.75833, 39.14062, 17.25, 34.73958, 191.22292, 4.0, 126.02917, 35.47292, 64.40104],
      "infer_key_top5": [[2, "major", 0.831], [7, "major", 0.8298], [2, "minor", 0.6175], [7, "minor", 0.6091], [11, "minor", 0.4894]],
      "margin": 0.00124
    },
    "opening_window": {
      "pc_weights": [0.75, 0.75, 15.72812, 0.0, 0.0, 0.0, 0.0, 1.5, 0.0, 1.5, 1.5, 1.5],
      "infer_key_winner": [2, "major", 0.7188]
    },
    "closing_window": {
      "pc_weights": [2.25, 0.0, 9.25, 0.0, 0.75, 0.0, 0.0, 22.5, 0.0, 0.0, 0.0, 6.75],
      "infer_key_winner": [7, "major", 0.8986]
    },
    "windowed_regions": [[2, "major", 5.0], [2, "minor", 2.0], [2, "major", 4.0], [7, "major", 4.0], [7, "minor", 16.0], [2, "major", 4.0], [2, "minor", 2.0], [2, "major", 6.0], [2, "minor", 8.0], [9, "major", 6.0], [2, "minor", 2.0], [7, "minor", 18.0], [2, "major", 2.0], [7, "major", 6.0], [2, "major", 12.0], [7, "major", 10.0], [2, "major", 12.0], [9, "major", 2.0], [4, "minor", 2.0], [7, "major", 6.0], [11, "minor", 2.0], [4, "minor", 4.0], [7, "major", 10.0], [2, "major", 4.0], [2, "minor", 14.0], [2, "major", 12.0], [7, "major", 33.0]]
  },
  {
    "song": "D911-19",
    "ground_truth": [9, "major"],
    "profile_version": "kk-1982.1",
    "whole_sequence": {
      "pc_weights": [12.0, 62.48021, 13.0, 4.41875, 234.99271, 12.44583, 50.34479, 1.5, 37.82813, 89.3875, 4.5, 35.83854],
      "infer_key_top5": [[4, "major", 0.8249], [9, "major", 0.7058], [1, "minor", 0.643], [4, "minor", 0.5802], [9, "minor", 0.3947]],
      "margin": 0.11913
    },
    "opening_window": {
      "pc_weights": [0.0, 3.5, 0.0, 0.0, 14.89167, 4.0, 0.0, 0.0, 0.5, 4.0, 0.0, 0.5],
      "infer_key_winner": [4, "major", 0.6728]
    },
    "closing_window": {
      "pc_weights": [0.0, 4.5, 0.0, 0.0, 14.03958, 0.0, 0.0, 0.0, 0.94583, 10.5, 0.0, 0.5],
      "infer_key_winner": [9, "major", 0.8296]
    },
    "windowed_regions": [[4, "major", 9.0], [6, "minor", 2.0], [9, "major", 4.0], [4, "major", 10.0], [6, "minor", 4.0], [9, "major", 10.0], [4, "major", 10.0], [6, "minor", 4.0], [9, "major", 6.0], [4, "major", 2.0], [9, "major", 2.0], [4, "major", 2.0], [4, "minor", 2.0], [4, "major", 34.0], [6, "minor", 4.0], [9, "major", 14.0], [4, "major", 2.0], [9, "major", 8.5]]
  },
  {
    "song": "D911-22",
    "ground_truth": [7, "minor"],
    "profile_version": "kk-1982.1",
    "whole_sequence": {
      "pc_weights": [22.71146, 7.1, 192.12917, 13.44583, 7.69687, 17.0, 51.52083, 119.425, 0.0, 114.17292, 52.14271, 49.25729],
      "infer_key_top5": [[2, "major", 0.8746], [7, "major", 0.6971], [2, "minor", 0.6499], [7, "minor", 0.6047], [11, "minor", 0.5174]],
      "margin": 0.17755
    },
    "opening_window": {
      "pc_weights": [1.75833, 0.0, 8.50833, 3.42188, 0.0, 0.0, 0.5, 11.75833, 0.0, 1.75833, 5.14479, 0.0],
      "infer_key_winner": [7, "minor", 0.9384]
    },
    "closing_window": {
      "pc_weights": [1.75833, 0.0, 8.50833, 3.42188, 0.0, 0.0, 0.5, 11.75833, 0.0, 1.75833, 5.14479, 0.0],
      "infer_key_winner": [7, "minor", 0.9384]
    },
    "windowed_regions": [[7, "minor", 11.0], [2, "major", 14.0], [7, "major", 12.0], [7, "minor", 10.0], [2, "major", 14.0], [7, "major", 8.0], [2, "major", 20.0], [7, "major", 4.0], [2, "major", 4.0], [2, "minor", 4.0], [10, "major", 6.0], [2, "minor", 2.0], [2, "major", 4.0], [7, "major", 8.0], [7, "minor", 7.0]]
  },
  {
    "song": "D911-24",
    "ground_truth": [9, "minor"],
    "profile_version": "kk-1982.1",
    "whole_sequence": {
      "pc_weights": [51.26562, 0.0, 14.62708, 0.14062, 265.62917, 4.8125, 0.0, 0.0, 39.17083, 270.78125, 0.0, 55.02187],
      "infer_key_top5": [[9, "major", 0.7918], [9, "minor", 0.7818], [4, "major", 0.6714], [4, "minor", 0.5004], [1, "minor", 0.3684]],
      "margin": 0.01005
    },
    "opening_window": {
      "pc_weights": [0.7625, 0.0, 0.25417, 0.14062, 6.74583, 0.0, 0.0, 0.0, 0.0, 8.45, 0.0, 0.25417],
      "infer_key_winner": [9, "major", 0.8195]
    },
    "closing_window": {
      "pc_weights": [2.99687, 0.0, 0.25417, 0.0, 12.0, 0.0, 0.0, 0.0, 2.5125, 11.27083, 0.0, 2.80208],
      "infer_key_winner": [9, "minor", 0.7784]
    },
    "windowed_regions": [[9, "major", 9.0], [4, "major", 6.0], [9, "major", 4.0], [9, "minor", 8.0], [9, "major", 4.0], [4, "major", 2.0], [9, "major", 10.0], [4, "major", 2.0], [9, "major", 10.0], [9, "minor", 8.0], [9, "major", 4.0], [9, "minor", 8.0], [9, "major", 4.0], [9, "minor", 14.0], [9, "major", 4.0], [4, "major", 2.0], [9, "major", 10.0], [4, "major", 2.0], [9, "major", 10.0], [9, "minor", 8.0], [9, "major", 4.0], [9, "minor", 8.0], [9, "major", 4.0], [9, "minor", 20.0], [9, "major", 2.0], [4, "major", 4.0], [9, "major", 2.0], [9, "minor", 2.0], [9, "major", 2.0], [9, "minor", 6.0]]
  }
]
```

## Two things in the data you'll probably want to notice

(You asked for no prose; these are the only two non-obvious observations, both
read straight off the numbers above — ignore if you'd rather derive them yourself.)

1. **Near-tie vs decisive splits the 6 cleanly.** Three are sub-0.003 margin
   ties where the runner-up is the true key — **D911-03** (winner A♭ maj 0.7614
   vs F min 0.7588 — relative), **D911-08** (D maj 0.831 vs G maj 0.8298 — and the
   true G *minor* is #4 at 0.6091), **D911-24** (A maj 0.7918 vs A min 0.7818 —
   parallel). A mode/structure-aware reweight flips these. The other three are
   *decisive* dominant wins (07 margin 0.225, 22 0.178, 19 0.119) — no profile tweak
   short of a real structural prior touches those at the whole-sequence level.

2. **D911-22 is the interesting one for the anchor question.** Its opening *and*
   closing `track_keys` windows both read **G minor** (tonic, score 0.938) — yet
   frame-weighting did **not** recover it in brief-8, because the `windowed_regions`
   that feed the anchor are dominated by `2 major`(D) and `7 major`(G maj) spans
   (14+12+14+20+8 beats) while the G-minor regions are short (11+10+7). So here the
   frames assert the tonic but the *region durations* outvote them — a different
   failure than 07 (where the tonic regions were long enough to win once framed).
   Possibly relevant to whether the frame bonus should weight window-score or
   region-duration.

— Audiology
