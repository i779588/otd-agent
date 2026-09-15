# References — external dependencies, located and explained

> **Why this file exists.** The Agent-PathToProd kit is a *reference-complete guidance layer*: it does **not** vendor (copy in) the build engines or SAP skills — SAP's guidance is to *consume the cookbooks as a reference, not fork them*. This index turns every "referenced but not in this repo" pointer into "referenced, located, and explained" so a developer never hits a dead end. For each dependency: **what it is**, **the canonical URL**, and **when you need it**.

## Cookbooks & programs (the build engines)

| Dependency | What it is | When you need it |
|---|---|---|
| **GDH AI Factory dev-tools** — `github.tools.sap/CE-A-Global-AI-Agents/cea-csd-gdh-dev-tools` | **Primary** global cookbook. Evaluate first. Consume as reference; do not fork. | Always — the entry reference before choosing a build route. |
| **CoE Cookbook** — `github.tools.sap/business-ai-platform/Custom-Agentic-solutions-CoE` | **Default build route (secondary).** Scaffolding, toolkit, recipes (scaffold → deploy → Joule), the `sap-*` skills, connectivity, deployment. | General SAP custom agents (tool/API actions, app integration, prototyping). |
| **KG Program / Cookbook-KG-CustomAI** — `pages.github.tools.sap/GDH-AIFactory-CodeAgents-KG/doc/` | **Specialized build route.** Knowledge-graph grounding on HANA (SPARQL + vector), ontology authoring, lifecycle/onboarding, architecture reference. | When the use case needs graph semantics, ontology-driven grounding, or relationship-centric reasoning. |
| **Agent Blueprint (hosted)** — `pages.github.tools.sap/GDH-Data-AI-Architecture-APAC/agent-blueprint/` | The hardening guide + live L0 checklist rendered as a site. | Reading the guide / using the interactive checklist. |
| **Developer Toolkit (hosted)** — `pages.github.tools.sap/GDH-Data-AI-Architecture-APAC/agent-blueprint/developer-toolkit/` | The guided builder, hosted. | Same content as [`developer-toolkit.md`](developer-toolkit.md), web form. |
| **This repo — Agent-PathToProd** — `github.tools.sap/GDH-Data-AI-Architecture-APAC/Agent-PathToProd` | The Golden Path starter kit (guidance + governance + recipes). | The map and rulebook that ties the above together. |

## Joule Studio skills (provided by Joule Studio / the CoE cookbook)

| Skill | What it does | Where it lives |
|---|---|---|
| `sap-agent-bootstrap` | Scaffolds a complete agent project skeleton. | Joule Studio; CoE cookbook `recipes/01-scaffold-agent`. Outside Joule Studio, scaffold from the CoE recipe. |
| `mcp-translation-file` | Converts EDMX specs → MCP tool definitions. | Joule Studio; equivalent to the `scripts/generate_mcp_translations.py` step ([`README.md` §5](README.md)). |
| `setup-solution` | Creates MCP server assets. | Joule Studio. |
| `mcp-mock-config` | Generates mock tool data (`mcp-mock.json`). | Joule Studio; or author by hand per [`README.md` §3 Mode A](README.md). |
| `sap-joule-capability` | Authors `.sapdas.yaml` capability bundles to register an agent's skills into Joule. | CoE cookbook `skills/sap-joule-capability`. See [`agent-skill-recipe.md`](agent-skill-recipe.md). |
| `sap-hana-data-prep` / `sap-hana-triple` / `sap-hana-vector` | KG/RAG build primitives (ingestion contract → triple store / vector index). | CoE cookbook `skills/`. See developer-toolkit §4 KG entry. |

> If a Joule Studio skill is unavailable (a Gate-0 check fails), the fallback is the manual equivalent — the EDMX pipeline scripts ([`README.md` §5](README.md)) or hand-authored mock/config.

## Pipeline scripts (EDMX → MCP → ORD)

| Script | What it does | Reference |
|---|---|---|
| `scripts/fetch_edmx.py` | Downloads `.edmx` from SAP API Business Hub. | [`README.md` §5 Step 1](README.md) |
| `scripts/generate_mcp_translations.py` | Parses EDMX → `mcp-translation-*.json`. | [`README.md` §5 Step 2](README.md) |
| `scripts/register_mcp_servers.py` | Registers translations as Agent Gateway MCP servers. | [`README.md` §5 Step 3](README.md) |

> These ship with the CoE scaffold / Joule Studio skills. This kit documents their contract; it does not vendor them (they evolve with the cookbook).

## Reference agents (worked examples)

| Agent | What it shows | Where |
|---|---|---|
| **Supply Chain Risk Agent** | Live S/4HANA read + external news + Claude synthesis; thread UI, risk cards, charts. | CoE cookbook `references/supply-chain-risk-agent/` |
| **Service Technician Companion** | S/4HANA plant maintenance on the public API Business Hub sandbox (no tenant needed). | CoE cookbook `references/service-technician-agent/` |
| **btp-joule-a2a-pro-code-agent (SwissKnife)** | A full public A2A pro-code agent reference. | CoE cookbook `references/btp-joule-a2a-pro-code-agent/` |

## Cost & commercial

| Dependency | What it is | Reference |
|---|---|---|
| **Cost Estimation Guide** | Self-contained runtime cost model (in this repo). | [`AI Agent Runtime Cost Estimation Guide v7.md`](AI%20Agent%20Runtime%20Cost%20Estimation%20Guide%20v7.md) |
| SAP AI Core Discovery-Center estimator | Live infra rate estimator. | `discovery-center.cloud.sap/serviceCatalog/sap-ai-core/` |
| Generative AI Hub pricing | AI unit / model pricing. | `sap.com/products/artificial-intelligence/ai-units.html` |
| **SAP Notes 3437766 & 3505347** | Authoritative / current AI Core rates. | SAP for Me → Notes |
| Idea2Value | CXO-ready value case (L0-1.0 traceability record). | `idea-agent.cfapps.us10-001.hana.ondemand.com` |

## API policy

| Dependency | What it is | Reference |
|---|---|---|
| SAP API Policy | OData usage clause / API policy. | `help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf` — verify with the global API policy team |
| **API Policy Compliance (internal wiki)** | GDH compliance checklist. | *`wiki.one.int.sap` — SAP-internal; add the specific requirements once captured (see [`QUICKSTART.md`](QUICKSTART.md)).* |

---

*If you add a new external pointer anywhere in this kit, add it here too — this file is the single index of everything the kit depends on but does not contain.*
