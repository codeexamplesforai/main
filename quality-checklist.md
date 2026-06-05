# FSD Quality Checklist

Run this checklist after the FSD is drafted and before delivery / sign-off. Every fail must be fixed.

Grounded in ISO/IEC/IEEE 29148 quality criteria, BABOK v3 verification practices, and practitioner conventions from regulated industries.

The `fsd-validator` agent runs this checklist mechanically and produces a pass/fail report. The bar is binary — partial credit is FAIL.

---

## Section 1 — Document control & structure

| # | Check | Pass = |
|---|---|---|
| 1.1 | Document Control table (§0) present with all 10 fields | Yes |
| 1.2 | Document has version, status, author, last-modified date | Yes |
| 1.3 | All 12 mandatory FSD sections present in canonical order | Yes (use "Not applicable" rather than omit) |
| 1.4 | All required appendices (A, B, C, F) present | Yes |
| 1.5 | Section numbering consistent (§1, §1.1, §1.1.1) | Yes |
| 1.6 | FSD-wide ID schemes used consistently (G-NN, S-NN, FR-NNN, BR-NN, UC-NN, NFR-XXX-NN) | Yes |

---

## Section 2 — Introduction & context

| # | Check | Pass = |
|---|---|---|
| 2.1 | Purpose statement (§1.1) names what FSD covers and what it does NOT | Yes |
| 2.2 | Document conventions (§1.2) defines "shall/should/may/will" | Yes |
| 2.3 | Audience guide (§1.3) names ≥3 distinct audiences with reading paths | Yes |
| 2.4 | Business problem (§2.1) stated in business terms, not solution terms | Yes |
| 2.5 | Business goals (§2.2) have unique IDs, measurable metrics, baselines, targets | Yes (all four for every goal) |
| 2.6 | Stakeholder register (§2.3) has ≥6 stakeholders covering all standard categories | Yes |
| 2.7 | Each stakeholder has RACI position, influence, interest, concerns | Yes |
| 2.8 | Current state (§2.4) describes existing process and pain points | Yes |
| 2.9 | Future state (§2.5) describes target operating model | Yes |
| 2.10 | Gap analysis (§2.6) explicitly compares as-is vs to-be | Yes |

---

## Section 3 — Overall description

| # | Check | Pass = |
|---|---|---|
| 3.1 | Product perspective (§3.1) includes a context diagram or description | Yes |
| 3.2 | Capability map (§3.2) is hierarchical, 2–3 levels deep | Yes |
| 3.3 | User classes (§3.3) named with characteristics (frequency, expertise, criticality) | Yes |
| 3.4 | Operating environment (§3.4) names specific versions/platforms | No "modern" or "current" |
| 3.5 | Design constraints (§3.5) listed with rationale | Yes |
| 3.6 | Assumptions (§3.6) each have ID, statement, confidence, risk if wrong | Yes |
| 3.7 | Dependencies (§3.6) each have ID, owner, needed-by date, status | Yes |

---

## Section 4 — Interfaces

| # | Check | Pass = |
|---|---|---|
| 4.1 | Software interfaces (§4.3) name every integration with: system, version, owner, purpose, direction, protocol, auth, fallback | Yes |
| 4.2 | Communication interfaces (§4.4) specify protocols and encryption | Yes |
| 4.3 | Hardware interfaces (§4.2) — N/A explicitly stated if not applicable | Yes |

---

## Section 5 — Functional requirements (the core)

Run these checks on **every single FR**. The validator iterates.

