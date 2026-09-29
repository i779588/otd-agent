# Implementation Plan — OTD-Fix-the-Risk (Claude-backed, Joule-frontable)

## Scope
- Build scope: **full custom agent** (pro-code A2A), ported from a Joule/AI-Core build to run LLM reasoning on the Anthropic API directly while remaining frontable by Joule.

## Selected approach
- Agent type: **ReAct** (LangGraph `create_agent`; tool-calling loop over read-only SAP tools)
- Path: **pro-code (scaffold)** — existing SAP CoE A2A scaffold, ported
- Platform / runtime: **standalone A2A server** (Starlette/uvicorn); Anthropic API for the LLM; **not** SAP AI Core. Joule fronts it via the agent card (gated registration).

## Selected assets
- Cookbook: **CoE** (pro-code A2A agent)
- Accelerator / starter: original `OTD-Fix-the-Risk/` Joule build (copied into `OTD-Fix-the-Risk-Claude/`)
- Grounding strategy: **OData** — 5 read-only S/4HANA services via declarative MCP translation specs (mock now; live read-only bridge scaffolded)

## Prerequisites
- Python 3.11+ and an `ANTHROPIC_API_KEY` (reasoning is billed by Anthropic).
- `.env` created from `.env.example` (secrets live only in `.env`).
- For live mode only: S/4HANA OData base URLs + XSUAA/Destination credentials.
- Governance: an **exception + security review** for running off SAP AI Core / Gen AI Hub (Golden Path deviation — see outcome report).

## What changed vs the original (SAP coupling surface)
The only proprietary dependency was `sap-cloud-sdk` (5 import sites, 3 files) + SAP-namespaced model strings. All other requirements are public PyPI.

| Area | Original (Joule / AI Core) | Ported (Claude) |
|---|---|---|
| LLM routing | LiteLLM → SAP AI Core (`sap/anthropic--claude-4.5-*`) | LiteLLM → Anthropic direct (`anthropic/claude-sonnet-4-5`, `anthropic/claude-haiku-4-5`), env-overridable |
| `sap_cloud_sdk` | proprietary SDK | local compatibility shim at `app/sap_cloud_sdk/` (decorators, checkpointer, aicore no-op, bootstrap no-op, agentgateway client) |
| Tools | SAP Agent Gateway | offline `mcp-mock.json` (IBD_TESTING=1) + read-only OData→MCP bridge at `app/bridge/` (live) |
| Identity | SAP principal propagation | `app/bridge/token_exchange.py` — passthrough / XSUAA jwt-bearer / BTP Destination |
| A2A server, agent card, skills, circuit breaker, injection detector, `util.py`, tests | — | **unchanged** |

## Ordered implementation steps
1. **Prepare** — copy solution into `OTD-Fix-the-Risk-Claude/`; leave originals read-only. (gate: L0-1)
2. **Configure** — env-drive model ids to Anthropic direct in `agent.py` + `prompt_injection_detector.py`; add `sap_cloud_sdk` shim; remove `sap-cloud-sdk` from requirements; `pythonpath = app` in `pytest.ini`. (gate: L0-2, L0-6)
3. **Build (mock-first, IBD_TESTING=1)** — author `mcp-mock.json`: 5 servers, 19 read-only tools, 6-order scenario covering all 4 root-cause categories + a healthy control. (gate: L0-6, L0-8)
4. **Connect knowledge & actions** — read-only OData→MCP bridge (`app/bridge/odata_mcp_server.py`) driven by the declarative translation specs; identity via `token_exchange.py`; zero-write enforced at the bridge. (gate: L0-6.6, L0-6.7, L0-9)
5. **Test (IBD_TESTING=1 pytest, offline)** — run the ported suite; confirm zero write tools; coverage ≥70%. (gate: L0-5, L0-7.1/7.6)
6. **Deploy & register** — `DEPLOY.md` gated runbook (host A2A app; register agent card with Joule). **Not executed.** (gate: L0-7, L0-6.8, L0-10)
7. **Cleanup** — no dead scaffold introduced; mock + demo retained behind `IBD_TESTING`. (gate: L0-6)

## Demo assets (mock-mode, IBD_TESTING=1)
- Mock data fixtures: `assets/otd-fix-the-risk-agent/mcp-mock.json` — 6 sales orders (4500001 material shortage, 4500002 capacity, 4500003 warehouse bottleneck, 4500004 transit delay, 4500005 healthy) cross-linked across sales-order / stock / production-order / outbound-delivery / freight-order services.
- Demo UI (HTML): `demo/index.html` + `demo/serve_demo.py` — standalone offline page labelled "DEMO — mock data"; proxies to the local A2A agent (no CORS change, `main.py` untouched).

## Cleanup checklist
- [x] Unused scaffold code / dead decorators removed — none introduced; shim is minimal and load-bearing
- [x] Unused accelerator/cookbook templates removed — none copied in
- [x] `[illustrative]` snippets removed or wired in — cross-reference fields in mock data are labelled illustrative
- [x] No secrets in code/markdown; `.env` gitignored — secrets only in `.env` (template provided)
- [x] Mock data + demo UI retained (gated by `IBD_TESTING`)

## Applicable checklist subset
Full custom agent → **L0-1 … L0-10 (all, as relevant)**. Grounding is OData-only, so RAG-specific L0-3 controls and KG-specific L0-9 controls are largely ⏭️ N/A. Commercialization (L0-4) and formal release/go-live (L0-7) are ⏭️/❌ — this is a hackathon port, not a productised release.

## Dependencies and owners
- Anthropic API key + billing → **agent owner / developer**
- S/4HANA OData endpoints + XSUAA/Destination config (live mode) → **SAP BASIS / BTP admin**
- AI-Core-bypass exception + security review → **GDH APAC Architect Group / Security**
- Joule agent-card registration → **Joule tenant admin** (gated)

## Next action
Run `IBD_TESTING=1 pytest` in `assets/otd-fix-the-risk-agent/` to confirm the offline suite is green, then (optionally) start the agent + `demo/serve_demo.py` for a live mock demo with an `ANTHROPIC_API_KEY`.
