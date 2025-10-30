"""Dynamic functional harmony templates and generator."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from ..core.bitmask import is_subset, mask_from_pcs
from ..core.quality import ChordQuality
from ..core.scale import Scale

# ---------------------------------------------------------------------------
# Feature flags controlling optional variants

FEATURE_DIATONIC = "diatonic"
FEATURE_SIXTH_CHORDS = "sixth_chords"
FEATURE_ADDED_TONES = "added_tones"
FEATURE_SUSPENDED = "suspended"
FEATURE_POWER_DYADS = "power_dyads"
FEATURE_EXTENDED = "extended"
FEATURE_LYDIAN_EXTENSIONS = "lydian_extensions"
FEATURE_ALTERED_DOMINANT = "altered_dominant"
FEATURE_LEADING_TONE = "leading_tone"
FEATURE_RAISED_SIXTH = "raised_sixth"
FEATURE_PARALLEL_MAJOR = "parallel_major"
FEATURE_PARALLEL_MINOR = "parallel_minor"

TAG_BORROWABLE = "borrowable"
TAG_BORROWED = "borrowed"
TAG_MODAL_MIX = "modal_mix"
TAG_HARMONIC_MINOR = "harmonic_minor"
TAG_MELODIC_MINOR = "melodic_minor"
TAG_SUBTONIC = "subtonic"
TAG_OMIT_11 = "omit_11"
TAG_AVOID_3_OR_11 = "avoid_3_or_11"
TAG_TONIC_PROLONGATION = "tonic_prolongation"
TAG_MODAL = "modal"
TAG_SCALE_FORM_DEPENDENT = "scale_form_dependent"


@dataclass(frozen=True)
class FunctionVariant:
    """A concrete chord option for a functional slot."""

    quality: str
    modal_label: str
    role: str
    tags: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class FunctionTemplate:
    """Functional slot described relative to the tonic (degree in semitones)."""

    degree: int
    variants: tuple[FunctionVariant, ...]


@dataclass(frozen=True)
class GeneratedFunction:
    """Resolved mapping for a scale after applying template rules."""

    degree_pc: int
    chord_quality: str
    intervals: tuple[int, ...]
    role: str
    modal_label: str
    role_subtype: str | None = None
    tags: tuple[str, ...] = ()


def _variant(
    quality: str,
    modal_label: str,
    role: str,
    *,
    diatonic: bool,
    requires: Sequence[str] = (),
    extra_tags: Sequence[str] = (),
) -> FunctionVariant:
    tags = set(extra_tags)
    if diatonic:
        tags.add(FEATURE_DIATONIC)
    else:
        tags.add(TAG_BORROWABLE)
    return FunctionVariant(
        quality=quality,
        modal_label=modal_label,
        role=role,
        tags=tuple(sorted(tags)),
        requires=tuple(sorted(set(requires))),
    )


# --- Template definitions --------------------------------------------------

TEMPLATES_MAJOR: tuple[FunctionTemplate, ...] = (
    FunctionTemplate(
        degree=0,
        variants=(
            _variant("maj", "I", "tonic", diatonic=True),
            _variant(
                "maj6",
                "I6",
                "tonic",
                diatonic=True,
                requires=(FEATURE_SIXTH_CHORDS,),
                extra_tags=(FEATURE_SIXTH_CHORDS,),
            ),
            _variant(
                "majadd9",
                "Iadd9",
                "tonic",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES,),
            ),
            _variant(
                "maj6add9",
                "I6add9",
                "tonic",
                diatonic=True,
                requires=(FEATURE_SIXTH_CHORDS, FEATURE_ADDED_TONES),
                extra_tags=(FEATURE_SIXTH_CHORDS, FEATURE_ADDED_TONES),
            ),
            _variant(
                "maj7",
                "Imaj7",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "maj9",
                "Imaj9",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "maj13",
                "Imaj13",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "maj7#11",
                "Imaj7#11",
                "tonic",
                diatonic=False,
                requires=(FEATURE_LYDIAN_EXTENSIONS,),
                extra_tags=(FEATURE_LYDIAN_EXTENSIONS, FEATURE_EXTENDED),
            ),
            _variant(
                "power",
                "I5",
                "tonic",
                diatonic=True,
                requires=(FEATURE_POWER_DYADS,),
                extra_tags=(FEATURE_POWER_DYADS,),
            ),
        ),
    ),
    FunctionTemplate(
        degree=2,
        variants=(
            _variant("min", "ii", "predominant", diatonic=True),
            _variant("min7", "ii7", "predominant", diatonic=True),
            _variant(
                "min9",
                "ii9",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "min11",
                "ii11",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "min13",
                "ii13",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
        ),
    ),
    FunctionTemplate(
        degree=4,
        variants=(
            _variant("min", "iii", TAG_TONIC_PROLONGATION, diatonic=True),
            _variant("min7", "iii7", TAG_TONIC_PROLONGATION, diatonic=True),
            _variant(
                "min9",
                "iii9",
                TAG_TONIC_PROLONGATION,
                diatonic=False,
                requires=(FEATURE_LYDIAN_EXTENSIONS,),
                extra_tags=(FEATURE_LYDIAN_EXTENSIONS, FEATURE_EXTENDED),
            ),
        ),
    ),
    FunctionTemplate(
        degree=5,
        variants=(
            _variant("maj", "IV", "predominant", diatonic=True),
            _variant(
                "maj6",
                "IV6",
                "predominant",
                diatonic=True,
                requires=(FEATURE_SIXTH_CHORDS,),
                extra_tags=(FEATURE_SIXTH_CHORDS,),
            ),
            _variant(
                "majadd9",
                "IVadd9",
                "predominant",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES,),
            ),
            _variant(
                "maj6add9",
                "IV6add9",
                "predominant",
                diatonic=True,
                requires=(FEATURE_SIXTH_CHORDS, FEATURE_ADDED_TONES),
                extra_tags=(FEATURE_SIXTH_CHORDS, FEATURE_ADDED_TONES),
            ),
            _variant(
                "sus2",
                "IVsus2",
                "predominant",
                diatonic=True,
                requires=(FEATURE_SUSPENDED,),
                extra_tags=(FEATURE_SUSPENDED, TAG_MODAL_MIX),
            ),
            _variant(
                "sus4",
                "IVsus4",
                "predominant",
                diatonic=True,
                requires=(FEATURE_SUSPENDED,),
                extra_tags=(FEATURE_SUSPENDED,),
            ),
            _variant(
                "maj7",
                "IVmaj7",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "maj9",
                "IVmaj9",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "maj7#11",
                "IVmaj7#11",
                "predominant",
                diatonic=False,
                requires=(FEATURE_LYDIAN_EXTENSIONS,),
                extra_tags=(FEATURE_LYDIAN_EXTENSIONS, FEATURE_EXTENDED),
            ),
            _variant(
                "maj9#11",
                "IVmaj9#11",
                "predominant",
                diatonic=False,
                requires=(FEATURE_LYDIAN_EXTENSIONS,),
                extra_tags=(FEATURE_LYDIAN_EXTENSIONS, FEATURE_EXTENDED),
            ),
        ),
    ),
    FunctionTemplate(
        degree=7,
        variants=(
            _variant("maj", "V", "dominant", diatonic=True),
            _variant("7", "V7", "dominant", diatonic=True),
            _variant(
                "7sus4",
                "V7sus4",
                "dominant",
                diatonic=True,
                requires=(FEATURE_SUSPENDED,),
                extra_tags=(FEATURE_SUSPENDED,),
            ),
            _variant(
                "9",
                "V9",
                "dominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "11",
                "V11",
                "dominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED, TAG_AVOID_3_OR_11),
            ),
            _variant(
                "13",
                "V13",
                "dominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED, TAG_OMIT_11),
            ),
            _variant(
                "7b5",
                "V7b5",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT,),
                extra_tags=(FEATURE_ALTERED_DOMINANT,),
            ),
            _variant(
                "7#5",
                "V7#5",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT,),
                extra_tags=(FEATURE_ALTERED_DOMINANT,),
            ),
            _variant(
                "7b9",
                "V7b9",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT,),
                extra_tags=(FEATURE_ALTERED_DOMINANT,),
            ),
            _variant(
                "7#9",
                "V7#9",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT,),
                extra_tags=(FEATURE_ALTERED_DOMINANT,),
            ),
            _variant(
                "7#11",
                "V7#11",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LYDIAN_EXTENSIONS,),
                extra_tags=(FEATURE_LYDIAN_EXTENSIONS, FEATURE_EXTENDED),
            ),
            _variant(
                "9b5",
                "V9b5",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT,),
                extra_tags=(FEATURE_ALTERED_DOMINANT, FEATURE_EXTENDED),
            ),
            _variant(
                "9#5",
                "V9#5",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT,),
                extra_tags=(FEATURE_ALTERED_DOMINANT, FEATURE_EXTENDED),
            ),
            _variant(
                "7alt",
                "Valt",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT,),
                extra_tags=(FEATURE_ALTERED_DOMINANT,),
            ),
        ),
    ),
    FunctionTemplate(
        degree=9,
        variants=(
            _variant("min", "vi", "tonic", diatonic=True),
            _variant("min7", "vi7", "tonic", diatonic=True),
            _variant(
                "minadd9",
                "viadd9",
                "tonic",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES,),
            ),
            _variant(
                "min9",
                "vi9",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "min11",
                "vi11",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "min6",
                "vi6",
                "tonic",
                diatonic=False,
                requires=(FEATURE_LYDIAN_EXTENSIONS,),
                extra_tags=(FEATURE_SIXTH_CHORDS, FEATURE_LYDIAN_EXTENSIONS),
            ),
            _variant(
                "min13",
                "vi13",
                "tonic",
                diatonic=False,
                requires=(FEATURE_LYDIAN_EXTENSIONS,),
                extra_tags=(FEATURE_LYDIAN_EXTENSIONS, FEATURE_EXTENDED),
            ),
        ),
    ),
    FunctionTemplate(
        degree=11,
        variants=(
            _variant("dim", "viidim", "dominant", diatonic=True),
            _variant("min7b5", "viiø7", "dominant", diatonic=True),
            _variant(
                "dim7",
                "viidim7",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE,),
                extra_tags=(FEATURE_LEADING_TONE,),
            ),
        ),
    ),
)

TEMPLATES_MINOR: tuple[FunctionTemplate, ...] = (
    FunctionTemplate(
        degree=0,
        variants=(
            _variant("min", "i", "tonic", diatonic=True),
            _variant(
                "minadd9",
                "iadd9",
                "tonic",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES,),
            ),
            _variant(
                "min6",
                "i6",
                "tonic",
                diatonic=False,
                requires=(FEATURE_RAISED_SIXTH,),
                extra_tags=(FEATURE_SIXTH_CHORDS, FEATURE_RAISED_SIXTH, TAG_MELODIC_MINOR),
            ),
            _variant(
                "min6add9",
                "i6add9",
                "tonic",
                diatonic=False,
                requires=(FEATURE_RAISED_SIXTH, FEATURE_ADDED_TONES),
                extra_tags=(FEATURE_SIXTH_CHORDS, FEATURE_ADDED_TONES, FEATURE_RAISED_SIXTH, TAG_MELODIC_MINOR),
            ),
            _variant("min7", "i7", "tonic", diatonic=True),
            _variant(
                "min9",
                "i9",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED, TAG_SCALE_FORM_DEPENDENT),
            ),
            _variant(
                "min11",
                "i11",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED, TAG_SCALE_FORM_DEPENDENT),
            ),
            _variant(
                "min13",
                "i13",
                "tonic",
                diatonic=False,
                requires=(FEATURE_RAISED_SIXTH,),
                extra_tags=(FEATURE_RAISED_SIXTH, FEATURE_EXTENDED, TAG_MELODIC_MINOR),
            ),
            _variant(
                "minmaj7",
                "imaj7",
                "tonic",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE,),
                extra_tags=(FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
            _variant(
                "power",
                "i5",
                "tonic",
                diatonic=True,
                requires=(FEATURE_POWER_DYADS,),
                extra_tags=(FEATURE_POWER_DYADS,),
            ),
        ),
    ),
    FunctionTemplate(
        degree=2,
        variants=(
            _variant("dim", "iidim", "predominant", diatonic=True),
            _variant("min7b5", "iiø7", "predominant", diatonic=True),
            _variant(
                "dim7",
                "iidim7",
                "predominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE,),
                extra_tags=(FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
        ),
    ),
    FunctionTemplate(
        degree=3,
        variants=(
            _variant("maj", "bIII", "tonic", diatonic=True),
            _variant(
                "majadd9",
                "bIIIadd9",
                "tonic",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES,),
            ),
            _variant(
                "maj6",
                "bIII6",
                "tonic",
                diatonic=True,
                requires=(FEATURE_SIXTH_CHORDS,),
                extra_tags=(FEATURE_SIXTH_CHORDS,),
            ),
            _variant(
                "maj7",
                "bIIImaj7",
                "tonic",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "maj9",
                "bIIImaj9",
                "tonic",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_EXTENDED, FEATURE_ADDED_TONES),
            ),
        ),
    ),
    FunctionTemplate(
        degree=5,
        variants=(
            _variant("min", "iv", "predominant", diatonic=True),
            _variant(
                "minadd9",
                "ivadd9",
                "predominant",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES, TAG_MELODIC_MINOR),
            ),
            _variant(
                "min6",
                "iv6",
                "predominant",
                diatonic=True,
                requires=(FEATURE_SIXTH_CHORDS,),
                extra_tags=(FEATURE_SIXTH_CHORDS, TAG_MODAL),
            ),
            _variant("min7", "iv7", "predominant", diatonic=True),
            _variant(
                "min9",
                "iv9",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED, TAG_SCALE_FORM_DEPENDENT),
            ),
            _variant(
                "min11",
                "iv11",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED, TAG_SCALE_FORM_DEPENDENT),
            ),
            _variant(
                "min13",
                "iv13",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED, TAG_SCALE_FORM_DEPENDENT),
            ),
        ),
    ),
    FunctionTemplate(
        degree=7,
        variants=(
            _variant("min", "v", "dominant", diatonic=True, extra_tags=(TAG_MODAL,)),
            _variant("min7", "v7", "dominant", diatonic=True, extra_tags=(TAG_MODAL,)),
            _variant(
                "7",
                "V7",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE,),
                extra_tags=(FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
            _variant(
                "9",
                "V9",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE, FEATURE_RAISED_SIXTH),
                extra_tags=(FEATURE_LEADING_TONE, FEATURE_RAISED_SIXTH, FEATURE_EXTENDED, TAG_HARMONIC_MINOR, TAG_MELODIC_MINOR),
            ),
            _variant(
                "11",
                "V11",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE, FEATURE_RAISED_SIXTH),
                extra_tags=(FEATURE_LEADING_TONE, FEATURE_RAISED_SIXTH, FEATURE_EXTENDED, TAG_HARMONIC_MINOR, TAG_MELODIC_MINOR),
            ),
            _variant(
                "13",
                "V13",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE, FEATURE_RAISED_SIXTH),
                extra_tags=(FEATURE_LEADING_TONE, FEATURE_RAISED_SIXTH, FEATURE_EXTENDED, TAG_HARMONIC_MINOR, TAG_MELODIC_MINOR),
            ),
            _variant(
                "7b9",
                "V7b9",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT, FEATURE_LEADING_TONE),
                extra_tags=(FEATURE_ALTERED_DOMINANT, FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
            _variant(
                "7#9",
                "V7#9",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT, FEATURE_LEADING_TONE),
                extra_tags=(FEATURE_ALTERED_DOMINANT, FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
            _variant(
                "7alt",
                "Valt",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ALTERED_DOMINANT, FEATURE_LEADING_TONE),
                extra_tags=(FEATURE_ALTERED_DOMINANT, FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
        ),
    ),
    FunctionTemplate(
        degree=8,
        variants=(
            _variant("maj", "bVI", "predominant", diatonic=True),
            _variant(
                "majadd9",
                "bVIadd9",
                "predominant",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES,),
            ),
            _variant(
                "maj6",
                "bVI6",
                "predominant",
                diatonic=True,
                requires=(FEATURE_SIXTH_CHORDS,),
                extra_tags=(FEATURE_SIXTH_CHORDS,),
            ),
            _variant(
                "maj7",
                "bVImaj7",
                "predominant",
                diatonic=True,
                extra_tags=(FEATURE_EXTENDED,),
            ),
            _variant(
                "maj9",
                "bVImaj9",
                "predominant",
                diatonic=True,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_EXTENDED, FEATURE_ADDED_TONES),
            ),
        ),
    ),
    FunctionTemplate(
        degree=10,
        variants=(
            _variant(
                "maj",
                "bVII",
                "dominant",
                diatonic=False,
                requires=(FEATURE_PARALLEL_MAJOR,),
                extra_tags=(FEATURE_PARALLEL_MAJOR, TAG_SUBTONIC),
            ),
            _variant(
                "majadd9",
                "bVIIadd9",
                "dominant",
                diatonic=False,
                requires=(FEATURE_ADDED_TONES,),
                extra_tags=(FEATURE_ADDED_TONES, FEATURE_PARALLEL_MAJOR, TAG_SUBTONIC),
            ),
            _variant(
                "7sus4",
                "bVII7sus4",
                "dominant",
                diatonic=False,
                requires=(FEATURE_SUSPENDED,),
                extra_tags=(FEATURE_SUSPENDED, FEATURE_PARALLEL_MAJOR, TAG_SUBTONIC),
            ),
            _variant(
                "7",
                "bVII7",
                "dominant",
                diatonic=False,
                requires=(FEATURE_PARALLEL_MAJOR,),
                extra_tags=(FEATURE_PARALLEL_MAJOR, TAG_SUBTONIC),
            ),
            _variant(
                "9",
                "bVII9",
                "dominant",
                diatonic=False,
                requires=(FEATURE_PARALLEL_MAJOR,),
                extra_tags=(FEATURE_EXTENDED, FEATURE_PARALLEL_MAJOR, TAG_SUBTONIC),
            ),
            _variant(
                "13",
                "bVII13",
                "dominant",
                diatonic=False,
                requires=(FEATURE_PARALLEL_MAJOR,),
                extra_tags=(FEATURE_EXTENDED, FEATURE_PARALLEL_MAJOR, TAG_SUBTONIC),
            ),
        ),
    ),
    FunctionTemplate(
        degree=11,
        variants=(
            _variant(
                "dim",
                "viidim",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE,),
                extra_tags=(FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
            _variant(
                "min7b5",
                "viiø7",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE,),
                extra_tags=(FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
            _variant(
                "dim7",
                "viidim7",
                "dominant",
                diatonic=False,
                requires=(FEATURE_LEADING_TONE,),
                extra_tags=(FEATURE_LEADING_TONE, TAG_HARMONIC_MINOR),
            ),
        ),
    ),
)

DEFAULT_FEATURES_MAJOR: frozenset[str] = frozenset(
    {
        FEATURE_DIATONIC,
        FEATURE_SIXTH_CHORDS,
        FEATURE_ADDED_TONES,
        FEATURE_SUSPENDED,
        FEATURE_EXTENDED,
    }
)

DEFAULT_FEATURES_MINOR: frozenset[str] = frozenset(
    {
        FEATURE_DIATONIC,
        FEATURE_ADDED_TONES,
        FEATURE_SUSPENDED,
        FEATURE_EXTENDED,
        FEATURE_LEADING_TONE,
        FEATURE_PARALLEL_MAJOR,
    }
)


def _filter_variants(variants: Sequence[FunctionVariant], enabled_features: set[str]) -> list[FunctionVariant]:
    usable: list[FunctionVariant] = []
    for variant in variants:
        required = set(variant.requires)
        if required.issubset(enabled_features):
            usable.append(variant)
    return usable


def _chord_pcs(degree_pc: int, intervals: Sequence[int]) -> tuple[int, ...]:
    pcs = { (degree_pc + iv) % 12 for iv in intervals }
    return tuple(sorted(pcs))


def generate_functions_for_scale(
    scale: Scale,
    chord_qualities: Mapping[str, ChordQuality],
    *,
    templates: Sequence[FunctionTemplate],
    enabled_features: Iterable[str],
    include_nondiatic: bool = True,
) -> list[GeneratedFunction]:
    """
    Build functional mappings for a scale using the supplied template collection.
    """
    feature_set = set(enabled_features)
    feature_set.add(FEATURE_DIATONIC)

    scale_mask = mask_from_pcs(scale.degrees)
    results: list[GeneratedFunction] = []

    for template in templates:
        for variant in _filter_variants(template.variants, feature_set):
            quality = chord_qualities.get(variant.quality)
            if quality is None:
                continue
            chord_pcs = _chord_pcs(template.degree % 12, quality.intervals)
            chord_mask = mask_from_pcs(chord_pcs)
            diatonic = is_subset(chord_mask, scale_mask)
            if not diatonic and not include_nondiatic:
                continue

            tags = set(variant.tags)
            if not diatonic:
                tags.discard(FEATURE_DIATONIC)
                tags.add(TAG_BORROWED)
            if TAG_MODAL_MIX in tags:
                tags.discard(FEATURE_DIATONIC)

            role_subtype = variant.role if variant.role == TAG_TONIC_PROLONGATION else None
            canonical_role = "tonic" if variant.role == TAG_TONIC_PROLONGATION else variant.role

            results.append(
                GeneratedFunction(
                    degree_pc=template.degree % 12,
                    chord_quality=variant.quality,
                    intervals=quality.intervals,
                    role=canonical_role,
                    modal_label=variant.modal_label,
                    role_subtype=role_subtype,
                    tags=tuple(sorted(tags)),
                )
            )

    return results
