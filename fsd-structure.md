# FSD Structure Reference

The section taxonomy for the requirements capture, the clarifying-question theme
bank, and a worked example. Used by `fsd-builder`.

## Table of contents
1. Section taxonomy (Part 1 output)
2. Clarifying-question theme bank (Part 2 output)
3. Worked example (input → output)
4. Style rules

---

## 1. Section taxonomy (Part 1 — Structured Requirements Capture)

Use these sections, in this order. Include a section only if it carries stated
content or a `[to confirm]` flag — do not pad with invented material.

1. **Module identity & context** — Module name; its position in the wider
   system/pipeline; the upstream that feeds it and the downstream it hands to;
   the end-to-end workflow it serves; and any *terminology notes* (overlaps with
   existing terms, naming to disambiguate).
2. **Objective** — What the module must achieve, in one or two lines, plus any
   guiding principle the user stated (e.g., "the right expertise handles the
   right item").
3. **Roles & permissions** — Each actor (end user, reviewer, lead, admin…) and
   precisely what each can do. One actor per bullet.
4. **Core entities & data** — The key objects and their attributes/fields; any
   enums or levels (with the exact level names); the primary "unit" the module
   processes and the fields it carries; and operational attributes the logic
   consumes (e.g., backlog, rate, availability).
5. **Functional capabilities** — Numbered F-1, F-2, … Each is one discrete
   capability with a one-line purpose. This is the spine of the spec.
6. **Business logic / rules / engine** *(when applicable)* — Separate
   **eligibility / hard constraints** (must-match filters) from **ranking /
   optimization factors** (soft preferences); state how factors combine
   (hard filter, weighted score, or priority order), any caps/limits,
   tie-breakers, and default behavior. Flag every unstated rule as `[to confirm]`.
7. **UI / screens** — The screens/views implied, grouped by the role that uses
   them.
8. **Integrations** — Upstream (what feeds it), internal (shared stores), and
   downstream (what it feeds); name the external systems/sources and the sync
   direction where stated.
9. **Non-functional requirements** *(only if stated)* — performance/SLA, audit &
   compliance, security, access control, data retention. If the domain is
   regulated and these were not given, list them as `[to confirm]` rather than
   inventing them.

---

## 2. Clarifying-question theme bank (Part 2 — Open Questions)

Generate questions only for genuine open decisions — places where assuming would
materially change the design. Group under themed headers. Draw from these themes:

- **Entity & data model** — granularity (per-pair vs global?), identifiers,
  exact enum/level definitions, lifecycle (expiry / renewal / versioning),
  ownership, and whether an audit trail of changes is required.
- **Input → behavior mapping** — the exact rule/threshold/mapping from inputs to
  outcomes (e.g., which input maps to which tier), and *where each value
  originates* — carried in from upstream vs derived/owned by this module.
- **Logic & algorithm** — how multiple factors combine (hard constraint /
  weighted score / fixed priority order); hard caps & limits; tie-breakers; and
  the default when nothing else decides.
- **Integrations & sources** — which concrete external systems/sources; sync
  direction; and handling of partial data or source failure.
- **Roles, permissions & workflow** — who can do what; automatic vs manual; any
  approval/confirmation step; and notifications.
- **Edge cases & exceptions** — empty / no-match; overflow / over-capacity;
  special user classes (e.g., trainees, guests, VIPs); and the fallback or
  escalation path.
- **Scope & boundaries** — what is explicitly in vs out of this module; its
  relationship to adjacent modules; and any terminology overlap to resolve.
- **Non-functional** — performance/SLA targets; audit & regulatory needs
  (especially in regulated domains); security; data retention.

Phrase each question so a single sentence answers it. Prefer concrete options
inside the question ("hard constraint, weighted score, or priority order?") over
open-ended prompts.

---

## 3. Worked example (compressed)

**Input (user brain-dump):** "Alerts get assigned to compliance analysts. Analysts
are certified for a product type and a risk typology, with an expertise level —
Trainee, Certified, Champion — set by the team lead. A complex alert on a product
should go to a Champion in it. Also consider backlog, the analyst's clear rate,
the expected close timeline, and their calendar/leave. Team lead can set skills
and reassign manually; an analyst can request reassignment with a reason."

**Output Part 1 (excerpt):**
- *Module identity & context* — Alert Assignment Module; entry point of the
  investigation layer; consumes the raised alert; routes to the analyst tier.
- *Roles & permissions* — Analyst: receives alerts, can request reassignment with
  a mandatory reason. Team Lead: sets skills/expertise, assigns/reassigns
  manually.
- *Core entities & data* — Analyst skill inventory: certified product types,
  certified typologies, expertise level `{Trainee, Certified, Champion}`. Alert:
  product, risk typology, details. Operational attributes: backlog, clear rate,
  availability (calendar/leave).
- *Business logic* — Eligibility: certified for the alert's product AND typology
  at the required level (complex → Champion). Ranking factors: backlog, clear
  rate, expected close timeline, availability. How these combine: `[to confirm]`.

**Output Part 2 (excerpt):**
- *Input → behavior mapping* — How is an alert's "complexity" determined, and what
  is the exact mapping of complexity → required level?
- *Logic & algorithm* — Combine the four factors as hard constraints, a weighted
  score, or a priority order? Any cap on open alerts per analyst? Tie-breaker?
- *Edge cases* — Fallback when no eligible analyst is available?

Note how every undecided rule became a `[to confirm]` flag and a grouped
question — nothing was invented.

---

## 4. Style rules

- Imperative, concise, faithful. No filler.
- Mark every uncertainty `[to confirm]`; never resolve it silently.
- Keep Part 1 free of opinion; put all judgment calls into Part 2 questions.
- End Part 2 with: "Answer what you can — even partial answers help," then offer
  to generate the full FSD / a generation-ready prompt and to write it to a file.
