---
description: Build the Requirements Traceability Matrix (RTM) from a validated FSD. Delegates to the fsd-traceability subagent. Produces the wide RTM table plus 5 orthogonal views (goal/stakeholder/compliance/verification/status coverage).
agent: fsd-traceability
---

You are building the Requirements Traceability Matrix for a validated FSD.

# FSD to trace / context

$ARGUMENTS

# Your task

Extract every FR/NFR from the FSD and build the RTM with full traceability links and the 5 orthogonal views.

Steps:

1. Read the FSD at the path the user provided above
2. Load `traceability-matrix-format.md` from the `fsd-authoring` skill
3. Build the wide RTM table — one row per FR and per NFR, with all 12 columns (FR ID, Title, Business Goals, Stakeholders, Source, Use Cases, Business Rules, NFR Refs, Priority, Verification, Test Cases, Status)
4. Build the 5 orthogonal views:
   - Goal coverage (flag goals with 0–1 FRs)
   - Stakeholder coverage (flag stakeholders with 0 FRs)
   - Compliance coverage (per regulatory citation)
   - Verification distribution
   - Status dashboard
5. Decide placement:
   - ≤80 FRs → write the full RTM into the FSD's Appendix C
   - >80 FRs → write the full RTM to companion `<Project>_RTM.md`, put a slim 5-column summary + pointer in Appendix C
6. Run the 11 RTM self-checks (every FR present, every row traces to a goal and stakeholder, no orphans, priorities match FSD body, etc.)
7. Output a 4-sentence summary with counts, orphans flagged, and the RTM path

If the user has not run `/fsd-validate` first, recommend it — building an RTM from a defective FSD produces a defective RTM. You may proceed with a warning if explicitly instructed.

You do not modify FRs. You extract them. If the FSD has defects, route back to `/fsd-validate` and `/fsd-write`.
