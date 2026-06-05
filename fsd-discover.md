---
description: Start a new FSD project by harvesting context from provided source material. Delegates to the fsd-discovery subagent to read business inputs (business case, interviews, current process docs, regulatory citations) and produce a Discovery Brief.
agent: fsd-discovery
---

You are starting the FSD authoring workflow for the project described below.

# Project context

$ARGUMENTS

# Your task

Read all source material the user has attached (or referenced above) and produce a Discovery Brief following the format in the `fsd-authoring` skill's `references/discovery-brief-format.md`.

Steps:

1. Inventory every source provided
2. Load `discovery-brief-format.md` and `babok-techniques.md` from the `fsd-authoring` skill
3. Read each source in full — including embedded diagrams in PDFs/docx
4. Apply BABOK v3 stakeholder analysis (identification across all 11 categories, RACI, Power-Interest grid)
5. Synthesize into the 16-section Discovery Brief template
6. Identify up to 8 critical open questions blocking FSD writing
7. Write the brief to `discovery/<project_slug>_discovery_brief.md`

Output a 4-sentence summary: brief path, sources read, stakeholder counts, open questions count.

The user will review the brief and answer the open questions (by editing the file directly) before invoking `/fsd-write`.

Do not write the FSD itself. That is the next step.
