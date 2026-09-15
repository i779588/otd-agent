# Worked Example — what "done" looks like

> **Why this file exists.** The kit ships an `agent-outcome-report.md` *template* ([`developer-toolkit.md` §12](developer-toolkit.md)) but no filled-in example. This is one — a realistic, completed report for a simple agent, so you can see what a "good" hand-off looks like, including honest ⚠️/⏭️ flags. It is **illustrative** (not a live agent); use it as a model for your own report.
>
> Use case chosen because it needs no customer tenant: a field-service Q&A agent on the **public SAP API Business Hub sandbox** (the Service Technician Companion pattern).

---

# Agent Outcome Report — service-tech-companion
Generated: 2026-09-15
Build scope: full custom agent

---

## 1. What was built
- **Agent name:** service-tech-companion
- **Intent:** Answer field technicians' questions about equipment, maintenance orders, and notifications from S/4HANA plant maintenance, advisory-only.
- **Agent type:** ReAct (tool-using)
- **Build path:** pro-code (scaffold)
- **Platform / runtime:** AI Core; Cloud Foundry (`us10`)
- **Cookbook used:** CoE (default build route — no graph semantics needed)
- **Grounding strategy:** OData (live reads from the public API Business Hub sandbox)

---

## 2. Deliverables produced
| Deliverable | Status | Notes |
|---|---|---|
| Agent code (scaffolded) | ✅ | `./service-tech-companion/` |
| `implementation-plan.md` | ✅ | |
| Mock data (IBD_TESTING=1) | ✅ | `mcp-mock.json` — equipment, maint-orders, notifications |
| Demo UI (HTML, offline) | ✅ | `app/ui.html` served at `/ui` |
| `.env` template | ✅ | `.env.example` lists `SAP_API_HUB_KEY`, AI Core vars |
| Cleanup complete | ✅ | No stray creds; `.env` gitignored |

---

## 3. L0-L10 Governance Checklist — status (representative rows)

**Flag key:** ✅ Satisfied · ⚠️ Partial · ❌ Not satisfied · ⏭️ Skipped — N/A (scope)

### L0-1 · Onboarding
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 1.0 | Idea2Value | ⚠️ | One-line intent captured; full value case skipped for a sandbox demo. |
| 1.1 | Feature Type Classification | ✅ | Agentic (ReAct). |
| 1.5 | GDH APAC Architect Group Support | ⏭️ | Internal demo, not a customer engagement. |

### L0-2 · LLM Selection
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 2.1 | Test Data Preparation | ✅ | 12 golden Q&A pairs incl. 3 edge cases (empty result, 404, ambiguous equipment id). |
| 2.6 | Frontier Model Justification | ⏭️ | Default `sap/anthropic--claude-3.5-sonnet`; no frontier tier requested. |

### L0-5 · Responsible AI
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 5.1 | Safety Dashboard Pre-Release | ⚠️ | Not a customer release; guardrails validated locally, formal dashboard run deferred. |
| 5.3 | Adversarial & Red Team | ✅ | Prompt-injection + role-boundary tests pass; agent refuses write requests. |

### L0-6 · Development & Deployment
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 6.1 | Agent Builder in Joule Studio | ✅ | Built via scaffold; A2A card registered. |
| 6.2 | Skill Builder | ✅ | One capability bundle published; `a2aSkillId` matches `agent_card.py`. See `agent-skill-recipe.md`. |
| 6.8 | Execution Observability | ✅ | Structured logs: `correlation_id`, `tool_name`, `latency_ms`, tokens. |

### L0-7 · Release
| # | Control | Status | Notes / Evidence |
|---|---|---|---|
| 7.1 | AI-Driven Exploratory Testing (AET) | ⏭️ | AET not GA (Dec 2027). Interim: 12-pair regression suite run on each change (per §7.1 interim note). |
| 7.4 | Cross-Functional Sign-Off | ⏭️ | Demo, not a production release. |

*(Full report enumerates all 70 controls; rows above are representative of each flag type.)*

---

## 4. Build checklist (README Stage 0–8)
- Stage 0–2: ✅ scaffold + mock + connectivity (sandbox OData).
- Stage 3: ✅ JWT validated at A2A boundary; advisory-only; token-window cap + payload summarization > 8 KB.
- Stage 4: ✅ structured logs, PII redaction; ⚠️ rate limiting at default (60/min user, 600/min instance) — tune before real scale.
- Stage 5–6: ✅ `cf push`; agent card live; Joule capability published.
- Stage 7–8: ⏭️ production sign-off (demo); 2.0-ready (A2A + ORD IDs confirmed).

---

## 5. Cost
Per the [Cost Estimation Guide](AI%20Agent%20Runtime%20Cost%20Estimation%20Guide%20v7.md): ~1 LLM call + 1–2 tool calls per query; sandbox usage negligible. Set a per-transaction ceiling (L0-4.8) before customer scale.

---

## 6. Gaps & go/no-go
- **Verdict:** ✅ go for **demo**; ❌ not for production (safety-dashboard run, cross-functional sign-off, and customer value case are outstanding — flagged ⚠️/⏭️ above, not silently skipped).
- **To productionize:** complete L0-1.0 value case, L0-5.1 Safety Dashboard, L0-7.4 sign-off; move off the public sandbox to the customer tenant with principal propagation.

---

*This is the shape every build should hand off in. Copy the full template from [`developer-toolkit.md` §12](developer-toolkit.md); never leave a relevant control blank — mark it ⚠️/❌/⏭️ with a reason.*
