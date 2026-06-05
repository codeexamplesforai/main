# Requirements Traceability Matrix (RTM) Format

The RTM is the navigable index that proves every requirement traces forward (to design, tests, code) and backward (to business goals, stakeholders, sources).

For regulated industries, the RTM is the artifact auditors ask for. It is not optional.

The RTM is written to Appendix C of the FSD as a sortable table (and optionally to a companion file `<Project>_RTM.md` if the matrix becomes too large for inline rendering).

Produced by the `fsd-traceability` agent after the FSD is otherwise complete.

---

## What an RTM proves

The regulator's question: *"For this regulation/business goal, show me the requirement that addresses it, the design that implements it, the test that verifies it, and the evidence the test passed."*

A complete RTM lets you answer that question in 30 seconds. Without an RTM, every audit response becomes a multi-week scramble.

The chain:

```
Business Goal (G-NN)
   ↓
Stakeholder Need (from Stakeholder S-NN)
   ↓
Functional Requirement (FR-NNN) or NFR (NFR-XXX-NN)
   ↓
Use Case (UC-NN) [where applicable]
   ↓
Business Rule (BR-NN) [where applicable]
   ↓
Verification Method (Test / Inspection / Demo / Analysis)
   ↓
Test Case (TC-NN) [defined in Test Plan, not FSD]
   ↓
Test Execution Result [defined in Test Plan, not FSD]
```

The FSD's RTM owns the top half (G → FR → Verification). The Test Plan extends it (TC → Result). Together they form the full audit trail.

---

## RTM table format (the canonical layout)

The RTM is a wide table. Rows = requirements (FRs and NFRs both). Columns = traceability links.

```markdown
| FR ID | Title | Business Goal(s) | Stakeholder(s) | Source | Use Case(s) | Business Rule(s) | NFR Refs | Priority | Verification | Test Case(s) | Status |
|-------|-------|------------------|----------------|--------|-------------|------------------|----------|----------|--------------|--------------|--------|
| FR-101 | Capture personal information | G-01, G-02 | S-01, S-04 | S-04 interview 2026-01-12 | UC-03 | BR-04, BR-07 | NFR-USA-02 | Must | Test | TC-101a, TC-101b | Approved |
| FR-102 | Validate personal information | G-03 | S-02 | GDPR Art. 5(1)(d) | UC-03 | BR-04 | NFR-SEC-04 | Must | Test | TC-102a–d | Approved |
| FR-103 | Display field-level error messages | G-01 | S-04 | UX research 2026-01-05 | UC-03 | — | NFR-USA-01 | Must | Demo | TC-103 | Draft |
| ... | | | | | | | | | | | |
| NFR-PERF-01 | Authentication response time | G-01 | S-01 | Predecessor system metrics | (all auth UCs) | — | — | Must | Test | TC-PERF-01 | Approved |
```

### Column-by-column meaning

| Column | What it contains | Bad sign |
|---|---|---|
| **FR ID** | Unique requirement identifier from FSD §5 or §6 | Duplicate IDs; gaps in numbering (renumbering) |
| **Title** | Short verb-phrase from the requirement | Different title than appears in the FSD body |
| **Business Goal(s)** | G-NN references from FSD §2.2 | Empty (FR untraceable to a goal — should be deleted) |
| **Stakeholder(s)** | S-NN references from FSD §2.3 | Empty (no one needed this?) |
| **Source** | Where the requirement came from — interview ID, document section, regulatory citation | "Best practice" or "internal discussion" |
| **Use Case(s)** | UC-NN references where this FR is exercised | "—" only valid for cross-cutting NFRs (security, performance) |
| **Business Rule(s)** | BR-NN references when the FR enforces a business rule | Empty when the FR clearly encodes policy logic |
| **NFR Refs** | NFR-XXX-NN cross-references | Missing for FRs with obvious quality implications |
| **Priority** | MoSCoW value matching the FSD | Mismatch with FSD body |
| **Verification** | Test / Inspection / Demonstration / Analysis | Missing or "TBD" |
| **Test Case(s)** | TC-NN references from Test Plan | "TBD" if Test Plan exists; acceptable if Test Plan is pending |
| **Status** | Draft / Reviewed / Approved / Implemented / Verified / Closed | Stale (out of sync with current state) |

---

## The orthogonal views — beyond the wide table

The wide table is the primary view. For audit and project management, several **orthogonal views** are derived from it:

### View 1 — Goal coverage

For each business goal, which FRs implement it. Answers: "do we have enough FRs to achieve goal G-NN?"

```markdown
| Business Goal | FR Count | Must | Should | Could | FR IDs |
|---|---|---|---|---|---|
| G-01 Reduce onboarding cycle time | 23 | 14 | 7 | 2 | FR-101, FR-102, ..., FR-148 |
| G-02 Reduce manual review burden | 15 | 9 | 5 | 1 | FR-110, FR-115, ..., FR-220 |
| G-03 Maintain compliance posture | 18 | 18 | 0 | 0 | FR-201–218 |
```

