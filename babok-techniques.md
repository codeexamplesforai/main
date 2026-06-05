# BABOK v3 Techniques — What an Experienced BA Brings

This reference summarizes the BABOK v3 (Business Analysis Body of Knowledge, IIBA) techniques that distinguish a real FSD from a code-generation prompt. Each section below is a technique. Apply them during discovery and writing.

The BABOK Guide is the IIBA's professional standard for business analysis. It defines 50+ techniques across six knowledge areas. The subset below is the practitioner-essential core for FSD work.

---

## Knowledge area 1 — Stakeholder analysis

A stakeholder is anyone whose interests are affected by the system. Missing stakeholders is the #1 cause of FSD failure — a forgotten user class becomes a "but you didn't mention…" surprise at UAT.

### Technique: Stakeholder identification (BABOK §10.43)

For every project, enumerate all stakeholder groups before discovery starts. Categories to check exhaustively:

- **Direct users** — those who interact with the system
- **Indirect users** — those affected by the system's outputs (downstream)
- **Approvers** — those with sign-off authority
- **Sponsors** — those funding the project
- **Operations & support** — those maintaining the system post-launch
- **Compliance / legal** — those auditing or accepting regulatory liability
- **Security** — those responsible for the security posture
- **External: customers** — the end users of the business
- **External: regulators** — government, industry bodies
- **External: partners / vendors** — those whose systems integrate
- **External: data subjects** — individuals whose data is processed (GDPR)

A complete stakeholder list usually has 8–15 entries. Fewer than 6 = you've missed groups.

### Technique: RACI (Responsible, Accountable, Consulted, Informed)

For each stakeholder, position them on RACI for the FSD itself:

- **R**esponsible — does the work (BA, often)
- **A**ccountable — owns the outcome (one person, typically the sponsor or product owner)
- **C**onsulted — provides input (subject matter experts)
- **I**nformed — kept aware (operations, downstream teams)

One Accountable per project. Multiple Responsible/Consulted/Informed are fine.

### Technique: Power-Interest grid (Mendelow's matrix)

For each stakeholder, place on a 2×2 of influence (power to affect the project) × interest (motivation to engage):

| | Low influence | High influence |
|---|---|---|
| **High interest** | Keep informed | Manage closely |
| **Low interest** | Monitor (minimal effort) | Keep satisfied |

