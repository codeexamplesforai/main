# ISO/IEC/IEEE 29148:2018 — FSD Template

This reference is the **structural backbone** of every FSD this package produces. It is grounded in ISO/IEC/IEEE 29148:2018 (the modern unified requirements engineering standard, successor to IEEE 830-1998) and adapted with BABOK v3 conventions.

The structure below is opinionated: certain optional 29148 sections are made mandatory (because audit trails matter), and certain BABOK techniques are layered in (stakeholder register, business goals, RTM).

If your client is in a regulated industry (banking, healthcare, defense, pharma, aerospace, automotive), this is the structure their auditors expect to see. Departures from it must be justified.

---

## Document structure (canonical section ordering)

```
0.   Document Control
1.   Introduction
     1.1  Purpose
     1.2  Document Conventions
     1.3  Intended Audience
     1.4  Project Scope
     1.5  References
     1.6  Glossary  (or pointer to Appendix A)
2.   Business Context
     2.1  Business Problem
     2.2  Business Goals & Success Metrics
     2.3  Stakeholder Register
     2.4  Current State (As-Is)
     2.5  Future State (To-Be)
     2.6  Gap Analysis
3.   Overall Description
     3.1  Product Perspective
     3.2  Product Functions (capability map)
     3.3  User Classes & Characteristics
     3.4  Operating Environment
     3.5  Design & Implementation Constraints
     3.6  Assumptions & Dependencies
4.   External Interface Requirements
     4.1  User Interfaces
     4.2  Hardware Interfaces  (typically N/A for SaaS)
     4.3  Software Interfaces  (integrations, APIs consumed)
     4.4  Communication Interfaces  (protocols, message formats)
5.   Functional Requirements
     5.1  Capability 1 — <name>
          5.1.1  Description & Priority
          5.1.2  Stimulus/Response sequences
          5.1.3  Functional Requirements (FR-1xx)
     5.2  Capability 2 — <name>
     ...
6.   Non-Functional Requirements
     6.1  Performance
     6.2  Reliability & Availability
     6.3  Security
     6.4  Usability & Accessibility
     6.5  Compatibility & Interoperability
     6.6  Portability
     6.7  Maintainability
     6.8  Compliance & Regulatory
7.   Data Requirements
     7.1  Data Entities (logical)
     7.2  Data Retention & Lifecycle
     7.3  Data Quality & Validation
     7.4  Data Privacy Classification
8.   Business Rules
     8.1  Decision Rules
     8.2  Calculation Rules
     8.3  Validation Rules
     8.4  Authorization Rules
9.   Use Cases
     (one per significant interaction, see use-case-templates.md)
10.  Out of Scope & Future Considerations
11.  Risks, Issues & Open Questions
12.  Approvals & Sign-Off
Appendices
A.   Glossary
B.   Acronyms
C.   Requirements Traceability Matrix (RTM)
D.   Mockups / Wireframes (if applicable)
E.   Reference Documents
F.   Revision History
```

Every section above appears in every FSD, **in this order**, even if a section is "Not applicable in this release" — write that explicitly rather than omitting the section. Auditors expect to find every section; missing sections raise questions about whether they were considered.

---

## Section-by-section content guide

### Section 0 — Document Control

A small table at the very top:

```markdown
| Field | Value |
|---|---|
| Document title | <Project> Functional Specification Document |
| Document ID | FSD-<PROJECT>-<NN> |
| Version | 1.0 |
| Status | Draft / In Review / Approved / Baselined |
| Author(s) | <name>, <role> |
| Reviewers | <names and roles> |
| Approval authority | <name(s), role(s)> |
| Last modified | YYYY-MM-DD |
| Classification | Internal / Confidential / Restricted |
| Distribution list | <names or DLs> |
```

This table is the only place this metadata appears. Don't repeat it elsewhere.

### Section 1 — Introduction

**1.1 Purpose.** Two or three sentences. What this FSD documents, and what it does not. Example: *"This FSD describes the functional and non-functional requirements for the Phase 2 release of the Customer Onboarding System. It does not include implementation design (see SDD-CUSTONBD-001) nor test cases (see TP-CUSTONBD-001)."*

**1.2 Document Conventions.** Vocabulary discipline (per `requirements-quality.md`):
- "shall" denotes a binding requirement
- "should" denotes a recommendation
- "may" denotes an option
- "will" denotes a declaration of intent or future action by an actor

