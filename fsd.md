---
description: Capture freeform notes into a structured FSD requirements doc + grouped clarifying questions
agent: fsd-writer
---

Run the FSD requirements-capture workflow on the input below.

Follow the `fsd-writer` method exactly: capture every stated detail, invent
nothing, flag missing facts as `[to confirm]`, and ask grouped clarifying
questions for the open decisions. First skim the repo for related design docs and
naming so the capture fits the existing system.

Respond in two parts:
- **Part 1 — Structured Requirements Capture** (module identity & context →
  objective → roles & permissions → core entities & data → functional
  capabilities → business logic/rules → UI/screens → integrations →
  non-functional). Include a section only if it has stated content or a
  `[to confirm]` flag.
- **Part 2 — Open Questions**, grouped by theme. End with: "Answer what you can —
  even partial answers help."

Then offer to generate the full FSD (or a generation-ready prompt) and to write
it to `docs/fsd/<module>.md`.

---

Input to capture:

$ARGUMENTS
