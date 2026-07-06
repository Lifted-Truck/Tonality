# NOTICE — Tonality → Audiology: RE-4 MCP surface unification (additive; one error-behavior change)

> 2026-07-06, dev loop (rigor & efficiency review, RE-4). Everything here is
> additive except item 3. The bridge-auth design call travels separately
> (`notice-bridge-hardening-design-call.md` — still awaiting your answer).

1. **One canonical event form everywhere (additive).** Every temporal tool
   now accepts `[onset_beats, duration_beats, midi_note, velocity?, voice?]`
   (velocity numeric at index 3, voice string at index 4). Your existing
   calls all keep working: the old string-at-3 voice form still reads
   (JSON types disambiguate), the old velocity-at-3 numeric form IS the
   canonical one, and tools that used to hard-reject extra elements
   (`key_tracking`, the melodic/rhythmic/swing tools) now accept them. The
   only rejected shape is the contradictory string-at-3 *plus* voice-at-4.
2. **`midi_file_analysis` / `piano_roll_view` now have conformance goldens**
   (their shapes are pinned typed results below the MCP layer). No wire
   change — the shapes are byte-compatible; they're just guaranteed now.
3. **Error-behavior change (the one to check):** those two pipelines used to
   swallow *every* `ValueError` from key/meter tracking as "no tonal/metric
   information" (`key_regions: null`). They now absorb only honest absence;
   a real input error — e.g. setting both `key_inertia` and
   `disambiguate_relative_keys` — **raises** instead of silently nulling the
   regions. If any of your pipeline calls relied on bad inputs quietly
   degrading, they'll now hear about it.
4. **Bridge: engine `TypeError`s are 500s** (bad kwargs still 400). Your
   500-alerts now mean "engine bug", never "client mistake".
5. Cosmetic: the stdio/bridge tool count is 46 (docs previously said 43).

Action: only item 3 warrants a check on your side; everything else is
free. Ack when absorbed.
