# Tonality Music Theory Engine

A lightweight, scriptable theory sandbox that keeps its data local. The core library handles pitch-class math, scales, chord qualities, and functional mappings, while the CLI and Push grid renderer make it easy to explore results in the terminal.

## Highlights

- **Comprehensive seed data** – JSON catalogues for scales (Push 3 set plus aliases), chord qualities (triads through altered 13ths), and functional harmony mappings.
- **Push Grid renderer** – `mts/layouts/push_grid.py` drives a text-based Ableton Push layout with color coding, chord overlays, and flexible row offsets (fourths/thirds/sequential).
- **Music-theory CLI** – `python -m mts.cli.push` previews the grid, lists available scales/qualities, and enforces in-scale validation with user-friendly warnings.
- **Extensible core** – Dataclasses for chords, scales, and intervals let you script new workflows or hook into other apps without external services.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
python examples/quickstart_engine_demo.py
```

You’ll get a short report covering interval, chord, and layout objects sourced from the bundled JSON data.

## Push Grid CLI

Render a Push-style lattice directly in your terminal:

```bash
python -m mts.cli.push \
  --key Eb \
  --scale Dorian \
  --chord "Bb:maj9" \
  --preset fourths \
  --mode in_scale \
  --degrees \
  --color always
```

Key features:

- Toggle layouts (`--preset fourths|thirds|sequential`) and anchoring (`--anchor fixed_C|fixed_root`).
- Choose chromatic vs. in-scale views, hide out-of-key pads, and bias enharmonics with `--key-sig`.
- Overlay chords by quality name or root/quality pair; strict in-scale checks warn or exit when tones fall outside the active scale.
- Discover available resources with `--list-scales`, `--list-qualities`, and the dynamic function catalog via `--list-functions` (add `--functions-feature altered_dominant`, `--functions-include-borrowed`, etc. to explore richer harmonic vocabularies).

Want a scripted tour? Run the sample:

```bash
python examples/push_grid_demo.py
```

It shows multiple layout presets, spelling biases, and origin settings using the same grid engine that powers the CLI.

## Data & Customisation

All reference material lives under `data/`:

- `scales.json` – the full Push 3 roster plus modal/ethnic sets, now with alias support (e.g., “Aeolian” and “Natural Minor” map to the same entry).
- `chord_qualities.json` – triads, sevenths, extensions, altered dominants, sus voicings, and more.
- `functions_major.json` / `functions_minor.json` – expanded functional harmony tables capturing multiple chord options per degree with interval stacks.
- `mts/theory/functions.py` – a procedural generator that derives functional mappings from template rules and scale definitions; experiment via `scripts/demo_function_generation.py` or the CLI’s `--list-functions` (which now prints both major and minor sets by default).

Adjust the JSON, reload via `mts.io.loaders`, and the CLI/Push grid pick up changes instantly.

## Validation Utilities

`scripts/validate_function_mappings.py` cross-checks functional mappings against Ionian/Aeolian masks (or whichever scales you configure) so you can spot borrowed/altered chords at a glance:

```bash
python3 scripts/validate_function_mappings.py
```

It reports any pitch-class mismatches along with the scale context used for comparison.

## Next Steps

- Tie the engine into a GUI or audio layer for real-time auditioning.
- Add more aliases or scale families and extend the validator to cover harmonic/melodic variants.
- Script additional CLIs for chord identification or progression generation using the enriched quality catalog.
