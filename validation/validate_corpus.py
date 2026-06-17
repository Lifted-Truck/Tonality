#!/usr/bin/env python3
"""Validate Tonality's key analysis against an annotated symbolic corpus.

DRAFT SCAFFOLD (Audiology → Tonality, brief-4 / response-4). Runs
`midi_file_analysis` over pieces with *human-annotated* harmonic ground truth and
scores the engine's inferred global key + local key-region timeline against it —
turning brief-3's N=1 Bohemian hand-check into a repeatable accuracy number.

Corpus: **When-in-Rome** (github.com/MarkGotham/When-in-Rome) — each piece folder
has `score.mxl` (MusicXML) + `analysis.txt` (RomanText: key, modulations, RNs).
music21 parses both and renders MIDI, so there is NO sheet-music→MIDI step.

Aligned to Tonality's response-4 rulings:
  * 2d — **compare in beats, not seconds.** Engine regions carry `start_beats`,
    RomanText offsets are quarterLengths → exact alignment, no tempo conversion,
    no multi-tempo caveat. Seconds are kept only for human-readable output.
  * 2c — **three global-key buckets** (exact / relative / wrong); the Finding-B
    headline is the *exact-rate delta* with vs without `disambiguate_relative_keys`
    (`--ab-disambiguate` runs both and reports it).
  * 2a — `(tonic_pc, major|minor)` is the engine's output space; **modal passages
    are reduced to their relative major and flagged**, so the engine isn't charged
    a miss for reading them as that relative major/minor (a documented limitation).
  * 2b — **frame agreement is the headline**; boundary-tolerance is reported as a
    secondary (change-point) metric.

Home (response-4 §1): the canonical copy lands in Tonality's new `validation/`
dir; music21 is a `[validation]` optional extra, never a runtime dep.

Run (from the Tonality repo root):
    pip install 'mts[validation]'   # music21
    python validation/validate_corpus.py \
        --corpus /path/to/When-in-Rome/Corpus --limit 25 --ab-disambiguate
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SAMPLE_STEP_BEATS = 0.5     # frame grid for region agreement (engine boundaries
                            # sit on the window/hop grid — don't sample finer)
BOUNDARY_TOL_BEATS = 2.0    # ± window for the secondary change-point metric
# Church modes → semitone offset of the tonic above the parent (Ionian) major.
MODE_TO_MAJOR_OFFSET = {"dorian": 2, "phrygian": 4, "lydian": 5, "mixolydian": 7, "locrian": 11}


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
def analyze(midi_path: str, *, coalesce: float | None, disambiguate: bool, smooth: bool, structural: bool = False,
            anchor_method: str = "most_prevalent_region") -> dict:
    """Call the engine. Corpus scores are quantized, so coalesce defaults off.

    With `structural=True`, the windowed `key_regions` (a tonicization-sensitive
    local-fit) are replaced by the **structural key-area** reduction
    (`structural_keys` #43 / response-6) — the apples-to-apples target for
    analyst key-areas — so the existing scorer compares against the right object.
    The global key (for the bucket + baseline) stays from `midi_file_analysis`,
    so `anchor_method` (which only moves the structural home anchor) never shifts
    the global-key bucket — only the structural region timeline it scores."""
    from mts.mcp import tools  # noqa: PLC0415 - lazy so --help works without mts
    result = tools.midi_file_analysis(
        midi_path,
        coalesce_window_beats=coalesce,
        disambiguate_relative_keys=disambiguate,
        smooth_key_regions=smooth,
    )
    if structural:
        result["key_regions"] = {"regions": structural_regions(
            midi_path, disambiguate=disambiguate, smooth=smooth, anchor_method=anchor_method)}
    return result


def structural_regions(midi_path: str, *, disambiguate: bool, smooth: bool,
                       anchor_method: str = "most_prevalent_region") -> list[dict]:
    """Structural key-areas for a MIDI as region dicts (start_beats/end_beats/
    tonic_pc/mode) — `structural_keys` takes note events, so build them from the
    sequence. Tonicizations are absorbed (recorded on each area), not emitted.

    `anchor_method` picks the home-key rule: 'most_prevalent_region' (default,
    longest summed local duration) or 'frame_weighted' (brief-7 slice 2 — weights
    the opening + closing frames so a repeatedly-tonicized dominant can't out-total
    the tonic by duration). frame_anchor_bonus is theory-set (1.0) — do NOT tune it
    against SWD (the overfit fence stands even though SWD is license-clean)."""
    from mts.io.midi import sequence_from_midi_file  # noqa: PLC0415
    from mts.mcp import tools  # noqa: PLC0415
    seq = sequence_from_midi_file(midi_path)
    events = [[e.onset, e.duration, e.pitch.midi] for e in seq.events]
    res = tools.structural_keys(events, window_beats=8.0, hop_beats=2.0,
                                disambiguate_relative=disambiguate, smoothing=smooth,
                                anchor_method=anchor_method)
    return [
        {"start_beats": a["start_beats"], "end_beats": a["end_beats"], "tonic_pc": a["tonic_pc"], "mode": a["mode"]}
        for a in (res.get("areas") or [])
    ]


# --------------------------------------------------------------------------- #
# Ground truth (When-in-Rome via music21) — in BEATS
# --------------------------------------------------------------------------- #
@dataclass
class KeySpan:
    start_beat: float
    pc: int
    mode: str            # "major" | "minor"
    modal: bool = False  # true = a church mode reduced to its relative major


@dataclass
class GroundTruth:
    piece: str
    global_pc: int
    global_mode: str
    timeline: list[KeySpan]   # sorted by start_beat; first span = opening key
    duration_beats: float


def _key_to_pc_mode(k) -> tuple[int, str, bool]:
    """music21 Key -> (tonic_pc, mode∈{major,minor}, is_modal). The engine emits
    only major/minor (kk-1982.1), so a modal annotation is reduced to its parent
    relative major and flagged (response-4 §2a) — frames in a modal span aren't
    charged against the engine."""
    mode = str(k.mode)
    pc = k.tonic.pitchClass
    if mode in ("major", "ionian"):
        return pc, "major", False
    if mode in ("minor", "aeolian"):  # aeolian == natural minor == engine's minor
        return pc, "minor", False
    if mode in MODE_TO_MAJOR_OFFSET:
        return (pc - MODE_TO_MAJOR_OFFSET[mode]) % 12, "major", True
    return pc, "major", True  # unknown mode: reduce + flag


def load_ground_truth(folder: Path) -> GroundTruth | None:
    """Parse a When-in-Rome folder into a key timeline in *beats* (quarterLengths).
    No tempo handling — offsets are beats, and we compare against the engine's
    `*_beats`."""
    from music21 import converter

    analysis_path = folder / "analysis.txt"
    score_path = folder / "score.mxl"
    if not analysis_path.exists() or not score_path.exists():
        return None  # remote.json-only folders skipped for now

    rn = converter.parse(analysis_path, format="romanText")
    spans: list[KeySpan] = []
    last: tuple[int, str] | None = None
    for el in rn.recurse().getElementsByClass("RomanNumeral"):
        pc, mode, modal = _key_to_pc_mode(el.key)
        if (pc, mode) != last:
            try:
                off = float(el.getOffsetInHierarchy(rn))
            except Exception:
                off = float(el.offset)
            spans.append(KeySpan(off, pc, mode, modal))
            last = (pc, mode)
    if not spans:
        return None

    duration = float(converter.parse(score_path).highestTime)
    return GroundTruth(folder.name, spans[0].pc, spans[0].mode, spans, duration)


def render_midi(score_path: Path) -> str:
    from music21 import converter

    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
        out = tmp.name
    converter.parse(score_path).write("midi", fp=out)
    return out


def iter_when_in_rome(corpus_dir: Path):
    for analysis in sorted(corpus_dir.rglob("analysis.txt")):
        if (analysis.parent / "score.mxl").exists():
            yield analysis.parent


# --------------------------------------------------------------------------- #
# Ground truth (Schubert Winterreise Dataset — CC BY 3.0, license-clean)
# --------------------------------------------------------------------------- #
# SWD ships per-song MIDI + score-aligned annotations as `start;end;key` CSVs
# (local key ×3 annotators, chords, global key). Positions are 1-indexed
# *measures*; we convert to the engine's quarter-beat axis with a beats-per-bar
# read empirically off the engine's own bar/onset_beats records, so it matches
# the engine's convention without assuming a time-signature mapping. Single-meter
# songs only (constant beats-per-bar); a meter change would need a bar→beat map.
_NOTE_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _parse_pitch(tok: str) -> int:
    pc = _NOTE_PC[tok[0].upper()]
    for c in tok[1:]:
        pc += 1 if c == "#" else -1 if c in ("b", "-") else 0
    return pc % 12


def parse_swd_key(s: str) -> tuple[int, str, bool]:
    """'E:min' / 'D#:maj' -> (tonic_pc, mode∈{major,minor}, is_modal). Same modal
    reduction as the RomanText path (response-4 §2a)."""
    root, _, mode = s.strip().strip('"').partition(":")
    pc = _parse_pitch(root)
    m = mode.lower()
    if m.startswith("min") or m == "aeolian":
        return pc, "minor", False
    if m.startswith("maj") or m in ("ionian", ""):
        return pc, "major", False
    if m in MODE_TO_MAJOR_OFFSET:
        return (pc - MODE_TO_MAJOR_OFFSET[m]) % 12, "major", True
    return pc, "major", True


def beats_per_bar(result: dict) -> float | None:
    """Empirical quarter-beats per bar from the engine's records — measured across
    downbeat (beat≈1) segments so it's exact for a constant meter, whatever beat
    convention the engine uses."""
    recs = (result.get("dataset") or {}).get("records") or []
    downs = [
        (p["bar"], p["onset_beats"])
        for r in recs
        if (p := r.get("placement")) and p.get("bar") and p.get("onset_beats") is not None and abs(p.get("beat", 0) - 1.0) < 1e-6
    ]
    pts = downs if len(downs) >= 2 else [
        (p["bar"], p["onset_beats"]) for r in recs if (p := r.get("placement")) and p.get("bar") and p.get("onset_beats") is not None
    ]
    if len(pts) < 2 or pts[-1][0] == pts[0][0]:
        return None
    return (pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0])


def swd_cases(root: Path) -> list[dict]:
    ann = root / "02_Annotations"
    glob: dict[str, str] = {}
    with open(ann / "ann_score_globalkey.csv") as fh:
        for row in csv.reader(fh, delimiter=";"):
            if len(row) >= 2 and row[0].strip('"') != "WorkID":
                glob[row[0].strip('"')] = row[1]
    midi_dir = root / "01_RawData" / "score_midi"
    cases = []
    for lk in sorted((ann / "ann_score_localkey-ann1").glob("*.csv")):
        sid = lk.stem
        midi = midi_dir / f"{sid}.mid"
        if midi.exists() and sid in glob:
            cases.append({"id": sid, "midi": str(midi), "localkey": lk, "global": glob[sid]})
    return cases


def load_swd_ground_truth(case: dict, bpb: float) -> GroundTruth | None:
    with open(case["localkey"]) as fh:
        rows = [r for r in csv.reader(fh, delimiter=";") if len(r) >= 3 and r[0] != "start"]
    if not rows:
        return None
    spans = [KeySpan((float(s) - 1.0) * bpb, *parse_swd_key(k)) for s, _e, k in rows]
    gpc, gmode, _ = parse_swd_key(case["global"])
    duration = (float(rows[-1][1]) - 1.0) * bpb
    return GroundTruth(case["id"], gpc, gmode, spans, duration)


def analyze_swd_piece(case: dict, *, coalesce, disambiguate, smooth, structural=False,
                      anchor_method="most_prevalent_region") -> tuple[GroundTruth, dict] | None:
    result = analyze(case["midi"], coalesce=coalesce, disambiguate=disambiguate, smooth=smooth,
                     structural=structural, anchor_method=anchor_method)
    bpb = beats_per_bar(result)
    if bpb is None:
        return None
    gt = load_swd_ground_truth(case, bpb)
    return (gt, result) if gt else None


# --------------------------------------------------------------------------- #
# Comparison (response-4 §2)
# --------------------------------------------------------------------------- #
def is_relative(a: tuple[int, str], b: tuple[int, str]) -> bool:
    """C major <-> A minor: relative pairs share a diatonic collection."""
    (pa, ma), (pb, mb) = a, b
    if ma == mb:
        return False
    maj, minr = (a, b) if ma == "major" else (b, a)
    return minr[0] == (maj[0] - 3) % 12


def global_bucket(engine: tuple[int, str], truth: tuple[int, str]) -> str:
    if engine == truth:
        return "exact"
    if is_relative(engine, truth):
        return "relative"
    return "wrong"


def _key_at(spans: list[tuple[float, int, str]], t: float) -> tuple[int, str]:
    cur = (spans[0][1], spans[0][2])
    for s, pc, mode in spans:
        if s <= t:
            cur = (pc, mode)
        else:
            break
    return cur


def _modal_at(gt: GroundTruth, t: float) -> bool:
    cur = gt.timeline[0].modal
    for s in gt.timeline:
        if s.start_beat <= t:
            cur = s.modal
        else:
            break
    return cur


def engine_spans(result: dict) -> list[tuple[float, int, str]]:
    regions = ((result.get("key_regions") or {}).get("regions")) or []
    return [(r["start_beats"], r["tonic_pc"], r["mode"]) for r in regions]


@dataclass
class PieceScore:
    piece: str
    gt_global: str
    engine_global: str
    bucket: str                       # exact | relative | wrong
    region_frame_agreement: float | None
    global_baseline_agreement: float | None  # frames right if you just used the global key everywhere
    modal_frames: int
    boundary_recall: float | None     # secondary: GT modulations matched within ±tol
    gt_modulations: int
    engine_modulations: int


def score_piece(gt: GroundTruth, result: dict) -> PieceScore:
    eng_g = (result["key"]["candidates"][0]["tonic_pc"], result["key"]["candidates"][0]["mode"])
    gt_g = (gt.global_pc, gt.global_mode)

    e_spans = engine_spans(result)
    gt_spans = [(s.start_beat, s.pc, s.mode) for s in gt.timeline]

    agreement: float | None = None
    baseline: float | None = None
    modal_frames = 0
    if e_spans:
        dur = max(gt.duration_beats, e_spans[-1][0] + SAMPLE_STEP_BEATS)
        n = max(1, int(dur / SAMPLE_STEP_BEATS))
        hits = base_hits = denom = 0
        for i in range(n):
            t = i * SAMPLE_STEP_BEATS
            if _modal_at(gt, t):           # don't charge modal spans (§2a)
                modal_frames += 1
                continue
            denom += 1
            truth = _key_at(gt_spans, t)
            if _key_at(e_spans, t) == truth:
                hits += 1
            if eng_g == truth:             # baseline: ignore modulations, use the global key
                base_hits += 1
        agreement = hits / denom if denom else None
        baseline = base_hits / denom if denom else None

    # Secondary (§2b): change-point recall — each GT modulation onset matched by
    # an engine boundary within ±BOUNDARY_TOL_BEATS.
    boundary_recall: float | None = None
    gt_bounds = [s.start_beat for s in gt.timeline[1:]]
    if gt_bounds:
        e_bounds = [s[0] for s in e_spans[1:]]
        matched = sum(any(abs(g - e) <= BOUNDARY_TOL_BEATS for e in e_bounds) for g in gt_bounds)
        boundary_recall = matched / len(gt_bounds)

    return PieceScore(
        piece=gt.piece,
        gt_global=_name(*gt_g),
        engine_global=_name(*eng_g),
        bucket=global_bucket(eng_g, gt_g),
        region_frame_agreement=agreement,
        global_baseline_agreement=baseline,
        modal_frames=modal_frames,
        boundary_recall=boundary_recall,
        gt_modulations=len(gt_spans) - 1,
        engine_modulations=max(0, len(e_spans) - 1),
    )


def _name(pc: int, mode: str) -> str:
    return f"{PC_NAMES[pc]} {mode}"


# CONTRACT (phase 2, stub — response-4 §4): chord-level scoring of per-segment
# namings vs RomanText per-beat RNs. Needs onset alignment + RN ⇄ (root, quality)
# reconciliation against name_pcs conventions. A separate round.
def score_chords(gt_folder: Path, result: dict) -> dict:  # noqa: ARG001
    return {"status": "not_implemented"}


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #
@dataclass
class Report:
    pieces: list[PieceScore] = field(default_factory=list)

    def summary(self) -> dict:
        n = len(self.pieces)
        if not n:
            return {"pieces": 0}
        buckets = {b: sum(p.bucket == b for p in self.pieces) for b in ("exact", "relative", "wrong")}
        ag = [p.region_frame_agreement for p in self.pieces if p.region_frame_agreement is not None]
        bl = [p.global_baseline_agreement for p in self.pieces if p.global_baseline_agreement is not None]
        br = [p.boundary_recall for p in self.pieces if p.boundary_recall is not None]
        return {
            "pieces": n,
            "global_key": {k: round(v / n, 3) for k, v in buckets.items()},   # exact / relative / wrong
            "mean_region_frame_agreement": round(sum(ag) / len(ag), 3) if ag else None,
            "mean_global_baseline_agreement": round(sum(bl) / len(bl), 3) if bl else None,  # regions only "help" if above this
            "mean_boundary_recall": round(sum(br) / len(br), 3) if br else None,  # secondary
        }


def analyze_piece(folder: Path, *, coalesce, disambiguate, smooth, structural=False,
                  anchor_method="most_prevalent_region") -> tuple[GroundTruth, dict] | None:
    gt = load_ground_truth(folder)
    if gt is None:
        return None
    midi = render_midi(folder / "score.mxl")
    try:
        result = analyze(midi, coalesce=coalesce, disambiguate=disambiguate, smooth=smooth,
                         structural=structural, anchor_method=anchor_method)
    finally:
        Path(midi).unlink(missing_ok=True)
    return gt, result


# A "producer" is (label, fn) where fn(coalesce, disambiguate, smooth) -> (gt,
# result) | None. This is the corpus-agnostic seam: When-in-Rome and SWD differ
# only in how they produce that pair, so run()/the A/B don't care which corpus.
def wir_producers(corpus_dir: Path) -> list[tuple[str, object]]:
    return [(f.name, partial(analyze_piece, f)) for f in iter_when_in_rome(corpus_dir)]


def swd_producers(swd_root: Path) -> list[tuple[str, object]]:
    return [(c["id"], partial(analyze_swd_piece, c)) for c in swd_cases(swd_root)]


def run(producers, *, limit, coalesce, disambiguate, smooth, structural=False,
        anchor_method="most_prevalent_region") -> Report:
    report = Report()
    for i, (label, fn) in enumerate(producers):
        if limit is not None and i >= limit:
            break
        try:
            got = fn(coalesce=coalesce, disambiguate=disambiguate, smooth=smooth,
                     structural=structural, anchor_method=anchor_method)
            if got is None:
                continue
            ps = score_piece(*got)
            report.pieces.append(ps)
            tag = {"exact": "OK  ", "relative": "~rel", "wrong": "MISS"}[ps.bucket]
            ag = f"{ps.region_frame_agreement:.0%}" if ps.region_frame_agreement is not None else "—"
            print(f"[{tag}] {ps.piece:<38} gt={ps.gt_global:<9} engine={ps.engine_global:<9} regions={ag}")
        except Exception as exc:  # a single bad piece shouldn't abort the sweep
            print(f"[ERR ] {label}: {type(exc).__name__}: {exc}", file=sys.stderr)
    return report


def run_ab_disambiguate(producers, *, limit, coalesce, smooth, structural=False) -> dict:
    """Finding-B instrument (response-4 §2c): analyze each piece with the relative-
    key tie-breaker OFF and ON; report the exact-rate delta. The tie-breaker earns
    its place iff it converts `relative` → `exact` without regressing → `wrong`."""
    off, on = Report(), Report()
    for i, (label, fn) in enumerate(producers):
        if limit is not None and i >= limit:
            break
        try:
            got_off = fn(coalesce=coalesce, disambiguate=False, smooth=smooth, structural=structural)
            if got_off is None:
                continue
            got_on = fn(coalesce=coalesce, disambiguate=True, smooth=smooth, structural=structural)
            if got_on is None:
                continue
            p_off, p_on = score_piece(*got_off), score_piece(*got_on)
            off.pieces.append(p_off)
            on.pieces.append(p_on)
            if p_off.bucket != p_on.bucket:
                print(f"[Δ] {label}: {p_off.bucket} → {p_on.bucket}")
        except Exception as exc:
            print(f"[ERR ] {label}: {type(exc).__name__}: {exc}", file=sys.stderr)
    s_off, s_on = off.summary(), on.summary()
    delta = None
    if s_off.get("global_key") and s_on.get("global_key"):
        delta = round(s_on["global_key"]["exact"] - s_off["global_key"]["exact"], 3)
    return {"disambiguate_off": s_off, "disambiguate_on": s_on, "exact_rate_delta": delta}


def run_ab_anchor(producers, *, limit, coalesce, disambiguate, smooth) -> dict:
    """brief-7 slice-2 instrument: score each piece's structural reduction with the
    home anchor under `most_prevalent_region` (default) and `frame_weighted`, then
    ask Tonality's question — does frame_weighted lift region-frame agreement on the
    global-key-MISS subset (relative+wrong) WITHOUT regressing the correctly-anchored
    (exact) songs? The global key comes from midi_file_analysis (unchanged by the
    anchor), so the bucket is shared across A/B; only the structural timeline moves."""
    rows: list[dict] = []
    for i, (label, fn) in enumerate(producers):
        if limit is not None and i >= limit:
            break
        try:
            got_d = fn(coalesce=coalesce, disambiguate=disambiguate, smooth=smooth,
                       structural=True, anchor_method="most_prevalent_region")
            if got_d is None:
                continue
            got_f = fn(coalesce=coalesce, disambiguate=disambiguate, smooth=smooth,
                       structural=True, anchor_method="frame_weighted")
            if got_f is None:
                continue
            pd, pf = score_piece(*got_d), score_piece(*got_f)
            ad, af = pd.region_frame_agreement, pf.region_frame_agreement
            d = round(af - ad, 3) if (ad is not None and af is not None) else None
            rows.append({"piece": pd.piece, "bucket": pd.bucket, "gt_global": pd.gt_global,
                         "engine_global": pd.engine_global, "default": ad, "frame_weighted": af, "delta": d})
            flag = ""
            if d is not None and pd.bucket == "exact" and d < -0.001:
                flag = "  ⚠ REGRESSION (exact)"
            elif d is not None and pd.bucket in ("relative", "wrong") and d > 0.001:
                flag = "  ✔ recovery (miss)"
            ad_s = f"{ad:.0%}" if ad is not None else "—"
            af_s = f"{af:.0%}" if af is not None else "—"
            d_s = f"{d:+.0%}" if d is not None else "—"
            tag = {"exact": "OK  ", "relative": "~rel", "wrong": "MISS"}[pd.bucket]
            print(f"[{tag}] {pd.piece:<24} default={ad_s:>5} frame={af_s:>5} Δ={d_s:>5}{flag}")
        except Exception as exc:
            print(f"[ERR ] {label}: {type(exc).__name__}: {exc}", file=sys.stderr)

    def _mean(xs: list[float]) -> float | None:
        return round(sum(xs) / len(xs), 3) if xs else None

    def _subset(pred) -> dict:
        sub = [r for r in rows if pred(r) and r["default"] is not None and r["frame_weighted"] is not None]
        md, mf = _mean([r["default"] for r in sub]), _mean([r["frame_weighted"] for r in sub])
        return {
            "pieces": len(sub),
            "mean_region_default": md,
            "mean_region_frame_weighted": mf,
            "mean_delta": round(mf - md, 3) if (md is not None and mf is not None) else None,
            "regressions": sum(1 for r in sub if r["delta"] is not None and r["delta"] < -0.001),
            "improvements": sum(1 for r in sub if r["delta"] is not None and r["delta"] > 0.001),
        }

    return {
        "all": _subset(lambda r: True),
        "global_key_miss_subset": _subset(lambda r: r["bucket"] in ("relative", "wrong")),
        "correctly_anchored_subset": _subset(lambda r: r["bucket"] == "exact"),
        "pieces": rows,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Tonality key analysis vs an annotated corpus.")
    ap.add_argument("--corpus", type=Path, help="When-in-Rome corpus dir (folders with score.mxl + analysis.txt) — CC BY-SA, read-only scoring")
    ap.add_argument("--swd", type=Path, help="Schubert Winterreise Dataset root (CC BY 3.0 — license-clean for prior recalibration)")
    ap.add_argument("--limit", type=int, default=None, help="cap the number of pieces")
    ap.add_argument("--coalesce", type=float, default=None, help="coalesce window in beats (corpus scores are quantized → leave off)")
    ap.add_argument("--disambiguate", action="store_true", help="enable disambiguate_relative_keys")
    ap.add_argument("--smooth", action="store_true", help="enable smooth_key_regions")
    ap.add_argument("--structural", action="store_true", help="score the structural key-area reduction (structural_keys #43) instead of the windowed track — the apples-to-apples target for analyst key-areas")
    ap.add_argument("--ab-disambiguate", action="store_true", help="run each piece with the tie-breaker off AND on; report the exact-rate delta (Finding B)")
    ap.add_argument("--ab-anchor", action="store_true", help="structural-only: score the home anchor under most_prevalent_region AND frame_weighted; report region-agreement deltas split by global-key bucket (brief-7 slice 2)")
    ap.add_argument("--anchor-method", choices=("most_prevalent_region", "frame_weighted"), default="most_prevalent_region", help="structural home-anchor rule for a plain --structural run")
    ap.add_argument("--json", type=Path, default=None, help="write the full report as JSON")
    args = ap.parse_args(argv)

    if not args.corpus and not args.swd:
        ap.error("pass --corpus (When-in-Rome) or --swd (Schubert Winterreise)")

    try:
        import music21  # noqa: F401
    except ImportError:
        print("music21 is required: pip install 'mts[validation]'", file=sys.stderr)
        return 2

    producers = swd_producers(args.swd) if args.swd else wir_producers(args.corpus)

    if args.ab_disambiguate:
        out = run_ab_disambiguate(producers, limit=args.limit, coalesce=args.coalesce, smooth=args.smooth, structural=args.structural)
        print("\n== A/B disambiguate_relative_keys ==")
        print(json.dumps(out, indent=2))
        if args.json:
            args.json.write_text(json.dumps(out, indent=2))
        return 0

    if args.ab_anchor:
        out = run_ab_anchor(producers, limit=args.limit, coalesce=args.coalesce, disambiguate=args.disambiguate, smooth=args.smooth)
        print("\n== A/B anchor_method (most_prevalent_region vs frame_weighted) ==")
        print(json.dumps({k: v for k, v in out.items() if k != "pieces"}, indent=2))
        if args.json:
            args.json.write_text(json.dumps(out, indent=2))
            print(f"wrote {args.json}")
        return 0

    report = run(producers, limit=args.limit, coalesce=args.coalesce, disambiguate=args.disambiguate, smooth=args.smooth, structural=args.structural, anchor_method=args.anchor_method)
    summary = report.summary()
    print("\n== summary ==")
    print(json.dumps(summary, indent=2))
    if args.json:
        args.json.write_text(json.dumps({"summary": summary, "pieces": [p.__dict__ for p in report.pieces]}, indent=2))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
