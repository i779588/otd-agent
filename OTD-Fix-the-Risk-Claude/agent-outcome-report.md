# Agent Outcome Report — OTD-Fix-the-Risk (Claude-backed, Joule-frontable)
Generated: 2026-09-28
Build scope: full custom agent (pro-code A2A), ported from a Joule / SAP AI Core build

---

## 1. What was built
- **Agent name:** otd-fix-the-risk-agent
- **Intent:** A zero-write, advisory-only On-Time-Delivery risk copilot that detects at-risk sales orders, classifies the root cause (material shortage / capacity / warehouse / transit), scores the risk, and produces an advisory dossier + executive summary from read-only S/4HANA data.
- **Agent type:** ReAct (LangGraph `create_agent`, tool-calling loop over read-only SAP tools).
- **Build path:** pro-code (scaffold) — existing SAP CoE A2A scaffold, ported.
- **Platform / runtime:** standalone A2A server (Starlette/uvicorn). Two LLM routing modes available via `OTD_LLM_ROUTE`: **`direct`** (Anthropic API via LiteLLM — governance deviation, see §4) and **`aicore`** (SAP Generative AI Hub → AI Core → Bedrock — Golden Path, compliant). Joule fronts the agent by discovering its agent card (gated registration).
- **Cookbook used:** CoE (pro-code A2A agent).
- **Grounding strategy:** OData — 5 read-only S/4HANA services via declarative MCP translation specs. Mock now (IBD_TESTING=1); live read-only OData→MCP bridge scaffolded.

---

## 2. Deliverables produced
| Deliverable | Status | Notes |
|---|---|---|
| Agent code (scaffolded) | ✅ | `OTD-Fix-the-Risk-Claude/` — copy of the original with SAP anchors replaced; `app/sap_cloud_sdk/` shim, `app/bridge/` read-only OData bridge + token exchange |
| `implementation-plan.md` | ✅ | Present at sub-folder root |
| Mock data (IBD_TESTING=1) | ✅ | `assets/otd-fix-the-risk-agent/mcp-mock.json` — 5 servers, 19 read-only tools, 5-order scenario (4 root-cause categories + healthy control) |
| Demo UI (HTML, offline) | ✅ | `demo/index.html` + stdlib proxy `demo/serve_demo.py` |
| `.env` template | ✅ | `.env.example` — secrets list provided to developer; no secret values committed |
| Cleanup complete | ✅ | No dead scaffold introduced; shim is minimal and load-bearing; mock + demo retained behind `IBD_TESTING` |

---

## 3. L0-L10 Governance Checklist — full status

**Flag key:** ✅ Satisfied · ⚠️ Partial · ❌ Not satisfied · ⏭️ Skipped — N/A (scope)

> **Scope note:** this is a **hackathon port**, not a productised release. Grounding is **OData-only** (no RAG, no Knowledge Graph), so L0-3 (RAG) and most of L0-9 (KG) are ⏭️ N/A. Commercialization (L0-4) and formal go-live (L0-7) are largely ❌/⏭️ because there is no release event. The defining architectural decision — **LLM routing** — is env-switchable: `OTD_LLM_ROUTE=aicore` (SAP Gen AI Hub, Golden Path) resolves the AI-Core-bypass flags (1.3, 6.3, 6.5, 4.3, 5.1); `OTD_LLM_ROUTE=direct` (Anthropic API direct, default) leaves them as ❌/⚠️. Statuses below reflect the **`direct` (default) route** — annotations note how each control changes when `aicore` is used.

