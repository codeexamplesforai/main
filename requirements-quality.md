# Requirements Quality — The Bar

This reference defines what "a good requirement" means. Every functional requirement in every FSD this package produces must satisfy these criteria.

Grounded in **ISO/IEC/IEEE 29148:2018** (Requirements engineering), the **BABOK v3 Guide** (IIBA), and the practitioner conventions used in regulated industries (banking, healthcare, aerospace, defense).

If you internalize nothing else from this skill, internalize this file. Bad requirements cannot be fixed downstream — they cause project failure at every later stage.

---

## The 9 properties of a well-formed requirement

Every functional requirement (FR) and non-functional requirement (NFR) must satisfy all nine. The acronym is **C-U-T-A-C-C-V-P-T** (mnemonic: "Cut a CCVPT").

| Property | What it means | Smell test |
|---|---|---|
| **Correct** | Accurately reflects a real stakeholder need | Can you cite a stakeholder, business goal, or regulatory source for it? |
| **Unambiguous** | Has exactly one interpretation | Could two engineers reading it produce two different implementations both honoring the literal text? If yes, it's ambiguous. |
| **Testable** | Can be verified by test, inspection, demonstration, or analysis | Could a QA engineer write a pass/fail check for it without asking you a question? |
| **Atomic** | Expresses exactly one thing | Does it contain "and" / "or" / "as well as" connecting separable behaviors? Split it. |
| **Complete** | States all conditions, including error paths, timeouts, edge cases | Does it specify what happens when the input is missing/invalid/duplicate/oversized? |
| **Consistent** | Does not contradict any other requirement | Have you grepped the FSD for any FR that contradicts this one? |
| **Verifiable** | The verification method is named (Test/Inspection/Demo/Analysis) | Is the verification approach explicit and feasible? |
| **Prioritized** | MoSCoW (Must / Should / Could / Won't) assigned | Is the priority labeled and justified? |
| **Traceable** | Has a unique ID; links to source, parent goal, and verifying test | Can a regulator follow the thread from business goal → FR → test case? |

These nine are not aspirational. They are the gate. The `fsd-validator` agent checks every FR against all nine. Failed FRs come back to the writer for rework.

---

## The Functional Requirement template

Every FR is rendered with this exact structure. No exceptions, no abbreviations.

```markdown
### FR-NNN — <Short verb-phrase title>

**Statement:** The system shall <verb> <object> when <condition>, producing <observable outcome>.

**Description:** <2–4 sentences elaborating intent, scope, and any boundary conditions.>

**Priority:** Must | Should | Could | Won't (this release)
**Source:** <Stakeholder ID or document section that drove this requirement>
**Rationale:** <One sentence explaining WHY this matters to the business.>
**Verification method:** Test | Inspection | Demonstration | Analysis
**Acceptance criteria:**
  - GIVEN <pre-condition>
    WHEN <triggering action>
    THEN <expected observable outcome>
  - GIVEN <alternate pre-condition>
    WHEN <action>
    THEN <outcome>

**Related use cases:** UC-XX, UC-YY
**Depends on:** FR-AAA, FR-BBB (other requirements that must be satisfied first)
**Conflicts with:** none (or list FR IDs)
**NFR considerations:** <which NFRs apply, e.g. NFR-PERF-02 latency, NFR-SEC-04 audit>
**Compliance refs:** <regulatory citation, if applicable>
**Owner:** <BA owner of this requirement>
**Status:** Draft | Reviewed | Approved | Implemented | Verified | Closed
```

Three things to internalize about this template:

1. **The "shall" verb is mandatory.** Per IEEE 29148: "shall" denotes a binding requirement. "Should" denotes a recommendation (Should-priority requirement). "May" denotes optional. "Will" denotes a declaration of intent. Use only these four; nothing else.

2. **Acceptance criteria use Gherkin (GIVEN/WHEN/THEN).** This forces testable phrasing. If you can't write Gherkin for the FR, the FR isn't testable yet — fix it.

3. **Source must be traceable.** Either a stakeholder ID from the Stakeholder Register, or a document section, or a regulatory citation. "Internal discussion" or "best practice" is not a valid source.

---

## MoSCoW prioritization — how to actually assign it

The four buckets, with the BABOK-aligned definition:

| Priority | Definition | Test |
|---|---|---|
| **Must** | Failure to deliver this means the release has failed and cannot go live. | "If we drop this, do we cancel the launch?" If yes, Must. |
| **Should** | Important but not vital to launch. Workaround acceptable for first release. | "Will users complain loudly but keep using the product?" Should. |
| **Could** | Nice to have. Included if time permits without compromising Must/Should. | "Would users notice if we silently dropped this?" If "barely", Could. |
| **Won't** | Explicitly out of scope for this release. Captured to avoid re-litigation. | "Has someone asked for this and we said no?" Won't. |

**Calibration check:** if your FSD has 80% Must, you haven't prioritized — you've labeled. Healthy distribution is roughly **40% Must / 30% Should / 20% Could / 10% Won't**. The Won't bucket prevents stakeholder amnesia ("but we discussed that") in three months.

---

## The "shall" test — vocabulary discipline

Words to use:

- **shall** — binding requirement
- **should** — recommendation, not binding
- **may** — explicitly optional
- **will** — declaration about the environment or future, not the system being built

Words **never** to use in FR statements:

- "support", "handle", "manage", "deal with", "cover" — vague verbs; specify exact behavior
- "user-friendly", "intuitive", "easy to use", "robust", "scalable", "fast" — non-measurable adjectives; turn into NFR with metric
- "etc.", "and so on", "including but not limited to" — incomplete enumeration; list all cases or define the rule
- "appropriate", "adequate", "sufficient", "reasonable", "as needed" — defers decision to implementer
- "if possible", "to the extent practical", "where applicable" — escape hatches; either it's a requirement or it isn't
- "approximately", "around", "circa", "about N" — replace with a specific tolerance: "100 ms ± 20 ms"
- "and/or" — split into two requirements or pick one

These are not stylistic preferences. ISO 29148 calls them out as defects.

---

## Atomicity — splitting compound requirements

A frequent failure mode: a single sentence describes multiple behaviors.

**Bad (atomicity violation):**
> The system shall allow users to upload, edit, share, and delete documents.

This is four FRs welded together. Split them:

```
FR-101 — Upload document
FR-102 — Edit document
FR-103 — Share document
FR-104 — Delete document
```

Each then gets its own acceptance criteria, priority, dependencies. (Maybe Upload is Must but Share is Should.)

**Bad (hidden conjunction):**
> When the user submits the form, the system shall validate the inputs and persist the record and send a confirmation email.

Three FRs hidden as one. Each can fail independently and each has different acceptance criteria.

---

## Unambiguity — sharpening fuzzy phrases

| Fuzzy phrase | Sharpened replacement |
|---|---|
| "fast response" | "p95 response time ≤ 200 ms" |
| "many users" | "concurrent users ≥ 1,000" |
| "secure" | NFR: "All PII shall be encrypted at rest using AES-256 and in transit using TLS 1.3" |
| "user data" | "PII fields enumerated in Appendix A.3" |
| "occasional batch" | "Once per 24-hour window beginning 02:00 UTC" |
| "modern browser" | "Chrome ≥ 110, Firefox ≥ 110, Safari ≥ 16, Edge ≥ 110" |
| "high availability" | "Uptime ≥ 99.95% measured monthly excluding scheduled maintenance windows" |
| "scalable" | "Horizontal scaling to 10× current peak load within 5 minutes" |
| "graceful degradation" | List specific failure modes and the expected behavior for each |

The pattern: **every adjective is a unit of measurement waiting to happen.** Find the measurement.

---

## INVEST criteria (for user stories specifically)

If FRs are expressed as user stories (some FSDs do this for agile projects), the INVEST criteria apply alongside the 9 properties above:

- **I**ndependent — stories can be developed in any order (or dependencies are explicit)
- **N**egotiable — details can be discussed, the story isn't a frozen spec
- **V**aluable — clear value to a user or business stakeholder
- **E**stimable — engineering can size it
- **S**mall — fits in one iteration (typically 1–8 person-days)
- **T**estable — has acceptance criteria

For regulated/enterprise FSDs, prefer the formal FR template above. User stories are appropriate for agile-managed feature work but lose the rigor regulators expect.

---

## Non-functional requirements — the categories

NFRs are easy to forget because they don't describe behaviors. Use **ISO/IEC 25010** as the checklist. Every FSD must cover (or explicitly mark "Not applicable") each category:

| Category | Examples |
|---|---|
| **Performance efficiency** | Response time, throughput, resource utilization |
| **Reliability** | Availability, fault tolerance, recoverability, MTBF |
| **Usability** | Learnability, accessibility (WCAG level), error prevention |
| **Security** | Authentication, authorization, audit, confidentiality, integrity, non-repudiation |
| **Compatibility** | Interoperability, coexistence with other systems |
| **Portability** | Adaptability to environments, installability |
| **Maintainability** | Modularity, reusability, analyzability, testability |
| **Functional suitability** | Completeness, correctness, appropriateness |

Each NFR uses the same FR template but with measurable constraints in the statement.

**NFR example (good):**

```markdown
### NFR-PERF-01 — Authentication response time

**Statement:** The authentication service shall return a response within 500 ms p99
under sustained load of 1,000 requests per second per region, measured at the
application gateway.

**Priority:** Must
**Source:** Stakeholder S-04 (Head of Engineering); NFR-baseline-v3 from
predecessor system
**Rationale:** Login latency above 500 ms causes measurable churn in the
existing system (8% abandonment per 100 ms increase, measured Q3 2025).
**Verification method:** Test (load test in pre-production environment)
**Acceptance criteria:**
  - GIVEN the auth service is deployed to production
    AND traffic is sustained at 1,000 RPS per region
    WHEN any authentication request is processed
    THEN the response time is ≤ 500 ms at the 99th percentile
    AND no 5xx responses are returned
**Verification artifacts:** k6 load test scripts (TC-PERF-LOAD-01)
```

**NFR example (bad — what we DON'T accept):**

> The system shall be fast and scalable, supporting many concurrent users with
> good performance under load.

Five smells: "fast", "scalable", "many", "good", "under load". Each is a measurement that wasn't taken.

---

## Verification methods — the four allowed values

Per IEEE 29148 and military/aerospace tradition (MIL-STD-961):

- **Test (T)** — execute the system and measure (functional tests, load tests, security tests)
- **Inspection (I)** — visual or document review (code review, design review)
- **Demonstration (D)** — show the operation, observe the outcome (UAT)
- **Analysis (A)** — calculation, simulation, modeling (performance modeling, failure mode analysis)

Every requirement names exactly one. If multiple apply, name the primary; secondary methods go in "verification artifacts".

---

## Common defects — the validator's hit list

The `fsd-validator` agent checks every FR for these defects. Top 20 to scan for:

1. Missing or duplicate FR ID
2. Statement does not use "shall"
3. "and/or" or compound verbs in statement (atomicity)
4. Vague adjective without measurement (ambiguity)
5. Missing priority
6. Priority is Must with no rationale (Must-overload)
7. Missing source (untraceable)
8. Missing acceptance criteria
9. Acceptance criteria not in GIVEN/WHEN/THEN (untestable phrasing)
10. Missing verification method
11. Acceptance criteria mention internal implementation details (over-specification)
12. References another FR that doesn't exist
13. Conflicts with another FR (contradiction)
14. Use case reference doesn't exist
15. Compliance reference is generic ("GDPR") not specific ("GDPR Art. 17 right to erasure")
16. NFR has no measurable threshold
17. Status field missing
18. Owner field missing or "TBD" with no follow-up
19. Two FRs describe the same behavior (duplication)
20. FR is actually a design decision (specifies "how", not "what")

Defect 20 is the most insidious and worth its own note below.

---

## The "what vs how" line

A functional requirement specifies **what** the system must do. A design decision specifies **how** it will do it. FSDs must contain the former and avoid the latter.

**FR (correct):**
> The system shall persist transaction records for at least 7 years.

**Design decision (does not belong in an FSD):**
> The system shall use PostgreSQL with monthly partitioning and tape-archive after 90 days for transaction records.

The retention period is a business requirement. The choice of PostgreSQL and partitioning is an engineering decision. Mixing them in the FSD over-specifies, prevents alternative implementations, and locks design decisions before engineering has done its job.

When in doubt: would the requirement still be true if we picked a completely different technology stack? If yes, it's an FR. If no, it's a design decision — move it to the SDD (System Design Document) or ADR.

---

## A note on traceability

Traceability is the property that lets you answer the regulator's question: *"For this regulation/business goal, show me the requirement that addresses it, the design that implements it, the test that verifies it, and the evidence the test passed."*

A complete traceability chain looks like this:

```
Business Goal (G-01)
   ↓
Stakeholder Need (SN-04 — from S-12 interview)
   ↓
Functional Requirement (FR-203)
   ↓
Use Case (UC-15) [if applicable]
   ↓
Test Case (TC-403)
   ↓
Test Result (TR-2026-04-15-403)
```

The `fsd-traceability` agent in this package builds the Requirements Traceability Matrix (RTM) that makes this chain navigable. The FSD owns one end of the chain; the test plan owns the other. Both must use the same FR IDs.

---

## Calibration: what good looks like

To calibrate yourself, ask of each FR you write or review:

1. Could you hand this FR to a contracted vendor and let them implement it without coming back to ask questions?
2. Could you hand this FR to a QA engineer and let them write a complete test plan without coming back to ask questions?
3. Could you hand this FR to an auditor 18 months from now and have them understand why it exists and how it was verified?

Three yeses = ready. Any no = rework.

This bar is the difference between a document that ships software and a document that gets photocopied into a project archive and never looked at again.
