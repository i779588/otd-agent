# QUICKSTART — from intent to a running SAP agent

> **Start here.** This is the central GDH APAC entry point. It routes you to the right cookbook and the fastest build path, then hands off to the detailed guides. Whole thing is ~5 minutes of reading before you start building.
>
> **The files in this kit:**
> | File | Use it for |
> |---|---|
> | **QUICKSTART.md** (this) | Route your use case → pick a path → start. |
> | [`developer-toolkit.md`](developer-toolkit.md) | The guided build flow + the full L0-1→L0-10 governance checklist (§10). |
> | [`README.md`](README.md) | The full build-and-harden engineering reference (Parts A–C). |
> | [`agent-skill-recipe.md`](agent-skill-recipe.md) | Build & publish a **Joule skill** (low-code or pro-code). |
> | [`example.md`](example.md) + [`CLAUDE.md`](CLAUDE.md) | The no-code guided path (drive it with Claude Code). |
> | [`references.md`](references.md) | Every external dependency, located and explained. |
> | [`worked-example.md`](worked-example.md) | A filled-in end-to-end example — what "done" looks like. |
> | [`AI Agent Runtime Cost Estimation Guide v7.md`](AI%20Agent%20Runtime%20Cost%20Estimation%20Guide%20v7.md) | Estimate runtime cost. |
> | [`Custom Agent Governance & Architecture`](Custom%20Agent%20Governance%20%26%20Architecture) | Governance summary + engagement journey. |

---

## Step 1 — Scope: what are you building?

| Scope | Go to |
|---|---|
| A **single Joule skill** (maps to a backend API) | [`agent-skill-recipe.md`](agent-skill-recipe.md) → low-code path |
| A **full custom agent** (custom logic, tools, grounding) | Step 2 below |
| A skill **served by a custom agent** | Build the agent (Step 2), then [`agent-skill-recipe.md`](agent-skill-recipe.md) → pro-code path |
| Not sure | Open this repo in Claude Code and say *"read developer-toolkit.md and build my agent"* — the toolkit's scope gate (§2.0) decides with you. |

## Step 2 — Route: which cookbook?

**Evaluate the [GDH AI Factory dev-tools](https://github.tools.sap/CE-A-Global-AI-Agents/cea-csd-gdh-dev-tools) cookbook first (primary).** Then pick a build route:

```
Does the use case need graph semantics / ontology-driven grounding /
relationship-centric reasoning / high explainability (citable facts)?
│
├─ NO  → CoE Cookbook  (default build route)
│        github.tools.sap/business-ai-platform/Custom-Agentic-solutions-CoE
│
└─ YES → KG Cookbook   (specialized route)
         pages.github.tools.sap/GDH-AIFactory-CodeAgents-KG/doc/

Standard document Q&A?  → evaluate SAP Document Grounding Service FIRST;
                          build custom RAG/KG only if you need custom chunking,
                          structure-aware extraction, chunk-level ACL, or
                          vector-store control.
```

See [`developer-toolkit.md` §4](developer-toolkit.md) for the full catalog (purpose, prerequisites, limitations, KG build sequence & governance).

## Step 3 — Build (the 3 stages)

Whichever route, the build follows three stages (CoE cookbook recipe order):

1. **Scaffold + mock** — generate the skeleton (`sap-agent-bootstrap` / CoE `recipes/01-scaffold-agent`), build against `mcp-mock.json`, get tests green offline (`IBD_TESTING=1`, coverage ≥ 70%). → [`README.md` §2–3](README.md)
2. **Deploy to BTP** — Cloud Foundry or Kyma; map `VCAP_SERVICES`; agent card live on the CF URL. → [`README.md` §6](README.md)
3. **Wire into Joule** — register the agent / publish its skills as a capability bundle. → [`agent-skill-recipe.md`](agent-skill-recipe.md) + [`README.md` §7](README.md)

> KG route adds a **grounding stage before Step 1**: `sap-hana-data-prep` → `sap-hana-triple`/`sap-hana-vector`, with the authoring pipeline (scoping → model-proposal → Revisor gate → load → index). See developer-toolkit §4 KG entry.

## Step 4 — Govern & ship

- Track every relevant **L0-1 → L0-10** control ([`developer-toolkit.md` §10](developer-toolkit.md)) with a status flag — never silently skip one.
- Walk the **Stage 0–8** build checklist ([`README.md` §Agent-PathToProd](README.md)).
- Estimate cost, confirm API policy + data residency, get the cross-functional sign-off (L0-7.4).
- **API Policy Compliance:** confirm against the GDH API policy compliance requirements (see [`references.md`](references.md) → API policy). *If your team maintains the internal wiki checklist, capture its items into `references.md` so this kit stays self-contained.*

## Step 5 — Migrate later (Joule 2.0)

Build 2.0-ready from day one (A2A surface, `asset.yaml` ORD IDs, `LLM_PROVIDER` isolation). When Joule 2.0 / standard migration is GA, it's an infrastructure swap — no code changes. → [`README.md` Part C](README.md)

---

*This kit is reference-complete: it points to the canonical cookbooks and skills rather than copying them (SAP: consume as reference, do not fork). Everything referenced is indexed in [`references.md`](references.md).*