### L0-1 · AI Feature & Agent Onboarding Governance
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 1.0 | Idea2Value | ⏭️ | No CXO value case run; hackathon port of an existing agent, not a new idea intake |
| 1.1 | Feature Type Classification | ✅ | Classified: **agentic** (ReAct, tool-using). Recorded in `implementation-plan.md` §Selected approach |
| 1.2 | Commercial Tier Determination | ⏭️ | Not monetised; no tier assigned |
| 1.3 | AI Golden Path | ⚠️→✅ | **`direct` route:** documented deviation — LLM served off AI Core (Anthropic API direct). Still requires exception request + ATQ AI/Agentic review + API Policy v.4.2026a self-check before any non-hackathon use (see §4). **`aicore` route (`OTD_LLM_ROUTE=aicore`):** ✅ — routes through SAP Gen AI Hub (deployment `d009d0ca6a44ae29`), meeting the Golden Path. Exception and extra review no longer required for this control |
| 1.4 | Document AI Commercialization Track | ⏭️ | No document-AI processing in scope |
| 1.5 | GDH APAC Architect Group Support | ❌ | Central architect group not yet engaged; required for the AI-Core-bypass exception |
| 1.6 | Onboarding Agent Templates | ✅ | Started from the CoE A2A scaffold (the original Joule build) |

### L0-2 · LLM Selection & Benchmarking
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 2.1 | Test Data Preparation & Submission | ⚠️ | Deterministic mock fixtures exercise all 4 root-cause categories + a healthy control, but no curated adversarial/multi-language eval set submitted |
| 2.2 | Automated Multi-Model Evaluation | ❌ | No multi-model benchmark run; model choice (Claude Sonnet 4.5 / Haiku 4.5) carried over from the original SAP build |
| 2.3 | Gen AI Evaluation Roadmap | ⏭️ | Gen AI Hub roadmap gates N/A off-platform |
| 2.4 | Results via Helm Dashboard | ⏭️ | Helm/AI Launchpad not used (off AI Core) |
| 2.5 | Ongoing Model Version Re-evaluation | ❌ | No re-eval process; model ids are env-overridable (`OTD_MODEL`, `OTD_SUMMARIZATION_MODEL`) but no regression gate wired |
| 2.6 | Frontier Model Justification Gate | ❌ | No documented justification for the frontier model per decision step |
| 2.7 | Model Update & Retraining Governance | ⏭️ | No fine-tuning / retraining; base models via API |

### L0-3 · Document Grounding & RAG Quality Evaluation
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 3.1 | Document Grounding Setup | ⏭️ | No RAG / document grounding — OData-only grounding |
| 3.2 | Vector Embedding & Retrieval Pipeline | ⏭️ | N/A — no vector store |
| 3.3 | RAG Triad — Context Relevance | ⏭️ | N/A — no RAG |
| 3.4 | RAG Triad — Faithfulness | ⏭️ | N/A — no RAG |
| 3.5 | RAG Triad — Answer Relevance | ⏭️ | N/A — no RAG |
| 3.6 | Prompt Engineering Governance | ⚠️ | Prompts/skills are version-controlled in the repo, but no formal change-approval workflow. Prompt-injection detector scans tool results |
| 3.7 | Automated Grounding Roadmap | ⏭️ | N/A — no document grounding |
| 3.8 | Runtime Hallucination Guardrail Architecture | ⚠️ | Grounding is deterministic read-only OData (low fabrication surface); financial disclaimer + advisory-only framing enforced; no confidence-threshold auto-rejection layer |

### L0-4 · AI Commercialization & Metering
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 4.1 | LLM Calculator | ⏭️ | Not monetised |
| 4.2 | BMP Expert Approval | ⏭️ | No commercial structure |
| 4.3 | AI Scenario Metering Integration | ❌→✅ | **`direct` route:** AI-Core-bypass — SAP scenario metering does not capture Anthropic-direct LLM calls; billing accrues on the Anthropic account. **`aicore` route:** ✅ — LLM calls flow through AI Core; SAP metering captures them automatically |
| 4.4 | Feature Activation via CBC | ⏭️ | No CBC / phased rollout |
| 4.5 | Floor Price Impact Review | ⏭️ | Not monetised |
| 4.6 | SAP Business AI Pricing Model | ⏭️ | Off-platform; not aligned to AI-units model |
| 4.7 | Customer Token Consumption Forecast | ❌ | No per-interaction token forecast produced |
| 4.8 | Cost Per Transaction Baseline | ❌ | No cost-per-invocation instrumentation |