The "Manage closely" quadrant gets the most BA time during elicitation. The "Keep satisfied" quadrant is where projects die quietly (executives who aren't tracking but can veto at the last minute).

---

## Knowledge area 2 — Elicitation

Elicitation is how requirements are discovered. BABOK §3 lists techniques; the high-yield ones for FSD work:

### Technique: Structured Interviews (BABOK §10.25)

For each stakeholder in "Manage closely" or "Consulted" position, conduct an interview with a prepared question set. Categories of questions to cover:

1. **Context** — What do you do today? What works? What doesn't?
2. **Goals** — What would success look like for you?
3. **Pain points** — Where do you waste time? Where do errors happen?
4. **Constraints** — What can't change? Regulatory, organizational, technical?
5. **Edge cases** — What happens when X goes wrong? When data is missing? When two users do the same thing simultaneously?
6. **Hidden processes** — What do you do that isn't in any process document?
7. **Validation** — When I describe back what I heard, does it match?

Document interview output in the **Discovery Brief** (see `discovery-brief-format.md`). Quote stakeholders verbatim where it captures intent; paraphrase otherwise.

### Technique: Document Analysis (BABOK §10.18)

Read everything provided. Standard sources:
- Existing policies & procedures
- Current system documentation (often outdated — note this)
- Regulatory filings (annual reports, compliance attestations)
- Vendor contracts & SLAs
- Prior FSDs (for predecessor systems)
- Help tickets / support logs (rich source of pain points)
- Training materials (reveal mental models)

Document analysis often surfaces business rules that no stakeholder remembers but that are embedded in policy.

### Technique: Observation (BABOK §10.30)

When possible, watch the as-is process being executed. This catches:
- Workarounds people don't admit to in interviews
- Real-world timing
- Implicit handoffs not in any process diagram
- Tools people actually use vs tools they're supposed to use

This package's agents cannot do real-world observation — but the user can. When working on a real FSD, push for observation time.

### Technique: Workshops / JAD (Joint Application Design) sessions

For complex projects, bring multiple stakeholders together to elicit requirements collectively. Effective when:
- Multiple stakeholders disagree and need to resolve it together
- Process spans multiple teams
- Building consensus on priority

This package supports JAD by producing pre-workshop materials and post-workshop synthesis, but JAD itself is a human activity.

---

## Knowledge area 3 — Analysis

Elicitation produces raw material. Analysis turns it into structured FRs.

### Technique: Process modeling (BABOK §10.35) — BPMN

Model both the as-is and to-be processes using BPMN 2.0 notation. Key elements:

- **Pools** = organizations or actors (Customer, Bank, Vendor)
- **Lanes** within pools = roles (Underwriter, Reviewer)
- **Tasks** = work performed
- **Gateways** = decisions (diamond shape)
- **Events** = triggers (start, intermediate, end)
- **Sequence flows** = order within a pool
- **Message flows** = inter-pool communication

Two BPMN diagrams (as-is, to-be) in §2.4 and §2.5 of the FSD are worth a thousand words of prose.

### Technique: Use Case 2.0

Use Case 2.0 (Ivar Jacobson) is the modernized practice of UML use cases. See `use-case-templates.md` for the format. Use cases:
- Tell the *narrative* of how an actor achieves a goal via the system
- Identify primary and alternate flows
- Surface exception paths
- Bridge between business stakeholders and developers

Use cases complement FRs. Use cases tell the story; FRs are the testable specs derived from the story.

### Technique: User stories (alternative to formal FRs in agile contexts)

When the receiving team works agile, FRs may be expressed as user stories:

```
As a <role>,
I want <capability>
So that <benefit>.

Acceptance criteria:
- GIVEN ... WHEN ... THEN ...
```

User stories are valuable for backlog ingestion but lose rigor required in regulated industries. For enterprise FSDs, prefer formal FRs; for agile feature work, user stories with INVEST validation are fine.

### Technique: Decision tables / decision modeling (DMN)

When business rules are complex (many conditions → many outcomes), express them as decision tables. Example:

| Customer age | Income | Existing customer | → Tier |
|---|---|---|---|
| ≥ 25 | ≥ $50K | Yes | Gold |
| ≥ 25 | ≥ $50K | No | Silver |
| ≥ 25 | < $50K | Yes | Silver |
| < 25 | any | any | Bronze |

A decision table in §8.1 prevents 20 paragraphs of nested if-then logic spread across multiple FRs.

### Technique: Functional decomposition (BABOK §10.20)

Break a high-level capability into its constituent functions. Top-down decomposition:
- Level 0: System purpose (one sentence)
- Level 1: Major capabilities (5–10)
- Level 2: Sub-capabilities per major (3–8 each)
- Level 3: Specific functions (each becomes an FR or small group of FRs)

Capability map in §3.2 of the FSD is the Level 1–2 view; FRs in §5 are Level 3.

---

## Knowledge area 4 — Prioritization

Without prioritization, every FR is "Must" and you ship nothing.

### Technique: MoSCoW (BABOK §10.30)

See `requirements-quality.md` for the canonical definitions. Apply MoSCoW after the full FR list is drafted, not during drafting.

Calibration: healthy distribution is roughly 40% Must / 30% Should / 20% Could / 10% Won't. If 80% are Must, you haven't prioritized.

### Technique: Kano model

Classify FRs by user perception:
- **Must-be** — expected; absence causes dissatisfaction; presence doesn't delight (login works, search returns results)
- **Performance** — linear satisfaction with capability (faster = better, more features = better)
- **Delighter** — unexpected; absence is fine; presence creates strong positive reaction

Kano helps allocate effort: don't over-invest in must-be requirements; look for cheap delighters.

### Technique: Value-vs-Effort matrix

For each FR, plot on a 2×2 of business value × implementation effort. Quadrants:

- High value / low effort → **Quick wins** (do first)
- High value / high effort → **Major projects** (plan carefully)
- Low value / low effort → **Fill-ins** (do if time)
- Low value / high effort → **Questionable** (challenge or drop)

This conversation happens during FSD review with stakeholders, captured in §11 risks/issues.

---

## Knowledge area 5 — Verification & Validation

Verification = "are we building the requirement correctly?" (does the FR meet quality criteria)
Validation = "are we building the right requirement?" (does the FR meet stakeholder need)

### Technique: Requirements traceability (BABOK §10.41) — RTM

Every FR must trace forward (to design, tests, code) and backward (to stakeholder need, business goal, source document).

The Requirements Traceability Matrix (RTM) is the navigable index. Produced by the `fsd-traceability` agent in this package. See `traceability-matrix-format.md`.

Traceability is not a clerical chore — it's how an auditor proves the regulator's question can be answered. Without traceability, the FSD does not pass regulated-industry audits.

### Technique: Stakeholder review & walkthrough

Before final FSD sign-off:
1. Walk through the FSD with each "Manage closely" stakeholder
2. Confirm the FRs trace back to their stated needs
3. Identify omissions and surprises
4. Update the FSD; re-circulate

This is where you find the late-stage gaps. Build the time in.

---

## Knowledge area 6 — Solution evaluation

Post-implementation: did the delivered solution achieve the business goals stated in §2.2?

This is outside the FSD writing phase but worth knowing: every success metric in §2.2 becomes a measurement at solution evaluation time. If you can't measure G-01, G-02, … after launch, the goals were too vague — fix during FSD writing.

---

## Where each technique applies in our agent workflow

| BABOK technique | Applied by | At which phase |
|---|---|---|
| Stakeholder identification | fsd-discovery | Phase 1 — discovery |
| RACI, Power-Interest | fsd-discovery | Phase 1 — discovery |
| Structured interviews | (user, with prompts from fsd-discovery) | Before FSD writing |
| Document analysis | fsd-discovery | Phase 1 — discovery |
| Process modeling (BPMN) | fsd-architect | Phase 4 — writing §2 |
| Use Case 2.0 | fsd-architect | Phase 4 — writing §9 |
| Decision tables (DMN) | fsd-architect | Phase 4 — writing §8 |
| Functional decomposition | fsd-architect | Phase 4 — writing §3.2 and §5 |
| MoSCoW prioritization | fsd-architect (with user review) | Phase 4 — writing |
| Requirements traceability (RTM) | fsd-traceability | Phase 6 — post-writing |
| Quality validation | fsd-validator | Phase 5 — post-writing |

---

## A note on what BAs do that engineers don't

If you come from an engineering background, here is what experienced BAs do that distinguishes their FSDs from engineer-written specs:

1. **They map stakeholders before they map data.** Engineers tend to start with the model. BAs start with people.
2. **They distinguish business rules from functional requirements.** Engineers tend to encode policy directly in FRs. BAs externalize policy into BRs so it can change without code change.
3. **They write the as-is before the to-be.** Engineers want to design the future. BAs document the present first, because the future without the present is fantasy.
4. **They quantify business impact.** Engineers describe behaviors. BAs cost them — "8 days median onboarding, $2.3M revenue impact."
5. **They prioritize ruthlessly with MoSCoW.** Engineers tend to flag everything Must (because it all seems necessary). BAs force the distribution.
6. **They write for multiple audiences.** Engineers write for engineers. BAs write so an exec, an architect, a developer, a tester, and a compliance officer all find what they need.
7. **They use neutral language for choices.** "The system shall persist records for 7 years" not "We'll use Postgres with archival." BAs preserve solution space.

These habits are why the FSD this package produces should feel different from a code-generation prompt. Same structure rigor, but business-grounded throughout.
