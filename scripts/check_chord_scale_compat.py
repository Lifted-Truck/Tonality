"""Explore chord-scale diatonic compatibility using pitch-class bitmasks."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_scales, load_chord_qualities
from mts.core.bitmask import mask_from_pcs, is_subset


def chord_mask(intervals: tuple[int, ...]) -> int:
    """Return bitmask for a rootless chord (root at 0)."""
    pcs = [(iv % 12) for iv in intervals]
    return mask_from_pcs(pcs)


def main() -> None:
    scales = load_scales()
    qualities = load_chord_qualities()

    # Precompute chord masks (rootless, major root assumed)
    quality_masks = {
        name: chord_mask(q.intervals)
        for name, q in qualities.items()
    }

    for scale_name, scale in sorted(scales.items()):
        scale_mask = scale.mask
        compatible = []
        borrowed = []
        for name, qmask in quality_masks.items():
            if is_subset(qmask, scale_mask):
                compatible.append(name)
            else:
                borrowed.append(name)

        print(f"\nScale: {scale_name}")
        print(f"  Compatible ({len(compatible)}): {', '.join(sorted(compatible))}")
        print(f"  Non-diatonic ({len(borrowed)}): {', '.join(sorted(borrowed))}")


if __name__ == "__main__":
    main()
