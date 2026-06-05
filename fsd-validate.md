---
description: Validate a draft FSD against the 17-section quality checklist. Delegates to the fsd-validator subagent. Produces a PASS/FAIL/NA report with verdict (Ready / Needs Revision / Requires Rewrite) and top-3 priority fixes.
agent: fsd-validator
---

You are validating an FSD against the quality checklist.

# FSD to validate / context

$ARGUMENTS

# Your task

Run the 17-section quality checklist mechanically against the FSD. Be strict — partial credit is FAIL.

Steps:

1. Read the FSD at the path the user provided above
2. Load `quality-checklist.md` and `requirements-quality.md` from the `fsd-authoring` skill
3. Run every check in every section in order:
   - Sections 1–4: structural and contextual
   - Section 5: per-FR (iterate over every single FR — this is the bulk of the work)
   - Section 6: per-NFR
   - Section 7: data requirements
   - Section 8: business rules separation
   - Section 9: use cases
   - Sections 10–12: out-of-scope, risks, approvals
   - Section 13: RTM (if present)
   - Section 14: cross-document consistency (verify every cross-reference resolves)
   - Section 15: multi-audience usability
   - Section 16: tone and language
   - Section 17: anti-pattern scan
4. Record PASS/FAIL/NA per check with specific citations for every FAIL
5. Compute the verdict per the checklist's thresholds
6. Write the validation report to `reviews/<FSD>_validation.md`
7. Output a 4-sentence summary with the verdict, counts, top FAIL category, and report path

Verdict thresholds (from the checklist):
- READY FOR REVIEW — 0 fails
- NEEDS REVISION — 1–10 fails, none in §1, §5 critical (5.1–5.13), or §13
- REQUIRES REWRITE OF AFFECTED SECTIONS — any fail in §1, §5 critical, or §13
- REWRITE FROM DISCOVERY BRIEF — >20 total fails

You do not edit the FSD. The architect addresses the fails in a follow-up pass.
