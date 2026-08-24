# Developer Toolkit — Guided Custom Agent Builder

*A guided path from **intent → recommended implementation → build execution** for SAP custom AI agents. This is not a compliance checklist — it is the wizard that walks you from "here's what I want to build" to a working, governed agent, choosing the right cookbook and accelerator for your use case along the way.*

> **Where this fits:** part of the **Agent-GoldenPath-Kit**. It sits on top of the two build cookbooks (CoE, KG), the Agent Blueprint, and the 10-pillar Agent Checklist — and uses the GDH AI Factory onboarding workflow to frame the intake. Clone the kit, open it in Claude Code, and say *"read developer-toolkit.md and help me build my agent."*

---

## 0 · How Claude should use this file

**When a developer opens this repo in a coding harness (Claude Code) and asks to build an agent, act on this file — do not just display it.**

1. **Set the scope first (§2.0).** Ask the one front-door question: full custom agent / Joule skill / plugin/tool / multi-agent / embedded feature? Default: **full custom agent**. If intent.md is clear, confirm without asking.
2. **Run the Use-case intake (§2)** — one cluster at a time; accept a single-line intent and infer the rest.
3. **Produce a Solution recommendation (§3)** — agent type, platform, low-code vs pro-code, cookbook/accelerator, rationale + one alternative. No hard-coded rules.
4. **Walk the Build journey (§6)** for the chosen scope. At every step, name the applicable checklist controls (§10) **and immediately assign a status flag to each:**
   - `✅ Satisfied` — demonstrably met by what was built/configured.
   - `⚠️ Partial` — partially met; document what is missing.
   - `❌ Not satisfied` — applies to this scope but not met; flag prominently with reason + remediation needed before production.
   - `⏭️ Skipped — N/A` — does not apply to this scope (per §10 scope table); state why.
   **Never silently omit a control. Every applicable control must have a status.**
5. **Write `implementation-plan.md` (§11)** into the new agent sub-folder — scope, approach, assets, ordered steps, demo UI + mock data (IBD_TESTING=1), cleanup task.
6. **Write `agent-outcome-report.md` (§12)** into the new agent sub-folder — the complete build record: what was built, every L0-L10 control with its flag, ❌/⚠️ items to resolve before production, go/no-go verdict. **This is the hand-off document.**
7. Only pause when something essential is missing or contradictory. Otherwise, keep moving.

**Inputs:** a statement of intent (one line is enough) + this repo.
**Outputs written to the agent sub-folder:** `implementation-plan.md` · `agent-outcome-report.md` · mock data · demo UI · cleaned-up agent code.

---

## 1 · How to use this guide

- **Audience:** developers building SAP custom agents.
- **The loop:** intake (§2) → recommendation (§3) → catalog (§4) → build journey (§6, with checklist flags at every step) → implementation-plan.md (§11) → agent-outcome-report.md (§12).
- **Templates (§7)** and **worked examples (§8)** are there to copy from. **Troubleshooting (§9)** is for when a step doesn't go to plan.
- **Onboarding frame:** mirrors the **GDH AI Factory** workflow — value case first, then architecture, then build — so what you produce here feeds cleanly into the wider governance path.

---

## 2 · Use-case intake

### 2.0 · Scope gate — what are you actually building? *(ask this first)*

*Claude: this single question routes everything after it. The **default and primary path is a full custom agent** — if the user just states intent, assume that and confirm. Offer the other scopes only if the work clearly isn't a standalone agent.*

| Scope | What it means | Typical build surface | Deploy reality |
|---|---|---|---|
| **Full custom agent** *(default)* | A new standalone agent, idea → production | Pro-code scaffold (cookbook) or Joule Studio | Own runtime on CF/Kyma, registered with Joule |
| **Joule skill** | One capability added to the *existing* Joule agent | Joule Studio Skill Builder (low-code) | No new runtime — published as a skill |
| **Plugin / tool** | A callable tool/action extending an existing agent | Tool definition + backend API | Bound to the host agent; no standalone deploy |
| **Multi-agent system** | Several agents collaborating / an orchestrator | Pro-code scaffold, per-agent + orchestration | Multiple runtimes + routing |
| **Embedded AI feature** | AI inside a business process (not conversational) | Feature code + AI Core | Ships with the host application |

**How the scope changes the flow:**
- It sets **which cookbook/accelerator (if any)** — a Joule skill or plugin may need *no* cookbook, just Skill Builder / a tool definition.
- It sets **which build-journey steps (§6) apply** — a skill/plugin skips "scaffold a runtime" and "deploy to CF/Kyma"; a multi-agent build adds orchestration + conflict resolution.
- It sets **which checklist controls (§10) fire** — see the scope→subset note at the top of §10. Don't impose the full 70-control gate on a single skill.

*Once scope is set, run the intake below at the right depth.*

---

*Claude: ask these in plain language, one cluster at a time. A one-line intent is valid — infer the rest and confirm.*

**A. What should the agent do?**
- The business outcome in one sentence (the "north-star" intent).
- The concrete tasks the agent performs (retrieve, summarise, recommend, act).
- Advisory-only, or does it take actions in SAP / external systems?

**B. Who will use it?**
- Primary users (role, technical level).
- Interaction channel: Joule, a custom UI, an API, an event trigger?

**C. What knowledge, systems, actions, and channels are needed?**
- **Knowledge / grounding:** structured SAP data (OData), documents (RAG), entity relationships (Knowledge Graph), or a mix?
- **Systems:** which SAP modules / APIs / external services?
- **Actions:** read-only, or write-back / workflow triggers?
- **Identity:** whose identity reaches SAP (technical user vs principal propagation)?

**D. Complexity and expected scale**
- Single-step (one LLM call) or multi-step reasoning / tool-calling / multi-agent?
- Expected volume and latency expectations.
- Data residency / sovereignty constraints.

> **Capture even a single line.** Restate your understanding back in one short summary, listing every assumption and default you applied, before moving to the recommendation.

---

## 3 · Solution recommendation

*Claude: derive this from §2 answers. No fixed rules — reason it out and justify.*

Produce a recommendation covering:

- **Scope confirmation** — restate the §2.0 scope (full agent / skill / plugin / multi-agent / embedded) so the rest of the recommendation is anchored to it.
- **Agent type** — reactive / chain-of-thought / ReAct (tool-using) / multi-agent.
- **Platform & runtime** — Joule Studio + AI Core; Cloud Foundry vs Kyma.
- **Low-code vs pro-code path** — Joule Studio Agent/Skill Builder (low-code) vs scaffolded code build (pro-code). Base this on the developer's stated skill level, customisation depth, and action complexity.
- **Recommended pattern / cookbook** — see the catalog (§4).
- **Recommended accelerator or repository** — the specific starter asset to clone.
- **Rationale and alternatives** — *why* this fits, and one credible alternative with the trade-off.

**Decision aid (guidance, not rules — Claude adapts):**

| If the use case is dominated by… | Lean toward… |
|---|---|
| General business logic, tool/API actions, fast prototyping | **CoE Cookbook** |
| Entity relationships, ontologies, semantic / multi-hop reasoning, structured KG grounding | **KG Cookbook** |
| Greenfield, unsure where to start, want the full guided scaffold + guardrails | **Agent-GoldenPath-Kit** scaffold |
| Document-heavy Q&A / grounding | Either cookbook + RAG grounding (see §6 Connect) |

---

## 4 · Cookbook and accelerator catalog