### L0-5 · Responsible AI & Safety Validation
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 5.1 | Safety Dashboard Pre-Release Evaluation | ❌→✅ | **`direct` route:** the internal Safety Dashboard is an AI Core / Gen AI Hub gate — not available off-platform; hard gate before any production release. **`aicore` route:** ✅ — LLM calls flow through AI Core so the Safety Dashboard pre-release evaluation can be run. Still must be executed before go-live |
| 5.2 | AI Bias & Fairness Assessment | ⚠️ | Low demographic-bias surface (operational logistics data, no personal decisions), but no formal bias framework run |
| 5.3 | Adversarial & Red Team Testing | ⚠️ | Prompt-injection detector (`prompt_injection_detector.py`) scans tool results with block/log modes + optional LLM detector; unit-tested. No structured red-team campaign documented |
| 5.4 | AI Ethics & Governance Alignment | ✅ | Advisory-only (zero-write), human-in-the-loop by construction (a planner reviews + executes), AI nature disclosed in UI + agent card, financial disclaimer present |
| 5.5 | GDPR / EU AI Act Compliance | ⚠️ | No personal-data processing in the OTD scenario; risk classification not formally documented |
| 5.6 | Indirect Prompt Injection via Business Data | ✅ | Tool results (business data) are scanned by the injection detector before reaching the model; block mode available |
| 5.7 | IP Rights & Data Ownership Governance | ❌→⚠️ | **`direct` route:** Anthropic data-usage / ownership / tenant-isolation terms not reconciled against SAP customer terms. **`aicore` route:** ⚠️ — Claude is served by SAP via AWS Bedrock; SAP's AI Core terms govern; Bedrock non-training commitments apply. Still requires legal review of output ownership and tenant isolation before customer data flows |

### L0-6 · Agent Development & Deployment Standards
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 6.1 | Agent Builder in Joule Studio | ⚠️ | Built **outside** Joule Studio (pro-code A2A) → per 6.1 this needs an exception + security review. Joule fronts it via agent card only |
| 6.2 | Skill Builder in Joule Studio | ⏭️ | Skills are pro-code (`app/skills/**`), not Joule Studio skills |
| 6.3 | Generative AI Hub (J17) | ❌→✅ | **`direct` route:** LLM calls bypass Gen AI Hub → no central access control / audit / metering. **`aicore` route:** ✅ — LLM calls route through Gen AI Hub deployment `d009d0ca6a44ae29`; central access control, audit log, and cost metering all apply |
| 6.4 | Skills Governance Agent (J2259) | ⏭️ | Not registered in the SAP skills catalogue (off-platform build). *Note: template references J1426; superseded by **J2259** per §10 of the toolkit* |
| 6.5 | SAP AI Core & AI Launchpad | ❌→✅ | **`direct` route:** AI Core is not the serving runtime; requires an approved exception. **`aicore` route:** ✅ — Claude inference served by AI Core (Bedrock backend) via Gen AI Hub; AI Launchpad metering and monitoring apply |
| 6.6 | Agent Tool Access Governance | ✅ | Least privilege by construction: **19 read-only tools only** (read/readByKey/metadata); bridge raises `PermissionError` on any non-read op; tool identity taken from request context, never tool args. **Live identity default = `basic` (fixed technical/communication user)** — every call acts as one identity, so per-user RBAC pass-through is not enforced on this path (deviation, see §4); the code also supports `passthrough` / `xsuaa` / `destination` for true principal propagation |
| 6.7 | Human-in-the-Loop Approval Governance | ✅ | Zero-write / advisory-only: the agent never mutates SAP; all recommendations require manual planner review + execution. No autonomous write path exists |
| 6.8 | Agent Execution Observability & Tracing | ⚠️ | Structured logging (no secrets/PII) + circuit breaker present; no step-level distributed tracing surface wired for production |

