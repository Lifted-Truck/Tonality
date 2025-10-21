"""Quickstart demo for the music theory engine."""

from __future__ import annotations

import sys
from pathlib import Path

# TODO: remove when package is installed in editable mode.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from mts.core.chord import Chord, chord_degree_labels, chord_in_scale
from mts.core.scale import Scale
from mts.io.loaders import load_chord_qualities, load_scales
from mts.layouts.push3 import Push3Layout


def print_scale_info(scale: Scale) -> None:
    print(f"Scale: {scale.name} degrees={list(scale.degrees)} symmetry_order={scale.symmetry_order}")


def print_chord_info(label: str, chord: Chord, ionian_mask: int, ionian_degrees: list[int]) -> None:
    spelled = chord.spelled()
    in_scale = chord_in_scale(chord, ionian_mask)
    degrees = chord_degree_labels(chord, scale_root_pc=0, scale_degrees=ionian_degrees)
    print(f"Chord {label}: spelled={spelled} in_C_Ionian={in_scale} degrees={degrees}")


def demo_push3_layout(row_offset: int, root_pc: int) -> None:
    layout = Push3Layout(row_offset=row_offset, root_pc=root_pc)
    grid = layout.grid()
    print("Push-3 layout (top-left 3 rows):")
    for row in grid[:3]:
        print(row)


def main() -> None:
    scales = load_scales()
    qualities = load_chord_qualities()

    ionian = scales["Ionian"]
    dorian = scales["Dorian"]

    print_scale_info(ionian)
    print_scale_info(dorian)

    cmaj7 = Chord.from_quality(0, qualities["maj7"])
    dmin7 = Chord.from_quality(2, qualities["min7"])
    g7 = Chord.from_quality(7, qualities["7"])

    ionian_degrees = list(ionian.degrees)
    for name, chord in [("Cmaj7", cmaj7), ("Dmin7", dmin7), ("G7", g7)]:
        print_chord_info(name, chord, ionian.mask, ionian_degrees)

    demo_push3_layout(row_offset=5, root_pc=0)


if __name__ == "__main__":
    main()
