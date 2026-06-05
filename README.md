# fsd-architect — OpenCode package for Functional Specification Documents

A four-agent OpenCode package that turns business inputs (business case, stakeholder interviews, current process docs, regulatory citations) into enterprise-grade Functional Specification Documents.

Grounded in **ISO/IEC/IEEE 29148:2018**, **BABOK v3** (IIBA), **Use Case 2.0** (Jacobson), and **ISO/IEC 25010**. Designed to produce the FSD a senior Business Analyst paired with a senior solution architect would write — and to pass audit in regulated industries (banking, healthcare, pharma, defense, automotive, aerospace).

Works with frontier models (Claude, GPT, Gemini) **and** open-weights models (Qwen-Coder, gpt-oss, Gemma, Llama, DeepSeek).

---

## TL;DR

```bash
# Install (global)
mkdir -p ~/.config/opencode/agents ~/.config/opencode/command ~/.config/opencode/skills
cp agents/*.md     ~/.config/opencode/agents/
cp command/*.md    ~/.config/opencode/command/
cp -r skills/fsd-authoring ~/.config/opencode/skills/

# Add to config (minimum): "permission": { "skill": { "fsd-authoring": "allow" } }
# See opencode.jsonc.example for the full template.

# Use (slash commands)
/fsd-discover   <attach business case, interview notes>   → Discovery Brief
/fsd-write      discovery/<project>_discovery_brief.md    → FSD
/fsd-validate   <Project>_FSD.md                          → Validation report
/fsd-trace      <Project>_FSD.md                          → RTM

# Or invoke agents directly
@fsd-discovery / @fsd-architect / @fsd-validator / @fsd-traceability
```

---

## Why this exists

