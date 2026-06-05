# Open-Weights Model Tips — for FSD Authoring

This reference adapts the FSD workflow for open-weights models (Qwen-Coder, gpt-oss, Gemma, Llama, DeepSeek). FSD writing is harder on small models than implementation-plan writing because it requires:

- Structured output across many requirements (each with 10+ fields)
- Vocabulary discipline ("shall" not "should/will/may" except deliberately)
- BABOK-grounded synthesis (not just transcription)
- Cross-document referencing (RTM must match FSD body)

Below are the adjustments that make it work.

---

## The single most important tip

**Use all four agents, in order.** `fsd-discovery` → `fsd-architect` → `fsd-validator` → `fsd-traceability`. The file-based handoffs (discovery brief → FSD → RTM) are what enable open-weights models to produce regulator-grade output.

Trying to write the whole FSD in one agent pass on a mid-size open-weights model produces draft-quality output. The four-agent split with intermediate inspection produces ship-quality output.

---

## Model tiers and where each fits

| Tier | Examples | discovery | architect | validator | traceability |
|------|----------|-----------|-----------|-----------|--------------|
| **Frontier closed** | Claude Opus/Sonnet, GPT-5, Gemini 2.5 Pro | Excellent | Excellent | Excellent | Excellent |
| **Frontier open, large** | gpt-oss-120b, Qwen3-Coder-480B, Llama-3.1-405B, DeepSeek-V3 | Excellent | Very good | Excellent | Excellent |
| **Mid open, capable** | Qwen2.5-Coder-32B, gpt-oss-20b, Gemma-3-27B, Qwen3-32B, Llama-3.3-70B | Very good | Good (loops with validator essential) | Excellent | Very good |
| **Mid open, smaller** | Qwen2.5-Coder-14B, Gemma-3-12B, Llama-3.1-8B | Good | OK for ~30 FR FSDs; struggles beyond | Very good | Good |
| **Small** | Gemma-3-4B, Qwen2.5-Coder-7B, Phi-4 | OK | Avoid | Acceptable for binary checks | Acceptable |

**Cost-effective combo for serious FSD work on open-weights:**

- discovery: Qwen3-Coder-32B (or Claude Sonnet for highest discovery fidelity)
- architect: gpt-oss-120b or Claude Sonnet (this is where capability matters most)
- validator: gpt-oss-20b or Qwen2.5-Coder-14B (binary checking; smaller models work)
- traceability: Qwen3-Coder-32B (table generation; mid models are reliable)

---

## Per-model notes

### Qwen-Coder (2.5, 3.x)

- **Strengths:** Strong at structured tabular output. Generates RTMs and FR templates reliably. Good Markdown discipline.
- **Watch out for:** Can be verbose in FR descriptions. Add explicit length guidance ("2–4 sentences max for Description").
- **Use for:** discovery and traceability primarily; architect for ≤50 FRs.

### gpt-oss (20b, 120b)

- **Strengths:** Strong reasoning, follows BABOK terminology well. 120b can handle long FSDs in one pass.
- **Watch out for:** Sometimes adds preamble before the deliverable. Add "Output the file content directly, no preamble" to system prompt.
- **Use for:** architect (120b) and validator (20b).

### Gemma 3 (12B, 27B)

- **Strengths:** Multimodal — actually reads BPMN diagrams in source PDFs natively. Strong at the discovery phase.
- **Watch out for:** Long FSDs (>80 FRs) can show sectional drift past row 60. Consider splitting into Phase 1 / Phase 2 FSDs.
- **Use for:** discovery (because of multimodal); validator.

### Llama (3.1, 3.3, 4.x)

- **Strengths:** Broadly capable; large context window in newer versions.
- **Watch out for:** Tone tends to drift into US-business-writing register; can lose the "shall" discipline. Reinforce with frequent reminders.
- **Use for:** Any role with explicit prompts. 3.3-70B is a solid all-rounder.

### DeepSeek-V3 / DeepSeek-Coder

- **Strengths:** Excellent reasoning, strong at requirements decomposition.
- **Watch out for:** Long thinking chains can blow context budget on local deployments.
- **Use for:** architect when budget allows; validator.

---

## Workflow adjustments specifically for open-weights

### 1. Lock vocabulary aggressively

Open-weights models drift on the "shall/should/may/will" discipline. Reinforce in the architect's invocation:

```
@fsd-architect produce FSD from discovery/<file>.md

VOCABULARY REQUIREMENT:
- "shall" denotes binding requirements (use for all FRs and NFRs)
- "should" denotes recommendations (use for Should-priority FRs only)
- "may" denotes options
- "will" denotes external/future declarations
- No other modal verbs in requirement statements (no "must", "needs to",
  "is required to", "is supposed to")

If you produce any requirement statement using a verb outside this set,
the validator will fail it.
```

Repeating this in the prompt is not redundancy — it's reinforcement against drift.

### 2. Generate FRs in small batches

For mid-size models, generating 80 FRs in one shot produces sectional drift. Generate them by capability:

