---
description: Produce the FSD from a Discovery Brief. Delegates to the fsd-architect subagent. Requires a discovery brief and that all critical open questions have been answered.
agent: fsd-architect
---

You are writing the Functional Specification Document for the project described in the discovery brief.

# Project context / file paths

$ARGUMENTS

# Your task

Produce a regulator-grade FSD following ISO/IEC/IEEE 29148:2018 structure with BABOK v3 techniques.

Steps:

1. Locate and read the discovery brief at `discovery/<project>_discovery_brief.md` (or the path the user specified above)
2. Verify all critical open questions in the brief are answered. If any remain unresolved, refuse to write and list which questions still need answers.
3. Load `iso-29148-template.md` from the `fsd-authoring` skill (Phase 2)
4. Plan the FSD structure (capabilities → FR numbering blocks, NFR categories, use case inventory)
5. Load `requirements-quality.md`, `use-case-templates.md`, and `babok-techniques.md` (Phase 4)
6. Write the FSD with all 12 sections + 6 appendices to `<Project>_FSD.md`
7. Honor the binding vocabulary discipline: "shall" / "should" / "may" / "will" only — no "must"
8. Self-review against the critical quality criteria
9. Output a 4-sentence summary and recommend `/fsd-validate` as the next step

Length expectations:
- Small project (3–10 capabilities, ~30 FRs): ~1,000 lines
- Medium project (10–20 capabilities, ~75 FRs): ~2,000 lines
- Large project (20+ capabilities, ~150+ FRs): ~3,000+ lines (consider companion Use Case Catalog)

Do not run validation yourself — `/fsd-validate` is a separate step run by a separate agent.

Do not produce the RTM — `/fsd-trace` is a separate step run by a separate agent.
