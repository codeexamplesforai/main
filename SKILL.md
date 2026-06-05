---
name: fsd-authoring
description: Methodology, templates, and quality gates for producing enterprise-grade Functional Specification Documents via a four-agent workflow (fsd-discovery → fsd-architect → fsd-validator → fsd-traceability). Grounded in ISO/IEC/IEEE 29148:2018, BABOK v3, Use Case 2.0, and ISO/IEC 25010. Load when you have business inputs (stakeholder interviews, business case, current process docs, regulatory citations) and need to produce a regulator-grade FSD with full traceability. Works across frontier (Claude, GPT, Gemini) and open-weights models (Qwen-Coder, gpt-oss, Gemma, Llama, DeepSeek).
license: MIT
compatibility: opencode
metadata:
  audience: business-analysts, product-managers, solution-architects, compliance-officers
  produces: functional-specification-document, requirements-traceability-matrix, discovery-brief, use-case-catalog
  workflow: four-agent (fsd-discovery + fsd-architect + fsd-validator + fsd-traceability)
  standards: ISO/IEC/IEEE 29148:2018, BABOK v3, Use Case 2.0, ISO/IEC 25010
  version: "1.0.0"
---

# FSD Authoring

The methodology for producing enterprise-grade Functional Specification Documents.

This skill is what an experienced BA + senior engineer would teach a new hire about FSD writing. It is grounded in international standards (ISO/IEC/IEEE 29148, BABOK v3) and tested in regulated industries (banking, healthcare, defense, pharma).

The four agents in this package — `fsd-discovery`, `fsd-architect`, `fsd-validator`, `fsd-traceability` — work as a pipeline. This skill is the playbook they follow.

---

## The four-agent workflow

```
   Sources & stakeholders                                                                                        
        │                                                                                                        
        ▼                                                                                                        
   ┌──────────────────┐   ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────────┐                
   │ fsd-discovery    │──▶│  fsd-architect  │──▶│  fsd-validator   │──▶│  fsd-traceability    │                
   └──────────────────┘   └─────────────────┘   └──────────────────┘   └──────────────────────┘                
        │                       │                      │                        │                                
        ▼                       ▼                      ▼                        ▼                                
   Discovery Brief         The FSD                Validation Report           RTM (Appendix C +
   (stakeholders,        (ISO 29148 +            (PASS/FAIL per check)        companion file)
    goals, current/      BABOK structure;
    future state,        FRs with quality
    open questions)      template)
```

Each agent has one job. They hand off via files on disk. Inspection points between agents catch errors early — you read the discovery brief before authorizing FSD writing, you read the validation report before authorizing RTM generation.

| Agent | Reads | Writes | Phases |
|---|---|---|---|
| `fsd-discovery` | Business case, interview notes, process docs, regulatory citations | `discovery/<project>_discovery_brief.md` | 6 steps |
| `fsd-architect` | The discovery brief | `<Project>_FSD.md` | 6 phases |
| `fsd-validator` | The FSD | `reviews/<FSD>_validation.md` | 5 steps |
| `fsd-traceability` | The FSD | RTM in Appendix C + `<Project>_RTM.md` (companion if large) | 4 steps |

If you are not using all four, you are not using the workflow correctly.

---

## When to use this skill

Use this skill when **all** of the following are true:

- The output deliverable is a Functional Specification Document (FSD) — not an implementation plan, not a design document, not a runbook
- The audience includes business stakeholders (not only engineers)
- Requirements need to be uniquely identified, prioritized (MoSCoW), and traceable
- The expected output is regulator-acceptable or close to it

Do **not** use this skill for:

- **Implementation plans** — use `spec-authoring` skill from the sibling package `opencode-spec-architect`
- **Architecture / design documents** — use a dedicated SDD skill
- **User stories alone** — write directly in your backlog tool; FSD overhead is wasted
- **Code generation specs** — use GitHub Spec Kit (specify→plan→tasks→implement)

---

## What an FSD is — and is not

An FSD is:

