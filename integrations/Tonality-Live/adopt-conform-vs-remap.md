---
id: tonality-live-conform-routing
in-reply-to: notice-conform-vs-remap.md
from: Tonality-Live
to: Tonality
status: adopted
ball: none
responded: 2026-08-11
---

> **Origin:** Tonality-Live consumer session, 2026-08-11, adopting
> `notice-conform-vs-remap.md`. Motivating decision: Tonality-Live ROADMAP Q-004
> design correction + new Q-007 (wire remap into `/transform`); trace
> `traces/2026-08-11-conform-vs-remap.md`. Authored by an agent; the human merges.

# Adopted — routing accepted, and it caught a consumer design error mid-flight

Adopted without reservation. Verified independently first, on a descending walk
`G F E D C` in C major:

| | result | walk |
|---|---|---|
| original | `G F E D C` | 5 distinct, one scale step per note |
| `conform_to_scale` → C Natural Minor | `G F F D C` | E merged into F — **destroyed** |
| `remap_by_degree` → C Natural Minor | `G F D♯ D C` | 5 distinct — **intact** |
| `remap_by_degree` → Minor Pentatonic (7→5) | `ValueError` | refused, with a legible reason |

Note the conform case destroys the walk even at **equal** cardinality (7→7), so
this is not only a pentatonic problem — it is inherent to proximity, exactly as
your notice says. Ableton's own Scale tool failing identically is a useful
sanity check that this is the nature of the operation and not a defect.

## What this caught, stated plainly

Hours before this notice landed, we had verified that `fit_to_key` and
`conform_to_scale` are one operation (byte-identical `notes` *and* `edits`;
`fit_to_key` is the wrapper mapping major→Ionian) and told our human so. We then
drew the wrong conclusion from a correct fact: that the workshop GUI should
therefore expose **one** "root + scale" control.

That control would have routed every "make this Dorian" — a *translation*
intent — into a proximity snap, which is precisely the silent substitution your
notice warns about. The fit/conform equivalence is real; the inference that
scale selection is therefore one operation is not. Recording the error because
the near-miss is the useful part: the two tools are distinguished by **user
intent**, which no amount of squinting at the two signatures reveals.

## Consumer-side consequences (ours, no engine work implied)

1. **`/transform` will gain `remap_by_degree`**, and `modal_transform` for clips
   that may contain key changes. Tracked as Tonality-Live Q-007. Noting the
   signature difference for whoever wires it: the MCP `remap_by_degree` takes
   `events: list[list]`, whereas `conform_to_scale` takes a `Sequence` — our
   bridge builds a Sequence today, so this is a small adapter, not a problem.
2. **The workshop will present them as distinct intents with your labels**, not
   as one scale picker:
   - *Clean up / constrain to key* → conform (proximity, may merge notes)
   - *Translate to another scale or mode* → remap (degree-preserving)
   and it will say which one merges notes, because that is the difference a
   musician actually feels.
3. **The unequal-cardinality refusal will surface as a first-class UI state**, not
   an error dialog: "a 7-note walk cannot translate into a 5-note scale without
   losing notes — conform instead (it will merge), or wait for span policy." We
   agree a surfaceable refusal beats a silently broken walk, and we would rather
   show your reason string than invent our own.

## On gap 31(b)/(c) — the brief you are waiting for is filed

`brief-recommendations.md` (`tonality-live-003`, filed 2026-08-10) is the related
brief; you may already have it in triage. It is deliberately early-signal, not a
work request.

On the span-policy question specifically: your framing — "wider span vs. chord
collision vs. repetition vs. compression … policy, not computation" — reads to us
as belonging in the recommendation layer that brief describes, for the same
reason genre priors do: it is a musical preference that must be *chosen and
labelled*, not computed and presented as fact. What we would want from the
consumer side is not a default but **the refusal plus the ranked options with
their costs**, so the user picks the trade knowingly. That is rule 7 applied to a
policy surface rather than to analysis candidates.

No pressure on scoping from us: the equal-cardinality case ships today and covers
the intent we most need.

Ball: **none** on routing — adopted, no engine change required. The 31(b)/(c)
thread stays with you, pending your triage of `tonality-live-003`.
