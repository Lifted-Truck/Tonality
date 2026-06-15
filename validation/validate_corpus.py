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
import json
import sys
import tempfile
from dataclasses import dataclass, field
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
def analyze(midi_path: str, *, coalesce: float | None, disambiguate: bool, smooth: bool) -> dict:
    """Call the engine. Corpus scores are quantized, so coalesce defaults off."""
    from mts.mcp import tools  # noqa: PLC0415 - lazy so --help works without mts
    return tools.midi_file_analysis(
        midi_path,
        coalesce_window_beats=coalesce,
        disambiguate_relative_keys=disambiguate,
        smooth_key_regions=smooth,
    )


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


def analyze_piece(folder: Path, *, coalesce, disambiguate, smooth) -> tuple[GroundTruth, dict] | None:
    gt = load_ground_truth(folder)
    if gt is None:
        return None
    midi = render_midi(folder / "score.mxl")
    try:
        result = analyze(midi, coalesce=coalesce, disambiguate=disambiguate, smooth=smooth)
    finally:
        Path(midi).unlink(missing_ok=True)
    return gt, result


def run(corpus_dir: Path, *, limit, coalesce, disambiguate, smooth) -> Report:
    report = Report()
    for i, folder in enumerate(iter_when_in_rome(corpus_dir)):
        if limit is not None and i >= limit:
            break
        try:
            got = analyze_piece(folder, coalesce=coalesce, disambiguate=disambiguate, smooth=smooth)
            if got is None:
                continue
            ps = score_piece(*got)
            report.pieces.append(ps)
            tag = {"exact": "OK  ", "relative": "~rel", "wrong": "MISS"}[ps.bucket]
            ag = f"{ps.region_frame_agreement:.0%}" if ps.region_frame_agreement is not None else "—"
            print(f"[{tag}] {ps.piece:<38} gt={ps.gt_global:<9} engine={ps.engine_global:<9} regions={ag}")
        except Exception as exc:  # a single bad piece shouldn't abort the sweep
            print(f"[ERR ] {folder.name}: {type(exc).__name__}: {exc}", file=sys.stderr)
    return report


def run_ab_disambiguate(corpus_dir: Path, *, limit, coalesce, smooth) -> dict:
    """Finding-B instrument (response-4 §2c): analyze each piece with the relative-
    key tie-breaker OFF and ON; report the exact-rate delta. The tie-breaker earns
    its place iff it converts `relative` → `exact` without regressing → `wrong`."""
    off, on = Report(), Report()
    for i, folder in enumerate(iter_when_in_rome(corpus_dir)):
        if limit is not None and i >= limit:
            break
        try:
            gt = load_ground_truth(folder)
            if gt is None:
                continue
            midi = render_midi(folder / "score.mxl")
            try:
                r_off = analyze(midi, coalesce=coalesce, disambiguate=False, smooth=smooth)
                r_on = analyze(midi, coalesce=coalesce, disambiguate=True, smooth=smooth)
            finally:
                Path(midi).unlink(missing_ok=True)
            p_off, p_on = score_piece(gt, r_off), score_piece(gt, r_on)
            off.pieces.append(p_off)
            on.pieces.append(p_on)
            if p_off.bucket != p_on.bucket:
                print(f"[Δ] {gt.piece:<38} {p_off.bucket} → {p_on.bucket}")
        except Exception as exc:
            print(f"[ERR ] {folder.name}: {type(exc).__name__}: {exc}", file=sys.stderr)
    s_off, s_on = off.summary(), on.summary()
    delta = None
    if s_off.get("global_key") and s_on.get("global_key"):
        delta = round(s_on["global_key"]["exact"] - s_off["global_key"]["exact"], 3)
    return {"disambiguate_off": s_off, "disambiguate_on": s_on, "exact_rate_delta": delta}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Tonality key analysis vs an annotated corpus.")
    ap.add_argument("--corpus", required=True, type=Path, help="When-in-Rome corpus dir (folders with score.mxl + analysis.txt)")
    ap.add_argument("--limit", type=int, default=None, help="cap the number of pieces")
    ap.add_argument("--coalesce", type=float, default=None, help="coalesce window in beats (corpus scores are quantized → leave off)")
    ap.add_argument("--disambiguate", action="store_true", help="enable disambiguate_relative_keys")
    ap.add_argument("--smooth", action="store_true", help="enable smooth_key_regions")
    ap.add_argument("--ab-disambiguate", action="store_true", help="run each piece with the tie-breaker off AND on; report the exact-rate delta (Finding B)")
    ap.add_argument("--json", type=Path, default=None, help="write the full report as JSON")
    args = ap.parse_args(argv)

    try:
        import music21  # noqa: F401
    except ImportError:
        print("music21 is required: pip install music21", file=sys.stderr)
        return 2

    if args.ab_disambiguate:
        out = run_ab_disambiguate(args.corpus, limit=args.limit, coalesce=args.coalesce, smooth=args.smooth)
        print("\n== A/B disambiguate_relative_keys ==")
        print(json.dumps(out, indent=2))
        if args.json:
            args.json.write_text(json.dumps(out, indent=2))
        return 0

    report = run(args.corpus, limit=args.limit, coalesce=args.coalesce, disambiguate=args.disambiguate, smooth=args.smooth)
    summary = report.summary()
    print("\n== summary ==")
    print(json.dumps(summary, indent=2))
    if args.json:
        args.json.write_text(json.dumps({"summary": summary, "pieces": [p.__dict__ for p in report.pieces]}, indent=2))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