State this verbatim. Auditors check for it.

**1.3 Intended Audience.** Multi-audience reading guide. Example:
- Business Analysts — read all sections
- Product Managers — read 1, 2, 5, 6
- Engineers — read 3, 4, 5, 6, 7, 8, 9
- QA — read 5, 6, 7, 8, 9, Appendix C
- Compliance — read 1, 2, 6.8, 7.4, 8, Appendix C
- Operations — read 4, 6.1, 6.2, 6.3

**1.4 Project Scope.** What the system delivers and the business value. 1–2 paragraphs. Reference the business case if one exists.

**1.5 References.** Numbered list of every external document this FSD depends on (regulations, predecessor FSDs, vendor specifications, ADRs). Format: `[1] ISO/IEC/IEEE 29148:2018. IEEE. 2018.`

**1.6 Glossary.** Either inline (short FSDs) or a pointer: *"See Appendix A — Glossary."*

### Section 2 — Business Context

This section is what separates a real FSD from a code-generation prompt. Spend time here.

**2.1 Business Problem.** 1–2 paragraphs. State the problem in business terms, not solution terms. *"Our customer onboarding process takes an average of 8 business days, of which 6 are manual review steps that could be automated. The current FY revenue loss attributable to drop-off during onboarding is estimated at $2.3M (Finance, Q3 2025)."*

**2.2 Business Goals & Success Metrics.** Each goal gets a unique ID (G-NN), a one-line statement, and one or more measurable success metrics with current baseline and target value.

```markdown
| ID | Business Goal | Success Metric | Baseline | Target | Owner |
|----|---------------|----------------|----------|--------|-------|
| G-01 | Reduce onboarding cycle time | Median onboarding days | 8 days | ≤ 2 days | COO |
| G-02 | Reduce manual review burden | Manual reviews / 100 applications | 100 | ≤ 30 | Head of Ops |
| G-03 | Maintain compliance posture | KYC checks passing audit | 100% | 100% | CCO |
```

Every FR in the FSD must trace to at least one business goal. The validator checks this.

**2.3 Stakeholder Register.** Per BABOK v3. Each stakeholder gets ID, role, RACI position (responsible/accountable/consulted/informed), influence (low/medium/high), and interest. This is what makes traceability work.

```markdown
| ID | Name / Role | RACI | Influence | Interest | Concerns |
|----|-------------|------|-----------|----------|----------|
| S-01 | COO | Accountable | High | High | Cycle time, cost |
| S-02 | Head of Compliance | Consulted | High | High | Regulatory adherence |
| S-03 | Onboarding ops team | Responsible | Medium | High | Day-to-day workflow |
| S-04 | Customer (external) | Informed | Low | High | Experience, speed |
```

**2.4 Current State (As-Is).** Describe the existing process, system, or absence thereof. Where possible include a BPMN diagram or a numbered process flow. List the top pain points with measurable impact.

**2.5 Future State (To-Be).** The target operating model post-implementation. BPMN diagram preferred. This is the "vision" the FRs collectively deliver.

**2.6 Gap Analysis.** What changes between as-is and to-be. Usually rendered as a table: capability / as-is / to-be / change required.

### Section 3 — Overall Description

