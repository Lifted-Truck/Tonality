import pytest

from mts.io.loaders import load_chord_qualities, load_scales
from mts.analysis import compare_chord_qualities


@pytest.fixture(scope="module")
def _catalogs():
    return load_chord_qualities(), load_scales()


def test_compare_chord_qualities_shared_scale(_catalogs):
    qualities, scales = _catalogs
    comp = compare_chord_qualities(qualities["maj7"], qualities["maj9"], catalog_scales=scales)

    assert comp.intervals_only_a == ()
    assert comp.intervals_only_b == (2,)

    shared_names = {placement.scale for placement in comp.shared_scales}
    assert "Ionian" in shared_names

    ionian = next(placement for placement in comp.shared_scales if placement.scale == "Ionian")
    assert ionian.degree_map_a[0] == ["I", "III", "V", "VII"]
    assert ionian.degree_map_b[0] == ["I", "II", "III", "V", "VII"]


def test_compare_chord_qualities_scale_filter(_catalogs):
    qualities, scales = _catalogs
    comp = compare_chord_qualities(
        qualities["maj7"],
        qualities["maj9"],
        catalog_scales=scales,
        include_scales=["Ionian"],
    )
    assert len(comp.shared_scales) == 1
    assert comp.shared_scales[0].scale == "Ionian"
