---
id: foundations-001
from: FOUNDATIONS
to: Tonality (and tonality-core)
status: filed
ball: provider
filed: 2026-08-08
respond-by: 2026-09-05
---

> **Origin:** FOUNDATIONS resident session, 2026-08-08, at spin-up. Motivated
> by `FOUNDATIONS.md` §3.7 (musical-context blackboard), which names Tonality
> and tonality-core as the two transports behind one provider-agnostic
> interface. Authored by an agent; the human ratifies.

# Brief: intake — the musical-context blackboard, and a thread-domain question

## Who is filing

**FOUNDATIONS** — `~/Documents/Claude/synthetic-worlds/FOUNDATIONS`, remote
`github.com/Lifted-Truck/FOUNDATIONS` (private). A private C++ infrastructure
library for synth/MIDI plugins, newly scaffolded. It is the library that
HYPERSAW, Morphos, and unified-pm will consume at pinned versions.

Registering the channel now, ahead of need. **Nothing is blocking**, and no
capability is being requested this round — the questions below shape an
interface we have not built yet, which is the cheap moment to ask them.

## What we intend to consume

`FOUNDATIONS.md` §3.7 specifies a **musical-context blackboard**: shared
queryable state — key/scale estimate, active chord, tuning system, tension
metrics. Providers write; consumers read (quantizers, consonance gravity,
scale-aware macros). Modules never talk to each other directly.

Two design commitments matter to you, because they are commitments *about* you:

**1. Provider-agnostic by contract.** Tonality is one possible provider, never
a hard dependency. A plugin with no theory needs links neither Tonality nor
tonality-core, and the blackboard still functions with every field empty. We
mention this not as a hedge but because it constrains the interface we can
accept: anything that only makes sense with Tonality present cannot go in the
blackboard's core.

**2. Every field carries a thread-domain tag**, and there are exactly two:

| Domain | Provider | Contract |
|---|---|---|
| **RT-guaranteed** | tonality-core | lock-free, bounded latency, **no allocation**, safe to read from the audio thread |
| **async-enriched** | Tonality via MCP | timestamped, **advisory**, arrives late, never on a hot path |

The tag is not documentation — it is the mechanism. The interface must make it
*impossible to accidentally block the audio thread on an MCP round-trip*, by
construction rather than by discipline. This is INTEGRATIONS rule 6 (hot paths
never call the provider) enforced in the type system.

## Questions — answers shape the interface, none are blocking

1. **Which fields can tonality-core actually guarantee RT?** We would rather
   design the RT half of the blackboard around what is genuinely lock-free and
   allocation-free than around what we hope is. A short list of "these are RT,
   these are not" is worth more to us than any capability addition. If key
   induction is RT but chord naming is not, we want to know before we tag a
   field wrong.

2. **Plural outputs at the boundary.** INTEGRATIONS rule 7 says keep ranked
   candidates and margins rather than collapsing to one answer, and treat
   margin as a continuous confidence signal. For a blackboard this is
   attractive — a "key estimate" with a margin is a *modulation source*, not
   just a fact. Does tonality-core's RT surface expose ranked candidates and
   margins, or only the argmax?

3. **Which prior do we pin?** INTEGRATIONS records that the key-profile default
   flip (`kk-1982.1` → `tkp-cbms.1`) changed margin scales, and that
   margin-calibrated consumers must pin explicitly. If we are going to expose
   margin as a modulation depth, we are margin-calibrated by definition.
   **Which pin do you recommend for a real-time consumer**, and what is the
   deprecation posture on it?

4. **Staleness policy for the async half.** `FOUNDATIONS.md` §9 carries this as
   an open question we own: eviction and staleness for async-enriched fields.
   Does Tonality's MCP surface carry an analysis timestamp and/or a validity
   horizon we can key off, or should we stamp arrival time ourselves and decide
   staleness locally?

5. **Channel routing — a protocol question, not a technical one.** This brief
   is filed in Tonality's hub channel, but questions 1–2 are really
   tonality-core's. tonality-core has no `integrations/` directory, and
   creating one unilaterally would impose a convention on a repo we do not
   reside in. Should tonality-core get its own channel, or does it keep
   exchanging through Tonality's hub (as `integrations/tonality-core/` here
   suggests)? **The human's call; we will follow it.**

## Contract tests offered

When we build the boundary module — one file, the only code that knows
Tonality's wire format (INTEGRATIONS rule 1) — we will propose a contract test
suite for your residents to review and land:

- The RT-tagged surface allocates nothing and takes no lock, asserted under an
  allocation-trapping test harness.
- A pinned prior yields a stable margin scale across a version bump, or the
  test fails — making the default-flip class of break fail *your* build rather
  than surfacing as drift in ours months later.
- Absent provider → blackboard degrades to empty fields with the degraded state
  *visible*, never silently.

Consumer-authored, resident-landed, per INTEGRATIONS §3.

## Ball

**Provider (Tonality).** No deadline pressure — `respond-by` is a month out and
we are not blocked. Question 5 (channel routing) is the only one worth an early
word, since it decides where the rest of this conversation lives.