| # | Check | Pass = |
|---|---|---|
| 5.1 | FR has unique ID (FR-NNN) | Yes |
| 5.2 | FR ID not reused or duplicated anywhere in document | Yes |
| 5.3 | FR statement uses "shall" (not "should/may/will" unless intentional) | Yes |
| 5.4 | FR statement is atomic (no "and/or" connecting separable behaviors) | Yes |
| 5.5 | FR statement free of vague adjectives ("appropriate", "robust", "fast", etc.) | Yes |
| 5.6 | FR statement free of incomplete enumeration ("etc.", "and so on") | Yes |
| 5.7 | FR has a Description elaborating intent (2–4 sentences) | Yes |
| 5.8 | FR has explicit Priority (Must/Should/Could/Won't) | Yes |
| 5.9 | FR has Source field that's traceable (stakeholder ID, doc section, or citation) | Yes |
| 5.10 | FR has Rationale (one sentence WHY) | Yes |
| 5.11 | FR has Verification method (Test/Inspection/Demonstration/Analysis) | Yes |
| 5.12 | FR has Acceptance criteria in GIVEN/WHEN/THEN form | Yes (≥1 criterion) |
| 5.13 | Acceptance criteria are testable without further clarification | Yes |
| 5.14 | FR has Status field | Yes |
| 5.15 | FR specifies "what" not "how" (no implementation specifics) | Yes |
| 5.16 | FR does not duplicate another FR | Yes |
| 5.17 | FR does not contradict another FR | Yes |

| # | Section-level check | Pass = |
|---|---|---|
| 5.18 | Each capability subsection has its own FR numbering block | Yes |
| 5.19 | FR numbering has intentional gaps for future additions (no renumbering after removal) | Yes |
| 5.20 | Capability priority is set (high-level MoSCoW for the capability itself) | Yes |
| 5.21 | Stimulus/response sequences described per capability | Yes |

---

## Section 6 — Non-functional requirements

| # | Check | Pass = |
|---|---|---|
| 6.1 | All 8 ISO/IEC 25010 categories addressed (or explicitly N/A) | Yes |
| 6.2 | Every NFR uses the same template as FRs (statement, priority, source, AC, etc.) | Yes |
| 6.3 | Every NFR has a MEASURABLE threshold in its statement | Yes |
| 6.4 | No NFR contains generic adjectives ("secure", "scalable") without metrics | Yes |
| 6.5 | NFR IDs follow NFR-CATEGORY-NN convention | Yes |
| 6.6 | Security NFRs cover: authn, authz, audit, confidentiality, integrity | Yes |
| 6.7 | Performance NFRs name percentile + load condition + measurement point | Yes |
| 6.8 | Reliability NFRs include uptime/availability target with measurement window | Yes |
| 6.9 | Compliance NFRs cite specific regulation/article (not generic "GDPR") | Yes |

---

## Section 7 — Data requirements

| # | Check | Pass = |
|---|---|---|
| 7.1 | Logical data entities listed with definitions | Yes |
| 7.2 | Retention period specified per entity with regulatory basis | Yes |
| 7.3 | Data privacy classification per entity (Public/Internal/Confidential/Restricted) | Yes |
| 7.4 | PII fields explicitly flagged | Yes |
| 7.5 | Regulatory scope (GDPR/CCPA/HIPAA/PCI) named where applicable | Yes |

---

## Section 8 — Business rules

| # | Check | Pass = |
|---|---|---|
| 8.1 | Business rules separated from FRs (in §8, not embedded in FR statements) | Yes |
| 8.2 | Each BR has unique ID (BR-NN), statement, source, owner, effective date | Yes |
| 8.3 | Complex decision logic rendered as decision table where ≥3 conditions | Yes |
| 8.4 | FRs reference BRs by ID rather than restating policy | Yes |

---

## Section 9 — Use cases

| # | Check | Pass = |
|---|---|---|
| 9.1 | At least one use case per significant interaction | Yes |
| 9.2 | Each use case has primary actor, preconditions, postconditions, main flow, extensions | Yes |
| 9.3 | Use case name is a verb phrase from actor's perspective | Yes |
| 9.4 | Main success scenario steps are numbered and start with actor or system | Yes |
| 9.5 | At least one alternative or exception flow per significant decision point | Yes |
| 9.6 | Each use case lists Related FRs by ID | Yes |
| 9.7 | Use case does not contain implementation details | Yes |

---

## Section 10 — Out of scope

| # | Check | Pass = |
|---|---|---|
| 10.1 | Out of scope section present | Yes |
| 10.2 | At least 5 items listed (small projects) or ≥10 (large projects) | Yes |
| 10.3 | Each out-of-scope item has a rationale | Yes |

If §10 has 0–2 items, you haven't thought about boundaries enough. Re-examine.

---

## Section 11 — Risks, issues, open questions

| # | Check | Pass = |
|---|---|---|
| 11.1 | Risk register present with at least 3 risks | Yes (no real project has zero risks) |
| 11.2 | Each risk has probability, impact, severity, mitigation, owner | Yes |
| 11.3 | Open questions section present | Yes |
| 11.4 | Any open question marked "blocks FSD baseline" has a needed-by date | Yes |

---

## Section 12 — Approvals

| # | Check | Pass = |
|---|---|---|
| 12.1 | Approvals section present with placeholders for all required signers | Yes |
| 12.2 | Required signers include: sponsor, compliance, architect, product owner | Yes (depending on industry) |
| 12.3 | Document status field is consistent with signature state | Yes |

---

## Section 13 — Appendix C — Requirements Traceability Matrix

| # | Check | Pass = |
|---|---|---|
| 13.1 | RTM present in Appendix C or as companion file | Yes |
| 13.2 | Every FR in §5 and NFR in §6 appears as a row in the RTM | Yes |
| 13.3 | Every row links to ≥1 business goal | Yes |
| 13.4 | Every row links to ≥1 stakeholder | Yes |
| 13.5 | Every row has a non-empty Source | Yes |
| 13.6 | Every row has a Verification method | Yes |
| 13.7 | Goal coverage view present (every goal has ≥1 FR) | Yes |
| 13.8 | Compliance coverage view present (every regulation cited has ≥1 FR) | Yes |
| 13.9 | RTM IDs match FSD body (no drift) | Yes |

---

## Section 14 — Cross-document consistency

| # | Check | Pass = |
|---|---|---|
| 14.1 | Glossary in Appendix A defines every domain term used in body | Yes |
| 14.2 | Acronyms in Appendix B include every acronym used in body | Yes |
| 14.3 | FRs referenced from use cases all exist in §5 | Yes |
| 14.4 | BRs referenced from FRs all exist in §8 | Yes |
| 14.5 | Stakeholders referenced from FR Source fields all exist in §2.3 | Yes |
| 14.6 | Business goals referenced from FRs all exist in §2.2 | Yes |

A FAIL in this section means broken references inside the document. The validator finds these mechanically.

---

## Section 15 — Multi-audience usability

The "can each audience use this document standalone?" test:

| # | Audience | Lens needed | Pass = |
|---|---|---|---|
| 15.1 | Executive sponsor | One-paragraph business problem + goals + scope | Can read §1, §2.1, §2.2, §10 and walk away informed |
| 15.2 | Compliance officer | Reg citations + audit FRs + data privacy + RTM compliance view | Can find compliance coverage in <5 minutes |
| 15.3 | Engineer | FRs, NFRs, interfaces, data model, use cases | Can implement without coming back to ask |
| 15.4 | QA | FRs with AC, NFRs with metrics, use cases with extensions | Can write a test plan from this document |
| 15.5 | Architect | Constraints, NFRs, interfaces, data | Can produce an SDD from this document |
| 15.6 | Product owner | Goals, capabilities, MoSCoW | Can defend the scope to senior management |

---

## Section 16 — Tone & language

| # | Check | Pass = |
|---|---|---|
| 16.1 | Body uses "shall" / "should" / "may" / "will" precisely (no other modal verbs in FR statements) | Yes |
| 16.2 | Future tense for system being built; present tense for current state; past tense for prior decisions | Yes |
| 16.3 | No marketing language ("best-in-class", "industry-leading", "cutting-edge") | Yes |
| 16.4 | No editorial commentary ("we believe", "we feel", "obviously") | Yes |
| 16.5 | No pseudo-code or IF/THEN constructs in FR statements | Yes |
| 16.6 | No bare bullets in FR statements; statements are prose sentences | Yes |

---

## Section 17 — Anti-patterns to scan for

Specifically check for these:

| # | Anti-pattern | If present, action |
|---|---|---|
| 17.1 | FR statement contains "user-friendly", "intuitive", "easy" | Convert to measurable NFR (usability test pass rate, task completion time) |
| 17.2 | "The system shall be scalable" without metric | Convert to NFR-PERF with horizontal scale targets |
| 17.3 | Compound FR with multiple "and" connecting verbs | Split into atomic FRs |
| 17.4 | "and/or" anywhere in FR statements | Split or pick |
| 17.5 | FR specifies database table or vendor product | Move to SDD; rewrite FR at behavior level |
| 17.6 | Use case with no extensions/exceptions | Add at least one exception flow per use case |
| 17.7 | NFR with no measurement point ("response time ≤ X seconds" — but measured where?) | Specify measurement point (gateway, client, etc.) |
| 17.8 | RTM has same FR ID twice | Resolve duplicate; consolidate or rename |
| 17.9 | Goal G-NN has 0 traced FRs | Either delete goal or add FRs |
| 17.10 | Stakeholder S-NN has 0 traced FRs | Either remove from register or add FRs |
| 17.11 | "TBD" present without an owner and due date | Either resolve or convert to Q-NN open question |
| 17.12 | FR status "Approved" but FR has unresolved open question | Inconsistency — revert status to Reviewed until question resolved |

---

## Verdict scoring

After running all checks:

- **0 fails** → READY FOR REVIEW (baseline if approvals complete)
- **1–10 fails, none in §1, §5 critical (5.3–5.13), §13** → NEEDS REVISION (fixable in place)
- **Any fail in §1 (structural), §5 critical, §13 (RTM)** → REQUIRES REWRITE OF AFFECTED SECTIONS
- **>20 fails total** → REWRITE FROM DISCOVERY BRIEF (the FSD doesn't match the foundation)

The validator reports the verdict with the top fails first, ordered by severity.

---

## A note on the "Must"-overload

A common failure: 80%+ of FRs marked Must.

This is not a quality fail in any single FR (each may be valid). It is a **prioritization failure** at the document level. The validator flags this:

```
WARN: 87% of FRs marked Must. Healthy distribution is ~40% Must.
Either the project genuinely has nothing to defer, or prioritization
has not been performed. Recommend revisiting MoSCoW with stakeholders.
```

This is a WARN, not FAIL, because it can be intentional in critical regulated work. But it must be acknowledged.

---

## Calibration

A well-crafted FSD typically has:

- 0 fails on first run (very rare — author was uncommonly careful)
- 5–15 fails (normal first draft)
- 30–50 fails (typical first AI-generated draft)
- 100+ fails (the FSD wasn't built from a discovery brief, or template wasn't followed)

The validator runs after each writer pass. Loop until 0 fails or the remaining fails are accepted with documented reason.
