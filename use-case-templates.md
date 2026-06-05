# Use Case Templates

Use cases tell the **narrative** of how an actor achieves a goal via the system. They complement FRs (which are atomic, testable specs). Both are needed:

- **FRs** answer "what must the system do?" — atomic, prioritized, traceable
- **Use cases** answer "how does a user actually accomplish their goal end-to-end?" — narrative, multi-step, with alternative and exception flows

Use cases appear in §9 of the FSD. Each significant interaction warrants one use case.

This reference provides two formats: **Fully Dressed** (formal, per Alistair Cockburn's classic) and **Use Case 2.0** (Ivar Jacobson's modernized, slice-oriented form). Use the fully dressed form for regulated industries; Use Case 2.0 for agile-managed work.

---

## Format 1 — Fully Dressed Use Case (Cockburn)

The canonical formal use case structure. Used in regulated industries (banking, healthcare, defense) because of its rigor.

```markdown
### UC-NN — <Use Case Name as a verb phrase>

**ID:** UC-NN
**Name:** <verb phrase from actor's perspective, e.g., "Submit Onboarding Application">
**Scope:** <system, subsystem, or business process>
**Level:** Sea level | User goal | Subfunction
**Primary actor:** <role / user class — refer to §3.3 of FSD>
**Stakeholders & interests:**
  - <Actor>: <what they want from this interaction>
  - <Other stakeholder>: <what they want / fear>
**Preconditions:** <what must be true before this use case can begin>
**Triggers:** <what initiates this use case (event, time, user action)>
**Postconditions:**
  - Success guarantee: <state after a successful run>
  - Minimal guarantee: <state guaranteed even if something fails>

**Main Success Scenario:**
1. <Actor> <does something>.
2. System <responds>.
3. <Actor> <does next thing>.
4. System validates <condition> and <action>.
5. System persists <outcome> and notifies <party>.
6. Use case ends with <observable end state>.

**Extensions (alternative and exception flows):**
2a. <Condition at step 2>:
    2a1. System <alternative response>.
    2a2. Resume at step 3.
4a. <Validation fails at step 4>:
    4a1. System <error response>.
    4a2. System logs <audit event>.
    4a3. Use case ends; minimal guarantee holds.
5a. <External dependency unavailable at step 5>:
    5a1. System queues the request.
    5a2. System notifies <actor> of delayed processing.
    5a3. Use case ends with delayed-completion state.

**Special requirements (non-functional):**
  - Performance: <response time, throughput>
  - Security: <auth, audit>
  - Compliance: <specific reg citation>

**Technology/data variations (optional):**
  - <Variation name>: <description>

**Frequency of occurrence:** <how often this use case runs>
**Related FRs:** FR-XXX, FR-XXY, FR-XXZ
**Related business rules:** BR-NN, BR-MM
**Related NFRs:** NFR-PERF-NN, NFR-SEC-NN
**Open issues:** <any TBDs specific to this use case>
```

### Worked example — Submit Onboarding Application

```markdown
### UC-03 — Submit Onboarding Application

**ID:** UC-03
**Name:** Submit Onboarding Application
**Scope:** Customer Onboarding System
**Level:** User goal
**Primary actor:** Prospective Customer (S-04)
**Stakeholders & interests:**
  - Prospective Customer: wants to open an account quickly with minimal friction
  - Bank: wants accurate, complete, compliant application data
  - Compliance: wants every required KYC field captured and validated
**Preconditions:**
  - Customer has accessed the application landing page
  - Customer has government-issued ID document available
**Triggers:** Customer clicks "Start Application" on the landing page.
**Postconditions:**
  - Success guarantee: Application is stored with status SUBMITTED;
    confirmation email is queued; reference number is shown to customer
  - Minimal guarantee: If submission fails, customer's partially-entered data
    is preserved for resumption within 7 days; no partial record exists in
    the compliance review queue

**Main Success Scenario:**
1. Customer initiates application; system displays the personal information form.
2. Customer completes personal information (per FR-101) and clicks Next.
3. System validates personal information against business rules BR-04, BR-07
   (per FR-102) and persists the partial application.
4. System displays the identity verification step.
5. Customer uploads government-issued ID document (per FR-105) and confirms.
6. System verifies the document via the Identity Provider integration
   (per FR-108) and stores the verification result.
7. System displays the application summary for customer review.
8. Customer confirms and submits.
9. System assigns a reference number, updates status to SUBMITTED, queues
   the confirmation email, and displays the reference number.
10. Use case ends.

**Extensions:**
3a. Personal information fails validation:
    3a1. System highlights the failing fields with specific error messages (per FR-103).
    3a2. Customer corrects the data; resume at step 3.
6a. Document verification fails (low confidence):
    6a1. System routes the application to manual review queue (per FR-110).
    6a2. System notifies customer that review will be completed within 24 hours.
    6a3. Use case ends with status PENDING_MANUAL_REVIEW.
6b. Identity Provider integration is unavailable:
    6b1. System queues the verification for retry (per FR-112).
    6b2. System notifies customer that verification is in progress.
    6b3. Use case ends with status VERIFICATION_QUEUED.
9a. Email service is unavailable:
    9a1. System persists the application as SUBMITTED.
    9a2. System queues the confirmation email for retry (per NFR-REL-04).
    9a3. Resume at step 10.

**Special requirements:**
  - Performance: Each step transition responds within 1 second p95 (NFR-PERF-01)
  - Security: All PII encrypted in transit and at rest (NFR-SEC-01)
  - Audit: Every state change logged with timestamp, actor, before/after state (NFR-SEC-04)
  - Accessibility: WCAG 2.1 AA conformance (NFR-USA-02)

**Frequency:** ~500 applications per day; peak 80/hour
**Related FRs:** FR-101, FR-102, FR-103, FR-105, FR-108, FR-110, FR-112
**Related business rules:** BR-04 (PII validation), BR-07 (jurisdictional rules)
**Related NFRs:** NFR-PERF-01, NFR-SEC-01, NFR-SEC-04, NFR-USA-02
**Open issues:** Confirm retry policy for email failures (depends on NFR-REL-04 decision)
```