- **The contract between business and engineering** for what the system must do
- **The basis for testing** — every requirement has acceptance criteria a tester can implement
- **The basis for audit** — every requirement traces to a stakeholder need and a regulatory or business source
- **A multi-audience document** — read by business, engineering, QA, compliance, operations

An FSD is **not**:

- A user manual (don't explain how to use the future product)
- A design document (don't choose technology stacks)
- A project plan (don't schedule)
- A marketing document (don't sell the system)

This distinction is essential. Many "FSDs" in the wild are some hybrid of all four. Real FSDs stay in their lane.

---

## The 9 rules (binding for every FSD)

These are non-negotiable. Every FR / NFR / use case in every FSD this skill produces honors these.

1. **Every requirement has a unique stable ID** that never gets renumbered (FR-NNN, NFR-XXX-NN, UC-NN, BR-NN, G-NN, S-NN). Gaps after deletion are fine.

2. **Every requirement uses "shall"** to denote binding. "Should" for recommendation, "may" for option, "will" for declaration. No other modal verbs.

3. **Every requirement is atomic** — one behavior per statement. Compound requirements get split.

4. **Every requirement has acceptance criteria** in GIVEN/WHEN/THEN form. If you can't write Gherkin, the requirement isn't testable yet.

5. **Every requirement has a MoSCoW priority** (Must/Should/Could/Won't), assigned after the full FR list exists.

6. **Every requirement traces to a business goal and a stakeholder** via the RTM.

7. **Every requirement has a verification method** (Test / Inspection / Demonstration / Analysis).

8. **Every NFR has a measurable threshold** in its statement. Adjectives without measurement are not requirements.

9. **The FSD separates what (FRs) from how (design)** — implementation choices belong in the SDD, not the FSD.

These rules are checked by the `fsd-validator` agent. They are not aspirations; they are the gate.

---

## The six-phase process

Each agent runs phases within the workflow. The skill's role is to tell each agent what to do at which phase.

### Discovery agent — 6 steps

1. Inventory sources (business case, interview notes, process docs, regulatory citations)
2. Load skill references (`discovery-brief-format.md`, `babok-techniques.md`)
3. Read sources thoroughly (including diagrams)
4. Apply BABOK stakeholder analysis (identification, RACI, power-interest)
5. Synthesize into the Discovery Brief template (15 sections)
6. Confirm and stop — list critical open questions for user resolution

### Architect agent — 6 phases

1. Read the discovery brief; refuse if critical questions unanswered
2. Load skill references (`iso-29148-template.md`)
3. Plan the FSD structure (capabilities → FR numbering blocks; use case inventory)
4. Write the FSD following the ISO 29148 structure with BABOK techniques (load `requirements-quality.md` and `use-case-templates.md` here)
5. Self-review against critical quality criteria
6. Deliver the FSD with a 4-sentence summary

### Validator agent — 5 steps

1. Read the FSD
2. Load `quality-checklist.md` and `requirements-quality.md`
3. Run every check in order; record PASS/FAIL/NA per check with citation
4. Write the validation report with verdict (Ready / Needs Revision / Requires Rewrite)
5. Confirm and stop — point at the top 3 priority fixes

### Traceability agent — 4 steps

1. Read the FSD (after validator passes)
2. Load `traceability-matrix-format.md`
3. Extract every FR/NFR; build the wide RTM table; build the 5 orthogonal views
4. Write the RTM to Appendix C inline (small FSDs) or to companion file (large FSDs)

---

## Reference loading — what to load when

Do not preload all references. Load each just-in-time per phase to keep model context efficient (especially on open-weights).

| Reference | Loaded by | At |
|---|---|---|
| `discovery-brief-format.md` | discovery | Step 2 |
| `babok-techniques.md` | discovery | Step 2; also architect Phase 4 if needed |
| `iso-29148-template.md` | architect | Phase 2 |
| `requirements-quality.md` | architect (Phase 4) and validator (Step 2) | as listed |
| `use-case-templates.md` | architect | Phase 4 (when writing §9) |
| `quality-checklist.md` | validator | Step 2 |
| `traceability-matrix-format.md` | traceability | Step 2 |
| `open-weights-tips.md` | any agent on open-weights | as needed |

---

## References overview

| File | Lines | Purpose |
|---|---|---|
| `requirements-quality.md` | ~280 | The 9 properties; the FR template; "shall" vocabulary discipline; MoSCoW calibration; the 20 common defects |
| `iso-29148-template.md` | ~270 | The 12-section FSD structure; per-section content guide; what-goes-where decisions |
| `babok-techniques.md` | ~220 | Stakeholder analysis, elicitation, BPMN, decision tables, MoSCoW, RTM, INVEST |
| `discovery-brief-format.md` | ~210 | The discovery brief template — the contract between discovery and architect |
| `use-case-templates.md` | ~190 | Cockburn fully-dressed + Jacobson Use Case 2.0 slices |
| `traceability-matrix-format.md` | ~190 | RTM table format, 5 orthogonal views, validator checks |
| `quality-checklist.md` | ~240 | 16 sections of pass/fail checks; the validator's master list |
| `open-weights-tips.md` | ~180 | Per-model tuning, workflow adjustments, failure modes |

Total: ~1,780 lines of methodology, loaded selectively per agent and per phase.

---

## How this skill compares to GitHub Spec Kit

[GitHub Spec Kit](https://github.com/github/spec-kit) is the most popular AI spec framework (71K+ stars). It uses a four-phase workflow: `/specify` → `/plan` → `/tasks` → `/implement`.

Spec Kit is for **spec-driven code generation**: write a spec, let an AI agent generate the code. The "spec" in Spec Kit is lightweight — focused on user journeys and acceptance criteria, optimized for downstream code generation.

This skill is for **enterprise FSD authoring**: produce a regulator-grade FSD with full BABOK structure, ISO 29148 compliance, and RTM. The FSD is a document, not a prompt for code generation.

| Aspect | Spec Kit | fsd-authoring |
|---|---|---|
| Standards followed | None specifically | ISO/IEC/IEEE 29148, BABOK v3, ISO 25010, Use Case 2.0 |
| Primary audience | Coding agents | Business + engineering + compliance + audit |
| Output | Lightweight spec + plan + tasks | Multi-section FSD + RTM |
| Stakeholder analysis | Implicit (user stories) | Explicit (BABOK §10.43, RACI, Power-Interest) |
| Requirements format | User stories | Formal FRs with 12-field template |
| Prioritization | None forced | MoSCoW with calibration |
| Traceability | None | Full RTM with 5 orthogonal views |
| Use cases | Often skipped | Mandatory section |
| Regulatory fit | Low (no compliance mapping) | High (compliance coverage view) |

Both are valid. Spec Kit excels at fast turnaround on green-field development. This skill excels at regulated, enterprise, multi-stakeholder projects where the FSD outlives the codebase.

---

## Anti-patterns this skill prevents

The validator agent specifically scans for these:

| Anti-pattern | Why it's bad |
|---|---|
| FR with "and/or" connecting verbs | Atomicity violation; can't test |
| FR with "user-friendly", "robust", "scalable" without metrics | Untestable; defers decision to implementer |
| FR specifying database or vendor product | Over-specification; locks design space |
| Business rule embedded in FR | Policy changes require FR change → unnecessary churn |
| Use case without exception flows | Hides where production bugs are born |
| NFR without measurement point | "Response time ≤ 200ms" — measured where? |
| Goal with 0 traced FRs | Goal isn't being delivered |
| Stakeholder with 0 traced FRs | Either irrelevant or missed in elicitation |
| RTM out of sync with FSD body | Audit risk |
| 80%+ Must priority | Hasn't been prioritized; just labeled |

A document that passes all checks is one a senior BA would sign their name to.

---

## A note on tone

The FSD this skill produces reads as if a careful, experienced BA wrote it for an attentive engineer to implement and an attentive auditor to verify. Plain, precise, every word load-bearing.

The vocabulary discipline is the most visible marker of quality: "shall" / "should" / "may" / "will" used precisely. Auditors read for this discipline. So do experienced engineering leads.

A well-written FSD is not exciting to read. It is exciting to *use*. That's the difference.
