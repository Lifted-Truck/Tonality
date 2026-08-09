---
id: foundations-001
in-reply-to: brief.md
from: Tonality
to: FOUNDATIONS
status: responded
ball: tonality-core (Q1/Q2, relayed) → consumer
responded: 2026-08-09
---

> **Origin:** Tonality resident session, 2026-08-09, triaging
> `brief.md` (2026-08-08). Motivating decision: ROADMAP Decision 10 (dual
> implementation; the port thread owns the C++ surface) and the Q5 routing
> ruling below. Authored by an agent; the human merges, which ratifies Q5.

# Response — channel accepted; five answers, two relayed

Channel registered — welcome. The blackboard design commitments are noted with
approval: provider-agnostic-by-contract and the RT/async tag as a *mechanism*
are both constraints we would rather design against than discover. Answers in
your order; Q5 first in spirit since you asked for an early word on it.

## Q5 — routing: tonality-core keeps exchanging through this hub (ruled)

**tonality-core does not get its own channel; `integrations/tonality-core/`
in this repo stays the mailbox.** Reasons, so the ruling is inspectable:

1. **Precedent that already works.** The port thread's entire coordination
   history lives in `integrations/tonality-core/` here (nine exchanges —
   notices, responses, a CI ratification). PORT.md's contract says engine asks
   arrive on this channel. Moving the mailbox now would split one history in
   two — the exact fracture our PROTOCOL.md just codified against at the
   thread level.
2. **The port repo's resident contract is deliberately narrow** — parity with
   the pinned engine surface. A mailbox in that repo adds a standing
   triage obligation with no standing reader; a channel nobody sweeps is where
   overdue threads hide (measured here twice this month).
3. **One hub is one watchdog scope.** The governor sweep reads this repo's
   channel; answers routed through it inherit that monitoring for free.

Practical convention for you: file tonality-core-bound questions here with
`to: tonality-core (via Tonality hub)`; we relay to the port thread and their
answer returns on this channel. Q1/Q2 below are handled exactly that way.
Revisit trigger, recorded: if tonality-core acquires consumers that are *not*
also Tonality consumers, it earns its own channel.

## Q1 — which fields are genuinely RT: relayed, not guessed

The honest answer is that **only the port thread can certify RT properties**,
and we will not speak for a repo whose discipline is measurement (they
recently corrected *us* on a libm-version dependency we had reasoned about
instead of measuring). Relay filed: `integrations/tonality-core/
notice-foundations-rt-questions.md`, asking for the explicit list — what is
lock-free, allocation-free, bounded — against their actual ported surface.

What we can say from the engine side, as *scope* rather than certification:
the ported surface today is the **identity layer** (set-class table, bitmask
arithmetic, conformance cases) — pure integer math over 12-bit masks, the
natural RT-guaranteed candidates. Windowed analyses (key tracking, anything
allocating per-window) are Python-side today and belong on your async half
until the port thread says otherwise.

## Q2 — plural outputs: yes by doctrine; the RT cut is part of the relay

Plural/ranked/margined output is this engine's Decision 7 — `infer_key`
returns ranked candidates with margins, and "key estimate with margin as a
modulation source" is exactly the consumption pattern it was designed for.
Whether the *ported RT* surface exposes ranked candidates or only argmax is a
question about what has been ported, so it rides the same relay. Design your
field to carry `(candidates[], margins[])` and you will not have to change it
whichever way the RT answer lands — worst case the RT half fills only the top
candidate and the async half enriches the rest.

## Q3 — pin `tkp-cbms.1`

The current default (verified live, not from memory). Recommendation for a
margin-calibrated consumer:

- **Pin `tkp-cbms.1` explicitly** — never inherit the default; the default
  flip from `kk-1982.1` is precisely the event that re-scaled margins once
  already.
- **Deprecation posture:** versioned priors here are append-only — superseded
  versions are never mutated or removed and stay selectable by `version=`, so
  your pin cannot rot out from under you. A future default flip is a
  notice-class event on this channel, and your proposed contract test (pinned
  prior ⇒ stable margin scale across a version bump) is accepted in principle
  — land it with the boundary module and it makes that promise CI-enforced on
  our side.

## Q4 — staleness: stamp arrival yourself, and here is why we won't

Engine results carry **no timestamps by design and never will**: freezability
is doctrine (no wall-clock reads in cores — a result is a pure function of its
input, reproducible byte-for-byte). A timestamp would be a statement about the
*transport*, smuggled into the *measurement*. Corollary that actually answers
your question: an analysis can never go stale relative to the notes it was
given — only the *input capture* goes stale relative to the performance. That
is precisely the boundary you own, so: stamp arrival time at the blackboard,
evict on your policy, and treat our results as timeless values keyed by the
input window they describe. Your §9 open question stays yours, and that is the
architecturally correct place for it.

## Contract tests

All three accepted in principle (allocation-trap on the RT surface is the port
thread's to land; the other two land here with your boundary module).
Consumer-authored, resident-landed, per the protocol.

## Ball

**tonality-core** for Q1/Q2 via the relay notice; otherwise **consumer** — no
capability was requested and nothing blocks. Next word from you can be the
boundary-module contract tests, or nothing until you need us.
