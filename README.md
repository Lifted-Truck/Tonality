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

## Analysis CLI Reference

The `scripts/` folder bundles several terminal tools that piggy‑back on the analysis layer. Each command prints a short usage summary via `-h/--help`; the cheat‑sheet below lists the most important flags.

### `scripts/analyze_scale.py`

```
python3 scripts/analyze_scale.py SCALE [options]
```

- `--tonic NOTE` spell the scale from a specific tonic (e.g., `--tonic Eb`).
- `--spelling auto|sharps|flats` bias enharmonic naming (defaults to `auto`).
- `--key-sig N` force a circle-of-fifths bias (-7..+7) when rendering note names.
- `--no-note-names` suppresses spelled degrees even when a tonic is supplied.
- `--json` dumps the complete analysis payload as pretty-printed JSON.

### `scripts/analyze_chord.py`

```
python3 scripts/analyze_chord.py ROOT QUALITY [options]
```

- `--tonic NOTE` reports chord intervals relative to a tonal center.
- `--spelling auto|sharps|flats` controls enharmonic preference for note names.
- `--key-sig N` applies a circle-of-fifths bias when spelling notes (-7..+7).
- `--interval-labels numeric|classical` switches between raw integers and P/M/m labels.
- `--no-inversions`, `--no-voicings`, `--no-enharmonics` skip heavy sections you do not need.
- `--json` emits the full analysis dictionary for downstream tooling.

### `scripts/check_chord_scale_compat.py`

```
python3 scripts/check_chord_scale_compat.py [options]
```

- `--scale NAME` limit the overview to a single scale (defaults to every scale).
- `--chord-quality NAME` test a specific quality against the selected scale.
- `--tonic NOTE`, `--spelling`, `--key-sig` provide the same enharmonic controls as the other CLIs.
- `--note-names` adds spelled chord tones alongside numeric root positions.
- `--label-style numeric|classical` toggles between raw semitone offsets and traditional interval names.
- `--list-scales`, `--list-qualities` enumerate available data and exit.
- When a chord is non-diatonic, the tool suggests modal-borrow sources and shows which pitch classes would be added or removed.

### `scripts/build_scale_or_chord.py`

```
python3 scripts/build_scale_or_chord.py scale NAME 0,2,3,6
python3 scripts/build_scale_or_chord.py chord NAME 0,3,7
```

- Subcommands: `scale` registers a manual scale (comma-separated pitch classes); `chord` registers a chord quality (comma-separated intervals).
- Registered objects live in the in-memory session registries exposed by `mts.analysis`.

See `mts/analysis/` for the Python interfaces behind these commands; the modules are designed so features can expand alongside the catalog data.

## Next Steps

- Tie the engine into a GUI or audio layer for real-time auditioning.
- Add more aliases or scale families and extend the validator to cover harmonic/melodic variants.
- Script additional CLIs for chord identification or progression generation using the enriched quality catalog.