---

## Format 2 — Use Case 2.0 Slices (Jacobson)

Modern, agile-friendly form. A "use case" is decomposed into "slices" — each slice is one specific path through the use case that can be developed independently.

Use this when:
- The team works agile
- Use cases are large and need decomposition for backlog ingestion
- You want explicit per-slice priority

```markdown
### UC-NN — <Use Case Name>

**Primary actor:** <role>
**Goal:** <one sentence>
**Trigger:** <what starts it>
**Slices (test cases through the use case):**

#### Slice UC-NN.1 — Happy path
**Priority:** Must
**Story:** Customer with complete data and valid ID submits a clean application.
**Outcome:** Application accepted; reference number issued.
**Acceptance:**
  - GIVEN customer has completed all required fields
    AND the ID document passes automated verification
    WHEN customer clicks Submit
    THEN application status is SUBMITTED
    AND confirmation email is sent within 60 seconds
    AND reference number is displayed to customer

#### Slice UC-NN.2 — Manual review required
**Priority:** Must
**Story:** Customer's ID verification falls below confidence threshold;
application routes to manual review.
**Outcome:** Application enters PENDING_MANUAL_REVIEW; customer notified.
**Acceptance:**
  - GIVEN ID document verification confidence is below 80%
    WHEN automated verification completes
    THEN application status is PENDING_MANUAL_REVIEW
    AND application appears in the compliance reviewer queue (UC-12)
    AND customer receives email within 60 seconds notifying review

#### Slice UC-NN.3 — Identity provider unavailable
**Priority:** Should
**Story:** Identity provider integration is down at submission time.
**Outcome:** Application queued; customer notified of pending verification.
**Acceptance:**
  - GIVEN the identity provider returns 5xx or times out
    WHEN customer submits the application
    THEN application status is VERIFICATION_QUEUED
    AND the verification job is added to retry queue (per FR-112)
    AND customer receives email within 60 seconds explaining delay

#### Slice UC-NN.4 — Customer resumes saved application
**Priority:** Should
**Story:** Customer returns within 7 days to continue a partially-completed application.
[... similar structure ...]

#### Slice UC-NN.5 — Resumption after 7+ days
**Priority:** Could
**Story:** Customer returns after the resumption window has expired.
[... similar structure ...]
```

The slices form the development backlog. Each slice is small (1–5 person-days), independently testable, and has its own MoSCoW priority.

---

## How many use cases does an FSD need?

Rough rule of thumb:

- **Small project** (1–3 month delivery): 5–15 use cases
- **Medium project** (3–6 months): 15–30 use cases
- **Large project** (6+ months): 30–60+ use cases — consider a separate Use Case Catalog document

For more than ~25 use cases, split into a companion `<Project>_Use_Case_Catalog.md` and reference from the FSD.

---

## Naming conventions

- Use case names are **verb phrases from the actor's perspective**: "Submit Onboarding Application", "Approve Manual Review", "Generate Compliance Report"
- Not: noun phrases ("Application Submission"), system perspective ("System Processes Application"), passive voice ("Application is Submitted")
- The actor doing the verb should be unambiguous from the name

Use case IDs: UC-01 onwards. Slices: UC-NN.M.

---

## What goes in extensions (alternative/exception flows)

Every step in the main success scenario can have extensions. Extensions cover:

1. **Validation failures** — input doesn't meet rules
2. **Missing data** — required field absent
3. **Permission denied** — actor lacks authorization
4. **External system unavailable** — integration down
5. **Timeout** — response not received in time
6. **Concurrent modification** — another actor changed state
7. **Resource exhaustion** — quota / rate limit
8. **State mismatch** — entity not in expected state
9. **Compliance trigger** — auto-escalation to review

For each significant extension, write the recovery flow. Extensions are where production bugs are born.

---

## Use cases vs FRs — which does which work

| Concern | Use Case | FR |
|---|---|---|
| Narrate end-to-end flow | ✓ | ✗ |
| Identify alternative paths | ✓ | ✗ |
| Identify exception paths | ✓ | ✗ |
| Atomic testable spec | ✗ | ✓ |
| MoSCoW priority | per slice / referenced FR | ✓ |
| Acceptance criteria | ✓ (per slice) | ✓ (per FR) |
| Implementation pointer | ✗ | ✓ |
| Source / traceability | ✓ (related FRs section) | ✓ |
| Compliance citation | optional | ✓ |

The relationship: a use case references FRs by ID; an FR may be referenced by multiple use cases. Both must exist for a complete FSD.

---

## What NOT to put in a use case

- **Implementation details** — "System calls PostgreSQL function `validate_pii()`" → wrong; just "System validates per FR-102"
- **UI specifics** — "Customer clicks the blue button labeled 'Submit' in the lower right" → wrong; UI specifics belong in UX docs
- **Internal system steps invisible to the actor** — "System enqueues message to Kafka topic `onboarding.events`" → wrong; that's how, not what
- **Future-tense for the existing system** — describe what the system being built will do, not what some current system does
- **Code-like pseudocode** — "FOR each field IN form DO validate(field)" → wrong; use natural prose

Use cases are the narrative bridge between business and engineering. Keep them at that level.