### L0-7 · End-to-End Release Validation & Go-Live
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 7.1 | AI-Driven Exploratory Testing (AET) | ⚠️ | AET not GA. Interim regression suite present: **119 tests pass offline** (IBD_TESTING=1), golden-path coverage of all scenario categories |
| 7.2 | Integration Validation | ❌ | No live tenant integration test — mock mode only. Live OData bridge scaffolded but unverified against a real S/4 system (gated) |
| 7.3 | CBC Toggle Activation | ⏭️ | No CBC in scope |
| 7.4 | Cross-Functional Sign-Off | ❌ | No release sign-off (hackathon; not going live) |
| 7.5 | Official Release (AI112) | ⏭️ | No release event |
| 7.6 | Agent Regression Testing Environment | ⚠️ | Versioned offline regression suite exists; no dedicated production-parity non-prod environment |

### L0-8 · Agent Design Classification & Performance Engineering
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 8.1 | Trigger Type Classification | ✅ | user-initiated (A2A `message/send` from Joule / demo UI). Documented |
| 8.2 | Agentic Reasoning Classification | ✅ | ReAct (tool-calling loop). Documented in `implementation-plan.md` |
| 8.3 | Cross-Agent Intent Conflict Resolution | ⏭️ | Single-agent; no multi-agent contention on shared entities |
| 8.4 | UI Layer Performance | ⚠️ | Demo UI functional; no p50/p95/p99 SLA measured under load |
| 8.5 | Orchestration / Reasoning Layer Performance | ⚠️ | Circuit breaker bounds runaway loops; summarization controls token growth; no formal per-hop budget documented |
| 8.6 | Backend / Tool Call Performance | ⚠️ | `OTD_HTTP_TIMEOUT_SECONDS` per tool call + retry wrapper; mock path deterministic; live-path latency unmeasured |

### L0-9 · Knowledge & Data Grounding Strategy
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 9.1 | SAP KG as Runtime Grounding Source | ⏭️ | Grounding is OData, not Knowledge Graph |
| 9.2 | Custom KG Design & Governance | ⏭️ | No custom KG |
| 9.3 | KG vs RAG Decision Framework | ✅ | Decision documented: structured OData lookups (deterministic), neither KG nor RAG required for this scenario |
| 9.4 | KG Freshness & Staleness Management | ⏭️ | No KG. Live OData reads are always current-of-query |
| 9.5 | Context Engineering — Structured Context Injection | ✅ | Read-only OData results injected as structured tool outputs; summarization step budgets the context window |

### L0-10 · Dependency & Change Resilience
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 10.1 | Runtime KG Dependency Resolution | ⏭️ | No KG dependency to resolve |
| 10.2 | Agent Tool Dependency Map | ⚠️ | Tools + service base URLs declared via translation specs + `OTD_SERVICE_BASE_URLS`; dependencies pinned in `requirements.txt`; no formal SLA / change-notification contact map |
| 10.3 | Model Drift Detection | ❌ | No drift monitoring vs a baseline |
| 10.4 | Data Drift Detection | ⏭️ | N/A — no RAG pipeline |
| 10.5 | Architecture Drift Detection | ❌ | No automated endpoint/tool/version drift detection |
| 10.6 | Continuous Accuracy Testing Pipeline | ⚠️ | Offline golden-set regression suite exists (run on change), but not wired into a daily/per-deploy automated pipeline |
| 10.7 | Post Go-Live Operational Governance | ❌ | No SLA framework / incident response / decommissioning governance (not going live) |
| 10.8 | Agent Incident Definition & Support Tier Ownership | ❌ | No incident taxonomy or L1/L2/L3 ownership defined |

---

## 4. Flagged items — must resolve before production

> **AI Core / Golden Path deviation:** the six rows marked **✅ with `aicore`** below are resolved simply by setting `OTD_LLM_ROUTE=aicore` + supplying AI Core credentials (see `.env.example` and `DEPLOY.md`). The remaining items are independent of the LLM route.

