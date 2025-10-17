from __future__ import annotations

import sys
from pathlib import Path

# ensure parent directory (project root) is in path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from mts.io.loaders import load_scales, load_chord_qualities
from mts.core.chord import Chord
from mts.layouts.push_grid import PushGrid

def show(title: str, grid: PushGrid) -> None:
    print("\n" + title)
    for line in grid.render_lines():
        print(line)

def main() -> None:
    scales = load_scales()
    qualities = load_chord_qualities()
    ionian = scales["Ionian"]

    # Context: key of C Ionian, chord Cmaj7
    chord = Chord.from_quality(0, qualities["maj7"])
    chord_pcs = list(chord.pcs)

    # 1) Chromatic, fixed C, Fourths, names
    g1 = PushGrid(preset="fourths", anchor="fixed_C",
                  tonic_pc=0, scale_degrees_rel=list(ionian.degrees),
                  chord_pcs_abs=chord_pcs,
                  layout_mode="chromatic", hide_out_of_key=False,
                  degree_style="names", spelling="auto")
    show("Chromatic • Fixed C • Fourths • Names", g1)

    # 2) In-scale, fixed_root, degrees (flats), hide OOK
    g2 = PushGrid(preset="fourths", anchor="fixed_root", root_pc=0,
                  tonic_pc=0, scale_degrees_rel=list(ionian.degrees),
                  chord_pcs_abs=chord_pcs,
                  layout_mode="in_scale", hide_out_of_key=True,
                  degree_style="degrees", spelling="flats")
    show("In-Scale • Fixed Root • Fourths • Degrees (flats) • Hidden OOK", g2)

    # 3) Try other presets
    for preset in ("thirds", "sequential"):
        g3 = PushGrid(preset=preset, anchor="fixed_C",
                      tonic_pc=0, scale_degrees_rel=list(ionian.degrees),
                      chord_pcs_abs=chord_pcs,
                      layout_mode="chromatic", degree_style="names")
        show(f"Chromatic • Fixed C • {preset.title()} • Names", g3)

if __name__ == "__main__":
    main()
