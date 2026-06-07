---
name: fsd-builder
description: >-
  Turn a freeform description of a module, feature, or system into a complete,
  faithful, structured requirements capture for a Functional Specification
  Document (FSD), and surface every open decision as grouped clarifying
  questions. Use this whenever the user pastes notes, instructions, or a
  brain-dump of what something "should do" and wants it organized for
  spec-writing — including phrases like "write an FSD", "functional spec",
  "structure these requirements", "turn this into a spec", "capture the
  requirements", or "prepare a prompt to generate the spec". Always prefer this
  over free-form drafting when the goal is a requirements document: it extracts
  every stated detail without dropping any, never invents missing decisions, and
  asks grouped clarifying questions instead of assuming.
---

# FSD Builder

Convert a freeform description (notes, a brain-dump, a verbal spec) of a module /
feature / system into a **structured requirements capture** suitable for writing
a Functional Specification Document, then surface every open decision as
**grouped clarifying questions**. The output is meant to be reviewed and answered
by the user, then handed to a generator (or back to this skill) to produce the
full FSD.

The value of this skill is its discipline: capture everything, invent nothing,
ask in organized clusters.

## Core principles (do not violate)

1. **Faithful capture.** Extract *every* discrete requirement the user stated —
   roles, entities, fields, behaviors, rules, UI, integrations, constraints.
   Drop nothing. Do not compress detail away.
2. **No assumptions.** Never fill a gap or invent a design decision. Where a fact
   or decision is missing, *flag it* (mark `[to confirm]`) and put it in the
   questions — never guess and never silently "reframe" the request into
   something more complete than it was.
3. **Fit the existing system.** Before producing output, ground yourself: read
   related material in the workspace (READMEs, architecture/design docs, adjacent
   module specs, data models, naming conventions). Reuse existing terminology and
   note overlaps or conflicts (e.g., a term that already means something else).
4. **Separate stated from open.** Part 1 contains only what was given. Everything
   uncertain or undecided lives in Part 2 (questions). Do not blur the two.
5. **Group the questions.** Never dump a flat list. Cluster by theme and tell the
   user partial answers are fine.

## Workflow

A. **Ingest** the provided content and instructions in full.

B. **Ground in the workspace.** Scan the repo/docs for related context (existing
   modules, data models, naming, the wider pipeline this module sits in). Note
   how this piece connects upstream/downstream and any terminology overlap.

C. **Extract & normalize** every requirement into discrete items (actor, entity,
   attribute, capability, rule, screen, integration, constraint).

D. **Organize** into the section taxonomy defined in
   `references/fsd-structure.md`. Read that file before producing output.

E. **Flag gaps inline** as `[to confirm]`. Do not invent values, thresholds,
   enums, SLAs, or behaviors that were not stated.

F. **Generate grouped clarifying questions** using the question-theme bank in
   `references/fsd-structure.md`. Cover the genuine open decisions only — the
   ones where assuming would materially change the design.

G. **Offer the next step.** Once the user answers, offer to produce either (a) a
   generation-ready prompt for an FSD generator, or (b) the full FSD document
   itself, and offer to write it to a file (e.g., `docs/fsd/<module>.md`).

## Output format

Always respond in exactly two parts:

**Part 1 — Structured Requirements Capture**
Follow the taxonomy in `references/fsd-structure.md` (module identity & context →
objective → roles & permissions → core entities & data → functional capabilities
→ business logic/rules → UI/screens → integrations → non-functional). Include a
section only if it has content or a `[to confirm]` flag; never pad with invented
material.

**Part 2 — Open Questions**
Grouped under themed headers (see the question bank). End with: "Answer what you
can — even partial answers help."

## After the questions are answered

Re-read the answers, fold them into Part 1 (replacing the matching `[to confirm]`
flags), and then produce whichever deliverable the user chose. If writing the
full FSD to a file, keep the same section taxonomy as the document's structure.

## Reference

`references/fsd-structure.md` — the full section taxonomy, the clarifying-question
theme bank, and a worked example. **Read it before generating output.**
