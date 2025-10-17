import sys
from pathlib import Path
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
    chord = Chord.from_quality(0, qualities["maj7"])
    chord_pcs = list(chord.pcs)

    # C Ionian, prefer flats for C? keep 'auto' but provide key_signature=0 (neutral)
    # Try setting key_signature=-1 (F major family) to see flats preferred.
    key_sig = 0  # change to -1 or +1 to see auto flats/sharps

    # 1) Chromatic, fixed C, Fourths, names, origin=lower
    g1 = PushGrid(
        preset="fourths", anchor="fixed_C", origin="lower",
        tonic_pc=0, scale_degrees_rel=list(ionian.degrees),
        chord_pcs_abs=chord_pcs,
        layout_mode="chromatic", hide_out_of_key=False,
        degree_style="names", spelling="auto",
        key_signature=key_sig,
    )
    show("Chromatic • Fixed C • Fourths • Names • Origin=lower", g1)

    # 2) In-scale, fixed_root, degrees (flats), hide OOK, origin=lower
    g2 = PushGrid(
        preset="fourths", anchor="fixed_root", root_pc=0, origin="lower",
        tonic_pc=0, scale_degrees_rel=list(ionian.degrees),
        chord_pcs_abs=chord_pcs,
        layout_mode="in_scale", hide_out_of_key=True,
        degree_style="degrees", spelling="flats",
        key_signature=-1,  # demonstrate flats bias
    )
    show("In-Scale • Fixed Root • Fourths • Degrees (flats) • Hidden OOK • Origin=lower", g2)

    # 3) Thirds and Sequential previews with origin=lower
    for preset in ("thirds", "sequential"):
        g3 = PushGrid(
            preset=preset, anchor="fixed_C", origin="lower",
            tonic_pc=0, scale_degrees_rel=list(ionian.degrees),
            chord_pcs_abs=chord_pcs,
            layout_mode="chromatic", degree_style="names",
            key_signature=key_sig,
        )
        show(f"Chromatic • Fixed C • {preset.title()} • Names • Origin=lower", g3)

if __name__ == "__main__":
    main()