The closest existing tool is [GitHub Spec Kit](https://github.com/github/spec-kit) (71K+ stars, MIT) — excellent for **spec-driven code generation** (`/specify → /plan → /tasks → /implement`). But Spec Kit's "spec" is a lightweight prompt for an AI to generate code from. It is not a regulator-grade FSD.

There was no OpenCode package for producing enterprise FSDs — documents with formal requirements (uniquely identified, MoSCoW-prioritized, acceptance-criteria-bearing, fully traceable), BABOK stakeholder analysis, ISO 25010 NFR coverage, and a Requirements Traceability Matrix. This package fills that gap.

| | GitHub Spec Kit | fsd-architect (this package) |
|---|---|---|
| Purpose | Spec → code generation | Enterprise FSD authoring |
| Standards | None specific | ISO/IEC/IEEE 29148, BABOK v3, ISO 25010, Use Case 2.0 |
| Output | Lightweight spec + plan + tasks | Multi-section FSD + RTM |
| Stakeholder analysis | Implicit (user stories) | Explicit (RACI, Power-Interest grid) |
| Requirements format | User stories | Formal FRs (12-field template) |
| Prioritization | None forced | MoSCoW with calibration |
| Traceability | None | Full RTM + 5 orthogonal views |
| Regulatory fit | Low | High (compliance coverage view) |

Both are valid. Use Spec Kit for fast green-field development. Use this package for regulated, enterprise, multi-stakeholder projects where the FSD outlives the codebase.

---

## The four agents

```
   Business inputs                                                                                              
  (case, interviews,                                                                                            
   process docs, regs)                                                                                          
        │                                                                                                       
        ▼                                                                                                       
  ┌───────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐                        
  │ fsd-discovery │──▶│  fsd-architect │──▶│  fsd-validator │──▶│  fsd-traceability  │                        
  └───────────────┘   └────────────────┘   └────────────────┘   └────────────────────┘                        
        │                    │                     │                       │                                    
        ▼                    ▼                     ▼                       ▼                                    
  Discovery Brief         The FSD            Validation Report           RTM                                   
  (stakeholders,        (ISO 29148 +        (PASS/FAIL/NA per          (Appendix C +
   goals, as-is/        BABOK; FRs with     check + verdict)           companion file;
   to-be, open Qs)      12-field template)                             5 coverage views)
```

| Agent | Reads | Writes | Edit scope |
|---|---|---|---|
| **fsd-discovery** | Business case, interviews, process docs, regulatory citations | `discovery/<project>_discovery_brief.md` | `discovery/**` only |
| **fsd-architect** | The discovery brief | `<Project>_FSD.md` | working dir (FSD) |
| **fsd-validator** | The FSD | `reviews/<FSD>_validation.md` | `reviews/**` only |
| **fsd-traceability** | The FSD | RTM in Appendix C + `<Project>_RTM.md` | `*_RTM.md` and `*_FSD.md` only |

Permissions are enforced in the agent frontmatter via glob patterns — discovery can't touch your code, the validator can't edit the FSD, etc.

Why four agents handing off via files (not one mega-agent)? Because file-based handoff is reliable across all model capability tiers, the intermediate artifacts are inspectable (you review the discovery brief before authorizing FSD writing), and independent validation catches what self-review misses.

---

## What it produces

1. **Discovery Brief** — 16 sections: stakeholder register (RACI, Power-Interest), business goals with metrics, as-is/to-be process, capability map, constraints, assumptions, risks, glossary, open questions.
2. **The FSD** — 12 sections + 6 appendices per ISO/IEC/IEEE 29148:
   - Document control, introduction, business context, overall description, external interfaces, functional requirements, NFRs, data requirements, business rules, use cases, out-of-scope, risks, approvals.
   - Every FR uses a 12-field template with GIVEN/WHEN/THEN acceptance criteria.
3. **Validation Report** — PASS/FAIL/NA against a 17-section, ~120-check quality checklist, with verdict.
4. **Requirements Traceability Matrix** — wide table + 5 orthogonal views (goal/stakeholder/compliance/verification/status coverage).

---

## Installation

### Step 1 — Copy the files

```bash
# From the unpacked package root:
mkdir -p ~/.config/opencode/agents
mkdir -p ~/.config/opencode/command
mkdir -p ~/.config/opencode/skills

# Four agents
cp agents/fsd-discovery.md     ~/.config/opencode/agents/
cp agents/fsd-architect.md     ~/.config/opencode/agents/
cp agents/fsd-validator.md     ~/.config/opencode/agents/
cp agents/fsd-traceability.md  ~/.config/opencode/agents/

# Four slash commands
cp command/fsd-discover.md  ~/.config/opencode/command/
cp command/fsd-write.md     ~/.config/opencode/command/
cp command/fsd-validate.md  ~/.config/opencode/command/
cp command/fsd-trace.md     ~/.config/opencode/command/

# The skill — WHOLE directory recursively (this pulls references/ along)
cp -r skills/fsd-authoring  ~/.config/opencode/skills/
```

### Step 2 — Verify

```bash
ls ~/.config/opencode/agents/
# fsd-architect.md  fsd-discovery.md  fsd-traceability.md  fsd-validator.md

ls ~/.config/opencode/command/
# fsd-discover.md  fsd-trace.md  fsd-validate.md  fsd-write.md

ls ~/.config/opencode/skills/fsd-authoring/
# SKILL.md  references/

ls ~/.config/opencode/skills/fsd-authoring/references/
# 8 files: babok-techniques.md  discovery-brief-format.md  iso-29148-template.md
#          open-weights-tips.md  quality-checklist.md  requirements-quality.md
#          traceability-matrix-format.md  use-case-templates.md
```

### Step 3 — Do I need to create the references folder?

**No.** The `references/` folder ships inside `skills/fsd-authoring/`. The `cp -r` in Step 1 copies it along with everything inside. If it's missing afterward, you copied without `-r` — re-run `cp -r skills/fsd-authoring ~/.config/opencode/skills/`.

OpenCode discovers references automatically. Each agent loads only the references it needs, at the phase it needs them.

### Step 4 — What goes in the config?

See `opencode.jsonc.example` for the full annotated template. The **minimum** addition to your existing config:

```jsonc
{
  "permission": {
    "skill": {
      "fsd-authoring": "allow"
    }
  }
}
```

**Recommended** (cost-effective model mix):

```jsonc
{
  "permission": { "skill": { "fsd-authoring": "allow" } },
  "agent": {
    "fsd-discovery":    { "model": "anthropic/claude-sonnet-4-5", "temperature": 0.1 },
    "fsd-architect":    { "model": "anthropic/claude-sonnet-4-5", "temperature": 0.2 },
    "fsd-validator":    { "model": "local/gpt-oss-20b",           "temperature": 0.0 },
    "fsd-traceability": { "model": "local/qwen3-coder-32b",       "temperature": 0.0 }
  }
}
```

### Step 5 — Restart OpenCode

```bash
opencode agent list   # should show the four fsd-* agents
```

Slash commands appear as `/fsd-discover`, `/fsd-write`, `/fsd-validate`, `/fsd-trace`.

### Project-scoped alternative

Replace `~/.config/opencode/` with `.opencode/` at your repo root. Commit `.opencode/` so your team shares the setup.

---

## Usage — full worked example

```text
# 1. Discovery — attach business case + interview notes
/fsd-discover Building a Customer Onboarding System to replace our 8-day manual
              process. Attached: business-case.pdf, COO-interview.md,
              current-process.docx, GDPR-scope.md

  → fsd-discovery reads everything, applies BABOK stakeholder analysis,
    writes discovery/customer_onboarding_discovery_brief.md
  → Flags 3 critical open questions

# 2. You review the brief, answer the 3 open questions by editing the file

# 3. Write the FSD
/fsd-write discovery/customer_onboarding_discovery_brief.md

  → fsd-architect verifies open questions are answered, writes
    CustomerOnboarding_FSD.md (~2,000 lines, 75 FRs, 18 use cases)

# 4. Validate
/fsd-validate CustomerOnboarding_FSD.md

  → fsd-validator runs ~120 checks, writes
    reviews/CustomerOnboarding_FSD_validation.md
  → Verdict: NEEDS REVISION (8 fails)

# 5. Fix
@fsd-architect address the fails in reviews/CustomerOnboarding_FSD_validation.md.
              Only fix items marked FAIL.

# 6. Re-validate until clean
/fsd-validate CustomerOnboarding_FSD.md   → READY FOR REVIEW

# 7. Build the traceability matrix
/fsd-trace CustomerOnboarding_FSD.md

  → fsd-traceability writes the RTM into Appendix C (or companion
    CustomerOnboarding_RTM.md) with 5 coverage views

# 8. Route FSD + RTM to approvers
```

---

## Open-weights compatibility

Built to work with open-weights models. See `skills/fsd-authoring/references/open-weights-tips.md` for:

- Model-tier matrix (which size fits which agent role)
- Per-model notes (Qwen-Coder, gpt-oss, Gemma, Llama, DeepSeek)
- Vocabulary-discipline reinforcement (open models drift on "shall" vs "must")
- Batch-by-capability FR generation for mid-size models
- Failure-mode → fix table

Cost-effective serious-work combo: discovery on Qwen3-Coder-32B (or Gemma-3-27B for diagram-heavy sources), architect on gpt-oss-120b or Claude Sonnet, validator on gpt-oss-20b, traceability on Qwen3-Coder-32B.

Match the model to the stakes: a regulated banking FSD should not run on a 4B model; an internal-tooling FSD might.

---

## File inventory

```
opencode-fsd-architect/
├── README.md                                       this file
├── opencode.jsonc.example                          annotated config template
├── agents/
│   ├── fsd-discovery.md                            reads inputs → discovery brief
│   ├── fsd-architect.md                            brief → FSD
│   ├── fsd-validator.md                            FSD → validation report
│   └── fsd-traceability.md                         FSD → RTM
├── command/
│   ├── fsd-discover.md                             /fsd-discover
│   ├── fsd-write.md                                /fsd-write
│   ├── fsd-validate.md                             /fsd-validate
│   └── fsd-trace.md                                /fsd-trace
└── skills/
    └── fsd-authoring/
        ├── SKILL.md                                methodology + workflow + 9 binding rules
        └── references/
            ├── requirements-quality.md             the 9 properties, FR template, MoSCoW, defects
            ├── iso-29148-template.md               the 12-section structure
            ├── babok-techniques.md                 stakeholder analysis, elicitation, BPMN, DMN
            ├── discovery-brief-format.md           the brief template (discovery↔architect contract)
            ├── use-case-templates.md               Cockburn + Use Case 2.0
            ├── traceability-matrix-format.md       RTM + 5 orthogonal views
            ├── quality-checklist.md                17-section validator checklist
            └── open-weights-tips.md                per-model tuning
```

Eighteen files. Four agents, four commands, one skill, eight references, one config, one README.

---

## Troubleshooting

**Agents/commands don't appear**

- Confirm files at `~/.config/opencode/agents/*.md` and `~/.config/opencode/command/*.md`.
- Check frontmatter parses — `description` required for both; `mode` required for agents; `agent` recommended for commands.
- Restart OpenCode.

**Skill doesn't load**

- Path must be `~/.config/opencode/skills/fsd-authoring/SKILL.md` (caps `SKILL.md`).
- Frontmatter `name: fsd-authoring` must match the directory name.
- `permission.skill.fsd-authoring` must not be `deny`.

**references/ folder missing after install**

- You used `cp` not `cp -r`. Re-run: `cp -r skills/fsd-authoring ~/.config/opencode/skills/`.

**Architect refuses to write**

- The discovery brief has unanswered critical open questions (§13). Answer them in the brief file, then re-invoke. This is by design.

**Architect uses "must" instead of "shall"** (open-weights models)

- Reinforce in the invocation: paste the vocabulary-discipline block from `open-weights-tips.md`. Or use a larger model for the architect role.

**Validator marks everything PASS**

- Validator model too small/lenient. Use Qwen2.5-Coder-14B+ or gpt-oss-20b+.

**FSD too long for one pass** (open-weights)

- Generate by capability: invoke `@fsd-architect` once per §5.X subsection. Or split into Phase 1 / Phase 2 FSDs.

---

## Customization

- **Add a document section:** edit `references/iso-29148-template.md`.
- **Tighten the quality bar:** edit `references/quality-checklist.md` (§17 anti-patterns is the usual place).
- **Add an industry profile:** add references for industry-specific regs (e.g., a `references/hipaa-profile.md`) and reference it from the architect's Phase 4.
- **Add a fifth agent:** drop a `.md` in `agents/`. Candidates: `fsd-impact-analyzer` (change impact across an existing FSD), `fsd-to-backlog` (decompose FRs into Jira-ready stories), `fsd-renderer` (Markdown → Word/PDF for sign-off).

---

## How this relates to the sibling package

This package has a sibling, **`opencode-spec-architect`**, which produces *implementation plans, functional/technical maps, starter code, ADRs, and reference specs* via a three-agent workflow (context-harvester → spec-architect → spec-reviewer).

The two are complementary:

| Need | Use |
|---|---|
| Business-facing FSD (what + why, stakeholder-grounded, regulator-ready) | **fsd-architect** (this package) |
| Engineering implementation plan (how, build order, code) | opencode-spec-architect |
| Both (regulated enterprise project) | FSD first → then implementation plan, with the FSD as a source input to the engineering dossier |

The FSD answers "what must the system do and why does the business need it?" The implementation plan answers "how do we build it, in what order?" Real enterprise projects need both.

---

## License

MIT.

---

## Acknowledgements & references

- **ISO/IEC/IEEE 29148:2018** — Systems and software engineering — Life cycle processes — Requirements engineering. The structural backbone.
- **BABOK v3** — A Guide to the Business Analysis Body of Knowledge, IIBA. The stakeholder analysis, elicitation, and traceability techniques.
- **Use Case 2.0** — Ivar Jacobson International. The use case slicing approach.
- **ISO/IEC 25010** — Systems and software Quality Requirements and Evaluation (SQuaRE). The NFR categories.
- **GitHub Spec Kit** — the four-phase sequential workflow with file artifacts and slash commands inspired the command structure here, adapted from code-generation to FSD authoring.
- The OpenCode skill ecosystem (zenobi-us/opencode-skillful, malhashemi/opencode-skills, joshuadavidthomas/opencode-agent-skills) for skill-loading conventions.

The patterns encode what experienced Business Analysts do that engineers tend to skip: map stakeholders before data, separate business rules from functional requirements, write the as-is before the to-be, quantify business impact, prioritize ruthlessly with MoSCoW, and preserve solution space by specifying *what* not *how*.