**Bad sign:** a business goal with 0 or 1 FR — the goal isn't being delivered. Either the goal is wrong or you're missing FRs.

### View 2 — Stakeholder coverage

For each stakeholder, which FRs address their concerns.

```markdown
| Stakeholder | FR Count | Critical Concerns | All Addressed? |
|---|---|---|---|
| S-01 COO | 28 | Cycle time, cost | Yes |
| S-02 Compliance | 18 | Regulatory adherence | Yes |
| S-03 Onboarding ops | 12 | Workflow efficiency | Partial — see Q-04 |
| S-04 Customer | 31 | Experience, speed | Yes |
```

**Bad sign:** a stakeholder with no FRs referencing them — were they actually consulted? Possibly the discovery brief missed them.

### View 3 — Compliance coverage

For each regulatory citation in scope, which FRs implement it.

```markdown
| Regulation / Clause | FR IDs | Verification Method | Coverage Confidence |
|---|---|---|---|
| GDPR Art. 17 (right to erasure) | FR-301, FR-302, FR-303 | Test | High |
| GDPR Art. 30 (records of processing) | FR-305 | Inspection | High |
| PCI-DSS 4.0 Req. 3.4 | NFR-SEC-08, FR-410 | Test | High |
| KYC AML Directive 6 | FR-110, FR-115, FR-120, FR-125 | Test + Audit | Medium (pending S-02 review) |
```

This is the view the auditor asks for first.

### View 4 — Verification coverage

How many requirements use each verification method.

```markdown
| Method | Count | % | Example FR IDs |
|---|---|---|---|
| Test | 87 | 73% | Most behavioral FRs |
| Inspection | 14 | 12% | NFR-SEC-04 audit logging, etc. |
| Demonstration | 12 | 10% | UI/UX FRs |
| Analysis | 6 | 5% | Performance modeling, FMEA |
```

**Bad sign:** verification distribution wildly skewed. ~70%+ Test is normal; <50% Test suggests under-specified acceptance criteria.

### View 5 — Status dashboard

For project tracking:

```markdown
| Status | Count | % |
|---|---|---|
| Draft | 0 | 0% |
| Reviewed | 4 | 3% |
| Approved | 119 | 99% |
| Implemented | 0 | 0% |
| Verified | 0 | 0% |
| Closed | 0 | 0% |
```

Updated continuously as the project progresses. Pre-development, "Approved" should be 100% for the baselined FSD.

---

## What the validator checks against the RTM

The `fsd-validator` agent runs these checks:

1. **Every FR in §5 and §6 appears in the RTM** — no orphan FRs
2. **Every FR ID in the RTM exists in §5 or §6** — no phantom RTM entries
3. **Every FR traces to ≥1 business goal** — no orphan requirements
4. **Every FR traces to ≥1 stakeholder** — no requirements without a "who wanted this"
5. **Every FR has a non-empty Source field** — traceable back to evidence
6. **Every FR has a Verification method** — not "TBD"
7. **Every business goal has ≥1 FR** — no goals without implementation
8. **Every stakeholder has ≥1 FR** — no consulted-but-not-addressed stakeholders
9. **Every regulatory citation in scope has ≥1 FR** — no compliance gaps
10. **FR-to-UC references in the RTM match the UC's "Related FRs" lists** — bidirectional consistency
11. **Priority in RTM matches priority in FSD body** — no drift

A failed check is a structural RTM defect. Validator escalates these as FAIL (not WARN).

---

## When the RTM doesn't fit in the FSD inline

For FSDs with more than ~80 FRs, the RTM table becomes unwieldy as inline content. Split:

- **Inside the FSD Appendix C:** a summary RTM (FR ID, title, priority, goal references, status) — readable inline
- **Companion file `<Project>_RTM.md`:** the full RTM (all 12+ columns), with the 5 orthogonal views

Cross-reference from Appendix C: *"Full traceability matrix in `<Project>_RTM.md`."*

---

## CSV / spreadsheet export

For tooling integration (Jira, Polarion, DOORS, etc.), the RTM should be exportable to CSV. The agent producing the RTM may write both markdown and CSV:

```
ID,Title,Goals,Stakeholders,Source,UseCases,BRs,NFRs,Priority,Verification,TestCases,Status
FR-101,"Capture personal information",G-01;G-02,S-01;S-04,"S-04 interview 2026-01-12",UC-03,BR-04;BR-07,NFR-USA-02,Must,Test,TC-101a;TC-101b,Approved
FR-102,...
```

If CSV is needed, generate it alongside the markdown to avoid drift.

---

## A note on RTM maintenance

The RTM is a **living document**. It must be updated:

- When an FR is added, modified, or removed
- When a use case changes
- When a stakeholder is added
- When a test case is created (status: Approved → Implemented)
- When a test case passes (Implemented → Verified)

A stale RTM is worse than no RTM — it gives false confidence. If the project doesn't have a discipline for RTM maintenance, the RTM should be regenerated from the (single source of truth) FSD as part of every FSD version release.

The `fsd-traceability` agent can regenerate the RTM from an updated FSD any time. Run it after every significant FSD change.
