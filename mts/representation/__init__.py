"""Representation layer (Phase 5): projections as data.

The engine emits **typed, render-agnostic descriptions** of musical objects
in their canonical representations; rendering to pixels/files/sound is a
thin edge consumer, never part of core (Decision: library-first, no in-repo
GUI). Every descriptor declares the specification level it consumed and
makes register-less projections explicit rather than inventing register —
the lattice's "reduce, never invent" applied to views.

Descriptors are numeric/structural only: no note names, no labels, no
colors — spelling and styling live at the display edge, per the standing
contract with consumers (A6 Audiology is this layer's primary customer).
"""

from .keyboard import KeyboardDescriptor, KeyboardKey, keyboard_descriptor
from .piano_roll import (
    ChordRegionOverlay,
    KeyBand,
    NoteRect,
    PianoRollDescriptor,
    piano_roll_descriptor,
)
from .bracelet import (
    BraceletAxis,
    BraceletDescriptor,
    BraceletPosition,
    bracelet_descriptor,
)
from .tonnetz import (
    TonnetzDescriptor,
    TonnetzEdge,
    TonnetzNode,
    tonnetz_descriptor,
)
from .chord_network import (
    ChordNetwork,
    ChordNetworkEdge,
    ChordNetworkNode,
    chord_network_descriptor,
)

__all__ = [
    "KeyboardDescriptor",
    "KeyboardKey",
    "keyboard_descriptor",
    "ChordRegionOverlay",
    "KeyBand",
    "NoteRect",
    "PianoRollDescriptor",
    "piano_roll_descriptor",
    "BraceletAxis",
    "BraceletDescriptor",
    "BraceletPosition",
    "bracelet_descriptor",
    "TonnetzDescriptor",
    "TonnetzEdge",
    "TonnetzNode",
    "tonnetz_descriptor",
    "ChordNetwork",
    "ChordNetworkEdge",
    "ChordNetworkNode",
    "chord_network_descriptor",
]
