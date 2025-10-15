# Tonality Music Theory Engine

This repository contains a minimal, extensible music theory engine ready for local experimentation.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
python examples/quickstart_engine_demo.py
```

The demo prints sample scale, chord, and layout information.

## Data files

All JSON seed data lives in the local `data/` directory inside this repository. When you clone the project or inspect it on disk, you will find files such as `data/functions_major.json` and `data/functions_minor.json` alongside the other resources that ship with the engine. They are not fetched remotely—everything you need is committed here so the demo can run without an internet connection.

## Functional defaults

The supplied functional-harmony tables use diatonic seventh chords to illustrate how dominant and modal tendencies appear when richer chord spellings are available. Both the major and minor collections share the same dominant entry (degree pitch class 7) because a V7 sonority resolves toward the tonic in either mode. You can freely extend or replace these entries to suit alternate harmonic vocabularies, including simple triads or mode-specific dominants.

## Next Steps

- Extend JSON data libraries with more intervals, scales, chords, and functional mappings.
- Integrate with a GUI or audio layer. # TODO: connect future front-end / audio components.
