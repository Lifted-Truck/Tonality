# The integrations protocol — how project agents file briefs, responses, and notices

> **Project-agnostic.** This document is written to be copied into any repo
> that hosts an integrations channel. "The provider" is the project whose repo
> hosts `integrations/`; "the consumer" is the external project writing in.
> The provider's own README in this directory may add project-specific
> details (capability docs, SOT location); where they conflict, the local
> README wins. Reference implementation: Tonality
> (`integrations/` + `INTEGRATION.md` + `ROADMAP.md`).

## Why files, not chat

Chat relays get triaged and forgotten. Files persist across sessions,
devices, and agent handoffs — the channel is the durable inbox/outbox
between the provider's agents and the agents building consumer projects.
Every exchange leaves a record a future agent can reconstruct without any
conversation history.

## Layout and naming

```
integrations/
  README.md / PROTOCOL.md     the protocol (this file)
  <project>/                  one directory per consumer, lowercase
    brief.md                  INBOUND — first ask, the consumer's voice
    response.md               OUTBOUND — the provider's triage verdicts
    brief-2.md, response-2.md further exchanges, numbered per round
    notice-<slug>.md          provider → consumer: a change that affects you
    ack-<slug>.md             consumer → provider: notice/response absorbed
    proposal-<slug>.md        RFC-sized inbound (a brief that proposes a
                              design rather than asking for capabilities)
```

Naming rules:

- The first exchange is `brief.md` / `response.md`; later rounds increment
  (`brief-N.md` / `response-N.md`). A response answers the brief with the
  same N. Multi-part responses split as `response-N-<topic>.md`.
- Notices and acks are slugged, not numbered — they attach to a change, not
  a round. An ack names what it acknowledges in its slug or first line.
- PR titles: `integration: <project> brief[-N]` (inbound),
  `integration: <triage summary>` (outbound), `integration: <notice/ack
  summary>` (either direction).

## Two filing routes

1. **Direct** — the consumer's agent has filesystem/`gh` access: write the
   file under `integrations/<project>/` on a branch **in the provider's
   repo** and open a PR containing only that file. This is the preferred
   route.
2. **Relay** — the brief travels through the human in chat; the provider's
   agent commits it **verbatim** as part of the triage PR, under a
   provenance header (see below).

## The verbatim rule (both routes)

A brief is the *consumer project's voice*. The provider never edits one —
not typos, not framing — only responds. A relayed brief gets a blockquote
provenance header above a horizontal rule:

```markdown
> Relayed <date> by <human> (filed by <provider>'s agent of record per the
> relay route). Original filename in the <consumer> repo: `<name>` (kept
> there as their copy of record). Verbatim below the rule.

---
```

## What a brief must contain

**Self-containment is the bar**: a reader with no chat history and no access
to the consumer's repo must be able to triage it. Concretely:

1. **Who you are** — one paragraph: what the project does, its architecture
   at the integration seam, repo link/path.
2. **The intake questions** (adapt to the domain; these are the general
   shape):
   - What do you **produce and consume**, in what formats?
   - Which **capabilities** do you want, at what **granularity/frequency**?
   - What are your **latency/runtime constraints** (offline batch,
     interactive, real-time — and what runtime can you ship)?
   - Which **integration door** (in-process import, IPC/HTTP, MCP,
     compiled-artifact consumption, vendored data)?
   - What stays **your side** of the division of labor? Say it explicitly —
     scoping what you are NOT asking for is as valuable as the asks.
3. **Numbered asks** — `R1..Rn`, one ask each, each tagged with what kind of
   answer it wants: *build request*, *design handshake / confirm-a-shape*,
   *documentation request*, *guidance*, or *note (not an ask)*.
4. **Guesses marked as guesses.** If your adapter was written best-effort
   against the provider's docs, say which shapes are assumptions and mark
   them in your source (a greppable `# SEAM` comment is the proven
   pattern). Never present an assumption as a verified fact — the triage
   verifies claims in code, and unmarked guesses waste that pass.
5. **A disposition line** — what happens after the response: are you blocked,
   building against the answers, or filing for the record?

## The triage contract (the provider's side)

The provider's agent of record, on receiving a brief:

1. **Verifies before recording.** Every "already exists" / "assumed shape"
   claim is checked in code, not believed. Corrections go in the response
   with evidence.
2. **Writes the response** with a per-ask verdict, one of:
   - ✅ **shipped** — exists now; cite the code/tool/tests and correct any
     wrong assumptions.
   - 📖 **documented** — the ask collapses to documentation; update the
     capability doc in the same PR and point at it.
   - 🕳 **recorded gap** — accepted as future work; record it in the SOT
     (roadmap) with the consumer named, and link the entry.
   - ✋ **boundary ruling** — declined because it belongs on the consumer's
     side of the division of labor. **A ruling is an answer, not a
     rejection**: state the reasoning so it isn't relitigated.
3. **Folds durable outcomes into the SOT in the same PR.** Decisions,
   consumer registrations, and gap entries live in the roadmap/SOT — the
   channel records *exchanges about* them, never the decisions themselves.
   An unrecorded decision isn't decided.
4. **Keeps intelligence out of the channel.** No plans, no forward-looking
   commitments in `integrations/` files — link the SOT entry instead.

## Notices and acks (the standing obligation)

- The provider files a **notice** when consumer-visible behavior changes:
  what changed, why, the action required, and the no-action default. File it
  in the same PR as the change.
- A mechanical guard beats a promise: where possible, pin the
  consumer-facing surface in the provider's test suite so changing it
  *fails tests* until the notice is filed (the pin-file pattern), and give
  the consumer a refresh/diff script on their side. Silent drift is the
  failure mode this whole protocol exists to prevent.
- The consumer **acks** notices and responses it has absorbed (including
  "no impact" — that's information). An unacknowledged notice is an open
  loop; the provider may nudge through the human.

## Fences (for agents operating across repos)

- A consumer's agent writes **only** under `integrations/<project>/` in the
  provider's repo — never to the provider's source, docs, or SOT. Engine
  asks are briefs, not patches.
- The provider's agent never edits the consumer's repo; corrections to a
  consumer's assumptions go in the response.
- One exchange file per PR unless closing a loop (a response + its SOT fold
  travel together; a notice + the change that caused it travel together).
- Don't stack channel PRs on unmerged branches. Doc-only exchanges may claim
  the trivial-scope exemption from acceptance blocks — claim it explicitly.

## Tone

Briefs and responses are engineer-to-engineer: specific, evidenced, no
salesmanship. Say what you verified, what you assumed, what you want, and
what you'll do with the answer. Both sides cite code, tests, versions, and
SOT anchors — "evidenced out" applies in both directions.