| Control | Flag (`direct`) | Flag (`aicore`) | Issue | Remediation |
|---|---|---|---|---|
| 1.3 AI Golden Path | ⚠️ | ✅ | **`direct`:** LLM served off AI Core (Anthropic API direct) — undocumented deviations are a release blocker | **`direct`:** file a Golden Path exception request + ATQ AI/Agentic review + API Policy v.4.2026a self-check. **`aicore`:** resolved — routes through Gen AI Hub deployment `d009d0ca6a44ae29` |
| 1.5 GDH APAC Architect Support | ❌ | ⚠️ | Central architect group not engaged | Engage GDH APAC Data & AI Architect Group for design review. Less urgent on the `aicore` path but still recommended |
| 6.3 Gen AI Hub (J17) | ❌ | ✅ | **`direct`:** LLM calls bypass Gen AI Hub → no central access control / audit / metering | **`direct`:** route through Gen AI Hub or obtain approved exception. **`aicore`:** resolved |
| 6.5 SAP AI Core & AI Launchpad | ❌ | ✅ | **`direct`:** AI Core not the serving runtime | **`direct`:** approved exception (with 6.3). **`aicore`:** resolved |
| 4.3 AI Scenario Metering | ❌ | ✅ | **`direct`:** off-platform LLM calls not captured by SAP metering | **`direct`:** instrument equivalent metering, or switch to `aicore`. **`aicore`:** resolved — AI Core metering captures calls automatically |
| 5.1 Safety Dashboard | ❌ | ✅ | **`direct`:** Safety Dashboard pre-release eval unavailable off-platform | **`direct`:** hard gate — requires AI Core path or approved equivalent. **`aicore`:** ✅ gate available — still **must be run** before go-live |
| 5.7 IP / Data Ownership | ❌ | ⚠️ | **`direct`:** Anthropic-direct terms not reconciled with SAP customer terms. **`aicore`:** SAP/Bedrock non-training terms apply but still need legal sign-off | Legal review of output ownership and tenant isolation before any customer data flows (both routes) |
| 2.2 / 2.6 Model benchmarking & justification | ❌ | ❌ | No multi-model eval or frontier-model justification | Run a benchmarking eval + document the frontier-model justification per decision step |
| 7.2 Integration Validation | ❌ | ❌ | Live tenant path unverified (mock only) | Validate the read-only OData bridge + token exchange end-to-end against a real S/4 tenant (gated) before go-live |
| 6.6 Identity model (live default) | ⚠️ | ⚠️ | Live default `basic` mode authenticates as a **single fixed technical/communication user** — no per-user RBAC pass-through | For production, switch to `xsuaa` (jwt-bearer) or a correctly-configured `destination` (OAuth2SAMLBearerAssertion / PrincipalPropagation). Zero-write holds on all paths |
| Windows symlink test | ⚠️ | ⚠️ | `prebuilt_tests/…::test_symlink_to_external_file_is_rejected` fails at `os.symlink` setup (WinError 1314) | **Environment, not code** — Windows requires Developer Mode/admin for symlinks. Passes on Linux/macOS. Deselected in local run |
| 6.1 Agent built outside Joule Studio | ⚠️ | ⚠️ | Pro-code A2A agent needs exception + security review per 6.1 | Security review of the standalone A2A deployment |

*(Remaining ⚠️ items — 3.6, 3.8, 5.2, 5.3, 5.5, 6.8, 8.4–8.6, 10.2, 10.6 — are hardening tasks for productisation, not hackathon blockers.)*

---

## 5. Mock mode & demo status
| Item | Status | Notes |
|---|---|---|
| `IBD_TESTING=1 pytest` passes offline | ✅ | **119 passed, 1 deselected** (Windows symlink env test) in ~20s; `test_report.json` written |
| Coverage ≥ 70% | ✅ | **TOTAL 71%** (agent.py 92%, circuit_breaker 100%, prompt_injection_detector 94%, odata_mcp_server.py 76%; live-only token_exchange/converters lower as they need a tenant) |
| Mock data fixtures present | ✅ | `mcp-mock.json` — 5 servers, 19 read-only tools, 5-order scenario |
| Demo UI (HTML) runs offline | ✅ | `demo/index.html` + `demo/serve_demo.py` (stdlib proxy; `main.py` untouched) |
| Demo clearly labelled "DEMO — mock data" | ✅ | Amber banner in the UI states mock data / no SAP contacted |

