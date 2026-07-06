# integrations/ — the cross-project communication channel

The durable inbox/outbox between **Tonality's agents** and the **agents
building external consumer projects** (synths, generators, visualizers — see
[INTEGRATION.md](../INTEGRATION.md) for the capability schematic they read
first). Chat relays get triaged and then forgotten; files here persist across
sessions, devices, and agent handoffs.

> **The generic protocol lives in [PROTOCOL.md](PROTOCOL.md)** — the
> project-agnostic clarifier (file naming, brief structure, triage contract,
> notices/acks, fences) shared across all projects that host an integrations
> channel. This README adds Tonality's specifics: the capability schematic is
> INTEGRATION.md, the SOT is [ROADMAP.md](../ROADMAP.md), and the intake
> questions below are the domain-tuned versions. Where wording differs,
> this README wins locally.

## Layout

```
integrations/
  README.md            this protocol
  <project>/
    brief.md           INBOUND — the project's voice, recorded verbatim
    response.md        OUTBOUND — Tonality's triage verdict
    (further numbered exchanges as needed: brief-2.md, response-2.md, …)
```

## Protocol

**Filing a brief (external project → Tonality).** Two equally valid routes:

1. **Direct:** the project's agent writes `integrations/<project>/brief.md`
   on a branch in this repo and opens a PR (agents on this machine have
   filesystem + `gh` access). Title it `integration: <project> brief`.
2. **Relay:** the brief goes through Julian in chat, and the Tonality agent
   of record commits it here verbatim as part of the triage PR.

A brief should answer the **six intake questions** in
[INTEGRATION.md](../INTEGRATION.md) ("What to send back"), plus anything
else worth recording: design context, epistemic commitments, specific
functionality requests, long-range notes. Verbatim is the norm — the brief
is the *other project's voice*; Tonality does not edit it, only respond.

**Triage (Tonality → external project).** The Tonality agent of record:

1. **Verifies before recording** — "already shipped" claims get checked in
   code, not assumed.
2. Writes `response.md`: per-request verdict (✅ shipped / 📖 documented /
   🕳 recorded gap / ✋ boundary ruling), with the evidence.
3. Folds the durable outcomes into the SOT in the same PR: target
   application entry, gap-list items, ROADMAP cross-references. **Decisions
   live in [ROADMAP.md](../ROADMAP.md)**, never here — response.md states
   verdicts and *links* phases/gaps (the SOT rule applies in this directory
   like everywhere else).
4. Updates [INTEGRATION.md](../INTEGRATION.md) where an ask collapsed to
   documentation (recipes, contracts).

**Reading a response (external project).** Everything Tonality committed to
is in the linked ROADMAP entries; everything usable *today* is in
INTEGRATION.md. `response.md` is the routing map between your brief and
those two documents.

## Ground rules

- **Verbatim in, evidenced out.** Briefs are not edited; responses cite code,
  tests, or ROADMAP anchors for every verdict.
- **No plans here.** Forward-looking commitments belong in ROADMAP.md (the
  single source of truth); this directory records *exchanges about* them.
- **Boundary rulings are part of the service.** When Tonality declines an
  ask because it belongs on the consumer's side of the division of labor
  (e.g. confidence thresholds over continuous evidence), that ruling is
  recorded in response.md with its reasoning — it's an answer, not a
  rejection.
- One directory per project, named in lowercase. The first exchange is
  `brief.md` / `response.md`; later rounds are numbered.