### CoE Cookbook — *Custom-Agentic-Solutions-CoE*
- **Purpose (plain language):** the main global build engine — scaffolding, toolkit, connectivity, and deployment for general SAP custom agents.
- **Best-fit scenarios:** tool-using business agents, SAP application integration, rapid prototyping, orchestrator patterns.
- **Prerequisites:** BTP subaccount (CF/Kyma), AI Core, Python toolchain.
- **Skill level:** developer-friendly; low-code entry via Joule Studio.
- **Limitations:** not optimised for heavy graph/ontology reasoning.
- **Repository:** <https://github.tools.sap/business-ai-platform/Custom-Agentic-solutions-CoE>
- **Quick-start:** clone → `sap-agent-bootstrap` → mock mode (see §6).

### KG Cookbook — *Cookbook-KG-CustomAI*
- **Purpose:** Knowledge-Graph-grounded agents on SAP HANA RDF — ontology, semantic search, multi-hop reasoning.
- **Best-fit scenarios:** relationship-rich enterprise use cases, explainable reasoning over entities, structured grounding.
- **Prerequisites:** SAP HANA Cloud (RDF/Vector), KG data model, AI Core.
- **Skill level:** developer; some data-modelling familiarity helps.
- **Limitations:** heavier setup; overkill for simple tool-calling agents.
- **Reference / program:** <https://pages.github.tools.sap/GDH-AIFactory-CodeAgents-KG/doc/>
- **Quick-start:** model the KG grounding first, then scaffold (see §6 Connect).

### Agent-GoldenPath-Kit — *the starter kit (this repo)*
- **Purpose:** clone-and-go starter bundling cookbooks, accelerators, this toolkit, and the checklist guardrails for Claude Code.
- **Best-fit scenarios:** greenfield builds, or when you want the guided end-to-end flow.
- **Prerequisites:** Claude Code (or a coding harness), repo access.
- **Skill level:** any developer; Claude drives the flow.
- **Limitations:** it orchestrates the cookbooks — the actual build engine is still the chosen cookbook.
- **Repository:** <https://github.tools.sap/I039198/Agent-PathToProd/tree/main>
- **Quick-start:** open in Claude Code → *"read developer-toolkit.md and build my agent."*

### Agent Blueprint (hardening guide)
- **Purpose:** the complete build-and-harden reference — the 8-stage flow, connectivity modes, switchable-code readiness.
- **Best-fit scenarios:** taking any agent from working to customer-ready/production.
- **Reference:** <https://pages.github.tools.sap/I778959/agent-blueprint/>

### Agent Checklist (10-pillar governance) — *embedded in full at §10*
- **Purpose:** the canonical L0-1→L0-10 governance controls. Referenced at each build stage and **embedded in full in §10** of this file so it works as a self-contained guardrail — no external fetch needed.
- **Live interactive version:** <https://pages.github.tools.sap/I778959/agent-blueprint/checklist/>

---

## 5 · Prerequisites (all paths)

- BTP subaccount with **Cloud Foundry or Kyma**, **AI Core**, and (if used) **Agent Gateway / Destination + Connectivity** entitlements.
- **Joule IAS** account and **JouleAdmin** role collection (for registration).
- Python toolchain for pro-code; Joule Studio access for low-code.
- Confirmed **API usage/policy** and **data residency/region** posture *(Checklist L0-1, L0-5)*.

---

## 6 · Step-by-step build journey

*Each step: what to do, plus the applicable Agent Checklist gate. Verify the referenced control IDs before advancing — see §10 for the mapping.*

> **Scope-aware:** the steps below are the **full custom agent** path (the default). For a **Joule skill** or **plugin/tool**, skip 6.3's runtime scaffold and most of 6.6's standalone deploy — you build/publish through Joule Studio Skill Builder or a tool definition instead. For a **multi-agent system**, add an orchestration + cross-agent conflict-resolution step (`L0-8.3`) between Build and Connect. Claude: adapt the journey to the §2.0 scope; don't force skipped steps.

### 6.1 Prepare
- Restate the intent as a value case; confirm API access, data residency, BTP entitlements.
- Pick the cookbook + accelerator from §3/§4.
- **Checklist gate:** `L0-1` (intake & classification), `L0-4` (commercial tier, if productised).

### 6.2 Configure
- Set up the local project from the chosen cookbook; configure `.env` (secrets go in `.env`, never in code or markdown).
- Choose model provider (default: AI Core) and runtime target.
- **Checklist gate:** `L0-2` (model selection), `L0-6` (dev standards).

### 6.3 Build
- Scaffold with `sap-agent-bootstrap`; implement the three mandatory decorators (agent card / skill / executor).
- Build **mock-first** — prove the agent fully offline before any live data. Mock mode is activated by the **`IBD_TESTING`** flag (`IBD_TESTING=1` / `="true"` → mock everywhere). **Do NOT branch on `IBD_TESTING` inside application code** — the test/mock harness (`conftest.py`) swaps the tool layer (`mcp_tools.get_mcp_tools`) before agent code runs, so agent code is byte-identical in mock and production. Gate mock behaviour at the **tool/data boundary**, not in business logic.
- **Produce mock data** (deterministic fixtures the mock tool layer returns) so the agent runs end-to-end offline under `IBD_TESTING=1`.
- **Produce a demo UI (HTML)** — a lightweight standalone page that exercises the agent for showcasing. It must run against **mock mode** (served through the `IBD_TESTING`-activated mock tool layer, no live SAP/credentials), so anyone can demo it offline.
- **Checklist gate:** `L0-6` (Agent Builder / Skill Builder), `L0-8` (design classification, performance).

### 6.4 Connect knowledge and actions
- **Grounding:** OData (structured) → CoE path; documents → RAG (validate the RAG Triad); relationships → KG cookbook.
- **Actions:** wire tools/skills; enforce least-privilege tool access; default advisory-only (no writes) unless required.
- **Checklist gate:** `L0-3` (RAG quality), `L0-9` (KG/grounding strategy), `L0-6.6` (tool access governance), `L0-6.7` (human-in-the-loop for actions).

### 6.5 Test
- Run the full suite in mock mode: `IBD_TESTING=1 pytest` (fully offline, coverage ≥70%, golden-set eval passes). Validate identity at the A2A boundary; exercise error/resilience paths.
- Confirm the demo UI (6.3) runs offline under `IBD_TESTING=1` against the mock data.
- **Checklist gate:** `L0-5` (safety, red-team, bias), `L0-7.1/7.6` (AET + regression environment).

### 6.6 Deploy
- Push to CF/Kyma; register the agent card with Joule Studio; wire intent routing.
- Confirm metering, observability, and rollback (CBC toggle).
- **Checklist gate:** `L0-7` (release validation & go-live), `L0-6.8` (observability/tracing), `L0-10` (post-go-live resilience).

