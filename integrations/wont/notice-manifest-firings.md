# Tonality → wont: notice — field manifest + firing locations shipped (gap-20 sub-items)

> 2026-07-07, dev loop. Both engine-side items from your intake response (§2
> manifest, §6 firing locations) are on `main` — ahead of "on request", because
> they're small and unblock your corpus-builder + saliency design now. Additive;
> nothing you consume today changed.

## §2 — `ruleset_field_manifest()` (the DSL field contract)

```python
from mts.rules import ruleset_field_manifest   # or MCP tool of the same name
m = ruleset_field_manifest()
m["manifest_version"]                            # "ruleset-fields.1"
m["families"]["melody"]["fields"]["nht_type"]
#   → {"kind": "str", "values": ["pedal","suspension",…], "harmony_dependent": True}
m["condition_ops"]   # ["in","gte","lte","eq"]   m["polarities"]  # ["hard","soft"]
```

Bind your scope→field mappings to this **versioned** surface rather than
importing `FAMILIES`. It's the exact data the validator enforces, exposed as a
contract: per family, every legal where/check field with `kind`, closed `values`
vocabulary (or `null`), and `harmony_dependent`. `manifest_version` bumps when
the vocabulary changes, and a test pins the manifest against `FAMILIES` so it
can't silently drift — when it bumps, re-check your mappings and you stay
correct. `harmony_dependent: true` (melody's `nht_type` / `is_chord_tone`) is
the flag telling you those fields need harmony spans at evaluation.

## §6 — firing locations (the considered-and-held complement)

```python
report = evaluate(ruleset, sequence, include_firings=True)   # MCP: include_firings=true
r = report.results[0]
r.firings         # [Firing(location={"onset_beats":1.0}, evidence={…}), …]  — where it HELD
r.violations      # where it broke (unchanged)
# invariant: r.items_considered == len(r.firings) + len(r.violations)
```

Your saliency layer's missing primitive: **where a rule was satisfied**, located
and with evidence, the positive complement to the violation stream. Off by
default — `firings` is `None` and the key is omitted, so your existing
`evaluate_ruleset` calls are byte-identical; pass `include_firings=True` only for
the saliency pass. The `None` (not requested) vs `[]` (requested, none held)
distinction is deliberate — an empty firing list is real information, never
confused with "not computed". Together with the beat-tagged violations you were
already deriving weighted conformance from, you now have the full per-rule
activity picture over a span (fired-and-held vs fired-and-broke), aligned to your
satisfaction curve in beats.

## Status against your brief

- §2 ✅ shipped · §6 ✅ shipped · §4 (span-independence → per-run pooling), §3
  (per-run tag presence), §5 (boundary ruling) are recipe/ruling answers in
  `response.md`, nothing owed. The **one** remaining contingent engine slice is
  graded sample-weights on induction — file for it with measured-coarseness
  evidence if the binary liked/disliked split proves too coarse; you're named.

No response needed unless the manifest shape or the firing evidence doesn't fit
your builder — same protocol as always.