**3.1 Product Perspective.** Where this system sits in the larger ecosystem. Context diagram (the only diagram that's worth doing in ASCII if no better option). Lists upstream and downstream systems, with their role.

**3.2 Product Functions.** The capability map. Not requirements yet — a hierarchical decomposition of capabilities. Example:

```
Customer Onboarding
├── Identity verification
│   ├── Document capture
│   ├── Document authentication
│   └── Biometric matching
├── Risk assessment
│   ├── Sanctions screening
│   ├── PEP screening
│   └── Adverse media screening
├── Account provisioning
│   ├── Account creation
│   ├── Initial credentials
│   └── Welcome communication
└── Compliance reporting
    └── SAR triggering
```

Each leaf becomes a Section 5 subsection.

**3.3 User Classes & Characteristics.** Per ISO 29148 §6.1.2.3. Describe each user class: who they are, what they need, technical proficiency, frequency of use, criticality.

**3.4 Operating Environment.** Hardware, OS, browser support, network requirements, deployment topology. State actual values; no "modern" or "current".

**3.5 Design & Implementation Constraints.** Anything that constrains the engineering choice space and isn't itself a functional/non-functional requirement: language/framework mandates from architecture standards, hosting requirements (on-prem only, FedRAMP, data residency), branding/UX guidelines to comply with, etc.

**3.6 Assumptions & Dependencies.** Each as a separate row with ID:
- **Assumptions** (A-NN): things believed true but not verified. Risk if assumption is wrong.
- **Dependencies** (D-NN): external things required for this project to succeed (other teams' deliverables, vendor SLAs, regulatory approvals).

### Section 4 — External Interface Requirements

**4.1 User Interfaces.** Not a UI spec (that's a separate UX document), but a description of: which user personas have UI access, what major UI surfaces exist (web app, mobile, kiosk), accessibility requirements (WCAG 2.1 AA at minimum), localization requirements.

**4.2 Hardware Interfaces.** Devices the system reads from or writes to: card readers, ID scanners, signature pads. For pure SaaS, state "Not applicable."

**4.3 Software Interfaces.** Every integration with another system. For each: system name, version, owner, integration purpose, direction (in/out/bidirectional), protocol, authentication, fallback behavior.

**4.4 Communication Interfaces.** Protocols, message formats, encryption requirements. Reference the API spec by ID if one exists.

### Section 5 — Functional Requirements

The heart of the document. One subsection per capability from §3.2. Each subsection has:

**5.X.1 Description & Priority.** 2–4 sentences. Capability-level MoSCoW priority.

**5.X.2 Stimulus/Response Sequences.** One paragraph or numbered list. The trigger and the resulting behavior at a capability level. Detailed steps go in the use cases (§9).

**5.X.3 Functional Requirements.** A series of FRs using the template from `requirements-quality.md`. Numbering convention: each capability uses a numbering block (5.1 = FR-100 series; 5.2 = FR-200 series; etc.). Within each block, leave gaps for future requirements (FR-101, FR-102, ..., FR-110 — skip FR-103 if a requirement is removed; don't renumber).

### Section 6 — Non-Functional Requirements

Use ISO/IEC 25010 categories (see `requirements-quality.md`). One subsection per category. For each NFR, use the same FR template but with measurable thresholds in the statement. Numbering: NFR-PERF-01, NFR-SEC-01, etc.

A common failure: writing NFRs as adjective lists ("must be secure, scalable, performant"). NFRs that aren't measured aren't requirements — they're wishes.

### Section 7 — Data Requirements

**7.1 Data Entities (logical).** The conceptual data model. Each entity: name, definition, key attributes, relationships. Not a physical schema — that's the SDD's job.

**7.2 Data Retention & Lifecycle.** Per entity: retention period, archival rules, deletion triggers, regulatory basis.

**7.3 Data Quality & Validation.** Validation rules at the data level (cross-cutting; specific validations live in FRs). Reference business rules in §8.

**7.4 Data Privacy Classification.** Per entity / per field: classification (Public / Internal / Confidential / Restricted), PII status, regulatory scope (GDPR / CCPA / HIPAA / PCI-DSS).

### Section 8 — Business Rules

Per BABOK, business rules are organizational policies that constrain the system but are not requirements themselves. They drive requirements.

Categories:
- **8.1 Decision Rules** — conditional logic the business has decided ("if customer is high-risk, escalate to manual review")
- **8.2 Calculation Rules** — formulas (interest rate calculations, eligibility scores)
- **8.3 Validation Rules** — data integrity ("phone number must match E.164")
- **8.4 Authorization Rules** — who can do what

Each rule gets a unique ID (BR-NN), statement, source, effective date, owner. FRs reference BRs by ID.

### Section 9 — Use Cases

One use case per significant interaction. Use the format in `use-case-templates.md`. Use cases give the narrative; FRs give the testable specs. Both are needed.

### Section 10 — Out of Scope & Future Considerations

Explicit list of things this release does NOT do. Two purposes:
1. Prevent scope creep ("we discussed that and it's W-12 in the Won't list")
2. Capture future roadmap so the next FSD can pick up where this one left off

Format: numbered list, each item with one-sentence rationale.

### Section 11 — Risks, Issues & Open Questions

Per BABOK risk register conventions.

**Risks** — things that *might* happen and would impact the project:

```markdown
| ID | Risk | Probability | Impact | Severity | Mitigation | Owner |
|----|------|-------------|--------|----------|-----------|-------|
| R-01 | Vendor X delays API delivery beyond Q2 | Medium | High | High | Build mock; renegotiate SLA | PM |
```

**Issues** — things that *have* happened and need resolution:

```markdown
| ID | Issue | Raised by | Raised on | Status | Resolution |
|----|-------|-----------|-----------|--------|-----------|
| I-01 | Conflict between FR-203 and FR-407 | A. Smith | 2026-01-15 | Open | TBD |
```

**Open Questions** — things needed to complete the FSD that the BA cannot resolve alone:

```markdown
| ID | Question | Owner | Needed by | Status |
|----|----------|-------|-----------|--------|
| Q-01 | Confirm retention period for KYC documents | Compliance | 2026-02-01 | Open |
```

### Section 12 — Approvals & Sign-Off

A table with one row per approving authority and signature/date columns. Initial version is blank; gets filled in as approvals occur. Without this section, you do not have an FSD — you have a draft.

### Appendices

**A. Glossary.** Every domain term used in the document. Sorted alphabetically. Two columns: term, definition. Resolve acronyms here too unless you have a separate Acronyms appendix.

**B. Acronyms.** Alphabetical. Two columns: acronym, expansion.

**C. Requirements Traceability Matrix (RTM).** Produced by the `fsd-traceability` agent. Cross-references: FR ↔ business goal ↔ stakeholder ↔ use case ↔ verification method ↔ test case.

**D. Mockups / Wireframes.** If applicable. Otherwise omit (don't include placeholder content).

**E. Reference Documents.** Pointers to related documents (predecessor FSDs, SDD, test plan, business case, regulatory citations).

**F. Revision History.** Table of versions with date, author, summary of changes.

---

## What goes where — common decisions

| Content | Belongs in | Not in |
|---|---|---|
| "The system shall encrypt PII at rest using AES-256" | NFR-SEC | FR (it's non-functional) |
| "When user submits form, system validates required fields" | FR | Business rule |
| "Required fields are name, email, DOB" | Business rule (BR-NN) referenced by FR | FR statement |
| "Use PostgreSQL with monthly partitioning" | SDD, not FSD | FSD |
| "Retention is 7 years for transaction records" | Data Requirements §7.2 | FR (it's a constraint) |
| "User flow for password reset" | Use Case (§9) | FR (FRs are atomic; use case is narrative) |
| "ID verification uses Vendor X API" | Software Interface §4.3 | Buried in FR description |
| "Customer must be 18+ to register" | Business Rule (BR-NN), referenced by FR | FR (BR can change without code change) |
| "p95 response time ≤ 200 ms" | NFR-PERF | FR description |
| "Mobile-first responsive design" | NFR-USABILITY or §3.5 constraint | FR |
| "We'll discuss mobile app in Phase 3" | §10 Out of Scope | Anywhere else |

When in doubt: ask "is this a behavior the system performs, a quality it must possess, or a policy that constrains it?" → FR / NFR / BR.

---

## What this template deliberately excludes

- **Code samples.** FSD describes behavior, not implementation.
- **Database schemas.** Logical entities yes; physical schema no.
- **Specific technology choices** (frameworks, libraries). Constraints yes; choices no.
- **Test cases.** Acceptance criteria yes; full test scripts no.
- **Project plan / timeline.** That's a separate project management artifact.
- **Detailed UI designs.** Wireframes optional; full design specs belong in UX doc.

If a stakeholder asks for any of the above in the FSD, redirect them to the appropriate document. Letting these creep in muddles audiences and ages the FSD prematurely.

---

## One final note on tone

A good FSD reads as if a careful, experienced BA wrote it for an attentive, experienced engineer to implement and an attentive auditor to verify. It is not:

- Marketing copy (don't sell the system)
- A user manual (don't explain how to use the future product)
- A philosophical document (don't discuss why the business cares about X — that belongs in the business case)
- Pseudo-code (don't write IF/THEN as if you were coding)

Plain, precise, every word load-bearing. Future-tense for the system being built ("the system shall ..."), present-tense for the current state ("the existing process requires ..."), past-tense for prior decisions ("the steering committee approved on YYYY-MM-DD that ...").
