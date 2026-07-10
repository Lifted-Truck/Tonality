"""Corpus exercise harness — rulesets + patterns over real open-source MIDI.

Runs the whole Phase 4.6 stack over a directory of MIDI files (default: the
vendored SWD smoke set — 5 Schubert Winterreise songs, CC BY, see
``validation/corpus/swd/ATTRIBUTION.md``) and emits one deterministic JSON
report:

- **per piece** — ingest → harmonic segmentation (inferred key, chord stream,
  unnameable-span count) → every **named ruleset** evaluated (harmony-family
  rules fed the segmented chords+key) → every **named pattern** matched (degree
  patterns fed the inferred key). Refusals and skipped voices are itemized,
  never silently dropped.
- **corpus level** — rule induction per note family over the pieces (pieces =
  files, the independence unit) + harmony induction over the segmented chord
  corpus; a degree-transition matrix built on all-but-one piece and scored on
  the held-out piece by **cross-entropy** (the held-out split is BY PIECE,
  sorted-name order, last held out — same music never straddles the split).

Layer-E per the oracle discipline: **measured, non-blocking** — this reports
what the engine does on real music; it asserts nothing aesthetic. The Layer-0
invariants (no-crash, determinism, honest refusals, induced-output validity)
live in ``tests/test_corpus_smoke.py`` and gate CI.

    .venv/bin/python3.13 validation/exercise_rules_patterns.py \
        [--corpus DIR] [--out report.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT_CORPUS = REPO / "validation" / "corpus" / "swd" / "01_RawData" / "score_midi"


def exercise_corpus(corpus_dir: Path) -> dict:
    """The full report for every ``*.mid`` under *corpus_dir* (sorted, deterministic)."""

    from mts.io.midi import sequence_from_midi_file
    from mts.patterns import find_pattern, list_named_patterns, load_named_pattern
    from mts.rules import (
        build_transition_matrix,
        evaluate,
        induce_ruleset,
        list_named_rulesets,
        load_named_ruleset,
        ruleset_to_payload,
        validation_errors,
    )
    from mts.temporal import segment_to_chords

    paths = sorted(corpus_dir.glob("*.mid"))
    if not paths:
        raise SystemExit(f"no .mid files under {corpus_dir}")

    rulesets = {name: load_named_ruleset(name) for name in list_named_rulesets()}
    patterns = {name: load_named_pattern(name) for name in list_named_patterns()}

    pieces: list[dict] = []
    sequences: list = []
    chord_corpus: list = []

    for path in paths:
        seq = sequence_from_midi_file(str(path))
        seg = segment_to_chords(seq)
        sequences.append(seq)
        chord_corpus.append((seg.chords, seg.key))

        ruleset_reports = {}
        for name, rs in rulesets.items():
            needs_chords = any(r.family == "harmony" for r in rs.rules)
            report = evaluate(
                rs, seq,
                chords=seg.chords if needs_chords else None,
                key=seg.key if needs_chords else None,
            )
            ruleset_reports[name] = {
                "hard_rules_hold": report.hard_rules_hold,
                "hard_violation_count": report.hard_violation_count,
                "soft_score": report.soft_score,
                # honest refusals, itemized — never silently skipped
                "not_applicable": {
                    r.rule_id: r.reason for r in report.results if not r.applicable
                },
            }

        pattern_reports = {}
        for name, pattern in patterns.items():
            matches = find_pattern(
                seq, pattern,
                key=seg.key if pattern.pitch_level == "degree" else None,
            )
            pattern_reports[name] = {
                "count": matches.count,
                "voices_skipped": list(matches.voices_skipped),
                "occurrence_beats": [o.start_beat for o in matches.occurrences],
            }

        pieces.append({
            "file": path.name,
            "events": len(seq.events),
            "voices": list(seq.voices()),
            "duration_beats": seq.duration_beats,
            "key": list(seg.key),
            "key_inferred": seg.key_inferred,
            "chords": len(seg.chords),
            "spans_unnameable": sum(1 for s in seg.spans if s.root_pc is None),
            "spans_total": len(seg.spans),
            "rulesets": ruleset_reports,
            "patterns": pattern_reports,
        })

    # --- corpus level ---------------------------------------------------------
    induction: dict = {}
    for family in ("melody", "rhythm", "voice_motion"):
        result = induce_ruleset(sequences, family=family)
        payload = ruleset_to_payload(result.ruleset) if result.ruleset.rules else None
        induction[family] = {
            "rules": len(result.ruleset.rules),
            "pieces": result.pieces,
            "exploratory": result.exploratory,
            "valid": (not validation_errors(payload)) if payload else None,
        }
    harmony_result = induce_ruleset(family="harmony", chord_corpus=chord_corpus)
    induction["harmony"] = {
        "rules": len(harmony_result.ruleset.rules),
        "pieces": harmony_result.pieces,
        "exploratory": harmony_result.exploratory,
        "valid": (
            not validation_errors(ruleset_to_payload(harmony_result.ruleset))
            if harmony_result.ruleset.rules else None
        ),
    }

    # held-out split BY PIECE (sorted order; last piece held out — response-2's
    # "the run/piece is the unit" applied to train/test partitioning).
    distribution: dict = {}
    if len(chord_corpus) >= 2:
        train, held = chord_corpus[:-1], chord_corpus[-1:]
        matrix = build_transition_matrix(train, state="degree", source=str(corpus_dir.name))
        ce = matrix.cross_entropy(held)
        distribution = {
            "train_pieces": len(train),
            "held_out_piece": pieces[-1]["file"],
            "states": list(matrix.states),
            "n_transitions": matrix.n_transitions,
            "cross_entropy_bits": ce.cross_entropy_bits,
            "perplexity": ce.perplexity,
            "scored_transitions": ce.scored_transitions,
            "oov_transitions": ce.oov_transitions,
        }

    return {
        "corpus": str(corpus_dir),
        "pieces": pieces,
        "induction": induction,
        "distribution": distribution,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    report = exercise_corpus(args.corpus)

    print(f"corpus: {report['corpus']}  ({len(report['pieces'])} pieces)\n")
    print(f"  {'piece':<24}{'key':>10}{'chords':>8}{'unnameable':>12}{'arch':>6}")
    for p in report["pieces"]:
        key = f"{p['key'][0]} {p['key'][1]}"
        arch = p["patterns"].get("arch-contour", {}).get("count", "-")
        print(f"  {p['file']:<24}{key:>10}{p['chords']:>8}"
              f"{p['spans_unnameable']:>7}/{p['spans_total']:<4}{arch:>6}")
    print("\n  induction (pieces = files; exploratory below the confirmatory floor):")
    for family, info in report["induction"].items():
        print(f"    {family:<14} rules={info['rules']:<4} exploratory={info['exploratory']}")
    if report["distribution"]:
        d = report["distribution"]
        perp = f"{d['perplexity']:.2f}" if d["perplexity"] is not None else "inf/None"
        print(f"\n  held-out ({d['held_out_piece']}): perplexity={perp} "
              f"scored={d['scored_transitions']} oov={d['oov_transitions']}")

    if args.out:
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