```
First, generate FSD §1–§4 (introduction through interfaces).
After review, generate §5.1 (capability 1 with its FRs).
After review, generate §5.2 (capability 2 with its FRs).
...
```

The architect agent supports this — invoke it once per capability if needed.

### 3. Validate aggressively, loop willingly

On open-weights models, expect 20–50 validator fails on the first pass for a 50-FR FSD. This is not the model failing; it's the FSD being early-draft. Loop:

```
@fsd-validator FSD.md → 35 FAIL
@fsd-architect fix the fails in review.md → revised FSD
@fsd-validator FSD.md → 8 FAIL
@fsd-architect fix the remaining fails
@fsd-validator FSD.md → 0 FAIL
```

Each loop takes 5–10 minutes. Three loops is normal. Five loops means the discovery brief was thin.

### 4. Run RTM generation last, separately

The traceability agent reads the FSD and produces the RTM. Do this after the architect's last revision. Doing it earlier wastes work — the RTM will be regenerated.

### 5. Keep the discovery brief as the source of truth

If a stakeholder later says "but I told you X", check the discovery brief. If X is there, the architect missed it; revise FSD. If X is not there, update the discovery brief first, then revise FSD. Never edit the FSD with new content that isn't in the brief.

### 6. Use structured output mode where available

If your serving stack supports JSON-schema-constrained generation (vLLM grammar, llama.cpp JSON mode), use it for:

- FR templates (the 12-field structure is regular enough for schema constraint)
- RTM rows (each row has the same 12 columns)
- Stakeholder register rows

Schema-constrained generation makes mid-size models produce structurally perfect output. The architect agent can be configured to use this mode.

### 7. Reference loading is just-in-time

Don't preload all 9 references at session start. The skill is large enough that loading everything wastes context. Load each at the relevant phase:

| Agent / phase | Load |
|---|---|
| discovery — Step 2 | discovery-brief-format.md, babok-techniques.md |
| architect — Phase 2 | iso-29148-template.md |
| architect — Phase 4 | requirements-quality.md, use-case-templates.md |
| validator — Step 2 | quality-checklist.md, requirements-quality.md |
| traceability — Step 2 | traceability-matrix-format.md |
| Any agent on small open-weights | open-weights-tips.md (this file) |

---

## Common failure modes on open-weights and fixes

| Symptom | Fix |
|---|---|
| Architect generates FRs without GIVEN/WHEN/THEN acceptance criteria | Add explicit instruction: "every FR MUST have ≥1 acceptance criterion in GIVEN/WHEN/THEN form" |
| Architect uses "must" instead of "shall" | Add the vocabulary discipline block (see above) |
| Architect renumbers FRs after deletion | Add: "FR IDs are stable; never renumber. Leave gaps." |
| FRs become repetitive in body text | Generate in smaller batches per capability |
| RTM has phantom entries (FRs in RTM that don't exist in FSD) | Run traceability AFTER architect's final pass; never in parallel |
| Use cases drift into implementation detail | Reload use-case-templates.md; restate "narrative, not implementation" |
| Validator marks everything PASS | Validator model too small; use Qwen-Coder-14B+ or larger |
| Validator hallucinates fails (claims fails that aren't there) | Add: "cite the exact line/section for every FAIL; if you cannot cite, change to PASS" |
| Discovery brief misses stakeholder categories | Add: "before writing brief, list every stakeholder category from BABOK techniques §1, and confirm coverage" |

---

## Serving stack tips

This package is provider-agnostic. Recommended setups:

- **vLLM with grammar/JSON constraints** — production-grade local serving, supports JSON-schema-constrained generation that significantly improves FR template adherence.
- **llama.cpp with JSON mode** — laptop-grade, gguf quantizations.
- **Ollama** — simplest solo dev experience.
- **LM Studio** — GUI for non-CLI users.
- **OpenRouter / DeepInfra / Together** — if you'd rather not self-host but want open-weights models via OpenAI-compatible APIs.

For grammar-constrained generation of FR templates, see `references/grammars/fr-template.gbnf` in the vLLM/llama.cpp grammar formats. (Optional — only include if you adopt grammar mode.)

---

## Reality check on what's achievable per tier

**Frontier closed:** Produces FSDs indistinguishable from a senior BA's output. Few validator fails.

**Frontier open large (gpt-oss-120b, Qwen3-Coder-480B):** Produces FSDs at consultant-grade with 2–3 validation loops. Cost: similar to or less than 1 senior BA week.

**Mid open capable (Qwen3-32B, gpt-oss-20b, Gemma-3-27B):** Produces FSDs at intermediate BA grade. Requires 3–5 validation loops. Cost: minimal. Best for: prototype FSDs, internal projects, drafts that a senior BA will review.

**Mid open smaller (Gemma-3-12B, Qwen2.5-14B):** Produces FSDs adequate for non-regulated internal projects. Not recommended for compliance-sensitive work without expert review.

**Small (<12B):** Use only for individual sections, not whole FSDs. Best for: validator role, RTM generation from a clean FSD.

Match the model to the stakes. A regulated banking project should not run on Gemma 3 4B. An internal tooling FSD might.
