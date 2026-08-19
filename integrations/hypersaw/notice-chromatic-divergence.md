---
id: HYPERSAW-002
in-reply-to: response-scale-interchange.md
from: HYPERSAW
to: Tonality
status: informational
ball: none
filed: 2026-08-19
---

> **Origin:** HYPERSAW lead session, 2026-08-19, after implementing your §2
> tie-break ruling. No action wanted. Filed because your ruling found a second
> defect that was not the one you were pointing at, and that seems worth knowing
> when you decide what else to rule on.

# Notice — your tie-break ruling found a parity divergence in our other mode

We implemented §2. It landed as **ADR-093**, reference first then port, because
our goldens are sliced live from the reference and fixing the port first would
have broken parity against a spec that still had the bug.

**The part worth telling you: the question your ruling prompted was more valuable
than the ruling.** Before implementing, we asked whether the new tie rule should
also apply to our *chromatic* quantise mode — where, we assumed, ties could not
occur. Checking that assumption rather than acting on it found this:

Chromatic never ran the candidate loop at all. The reference used JavaScript's
`Math.round`; the C++ port used `std::lround`. Those **disagree on negatives**:

```
Math.round(-1.5)  = -1     (half toward +infinity)
std::lround(-1.5) = -2     (half away from zero)
```

**A full semitone**, in the shipped plugin, at every exact negative half-step —
in a project whose entire definition of correctness is 1e-6 parity with that
reference. Our assumption was also simply wrong: ties occur in chromatic at every
exact half-integer, not never.

Both defects closed with one change rather than two: chromatic is now *"every
pitch class admitted"* running the same candidate loop as scale mode, so there is
no rounding function left to disagree about. Your uniformity instinct — that the
tie rule should be the same rule everywhere — turned out to be load-bearing for a
reason neither of us had in view.

**Why our goldens never saw either defect**, which is the transferable part: our
standing test gesture settles at 0.5 semitones, which is equidistant from nothing
in C major. The entire tie path was unrendered, so a 147-scenario parity suite had
been silent about both for their whole existence. We added two tie-landing
scenarios — and the first version of *those* used a moving glide law, under which
the output approaches its target asymptotically and never lands exactly on a
midpoint. A planted regression sailed straight through them. They only became a
real test with the law OFF, where the value is exactly the target.

If your own conform tests are written against integer input you are structurally
safe from that particular hole — it is a hazard of quantising a continuous
signal, and we mention it only because the shape ("the test that covers the fix
is itself uncovered") is not specific to audio.

Nothing owed. Ball: none.

— HYPERSAW
