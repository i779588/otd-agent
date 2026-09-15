# API Policy Compliance — custom agents & Agent Labs

> **Source:** SAP **API Policy v.4.2026a** (published April 2026) — a mandatory cross-portfolio governance framework applying to **all** SAP solutions and all parties consuming SAP APIs, including solutions CIS builds for customers. This file maps the policy to the way this kit builds agents, so a project can self-check before the ATQ gate.
>
> **Key resources:** SAP API Policy (full text) · API Policy FAQ (40+ Q) · [SAP Business Accelerator Hub](https://api.sap.com) (authoritative Published-API catalog) · [Architecture Center AI Golden Path](https://architecture.learning.sap.com/docs/ai-golden-path) (endorsed AI architectures).

---

## Two layers every custom agent must clear

1. **Mandatory requirements for all projects** (4 rules, below).
2. **The AI/Agentic Review Gate** — triggers for *any* AI agent, MCP server, or LLM-driven orchestration that calls SAP APIs. **Every custom agent hits this gate**, so **contact ATQ before implementation** (not after).

> **Compliant ≠ endorsed-architecture-alone.** A project is *fully compliant* only when it (a) uses an **endorsed architecture**, (b) touches only **Published, Level-A** APIs, (c) never **circumvents** the governance layer, **and** (d) has an **ATQ sign-off on record**. This kit delivers (a)–(c) by design; (d) is a per-project action.

---

## Scorecard — this kit's default pattern (A2A + Agent Gateway + AI Core)

| Policy requirement | This kit's pattern | Verdict | Why |
|---|---|---|---|
| **1. Only Published APIs** | Consumes only SAP Business Accelerator Hub / documented OData; on-prem entity sets discovered via `/IWFND/MAINT_SERVICE` (documented services) — [README §5](README.md) | ✅ | Never uses blog/forum/reverse-engineered APIs, or `$metadata`-only endpoints without a Hub listing |
| **2. No circumvention via custom code** | Z/Y code reads via **published** APIs; no wrapper/proxy to reach private interfaces; **advisory-only — no POST/PATCH/DELETE** ([README §Data Governance](README.md)) | ✅ | Creates no pathway to prohibited use; does not bypass API controls |
| **3. Rate-limit awareness** | 429 exponential backoff, circuit breaker (3 consecutive failures), caching, consumption monitoring — [README §3b](README.md) + §Security | ✅ | All four controls the policy asks for are present |
| **4. Clean Core level** | Targets **Level A (Released)** APIs | ✅ | Level A = "Fully compliant — target for all new development" |
| **AI/Agentic Review Gate** | **A2A via SAP Agent Gateway** + **SAP AI Core / Generative AI Hub** — both named **Endorsed Architectures** | ✅ (architecture) | These are on SAP's endorsed list; still requires the ATQ sign-off (see below) |
| **ODP-RFC hard block (Jun 9 2026)** | Uses OData / Agent Gateway, **not** ODP-RFC extraction to non-SAP targets | ✅ | Only ODP-RFC extraction to non-SAP targets is technically blocked |

---

## Endorsed vs NOT endorsed (from the policy)

**Endorsed (compliant) architectures:**
- **MCP Gateway on SAP Integration Suite** — governed MCP access (auth, authz, rate limiting, audit logging).
- **Agent2Agent (A2A) via SAP Agent Gateway** — multi-agent collaboration between external AI platforms and SAP agents. ← *this kit's primary mode.*
- **SAP AI Core / Generative AI Hub** — foundation-model access with SAP's security/governance layer. ← *this kit's model layer.*
- **SAP-published MCP servers** (CAP / UI5 / Fiori Elements MCP Server) — developer tooling only.

**NOT endorsed (non-compliant):**
- Community-built MCP servers on BTP wrapping SAP business APIs.
- Direct agentic access to OData/REST **without a governance layer**.
- Custom agent orchestrators making **unbounded** API call sequences.
- Using **ADT APIs** for business-data access, SQL execution, or agentic workflows (ADT is dev-tooling only).

> **Why community MCP servers are rejected (SAP's stated data):** ~40–45% agentic accuracy, up to **5× more tokens**, **80% violate OWASP Top 10**, and they lack SAP Knowledge Graph business-semantic context. The endorsed Agent Gateway / AI Core path is exactly what avoids this.

---

## Clean Core level mapping

| Level | API Policy status | Guidance |
|---|---|---|
| **A** — Released APIs | Fully compliant | Target for all new development |
| **B** — Classic APIs | Compliant | Acceptable; monitor deprecation |
| **C** — Internal/undocumented | "At own risk" — may become prohibited | Requires documented justification + migration plan |
| **D** — Not recommended/obsolete | Non-compliant — highest risk | Not permitted for new projects |

> **The prohibited list will grow.** ODP-RFC is currently the only explicitly prohibited API, but SAP will reclassify more internal interfaces over time — today's Level C can become Level D. Stay on **Level A**.

---

## Project self-check (do before the ATQ gate)

- [ ] Every SAP API used is verified **Published** on the SAP Business Accelerator Hub (or documented in SAP Help / Ariba / Concur portals).
- [ ] Clean Core **Level A** targeted (justify + plan migration for any Level C; no Level D).
- [ ] Connectivity uses an **endorsed** path — **A2A via SAP Agent Gateway** and/or **MCP Gateway on Integration Suite**; models via **AI Core / GenAI Hub**.
- [ ] **No** community MCP server, ungoverned direct OData agentic access, unbounded call loops, or ADT-for-business-data.
- [ ] Advisory-only writes posture (no POST/PATCH/DELETE) unless a write use case is separately reviewed.
- [ ] Rate-limit controls in place: 429 backoff, circuit breaker, caching, consumption monitoring.
- [ ] **Not** extracting via ODP-RFC to a non-SAP target (hard-blocked from Jun 9 2026; opt-out only to end 2026).
- [ ] For S/4HANA ABAP: run **ABAP Test Cockpit (ATC)** Cloud Readiness / Clean Core checks ([github.com/SAP/abap-atc-cr-cv-s4hc](https://github.com/SAP/abap-atc-cr-cv-s4hc)).
- [ ] **ATQ contacted and sign-off recorded** — mandatory for any AI agent / MCP / autonomous orchestration.

## Review process (ATQ)

1. Contact **ATQ** with a description of the planned AI/agentic architecture (`api-policy@global.corp.sap` for policy Qs; ATQ Architecture & Technology Quality team for the gate).
2. ATQ assesses against the API Policy + endorsed architectures.
3. Compliant → proceed. Not compliant → ATQ advises an alternative endorsed pattern.

## What does NOT change
- Z/Y-namespace custom code remains permitted (within the boundaries above).
- Existing integrations using Published APIs for documented purposes are unaffected.
- Rule-based RPA (deterministic, no AI reasoning) is not restricted.
- Third-party middleware consuming Published APIs remains permitted. No new commercial models/costs.

---

*Contacts: API Policy — `api-policy@global.corp.sap` · ODP-RFC — `odprfc@global.corp.sap` · Gate — ATQ (Architecture & Technology Quality). Local source PDF archived in the portal repo; the authoritative page is the internal `wiki.one.int.sap` API Policy Compliance page.*