---

## 6. Cleanup status
| Item | Status |
|---|---|
| Unused scaffold code removed | ✅ (none introduced; shim is minimal & load-bearing) |
| Unused accelerator/cookbook templates removed | ✅ (none copied in) |
| `[illustrative]` snippets removed or wired in | ✅ (mock cross-reference fields labelled illustrative) |
| No secrets in code/markdown; `.env` gitignored | ✅ (secrets only in `.env`; template provided) |

---

## 7. Summary scorecard
| Category | ✅ Satisfied | ⚠️ Partial | ❌ Not satisfied | ⏭️ Skipped N/A |
|---|---|---|---|---|
| L0-1 Onboarding | 2 | 1 | 1 | 3 |
| L0-2 LLM | 0 | 1 | 3 | 3 |
| L0-3 Grounding | 0 | 2 | 0 | 6 |
| L0-4 Commercial | 0 | 0 | 3 | 5 |
| L0-5 Responsible AI | 2 | 4 | 1 | 0 |
| L0-6 Dev Standards | 2 | 2 | 2 | 2 |
| L0-7 Release | 0 | 2 | 2 | 2 |
| L0-8 Design/Perf | 2 | 3 | 0 | 1 |
| L0-9 KG/Grounding | 2 | 0 | 0 | 3 |
| L0-10 Resilience | 0 | 2 | 4 | 2 |
| **Total** | **10** | **17** | **16** | **27** |

*(70 controls across the 10 pillars.)*

---

## 8. Go / No-Go verdict

> **CONDITIONAL GO ⚠️** — for hackathon / demo use only. **NO-GO for production** pending governance remediation.
>
> The agent is functionally complete and safe by construction for a demo: it is **zero-write and advisory-only** (19 read-only tools, `PermissionError` enforced on any non-read op, no SAP write path exists), runs fully offline on deterministic mock data (119 tests green, 71% coverage), discloses its AI nature, and carries the financial disclaimer. It is safe to demo and to front from Joule via its agent card.
>
> It is **not production-ready.** The defining decision — running LLM reasoning **off SAP AI Core on the Anthropic API directly** — is a **Golden Path deviation** that must be cleared before any production or customer use. Blocking items, by owner:
> - **GDH APAC Architect Group / Security:** Golden Path exception + ATQ review (1.3), architect engagement (1.5), security review of the off-Joule A2A build (6.1).
> - **Platform:** Gen AI Hub / AI Core exception or re-route (6.3, 6.5) and equivalent metering (4.3) if commercialised.
> - **Responsible AI:** Safety Dashboard pre-release evaluation (5.1).
> - **Legal:** Anthropic-direct data-ownership / tenant-isolation / non-training reconciliation before any customer data flows (5.7).
> - **Engineering:** multi-model benchmark + frontier justification (2.2/2.6); live-tenant integration validation of the read-only bridge (7.2).

---

## 9. Next steps
1. **Demo now (safe):** `IBD_TESTING=1 ANTHROPIC_API_KEY=… python app/main.py` from the agent folder, then `python demo/serve_demo.py` → http://localhost:8000. Fully offline, mock data, no SAP.
2. **Before any production use** — GDH APAC Architect Group + Security: raise the Golden Path exception for the AI-Core bypass (owns 1.3, 1.5, 6.1, 6.3, 6.5, 5.1).
3. **Legal:** reconcile Anthropic-direct terms with SAP customer data terms (5.7) before pointing the live bridge at real customer data.
4. **Engineering (gated):** validate the read-only OData bridge + token exchange against a real S/4 tenant (7.2), then follow `DEPLOY.md` for hosting + gated Joule agent-card registration.