### 6.7 Cleanup (before hand-off)
- **Remove unused code and template stubs** left by the scaffold — dead decorators, placeholder tools, sample files, and any `[illustrative]` snippets that were never wired in.
- Remove any accelerator/cookbook templates you copied but didn't use.
- Keep the **mock data + demo UI** (they're deliverables, gated by `IBD_TESTING`) — but delete scaffolding that isn't part of the final agent.
- Confirm no secrets in code/markdown; `.env` gitignored; no invented imports remain.
- **Checklist gate:** `L0-6` (dev standards — no credentials committed, no invented imports).

---

## 7 · Reusable templates

Copy and fill these. Claude will populate them from the intake where possible.

### 7.1 Use-case definition
```
Intent (one line):
Primary users / channel:
Tasks the agent performs:
Advisory-only or takes actions:
Knowledge sources (OData / RAG / KG):
Systems & APIs:
Complexity (single-step / multi-step / multi-agent):
Scale & latency:
Data residency / sovereignty:
```

### 7.2 Agent instructions (system prompt skeleton)
```
Role:
Scope & boundaries (what it must NOT do):
Mandatory rules (advisory-only, no fabrication, disclaimer on outputs):
Grounding sources it may cite:
Tone / output format:
```

### 7.3 Knowledge-source mapping
```
| Query type | Grounding strategy | Source | Freshness/SLA |
|---|---|---|---|
```

### 7.4 Tool / action definition
```
Tool name:
Backend API / call:
Input schema / Output schema:
Permission scope (least privilege):
Failure / timeout fallback:
Human-in-the-loop required? (Y/N)
```

### 7.5 Test scenarios
```
| Scenario | Input | Expected behaviour | Pass/Fail |
|---|---|---|---|
(include edge cases, adversarial prompts, downstream-failure handling)
```

### 7.6 Architecture decision record (ADR)
```
Decision:
Context:
Options considered:
Chosen option & rationale:
Consequences / trade-offs:
Checklist controls satisfied:
```

### 7.7 Mock data (offline fixtures, `IBD_TESTING`)
```
# Deterministic fixtures returned by the mock tool layer when IBD_TESTING=1.
# Keyed by tool/entity so the agent runs end-to-end offline with no live SAP.
Tool / entity:
Sample request:
Sample response (mock):
Edge / error cases represented:
```

### 7.8 Demo UI (HTML, mock-mode only)
```
# A standalone HTML page that exercises the agent for showcasing.
# Runs against mock mode (IBD_TESTING=1) — no live SAP, no credentials.
- Single self-contained index.html (inline CSS/JS; no build step).
- Calls the local agent endpoint running under IBD_TESTING=1.
- Shows: input box → agent response → the mock data it "retrieved".
- Clearly labelled "DEMO — mock data" so it's never mistaken for live.
```

---

## 8 · Examples

*Illustrative — Claude tailors to real answers.*

1. **Supply Chain Risk advisor** — reads S/4HANA (OData), summarises risk, advisory-only.
   Answers: multi-step, structured data, no writes → **CoE Cookbook**, ReAct pattern, CF deploy.
2. **Policy Q&A assistant** — answers from a document corpus.
   Answers: document-heavy, read-only → **CoE Cookbook + RAG grounding**, RAG Triad validated (`L0-3`).
3. **Master-data relationship explorer** — traverses entity relationships/ontology.
   Answers: relationship-rich, explainable → **KG Cookbook**, structured KG grounding (`L0-9`).
4. **Procurement action agent** — drafts POs / raises tickets.
   Answers: takes actions, write-back → **CoE Cookbook**, tool access governance (`L0-6.6`) + human-in-the-loop (`L0-6.7`).
5. **Greenfield / undecided** — dev unsure of pattern.
   Answers: exploratory → **Agent-GoldenPath-Kit scaffold**, mock-first, decide grounding after intake.

Each example resolves to: user answers → recommended cookbook/accelerator → expected final architecture (agent type + grounding + runtime).

---

## 9 · Troubleshooting and decision support

**Common errors**
- *Live-data 403/404 before mock is proven* → always build mock-first (§6.3); debugging live data is far harder.
- *Agent card returns invalid JSON* → check the three mandatory decorators and coverage ≥70%.
- *Grounding returns irrelevant chunks* → tune retrieval / chunk size; validate context relevance (`L0-3`).
- *Identity errors at A2A boundary* → validate the JWT; never trust client-supplied identity.

**"If this happens, use this approach"**
- *Reasoning loops run away / cost spikes* → bound steps; measure orchestration-layer performance (`L0-8.5`), set a cost-per-transaction ceiling (`L0-4.8`).
- *Answers plausible but wrong* → add the runtime hallucination guardrail (`L0-3.8`) and continuous accuracy pipeline (`L0-10.6`).

**When to switch from low-code to pro-code**
- Custom orchestration, non-standard tools, complex state, or performance tuning beyond what Joule Studio exposes → move to the scaffolded pro-code path.

**Escalation / support**
- Engage the **GDH APAC Data & AI Architect Group** early (`L0-1.5`) for design review and escalation paths.

---

## 10 · Agent Checklist — 10 pillars, 70 controls (embedded, full)

**The complete L0-1 → L0-10 governance checklist is embedded below** so this toolkit is self-contained. Use the stage→pillar map to know *which* controls apply at each build step (§6); tick the items as you go. Live interactive version: <https://pages.github.tools.sap/I778959/agent-blueprint/checklist/>.

> **Scope the controls to the unit of work (§2.0) — don't impose all 70 on a small build.** A **full custom agent** clears all applicable pillars. A **Joule skill** or **plugin/tool** typically needs only the intake, model, dev-standards, grounding/tool-access, and safety controls — not the standalone go-live (L0-7) or change-resilience (L0-10) pillars that assume an independent runtime. A **multi-agent system** additionally needs `L0-8.3` (conflict resolution) and per-agent drift detection. Claude: present the applicable subset for the chosen scope, and say plainly which pillars you're skipping and why.
>
> | Scope | Typically applicable | Typically light / N/A |
> |---|---|---|
> | Full custom agent | L0-1 … L0-10 (all, as relevant) | — |
> | Joule skill | L0-1, L0-2, L0-3/9 (if grounded), L0-5, L0-6 | L0-4*, L0-7, L0-10 |
> | Plugin / tool | L0-1, L0-6.6, L0-6.7, L0-5 (if it acts) | L0-2, L0-4, L0-7, L0-10 |
> | Multi-agent system | all + L0-8.3, per-agent L0-10 | — |
> | Embedded AI feature | L0-1, L0-2, L0-3, L0-5, L0-4 | L0-6 (agent tooling), parts of L0-7 |
>
> \*commercial pillars still apply if the skill/feature is monetised.

### Stage → pillar map

| Build stage | Applicable pillars / controls |
|---|---|
| Prepare | `L0-1` onboarding & classification · `L0-5` data governance · `L0-4` commercial tier |
| Configure | `L0-2` model selection · `L0-6` dev standards |
| Build | `L0-6` Agent/Skill Builder · `L0-8` design classification & performance |
| Connect knowledge & actions | `L0-3` RAG quality · `L0-9` KG/grounding · `L0-6.6` tool access · `L0-6.7` human-in-the-loop |
| Test | `L0-5` safety/red-team/bias · `L0-7.1` AET · `L0-7.6` regression env |
| Deploy | `L0-7` release & go-live · `L0-6.8` observability · `L0-10` change resilience |

> **Link key:** `ekg.cloud.sap` = SAP Knowledge Graph URIs (source of truth); `idea-agent` = Idea2Value tool; others are SAP Help Portal, API Business Hub, Discovery Center, learning.sap.com, or the Trust Centre.

---

### L0-1 · AI Feature & Agent Onboarding Governance
*Structured intake and classification for every AI feature or agent.*

- [ ] **1.0 Idea2Value** — Convert an unstructured idea into a CXO-ready value case via guided Socratic conversation grounded in 14+ SAP Enterprise Knowledge sources (Discovery, Grounding, Tools, ROI, TRUST — each with an evidence gate). Primary traceability record for 4.2, 1.5, 7.5. — [Idea2Value](https://idea-agent.cfapps.us10-001.hana.ondemand.com/) · [ESCE](https://ekg.cloud.sap/SAP/LX/TM/TRM/ESCE5CF3FCDB46F61EE7A8859EFC21919645)
- [ ] **1.1 Feature Type Classification** — Classify embedded / generative / agentic / process-automation before design; routes the sub-checklist, LLM depth and Responsible AI tier. — [Golden Path](https://architecture.learning.sap.com/docs/ai-golden-path)
- [ ] **1.2 Commercial Tier Determination** — Assign included/optional/premium tier by cost, volume, value; input to 4.2, gates 4.5. — [Pricing](https://www.sap.com/products/artificial-intelligence/ai-units.html) · [AI Core Pricing](https://discovery-center.cloud.sap/serviceCatalog/sap-ai-core/?region=all&tab=service_plan&commercialModel=payg)
- [ ] **1.3 AI Golden Path** — SAP's prescribed governance pathway; undocumented deviations are a release blocker. — [Golden Path](https://architecture.learning.sap.com/docs/ai-golden-path)
- [ ] **1.4 Document AI Commercialization Track** — Compare per-page vs accelerator volume economics; document break-even before customer-scale processing. — [Pricing](https://www.sap.com/products/artificial-intelligence/ai-units.html)
- [ ] **1.5 GDH APAC Data & AI Architect Group Support** — Engage the central architect group early for design review, platform guidance, escalation paths; confirm before build. — [ESCE](https://ekg.cloud.sap/SAP/LX/TM/TRM/ESCE5CF3FCDB46F61EE7A8859EFC21919645)
- [ ] **1.6 Onboarding Agent Templates** — Point to the central GDH APAC md carrying both cookbooks. *(To be finalised.)* — [CoE](https://github.tools.sap/business-ai-platform/Custom-Agentic-solutions-CoE) · [KG Program](https://github.tools.sap/GDH-AIFactory-CodeAgents-KG/doc)

### L0-2 · LLM Selection & Benchmarking
*Select the right model per use case, balancing performance and cost.*

- [ ] **2.1 Test Data Preparation & Submission** — Curate a representative eval dataset (edge cases, multi-language, adversarial); synthetic/masked only, no production customer data. — [Gen AI Hub](https://www.sap.com/products/artificial-intelligence/generative-ai-hub.html)
- [ ] **2.2 Automated Multi-Model Evaluation** — Run the dataset against all candidates for comparable accuracy/token/safety/cost; evidence base for 2.6. — [AI Core API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/AICoreAI_CORE_API)
- [ ] **2.3 Generative AI Evaluation Roadmap** — Track upcoming mandatory criteria; build into test data before they become GA gates. — [Gen AI Hub](https://www.sap.com/products/artificial-intelligence/generative-ai-hub.html)
- [ ] **2.4 Results via Helm Dashboard** — Immutable reporting surface; canonical evidence for 2.6, baseline for 2.5. — [AI Launchpad](https://help.sap.com/docs/ai-launchpad/sap-ai-launchpad/what-is-sap-ai-launchpad?locale=en-US)
- [ ] **2.5 Ongoing Model Version Re-evaluation** — Re-run the suite on any provider update/patch/infra swap; resolve regressions before customer tenants. Triggers 10.3. — [AI Launchpad](https://help.sap.com/docs/ai-launchpad/sap-ai-launchpad/what-is-sap-ai-launchpad?locale=en-US)
- [ ] **2.6 Frontier Model Justification Gate** `NEW` — Document why a frontier model beats a cheaper one per agentic decision step (evidence from 2.2); dual approval before provisioning. — [Gen AI Hub](https://www.sap.com/products/artificial-intelligence/generative-ai-hub.html)
- [ ] **2.7 Model Update & Retraining Governance** `NEW` — Fine-tuning cadence, swap schedule, customer notification, data-usage policy; attest no customer data used without consent. Connects to 10.6. — [Responsible AI](https://www.sap.com/india/products/artificial-intelligence/ai-ethics.html)

### L0-3 · Document Grounding & RAG Quality Evaluation
*Ground outputs in enterprise documents; validate with the RAG Triad.*

- [ ] **3.1 Document Grounding Setup** — Connect via Document Grounding API (chunking, metadata, access filters); validate against the Triad before prod; only governance-approved docs indexed. — [Doc Grounding API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/GroundingDOCUMENT_GROUNDING_API)
- [ ] **3.2 Vector Embedding & Retrieval Pipeline** — Select embedding model, configure vector store, validate precision/recall; SAP HANA Cloud Vector Engine is native; version-control params. — [Doc Grounding API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/GroundingDOCUMENT_GROUNDING_API)
- [ ] **3.3 RAG Triad — Context Relevance** — Measure proportion of retrieved chunks relevant to the query; irrelevant chunks are the top upstream cause of hallucination. — [Doc Grounding API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/GroundingDOCUMENT_GROUNDING_API)
- [ ] **3.4 RAG Triad — Faithfulness** — Verify every claim is grounded in retrieved context (LLM-as-judge); below-threshold is an automatic release blocker. — [Responsible AI](https://www.sap.com/india/products/artificial-intelligence/ai-ethics.html)
- [ ] **3.5 RAG Triad — Answer Relevance** — Measure how directly the answer addresses the query; all three triad scores must pass together. — [Gen AI Hub](https://www.sap.com/products/artificial-intelligence/generative-ai-hub.html)
- [ ] **3.6 Prompt Engineering Governance** — Version-control all prompts/templates with a change-approval workflow; review for injection & role-boundary erosion. — [Gen AI Hub](https://www.sap.com/products/artificial-intelligence/generative-ai-hub.html)
- [ ] **3.7 Automated Grounding Roadmap** — Anticipate when manual grounding steps are automated and new thresholds become gates. — [Doc Grounding](https://discovery-center.cloud.sap/ai-feature/fedeca14-3e69-472c-a0ea-82396735c35f/)
- [ ] **3.8 Runtime Hallucination Guardrail Architecture** `NEW` — Output-validation layer: confidence threshold, auto-rejection, customer-visible citations, monitoring + alert threshold. Connects to 10.6. — [Doc Grounding API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/GroundingDOCUMENT_GROUNDING_API)

### L0-4 · AI Commercialization & Metering
*Commercial lifecycle from pricing to production billing.*

- [ ] **4.1 LLM Calculator** — Internal tool estimating the LLM cost component; input to 4.2 and 4.5; save dated snapshots. — [Pricing](https://www.sap.com/products/artificial-intelligence/ai-units.html)
- [ ] **4.2 BMP Expert Approval** — Pricing expert validates cost assumptions and approves the commercial structure before CBC activation; prerequisite for 7.4. — [Pricing](https://www.sap.com/products/artificial-intelligence/ai-units.html)
- [ ] **4.3 AI Scenario Metering Integration** — Attribute every LLM call/invocation/tool execution to tenant/scenario/SKU; validate before go-live; failures are a P1 commercial incident. — [AI Core API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/AICoreAI_CORE_API)
- [ ] **4.4 Feature Activation via CBC** — Content Based Configuration enables features (phased rollout, opt-in, emergency disable, no code deploy); test activation + deactivation + rollback. — [AI Launchpad](https://help.sap.com/docs/ai-launchpad/sap-ai-launchpad/what-is-sap-ai-launchpad?locale=en-US)
- [ ] **4.5 Floor Price Impact Review** — Confirm tier price exceeds the direct LLM cost floor across the usage distribution. — [Pricing](https://www.sap.com/products/artificial-intelligence/ai-units.html)
- [ ] **4.6 SAP Business AI Pricing Model** — Consumption-based (AI units/credits); align metering (4.3) exactly with the published model. — [Pricing](https://www.sap.com/products/artificial-intelligence/ai-units.html)
- [ ] **4.7 Customer Token Consumption Forecast** `NEW` — Pre-deployment estimate of tokens per interaction type given to the customer (distinct from internal 4.1). — [Pricing](https://www.sap.com/products/artificial-intelligence/ai-units.html)
- [ ] **4.8 Cost Per Transaction Baseline** `NEW` — Instrument cost per invocation across LLM/tool/retrieval; set ceilings before go-live, review quarterly. — [AI Core API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/AICoreAI_CORE_API)

### L0-5 · Responsible AI & Safety Validation
*Mandatory pre-release evaluation — safety, ethics, fairness, compliance.*

- [ ] **5.1 Safety Dashboard Pre-Release Evaluation** — Run through the internal Safety Dashboard (harm, content safety, bias, regulatory); hard gate before 7.4. — [Responsible AI](https://www.sap.com/india/products/artificial-intelligence/ai-ethics.html)
- [ ] **5.2 AI Bias & Fairness Assessment** `EXPANDED` — Evaluate demographic bias with a defined framework + thresholds + customer disclosure; re-evaluate ≥ 6-monthly or after model change. — [Responsible AI](https://www.sap.com/india/products/artificial-intelligence/ai-ethics.html)
- [ ] **5.3 Adversarial & Red Team Testing** — Direct prompt injection, jailbreaks, role-boundary erosion, DoS; document severity/repro/remediation; repeat after prompt/model changes. — [Adversarial Attacks](https://learning.sap.com/courses/architecting-security-for-sap-business-technology-platform/differentiating-ai-vulnerabilities-and-attack-vectors)
- [ ] **5.4 AI Ethics & Governance Alignment** — Transparency, explainability, human oversight, high-risk prohibitions; sign-off from the Responsible AI function; disclose AI nature. — [Responsible AI](https://www.sap.com/india/products/artificial-intelligence/ai-ethics.html)
- [ ] **5.5 GDPR / EU AI Act Compliance** — Risk classification, technical docs, conformity assessment, human oversight; state category + evidence. — [Responsible AI](https://www.sap.com/india/products/artificial-intelligence/ai-ethics.html)
- [ ] **5.6 Indirect Prompt Injection via Business Data** `NEW` — Scan the RAG corpus + connected business data (CRM, supplier, procurement, HR) for injected instructions; automated scan + human review + sanitisation; re-run on new sources. — [Doc Grounding API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/GroundingDOCUMENT_GROUNDING_API)
- [ ] **5.7 IP Rights & Data Ownership Governance** `NEW` — Declare output ownership, tenant isolation, non-use of customer data in training, copyright, indemnification; a distinct artefact; define dispute escalation. — [Responsible AI](https://www.sap.com/india/products/artificial-intelligence/ai-ethics.html)

### L0-6 · Agent Development & Deployment Standards
*Tooling, patterns, governance for building, registering, deploying.*

- [ ] **6.1 Agent Builder in Joule Studio** — Configure/test/register agents against the SAP agent framework; agents built outside need an exception + security review. — [Agent Builder](https://www.sap.com/products/financial-management/joule-studio-agent-builder.html)
- [ ] **6.2 Skill Builder in Joule Studio** — Define/test/publish skills; each maps to backend APIs with a declared scope; auto-registered in 6.4; include I/O schema, error handling, latency SLA. — [Joule Studio](https://www.sap.com/products/artificial-intelligence/joule-studio.html)
- [ ] **6.3 Generative AI Hub (J17)** — Managed LLM access layer; all LLM calls route through it for access control, audit, cost metering. — [Gen AI Hub](https://www.sap.com/products/artificial-intelligence/generative-ai-hub.html)
- [ ] **6.4 Skills Governance Agent (J1426)** — Catalog of approved skills (version control, access policy, quality). *KG identifies this as J2259 — verify the current feature ID.* — [Skills Gov (J2259)](https://learning.sap.com/courses/exploring-joule-and-ai-agents-in-sap-successfactors/introducing-skills-assistants-and-agents_ad8e62d6-372b-4ba4-ad74-152130786666)
- [ ] **6.5 SAP AI Core & AI Launchpad** — AI Core is the serving runtime for agentic workloads; AI Launchpad the ops interface; use AI Core unless an approved exception. — [AI Core API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/AICoreAI_CORE_API)
- [ ] **6.6 Agent Tool Access Governance** `NEW` — RBAC for all tool invocations, per-tenant policy, least privilege, approval workflow; enumerate callable tools, min scope, audit-log schema; SoD for financial/procurement/HR writes. — [RBAC](https://ekg.cloud.sap/SAP/LX/TM/CPT/RoleBasedAccessControl42010AEF0E491EECB388711182364F45)
- [ ] **6.7 Human-in-the-Loop Approval Governance** `NEW` — Define which actions need mandatory human sign-off vs autonomous; action classification table; override events logged with approver/timestamp/reason. — [Human-in-the-Loop](https://ekg.cloud.sap/SAP/LX/TM/TRM/HumanInTheLoop42010AEF4E231FD0B1BF8B43444361B3)
- [ ] **6.8 Agent Execution Observability & Tracing** `NEW` — Step-level structured tracing for multi-hop agents (step ID, type, inputs, outputs, latency, model/tool, error); accessible to engineering + support with retention. — [AI Launchpad](https://help.sap.com/docs/ai-launchpad/sap-ai-launchpad/what-is-sap-ai-launchpad?locale=en-US)

### L0-7 · End-to-End Release Validation & Go-Live
*Final gate confirming all pillars are satisfied before release.*

- [ ] **7.1 AI-Driven Exploratory Testing (AET)** — J1186 generates/executes test cases across the functional surface incl. edge cases. *GA Dec 2027 — verify availability, keep an interim approach.* — [AET](https://ekg.cloud.sap/SAP/MXP/JV/AIF/AIDrivenExploratoryTestingAETAutomatedTestCaseGenerationJ1186)
- [ ] **7.2 Integration Validation** — End-to-end with all backends/APIs under production-like conditions; auth, permission boundaries, downstream failure, peak load; repeat after any change. — [AI Core API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/AICoreAI_CORE_API)
- [ ] **7.3 CBC Toggle Activation** — Final config step before live; test activation + deactivation; document and test rollback. Monitored by 10.5.
- [ ] **7.4 Cross-Functional Sign-Off** — Product, Engineering, Commercialisation, Legal/Compliance, Responsible AI, Support (ESCE), Security; final gate before CBC + release record. — [ESCE](https://ekg.cloud.sap/SAP/LX/TM/TRM/ESCE5CF3FCDB46F61EE7A8859EFC21919645)
- [ ] **7.5 Official Release (AI112)** `CORRECTED` — The release event (identifier **AI112**) confirming GA; closes the pre-release record, opens L0-10 monitoring; traceable to 1.0, 4.2, 7.4.
- [ ] **7.6 Agent Regression Testing Environment** `NEW` — Dedicated non-prod env with production parity + versioned regression suite; mandatory before any model/tool/KG/prompt change; regression = automatic release blocker. — [AET](https://ekg.cloud.sap/SAP/MXP/JV/AIF/AIDrivenExploratoryTestingAETAutomatedTestCaseGenerationJ1186)

### L0-8 · Agent Design Classification & Performance Engineering
*Classify every step by trigger and reasoning mode; measure per layer.*

- [ ] **8.1 Trigger Type Classification** — user-initiated / event-driven / scheduled / multi-agent; sets timeout budget, error handling, UX; documented before SLAs. — [Agent Builder](https://www.sap.com/products/financial-management/joule-studio-agent-builder.html)
- [ ] **8.2 Agentic Reasoning Classification** — reactive / chain-of-thought / ReAct / multi-agent delegation; determines which governance applies; input to 2.6. — [Gen AI Hub](https://www.sap.com/products/artificial-intelligence/generative-ai-hub.html)
- [ ] **8.3 Cross-Agent Intent Conflict Resolution** `CORRECTED` — When 2+ agents act on the same entity, define a conflict-resolution priority hierarchy + escalation path; test in the regression env (7.6). — [Agent Builder](https://www.sap.com/products/financial-management/joule-studio-agent-builder.html)
- [ ] **8.4 UI Layer Performance** — Response-time budget from input to first visible response; SLAs at p50/p95/p99 validated end-to-end under peak load. — [Joule Studio](https://www.sap.com/products/artificial-intelligence/joule-studio.html)
- [ ] **8.5 Orchestration / Reasoning Layer Performance** `CORRECTED` — Time + token cost of orchestration/reasoning, excluding UI/backend; per-hop budget; bound runaway loops. Impacts 4.8. — [Orchestration](https://help.sap.com/docs/ai-launchpad/sap-ai-launchpad/orchestration-4953dc10c6dd48fe85f37b41109dffe2?locale=en-US)
- [ ] **8.6 Backend / Tool Call Performance** — Measure each tool call independently (often dominant); each tool has a timeout + tested fallback; logged by 6.8. — [AI Core API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/AICoreAI_CORE_API)

### L0-9 · Knowledge & Data Grounding Strategy
*When and how agents use SAP KG, custom KG, and document RAG — at runtime.*

- [ ] **9.1 SAP KG as Runtime Grounding Source** — Authoritative structured source; document entity types queried, latency, staleness threshold (9.4), unavailability handling. — [Knowledge Graph](https://www.sap.com/products/artificial-intelligence/knowledge-graph.html)
- [ ] **9.2 Custom KG Design & Governance** — Custom extension following SAP conventions with governance owner, ingestion cadence, versioning, data-architecture review before prod. — [Knowledge Graph](https://www.sap.com/products/artificial-intelligence/knowledge-graph.html)
- [ ] **9.3 KG vs RAG Decision Framework** — Documented per query category: KG for structured lookups, RAG for unstructured/dynamic, structured injection (9.5) for small deterministic sets. — [Knowledge Graph](https://www.sap.com/products/artificial-intelligence/knowledge-graph.html)
- [ ] **9.4 KG Freshness & Staleness Management** — Max data age per entity type + staleness detection with alerts; critical for write-back workflows. — [Knowledge Graph](https://www.sap.com/products/artificial-intelligence/knowledge-graph.html)
- [ ] **9.5 Context Engineering — Structured Context Injection** — Inject small deterministic sets directly into the prompt (lower latency, higher determinism); budget the context window to prevent overflow. — [Prompt Engineering](https://learning.sap.com/courses/solve-your-business-problems-using-prompts-and-llms-in-sap-generative-ai-hub/implementing-prompt-engineering-techniques)

### L0-10 · Dependency & Change Resilience
*Adapt to architectural change via runtime KG; maintain quality via drift detection.*

- [ ] **10.1 Runtime KG Dependency Resolution** — Resolve dependencies via the KG at runtime (not hard-coded); tested fallback so a KG outage isn't an agent outage. — [Knowledge Graph](https://www.sap.com/products/artificial-intelligence/knowledge-graph.html)
- [ ] **10.2 Agent Tool Dependency Map** — Live map of every tool/API/source/endpoint with version pinning, SLA, change-notification contacts; input to impact analysis; used by 7.6. — [AI Core API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/AICoreAI_CORE_API)
- [ ] **10.3 Model Drift Detection** — Continuously monitor the LLM vs baseline; primary trigger for 2.5; automated alert with quantitative comparison; threshold + escalation before go-live.
- [ ] **10.4 Data Drift Detection** — Monitor statistical properties through the RAG pipeline; undetected drift silently reduces faithfulness/relevance; alerts trigger RAG Triad re-evaluation. — [Doc Grounding API](https://ekg.cloud.sap/SAP/BAH/SAPIH/RAP/GroundingDOCUMENT_GROUNDING_API)
- [ ] **10.5 Architecture Drift Detection** — Detect unauthorised/unplanned changes (endpoint substitution, tool versions, KG schema, infra config); closes the loop with 10.2; investigate + accept or remediate within SLA. — [Reference Architecture](https://architecture.learning.sap.com/docs/ref-arch/39eb58)
- [ ] **10.6 Continuous Accuracy Testing Pipeline** `CORRECTED` — Automated pipeline evaluating output quality vs baseline on a golden dataset (daily/per deploy); a threshold-crossing regression is a production incident. — [Evaluations](https://help.sap.com/docs/sap-ai-core/generative-ai/evaluations?locale=en-US)
- [ ] **10.7 Post Go-Live Operational Governance** `NEW` — SLA framework (uptime/latency/accuracy) with breach procedures; incident response + escalation; tiered support; end-user feedback loop routing back through L0-3/L0-2; decommissioning governance. — [ESCE](https://ekg.cloud.sap/SAP/LX/TM/TRM/ESCE5CF3FCDB46F61EE7A8859EFC21919645)
- [ ] **10.8 Agent Incident Definition & Support Tier Ownership** `NEW` — Incident taxonomy including **accuracy degradation as a first-class incident type** independent of component health; assign L1/L2/L3 ownership, escalation criteria, response SLA, handoff protocol; agreed before go-live. — [ESCE](https://ekg.cloud.sap/SAP/LX/TM/TRM/ESCE5CF3FCDB46F61EE7A8859EFC21919645)

### Cross-Pillar Feedback Loops
*Three continuous loops that turn quality gates into quality pipelines.*

- **Loop 1 — Model Quality (`L0-2 ↔ 10.3`):** drift alerts (10.3) trigger an automatic re-evaluation run (2.5), assessed against the Frontier Model Justification Gate (2.6).
- **Loop 2 — Data & Grounding Quality (`L0-3 ↔ 10.4`):** data drift alerts (10.4) trigger re-evaluation of the RAG Triad (3.3–3.5) and review of grounding setup (3.1).
- **Loop 3 — Architecture Resilience (`L0-9.1 ↔ 10.1`):** architecture drift (10.5) and KG staleness (9.4) trigger re-validation of KG-dependent behaviour against the regression env (7.6).

---

## 11 · Final output — write `implementation-plan.md`

*Claude: from the intake and recommendation, **write a distinct `implementation-plan.md`** into the new agent sub-folder (not just inline chat). It is the developer's actionable, self-contained plan. Use the template below.*

The plan **must** include, in addition to the approach and steps:
- **Demo UI (HTML)** — a standalone mock-mode showcase page (template §7.8), runnable offline under `IBD_TESTING=1`.
- **Mock data** — deterministic offline fixtures (template §7.7) the mock tool layer returns under `IBD_TESTING=1`.
- **Cleanup task** — an explicit final task to remove unused code and unused templates/scaffolding (see §6.7).

```
# Implementation Plan — {{agent_name}}

## Scope
- Build scope: {{full custom agent | Joule skill | plugin/tool | multi-agent | embedded feature}}

## Selected approach
- Agent type: {{reactive | chain-of-thought | ReAct | multi-agent}}
- Path: {{low-code (Joule Studio) | pro-code (scaffold)}}
- Platform / runtime: {{Joule Studio + AI Core; CF | Kyma | none (skill/plugin)}}

## Selected assets
- Cookbook: {{CoE | KG}}
- Accelerator / starter: {{Agent-GoldenPath-Kit | specific template}}
- Grounding strategy: {{OData | RAG | KG | mix}}

## Prerequisites
- {{BTP entitlements, IAS/JouleAdmin, API policy, data residency}}

## Ordered implementation steps
*(Omit steps that don't apply to the scope — e.g. a Joule skill skips standalone scaffold/deploy.)*
1. Prepare — {{…}}  (gate: L0-1, L0-4/5)
2. Configure — {{…}}  (gate: L0-2, L0-6)
3. Build (mock-first, IBD_TESTING=1) — {{…}}  (gate: L0-6, L0-8)
4. Connect knowledge & actions — {{…}}  (gate: L0-3/9, L0-6.6/6.7)
5. Test (IBD_TESTING=1 pytest, offline) — {{…}}  (gate: L0-5, L0-7.1/7.6)
6. Deploy & register — {{…}}  (gate: L0-7, L0-6.8, L0-10)
7. Cleanup — remove unused code + unused templates/scaffolding — {{…}}  (gate: L0-6)

## Demo assets (mock-mode, IBD_TESTING=1)
- Mock data fixtures: {{files + what they cover — template §7.7}}
- Demo UI (HTML): {{standalone page, offline, "DEMO — mock data" labelled — template §7.8}}

## Cleanup checklist
- [ ] Unused scaffold code / dead decorators removed
- [ ] Unused accelerator/cookbook templates removed
- [ ] `[illustrative]` snippets removed or wired in
- [ ] No secrets in code/markdown; `.env` gitignored
- [ ] Mock data + demo UI retained (gated by `IBD_TESTING`)

## Applicable checklist subset
- {{list only the pillars that apply to this scope, per the §10 scope table}}

## Dependencies and owners
- {{dependency → owner}}

## Next action
- {{the single next concrete step for the developer}}
```

---

## 12 · Agent Outcome Report — write `agent-outcome-report.md`

*Claude: after the build is complete, **write `agent-outcome-report.md`** into the new agent sub-folder. This is the definitive hand-off document — governance record, demo/mock status, and go/no-go verdict. Use the template below.*

> **Purpose:** anyone picking up this agent — a reviewer, a delivery lead, a customer team — can open `agent-outcome-report.md` and know exactly what was built, what governance controls were satisfied, what gaps remain, and whether the agent is production-ready.

```markdown
# Agent Outcome Report — {{agent_name}}
Generated: {{date}}
Build scope: {{full custom agent | Joule skill | plugin/tool | multi-agent | embedded feature}}

---

## 1. What was built
- **Agent name:** {{agent_name}}
- **Intent:** {{one-line statement of what the agent does}}
- **Agent type:** {{reactive | chain-of-thought | ReAct | multi-agent}}
- **Build path:** {{low-code (Joule Studio) | pro-code (scaffold)}}
- **Platform / runtime:** {{AI Core; CF | Kyma | Joule Studio only}}
- **Cookbook used:** {{CoE | KG | none}}
- **Grounding strategy:** {{OData | RAG | KG | mix | none}}

---

## 2. Deliverables produced
| Deliverable | Status | Notes |
|---|---|---|
| Agent code (scaffolded) | {{✅ / ❌}} | {{sub-folder path}} |
| `implementation-plan.md` | {{✅ / ❌}} | |
| Mock data (IBD_TESTING=1) | {{✅ / ❌}} | {{files}} |
| Demo UI (HTML, offline) | {{✅ / ❌}} | {{file}} |
| `.env` template | {{✅ / ❌}} | Secrets list provided to developer |
| Cleanup complete | {{✅ / ⚠️ / ❌}} | {{what remains if not complete}} |

---

## 3. L0-L10 Governance Checklist — full status

**Flag key:** ✅ Satisfied · ⚠️ Partial · ❌ Not satisfied · ⏭️ Skipped — N/A (scope)

### L0-1 · AI Feature & Agent Onboarding Governance
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 1.0 | Idea2Value | {{flag}} | |
| 1.1 | Feature Type Classification | {{flag}} | |
| 1.2 | Commercial Tier Determination | {{flag}} | |
| 1.3 | AI Golden Path | {{flag}} | |
| 1.4 | Document AI Commercialization Track | {{flag}} | |
| 1.5 | GDH APAC Architect Group Support | {{flag}} | |
| 1.6 | Onboarding Agent Templates | {{flag}} | |

### L0-2 · LLM Selection & Benchmarking
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 2.1 | Test Data Preparation & Submission | {{flag}} | |
| 2.2 | Automated Multi-Model Evaluation | {{flag}} | |
| 2.3 | Gen AI Evaluation Roadmap | {{flag}} | |
| 2.4 | Results via Helm Dashboard | {{flag}} | |
| 2.5 | Ongoing Model Version Re-evaluation | {{flag}} | |
| 2.6 | Frontier Model Justification Gate | {{flag}} | |
| 2.7 | Model Update & Retraining Governance | {{flag}} | |

### L0-3 · Document Grounding & RAG Quality Evaluation
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 3.1 | Document Grounding Setup | {{flag}} | |
| 3.2 | Vector Embedding & Retrieval Pipeline | {{flag}} | |
| 3.3 | RAG Triad — Context Relevance | {{flag}} | |
| 3.4 | RAG Triad — Faithfulness | {{flag}} | |
| 3.5 | RAG Triad — Answer Relevance | {{flag}} | |
| 3.6 | Prompt Engineering Governance | {{flag}} | |
| 3.7 | Automated Grounding Roadmap | {{flag}} | |
| 3.8 | Runtime Hallucination Guardrail Architecture | {{flag}} | |

### L0-4 · AI Commercialization & Metering
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 4.1 | LLM Calculator | {{flag}} | |
| 4.2 | BMP Expert Approval | {{flag}} | |
| 4.3 | AI Scenario Metering Integration | {{flag}} | |
| 4.4 | Feature Activation via CBC | {{flag}} | |
| 4.5 | Floor Price Impact Review | {{flag}} | |
| 4.6 | SAP Business AI Pricing Model | {{flag}} | |
| 4.7 | Customer Token Consumption Forecast | {{flag}} | |
| 4.8 | Cost Per Transaction Baseline | {{flag}} | |

### L0-5 · Responsible AI & Safety Validation
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 5.1 | Safety Dashboard Pre-Release Evaluation | {{flag}} | |
| 5.2 | AI Bias & Fairness Assessment | {{flag}} | |
| 5.3 | Adversarial & Red Team Testing | {{flag}} | |
| 5.4 | AI Ethics & Governance Alignment | {{flag}} | |
| 5.5 | GDPR / EU AI Act Compliance | {{flag}} | |
| 5.6 | Indirect Prompt Injection via Business Data | {{flag}} | |
| 5.7 | IP Rights & Data Ownership Governance | {{flag}} | |

### L0-6 · Agent Development & Deployment Standards
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 6.1 | Agent Builder in Joule Studio | {{flag}} | |
| 6.2 | Skill Builder in Joule Studio | {{flag}} | |
| 6.3 | Generative AI Hub (J17) | {{flag}} | |
| 6.4 | Skills Governance Agent (J1426) | {{flag}} | |
| 6.5 | SAP AI Core & AI Launchpad | {{flag}} | |
| 6.6 | Agent Tool Access Governance | {{flag}} | |
| 6.7 | Human-in-the-Loop Approval Governance | {{flag}} | |
| 6.8 | Agent Execution Observability & Tracing | {{flag}} | |

### L0-7 · End-to-End Release Validation & Go-Live
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 7.1 | AI-Driven Exploratory Testing (AET) | {{flag}} | |
| 7.2 | Integration Validation | {{flag}} | |
| 7.3 | CBC Toggle Activation | {{flag}} | |
| 7.4 | Cross-Functional Sign-Off | {{flag}} | |
| 7.5 | Official Release (AI112) | {{flag}} | |
| 7.6 | Agent Regression Testing Environment | {{flag}} | |

### L0-8 · Agent Design Classification & Performance Engineering
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 8.1 | Trigger Type Classification | {{flag}} | |
| 8.2 | Agentic Reasoning Classification | {{flag}} | |
| 8.3 | Cross-Agent Intent Conflict Resolution | {{flag}} | |
| 8.4 | UI Layer Performance | {{flag}} | |
| 8.5 | Orchestration / Reasoning Layer Performance | {{flag}} | |
| 8.6 | Backend / Tool Call Performance | {{flag}} | |

### L0-9 · Knowledge & Data Grounding Strategy
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 9.1 | SAP KG as Runtime Grounding Source | {{flag}} | |
| 9.2 | Custom KG Design & Governance | {{flag}} | |
| 9.3 | KG vs RAG Decision Framework | {{flag}} | |
| 9.4 | KG Freshness & Staleness Management | {{flag}} | |
| 9.5 | Context Engineering — Structured Context Injection | {{flag}} | |

### L0-10 · Dependency & Change Resilience
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 10.1 | Runtime KG Dependency Resolution | {{flag}} | |
| 10.2 | Agent Tool Dependency Map | {{flag}} | |
| 10.3 | Model Drift Detection | {{flag}} | |
| 10.4 | Data Drift Detection | {{flag}} | |
| 10.5 | Architecture Drift Detection | {{flag}} | |
| 10.6 | Continuous Accuracy Testing Pipeline | {{flag}} | |
| 10.7 | Post Go-Live Operational Governance | {{flag}} | |
| 10.8 | Agent Incident Definition & Support Tier Ownership | {{flag}} | |

---

## 4. Flagged items — must resolve before production

*Claude: list every ❌ and ⚠️ item here with a clear remediation action. If there are none, write "None — all applicable controls satisfied."*

| Control | Flag | Issue | Remediation required |
|---|---|---|---|
| {{e.g. 5.1 Safety Dashboard}} | ❌ | {{reason not satisfied}} | {{what must be done}} |
| {{e.g. 3.4 RAG Faithfulness}} | ⚠️ | {{what is partial}} | {{what remains}} |

---

## 5. Mock mode & demo status
| Item | Status | Notes |
|---|---|---|
| `IBD_TESTING=1 pytest` passes offline | {{✅ / ❌}} | |
| Coverage ≥ 70% | {{✅ / ❌}} | |
| Mock data fixtures present | {{✅ / ❌}} | |
| Demo UI (HTML) runs offline | {{✅ / ❌}} | |
| Demo clearly labelled "DEMO — mock data" | {{✅ / ❌}} | |

---

## 6. Cleanup status
| Item | Status |
|---|---|
| Unused scaffold code removed | {{✅ / ❌}} |
| Unused accelerator/cookbook templates removed | {{✅ / ❌}} |
| `[illustrative]` snippets removed or wired in | {{✅ / ❌}} |
| No secrets in code/markdown; `.env` gitignored | {{✅ / ❌}} |

---

## 7. Summary scorecard
| Category | ✅ Satisfied | ⚠️ Partial | ❌ Not satisfied | ⏭️ Skipped N/A |
|---|---|---|---|---|
| L0-1 Onboarding | | | | |
| L0-2 LLM | | | | |
| L0-3 Grounding | | | | |
| L0-4 Commercial | | | | |
| L0-5 Responsible AI | | | | |
| L0-6 Dev Standards | | | | |
| L0-7 Release | | | | |
| L0-8 Design/Perf | | | | |
| L0-9 KG/Grounding | | | | |
| L0-10 Resilience | | | | |
| **Total** | | | | |

---

## 8. Go / No-Go verdict

> **{{GO ✅ | NO-GO ❌ | CONDITIONAL GO ⚠️}}**
>
> {{One paragraph: overall assessment. If NO-GO or CONDITIONAL GO, list the specific ❌ items that must be resolved and by whom before production.}}

---

## 9. Next steps
1. {{first action, owner, deadline}}
2. {{second action}}
```

---

## 13 · Complete testing plan

*How to validate the toolkit end-to-end before using it for a real engagement.*

### 13.1 Prerequisites
- Claude Code installed, repo cloned: `git clone https://github.tools.sap/I039198/Agent-PathToProd.git`
- Python 3.9+ for local mock runs.

### 13.2 Test 1 — Auto-fire (no explicit command)
1. Open the repo folder in Claude Code.
2. Say nothing — just open it.
3. **Expected:** Claude reads `CLAUDE.md` → `developer-toolkit.md` → asks for scope or reads `intent.md` automatically.
4. **Pass:** Claude does not wait for a "start" command.

### 13.3 Test 2 — Minimal intent (one line)
1. Create `intent.md` with exactly: `Build an agent that answers S/4HANA inventory questions.`
2. Open in Claude Code.
3. **Expected:** Claude reads the intent, assumes full custom agent, runs intake with ≤4 focused questions, produces a recommendation, walks the build, flags all L0-L10 controls, writes `implementation-plan.md` and `agent-outcome-report.md`.
4. **Pass:** both files exist in the new sub-folder; every checklist control has a flag; no silent omissions.

### 13.4 Test 3 — Idea2Value-rich intent
1. Run a use case through `https://idea-agent.cfapps.us10-001.hana.ondemand.com`
2. Copy the output into `intent.md`.
3. Open in Claude Code.
4. **Expected:** Claude asks fewer questions (most are already answered); recommendation is more specific; outcome report references the Idea2Value document at `1.0`.
5. **Pass:** 1.0 (Idea2Value) is flagged `✅` in the outcome report.

### 13.5 Test 4 — Non-default scope (Joule skill)
1. Create `intent.md`: `Add a skill to Joule that summarises open purchase orders.`
2. **Expected:** Claude identifies this as a **Joule skill**, not a full agent; skips CF/Kyma deploy, skips L0-7 go-live; applies the lighter checklist subset; still flags each control with ⏭️ where N/A.
3. **Pass:** no standalone scaffold created; L0-7, L0-10 controls marked `⏭️ Skipped — N/A`; outcome report reflects lighter scope.

### 13.6 Test 5 — Mock mode & demo UI
1. Use any intent.
2. After the build, run: `IBD_TESTING=1 pytest` in the new sub-folder.
3. Open the generated `demo/index.html` in a browser (no server needed).
4. **Expected:** all tests pass offline; demo UI shows a response; page is labelled "DEMO — mock data".
5. **Pass:** zero live SAP calls; no credentials needed.

### 13.7 Test 6 — Checklist flags & outcome report
1. Use any intent.
2. Open `agent-outcome-report.md` after the build.
3. **Expected:**
   - Every L0-L10 control row is present (70 rows total).
   - No row has a blank status.
   - Any ❌/⚠️ item appears in Section 4 (Flagged items) with a remediation.
   - Section 7 scorecard totals add up.
   - Section 8 gives a clear GO/NO-GO verdict.
4. **Pass:** above conditions all met.

### 13.8 Test 7 — Cleanup
1. After the build, review the sub-folder.
2. **Expected:** no `[illustrative]` comments remain; no unused decorator stubs; no unused template files; `.env` gitignored; mock data + demo UI retained.
3. **Pass:** cleanup checklist in `agent-outcome-report.md` Section 6 is all `✅`.

---

*Part of the Agent-GoldenPath-Kit. Build engine: the CoE / KG cookbooks. Hardening: the Agent Blueprint. Governance: the 10-pillar Agent Checklist. Onboarding frame: the GDH AI Factory workflow.*
