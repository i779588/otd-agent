> Related guidelines: [guidelines-agent.md](guidelines-agent.md) | [guidelines.md](guidelines.md) | [AI Agent Runtime Cost Estimation Guide.md](AI%20Agent%20Runtime%20Cost%20Estimation%20Guide%20v7.md)
> Guided build: [example.md](example.md) (no-code walkthrough) · [CLAUDE.md](CLAUDE.md) (auto-start for coding harnesses)
> Main repo: [Custom Agentic Solutions CoE cookbook](https://github.tools.sap/business-ai-platform/Custom-Agentic-solutions-CoE)

---

# SAP Custom Agent Blueprint: Joule Studio Build & Joule 2.0 Migration Guide

*A neutral, reusable blueprint for building SAP AI agents — from first scaffold to production integration and future migration. Two paths, starting with a Joule 2.0-ready build for custom agent development and productive deployment on Joule Studio, then migrating to Joule 2.0 in future.*

## 📌 Read this first

**The [Custom Agentic Solutions CoE cookbook](https://github.tools.sap/business-ai-platform/Custom-Agentic-solutions-CoE) is the main repository** for building SAP custom agents — scaffolding, toolkit, recipe checkpoints, connectivity, and deployment.

**This document is the complete build-and-harden guide** and adds the pieces a *customer-ready* agent needs that aren't spelled out there: production hardening (identity propagation, resilience, observability, data governance), the guided no-code build flow, sovereign/regional handling, and Joule 2.0 migration readiness. Use the cookbook to get started; use this guide to build it right and take it to production.

**What's in this file:**
- **Guided Quick-Start** — the no-code path via [`example.md`](example.md) + [`CLAUDE.md`](CLAUDE.md).
- **Part A — Build:** landscape, model-provider isolation, road-to-production (observability, governance, security), regional/sovereign, scaffold, connectivity modes, authorization & identity, resilience, system prompts, EDMX pipeline.
- **Part B — Integrate:** deploy (Cloud Foundry / Kyma), Joule Studio registration, A2A protocols & endpoints.
- **Part C — Migrate:** Joule 2.0 migration path, event-driven triggers, optional capabilities, reference agents, Quick Reference, and the Agent-PathToProd checklist.

---

## Who This Is For

SAP developers building custom AI agents that need to consume SAP data and integrate with SAP Joule. This guide covers:
- Starting from the Joule Studio scaffold
- Connecting to SAP APIs via three first-class modes
- Deploying to Cloud Foundry and registering in Joule Studio
- Building for regulated regions where Joule BYOA is not yet GA
- Future migration to Joule 2.0 when available

---

**Two ways to use this blueprint:**

1. **Guided, no-code** — hand [`example.md`](example.md) to a coding harness (Claude Code or similar). It interviews you, tells you which values to place in a `.env`, then scaffolds, tests, and launches a working agent. See [Guided Quick-Start](#guided-quick-start) below. This is the fastest path and applies every practice in this document for you.
2. **Manual, engineer-driven** — follow Parts A–C directly. This is the reference the guided path is built on, and the source of truth for every engineering decision.

---

## Guided Quick-Start

If you want a working agent fast without writing code, use the guided files that ship alongside this blueprint:

| File | Role |
|---|---|
| [`example.md`](example.md) | Self-contained, no-code recipe. Drop it in an empty folder, and a coding harness interviews you → builds → tests → launches. |
| [`CLAUDE.md`](CLAUDE.md) | Auto-loaded by Claude Code when the folder opens. Greets the user, routes them into `example.md`, and enforces the guardrails (work in a new sub-folder, never touch reference files, secrets only in `.env`). |

**Steps for the end user:**

1. Create a new empty folder (e.g. `my-agent/`).
2. Copy `example.md`, `CLAUDE.md`, and (optionally) this `README-5.md` into it.
3. Open the folder in Claude Code.
4. Type **`start`** (auto-start via `CLAUDE.md`) — or paste the kickoff prompt in `example.md` §1.
5. Answer the interview questions; paste API values into `.env` when asked.
6. When every build gate is green, tell the agent to **launch**.

The guided path never edits the reference files or any other project; it
scaffolds into a fresh sub-folder and asks before anything non-local. The rest of
this document is the engineering blueprint behind it.

---

# Part A — Build

## 1. The SAP Agent Landscape

### What Joule Studio provides today

Joule Studio is the current SAP development environment for custom AI agents. It provides:
- **`sap-agent-bootstrap` skill** — scaffolds a complete agent project
- **`mcp-translation-file` skill** — converts EDMX specs to MCP tool definitions
- **`setup-solution` skill** — creates MCP server assets
- **`mcp-mock-config` skill** — generates mock tool data
- **SAP AI Core** integration for LLM access (Claude, GPT, etc.)
- **A2A protocol** (Agent-to-Agent) as the standard agent communication layer

### Where Joule 2.0 is headed

Joule 2.0 (in development) will provide native agent orchestration — custom agents become first-class Joule skills without a separate deployment step. The A2A protocol and `asset.yaml` ORD IDs you define today are exactly the registration format Joule 2.0 uses. **An agent built correctly today migrates to Joule 2.0 with infrastructure changes only — no code changes.**

### A layered design that survives platform change

Because the platform is moving (Joule Studio today → Joule 2.0 → a consolidated
SAP Business AI platform tomorrow), this blueprint deliberately isolates the
parts most likely to change so a later migration is a swap, not a rewrite:

- **Model access** is isolated behind a single switch — `LLM_PROVIDER` (`aicore` | `openai-compatible`). Swapping the model provider (including for a regulated region) touches configuration only, never tool or business logic. See [§1a](#1a-model-provider-isolation).
- **Agent transport** is A2A — a stable protocol that is native in Joule 2.0.
- **Persistence** is in-memory by default (fine for MVPs); a durable store (HANA Cloud) is a drop-in where state must survive restarts.
- **Regional assumptions** live in one place per concern, not scattered through code. See [§1c](#1c-regional--sovereign-deployments).

When the platform matures, replace the model provider, keep the A2A surface, the
Joule capability files, the tool APIs, the persistence schema, and the regional
checks.

### Build Joule 2.0-first, fall back to Joule 1.0
Write the agent against the Joule 2.0-native constructs from day one, and treat Joule 1.0 (Joule Studio) as the fallback path — not the other way round. Concretely, make these your first choice, because they are exactly what Joule 2.0 consumes natively:
- Agent Gateway as the primary connectivity mode — ORD-registered MCP servers are the Joule 2.0 tool-registration format. Direct (Destination + Connectivity) is the fallback for on-prem / unregistered endpoints. (ORD — Open Resource Discovery — the ID scheme (sap.s4:apiResource:...) used in asset.yaml; the Joule 2.0 registration key)
- EDMX → MCP translation → ORD (Open Resource Discovery) registration as the primary tool-definition pipeline (§5), so every tool carries a stable ORD ID from the start.
- asset.yaml ORD IDs authored up front — these are the Joule 2.0 registration keys, so no rework at migration.
- A2A transport as the only agent surface — native in Joule 2.0, HTTP-wrapped in 1.0.

An agent built this way runs on Joule 1.0 today via the fallbacks (Joule Studio registration, Destination mode where AGW isn't entitled) and migrates to Joule 2.0 with infrastructure changes only — no code changes.

### Three SAP connectivity modes

These are first-class choices — not a hierarchy. Pick the right one for your context:

| Mode | When to use | Key credential |
|---|---|---|
| **Mock** | Dev, tests, demos, offline | None — `mcp-mock.json` |
| **Agent Gateway** | Cloud-native production, AGW entitled in BTP | `AGW_CREDENTIALS_JSON` |
| **Direct (Destination + Connectivity)** | On-prem SAP, AGW not available, custom endpoints | `DEST_*` + `CONN_*` vars |

> You can switch modes per-deployment (env var) or per-request (message metadata). Mock always overrides the others.

### Protocol stack

```
User / Joule / External Agent
        ↓ A2A JSON-RPC
Your CF Agent (port 5000)
        ↓ LiteLLM
SAP AI Core (Claude / GPT)
        ↓ LangChain tool calls
SAP APIs — via one of the three modes above
```

---

## 1a. Model Provider Isolation

The LLM endpoint is the single most portable part of the stack. Keep it behind
one switch so it can be swapped per environment (dev vs prod), per contract, or
per region (see [§1c](#1c-regional--sovereign-deployments)) without touching
anything else.

| `LLM_PROVIDER` | Endpoint | Use when |
|---|---|---|
| `aicore` | SAP AI Core / Generative AI Hub (Claude, GPT, …) via LiteLLM | You have an AI Core instance; the standard commercial path. |
| `openai-compatible` | Any hosted OpenAI-compatible gateway | AI Core is unavailable in your region, or you must route through a customer-approved model gateway. |

**AI Core (`aicore`):**

```bash
LLM_PROVIDER=aicore
AGENT_MODEL=sap/anthropic--claude-3.5-sonnet     # or your deployed model
AICORE_CLIENT_ID=<from AI Core service key>
AICORE_CLIENT_SECRET=<from AI Core service key>
AICORE_AUTH_URL=<from AI Core service key>
AICORE_BASE_URL=<from AI Core service key>
AICORE_RESOURCE_GROUP=default
```

**OpenAI-compatible model gateway (`openai-compatible`):**

```bash
LLM_PROVIDER=openai-compatible
MODEL_GATEWAY_URL=https://model-gateway.example.com/v1
MODEL_GATEWAY_API_KEY=<from your secret store>
MODEL_NAME=<model-deployment-name>
```

> The model provider is orthogonal to the SAP connectivity mode. Live business
> data is read over plain HTTP/OData against the customer's own system and is
> region-agnostic — only the *model* endpoint changes when you move providers.

---

## 1b. Road to Production: Key Considerations

Before building, validate these conditions. Discovering them late is expensive.

### SAP API Access

| Checkpoint | How to verify | Comments |
|---|---|---|
| OData Service Usage Clause | Product-team guidance → [API Policy PDF](https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf) | IMPORTANT: verify with the global API policy team |


> Agree the way ahead with the right stakeholders; keep the confirming emails for reference.


**Recommended for production:**

- **Application Logging** (`application-logs` service) — bind in `manifest.yml` for CF log aggregation
- **Alert on 403/404 tool failures** — set up CF log drain to monitoring; tool access issues need Basis team response
- **Version the system prompt** — track prompt changes that affect simulation outputs


**Observability & tracing:**

- **Correlation ID per request** — generate (or accept from the caller) an ID at the A2A boundary and thread it through every downstream call and every log line. Use the incoming `messageId`/`contextId` as the correlation key so a Joule conversation can be traced end-to-end.
- **Structured logs, not prose** — emit one structured record per tool call with at least: `correlation_id`, `context_id`, `tool_name`, `sap_mode` (mock/gateway/cloud/onprem), `status`, `latency_ms`, `prompt_tokens`, `completion_tokens`. This makes the CF log drain queryable rather than just readable.
- **Redact before logging** — sanitise tool args before they hit logs; SAP user IDs and vendor names are PII in some jurisdictions (see Data Governance below). Log the correlation ID, not the payload.
- **Prompt-regression signal** — because each log line carries the prompt version (Prompt versioning), a behavior change can be traced to the exact prompt revision that introduced it.

### Data Governance & Compliance

- **Advisory-only principle** — agents must never write to SAP systems. System prompt must explicitly forbid `POST`/`PATCH`/`DELETE` operations
- **Disclaimer on all financial outputs** — *"These are estimates based on available SAP data. Validate with your finance team before acting."* Non-negotiable
- **No PII in logs** — sanitise tool call args before logging; SAP user IDs and vendor names count as PII in some jurisdictions
- **Data residency** — SAP AI Core region must match your SAP system's data residency requirements

### BTP Infrastructure

- **Space Developer role** — required for `cf create-service`, `cf create-service-key`. Without it you can see services but can't create keys. Request from space admin before starting
- **Memory quota** — default CF space quota is often insufficient for ML apps. Request 512M minimum (1G will typically exceed shared space quota)
- **Agent Gateway entitlement** — check `cf marketplace | grep agent-gateway` before planning Mode B. Not available in all BTP accounts
- **Joule IAS tenant** — Joule uses a separate IAS tenant (`das-ias`). Your SAP account doesn't automatically exist there. Request access from Joule admin before starting Part B

### Security

- **Never commit credentials** — `.env` must be in `.gitignore`. CF credentials come from service bindings (VCAP_SERVICES) in production
- **CORS policy** — `allow_origins=["*"]` is fine for internal demos; restrict to specific origins before external exposure
- **Agent Gateway mTLS** — production Agent Gateway uses mutual TLS. Keep `AGW_CREDENTIALS_JSON` in a secrets store, not env vars, for production
- **Rate limiting** — LLM calls are expensive. Add request throttling before exposing to end users at scale

### Testing Gate Before CF Push

```bash
IBD_TESTING=1 pytest            # all tests pass
pytest --cov=app                # coverage ≥ 70%
# Verify mock mode demo works end-to-end
IBD_TESTING=1 python3 app/main.py &
curl -s http://localhost:5000/.well-known/agent.json | python3 -m json.tool
```

All of the above must pass before `cf push`. Production 403s on real data are dramatically harder to debug than local mock failures.

---

## 1c. Regional & Sovereign Deployments

The commercial path (Joule BYOA + SAP AI Core / Generative AI Hub) is GA in
`eu10` and rolling out across regular commercial regions. It is **not** available
everywhere — notably China Landing, NS2, and KSA non-regulated. This blueprint
treats regulated / sovereign regions as **first-class**, not an afterthought, so
you can build customer value now and migrate cleanly later.

**Principles for a region-portable agent:**

1. **Isolate the model.** Where AI Core isn't available, set `LLM_PROVIDER=openai-compatible` and point at a customer-approved model gateway ([§1a](#1a-model-provider-isolation)). Nothing else in the agent changes.
2. **Keep the data path region-agnostic.** Reading business data is a plain HTTP/OData call to the customer's own system — it works identically regardless of model region.
3. **Verify the region before you commit.** Confirm which services (Joule, AI Core, Agent Gateway, HANA) are actually available in the target subaccount *before* designing around them. Re-verify periodically (regional availability changes).
4. **Have a UI fallback where Joule isn't GA.** If the region has no Joule control plane, surface the agent through a custom UI shell (e.g. a UI5 chat shell) instead of the Joule consumer experience. The agent itself is unchanged; only the front door differs.

**Fast path (regulated region), end to end:**

```bash
# 1. Verify what the region exposes (services, entitlements) before building.
btp --format json list accounts/entitlement --subaccount <SUBACCOUNT_ID>

# 2. Scaffold, pointing the model at the approved gateway.
export LLM_PROVIDER=openai-compatible
export MODEL_GATEWAY_URL=https://model-gateway.example.com/v1
export MODEL_GATEWAY_API_KEY=<from-secret-store>
export MODEL_NAME=<model-deployment-name>

# 3. Build and test in mock mode (offline), then connect live data over OData.
# 4. Deploy to CF or Kyma; surface via Joule where available, else a UI5 shell.
```

Joule availability, summarized (verify per tenant — this moves):

| Region | Joule (BYOA + A2A) | Fallback if not GA |
|---|---|---|
| `eu10` | GA — happy path | — |
| `eu11 / us10 / us20 / us21 / jp10 / ap10 / ap11` | Rolling out | Verify per tenant |
| China (`cn40`) | Not GA | UI5 chat shell + Work Zone tile |
| NS2 | Not GA | Custom UI shell |
| KSA non-regulated | Not GA | UI5 chat shell |
| KSA regulated | Verify per tenant (AI Core available) | — |

---

## 2. Scaffold from Joule Studio

### Generate the project skeleton

Generate the project skeleton from Joule 2.0 or use generated accelerator boilerplate that complies to Joule 2.0.
From inside `assets/<your-agent-name>/`, invoke the bootstrap skill in Joule Studio:

```
/sap-agent-bootstrap
```

This generates:
```
assets/<agent-name>/
├── app/
│   ├── main.py              ← A2A server entry point
│   ├── agent.py             ← LLM agent + system prompt
│   ├── agent_executor.py    ← A2A protocol adapter
│   └── mcp_tools.py         ← MCP tool loader
├── asset.yaml               ← SAP platform descriptor
├── requirements.txt
├── conftest.py              ← IBD_TESTING=1 for all tests
└── pytest.ini
```

### Three mandatory decorators in `app/agent.py`

These are the **complete and final set** — never add more:

```python
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

@agent_model(key="config.model", label="LLM Model", description="...")
def get_model_name() -> str:
    return os.environ.get("AGENT_MODEL", "sap/anthropic--claude-3.5-sonnet")

@agent_config(key="config.temperature", label="LLM Temperature", description="...")
def get_temperature() -> float:
    return 0.0   # temperature only — @agent_config is not general-purpose

@prompt_section(key="prompts.system", label="System Prompt", description="...")
def get_system_prompt() -> str:
    return "Your domain-specific system prompt here..."
```

> ⚠️ `@agent_config` exposes values to the BTP admin UI. All other configuration must be plain Python constants.

### Start with mock mode — always

Before connecting any SAP system, make the full agent work in mock mode. This guarantees:
- All tests pass offline
- CI/CD pipeline never needs SAP credentials
- Demo works without SAP access

```bash
export IBD_TESTING=1
pytest                        # all tests must pass
python3 app/main.py           # start server
curl http://localhost:5000/.well-known/agent.json   # verify agent card
```

---

## 3. Connect SAP Data — Three Modes

### Mode A: Mock (always build first)

Create `mcp-mock.json` at the asset root. This defines all tools with deterministic responses:

```json
{
  "metadata": {"version": "1.0.0", "mock_mode": true, "deterministic": true},
  "servers": {
    "my-sap-api": {
      "mcp_server_name": "sap.s4:apiResource:MY_API:v1",
      "description": "What this API does",
      "tools": {
        "MyEntityTool": {
          "description": "Retrieve X from SAP",
          "input_schema": {
            "type": "object",
            "properties": {
              "Id": {"type": "string", "description": "Record ID"},
              "top": {"type": "integer", "description": "Max results (max 100)"}
            },
            "required": ["Id"]
          },
          "mock_response": {"value": [{"Id": "TEST-001", "Status": "Active"}]}
        }
      }
    }
  }
}
```

The mock tool is structurally identical to a production tool — same name, schema, and `arun()` interface. Tests and business logic never need to change when switching to live data.

**Switching mock per-request from the client:**

```json
{
  "method": "message/send",
  "params": {
    "message": {
      "metadata": {"mock": true}
    }
  }
}
```

In `agent_executor.py`, read this flag and set `IBD_TESTING` for the request duration:

```python
use_mock = str(msg_metadata.get("mock", "")).lower() in ("1", "true")
if use_mock:
    os.environ["IBD_TESTING"] = "1"
try:
    # ... process request ...
finally:
    if use_mock:
        os.environ.pop("IBD_TESTING", None)
```

---

### Mode B: Agent Gateway (preferred production)

Agent Gateway is a BTP service that acts as a managed proxy between your agent and SAP APIs. It handles authentication, Cloud Connector routing, and MCP tool registration.

**Why prefer it:**
- Single credential (`AGW_CREDENTIALS_JSON`) replaces 3-step auth chain
- Manages Cloud Connector routing — your agent code has no network awareness
- Tool registration via ORD IDs — standard across SAP systems
- No entity set name guessing — tools registered via translation files

**Setup:**

1. Check entitlement: BTP Cockpit → Entitlements → search "agent gateway"
2. Create instance: `cf create-service agent-gateway standard my-agw`
3. Get service key: `cf create-service-key my-agw my-agw-key && cf service-key my-agw my-agw-key`
4. Set in `.env`: `AGW_CREDENTIALS_JSON='<full JSON>'`

**`mcp_tools.py` uses it automatically:**

```python
from sap_cloud_sdk.agentgateway import create_client

agw_client = create_client()   # reads AGW_CREDENTIALS_JSON
mcp_tools = await agw_client.list_mcp_tools()
```

**Declare dependencies in `asset.yaml`:**

```yaml
requires:
  - name: my-sap-api
    kind: mcp-server
    ordId: sap.s4:apiResource:MY_API:v1
```

---

### Mode C: Direct via Destination + Connectivity

Use this when Agent Gateway is not available, or for on-premise SAP systems.

> This is a **first-class production mode**, not just a fallback. Set it explicitly with `SAP_MODE`.

**When to choose this mode:**
- Agent Gateway not entitled in your BTP subaccount
- On-premise S/4HANA via Cloud Connector
- Custom SAP endpoint not registered in Agent Gateway
- Explicit control over OData service paths needed

**Create the BTP service instances:**

```bash
cf create-service destination  lite my-dest
cf create-service connectivity lite my-conn
cf create-service-key my-dest  my-dest-key  && cf service-key my-dest my-dest-key
cf create-service-key my-conn  my-conn-key  && cf service-key my-conn my-conn-key
```

**Add to `.env`:**

```bash
DEST_CLIENT_ID="..."
DEST_CLIENT_SECRET="..."
DEST_AUTH_URL=https://<subaccount>.authentication.<region>.hana.ondemand.com
DEST_SERVICE_URI=https://destination-configuration.cfapps.<region>.hana.ondemand.com
DEST_NAME=MY_SAP_SYSTEM   # name of the destination in BTP Cockpit

CONN_CLIENT_ID="..."
CONN_CLIENT_SECRET="..."
CONN_AUTH_URL=https://<subaccount>.authentication.<region>.hana.ondemand.com
CONN_PROXY_HOST=connectivityproxy.internal.cf.<region>.hana.ondemand.com
CONN_PROXY_PORT=20003
```

**The 3-step auth chain (per OData call):**

```
Step 1: GET OAuth token from Destination Service
  POST <DEST_AUTH_URL>/oauth/token (DEST_CLIENT_ID + DEST_CLIENT_SECRET)
  ↓
  GET <DEST_SERVICE_URI>/destination-configuration/v1/destinations/<DEST_NAME>
  ← Returns: SAP system URL, sap-client, Cloud Connector location ID, pre-built Basic auth header

Step 2: GET OAuth token from Connectivity Service
  POST <CONN_AUTH_URL>/oauth/token (CONN_CLIENT_ID + CONN_CLIENT_SECRET)
  ← Returns: proxy_token

Step 3: Call SAP OData via the proxy
  GET <sap-system-url>/sap/opu/odata/...
    Authorization: Basic <from Step 1>
    Proxy-Authorization: Bearer <proxy_token>
    SAP-Connectivity-SCC-Location_ID: <from Step 1>
  → connectivityproxy.internal.cf...:20003
  → Cloud Connector → SAP backend
```

> ⚠️ The connectivity proxy hostname only resolves inside Cloud Foundry. All three steps work locally but Step 3 will timeout from a developer laptop.

**Cloud vs on-premise OData paths differ:**

| Aspect | S/4HANA Cloud | On-Premise (ERP/S/4HANA) |
|---|---|---|
| PO items service | `CE_PURCHASEORDER_0001` OData v4 | `MM_PUR_PO_MAINT_V2_SRV` OData v2 |
| PO items entity | `PurchaseOrderItem` | `C_PurchaseOrderItemTP` (NOT `Set`) |
| FM commitments | `API_FNDSMGMTCMTMTACTLITEM` | `C_PurchaseOrderCommitment` in MM service |
| Change Records | `CE_CHANGERECORD_0001` | `PLM_ENGINEERING_CHANGE_SRV` (role needed) |

> ⚠️ On-premise entity set names must be discovered, not assumed. Use the SAP Gateway Client (`/IWFND/MAINT_SERVICE` → SAP Gateway Client button) to test paths before coding.

**Configure as first-class primary via `SAP_MODE`:**

```yaml
# manifest.yml — deployment-level choice
env:
  SAP_MODE: onprem   # or: cloud, gateway
```

```json
// Per-request override via message metadata
{"metadata": {"sap_mode": "onprem"}}
```

```python
# agent_executor.py — reads metadata, sets env for request duration
sap_mode = msg_metadata.get("sap_mode", os.environ.get("SAP_MODE", "gateway"))
if sap_mode in ("cloud", "onprem"):
    os.environ["SAP_MODE"] = sap_mode
try:
    # ... process ...
finally:
    # restore original value
```

```python
# mcp_tools.py — respects SAP_MODE as primary, not just fallback
async def get_mcp_tools():
    if os.environ.get("IBD_TESTING") == "1":
        return _build_mock_tools()

    mode = os.environ.get("SAP_MODE", "gateway")

    if mode == "gateway":
        # Agent Gateway path
        agw_client = create_client()
        return convert_tools(await agw_client.list_mcp_tools())

    elif mode in ("cloud", "onprem"):
        # Direct Destination+Connectivity path
        return build_direct_tools(mode=mode)
```

---

## 3a. Authorization & Identity Propagation - Decide **whose identity reaches the SAP backend** before you build.

### Two identity models — pick one per deployment

| Model | Who SAP sees | When to use | Trade-off |
|---|---|---|---|
| **Technical user** | One fixed service account | Batch/event-driven agents, no per-user authorization needed | Simple; but SAP audit log shows the service account, not the end user. No row-level authorization by user. |
| **Principal propagation** | The actual end user | Interactive agents where SAP authorizations must apply per user | Correct audit trail + row-level security; requires trust config between IAS/XSUAA and the SAP backend. |

> ⚠️ Advisory-only agents (this blueprint's default) still often need **principal propagation** — a user must only *see* data they're authorized to read. A technical user with broad read access can leak data across authorization boundaries even without writing anything.

### How identity flows (principal propagation)

```
End user → Joule (IAS login)
   ↓ OIDC/JWT (user identity)
A2A endpoint on your CF agent   ← validate JWT here (XSUAA)
   ↓ exchange user JWT for backend assertion
Destination (Authentication = OAuth2SAMLBearerAssertion / PrincipalPropagation)
   ↓ user's SAML assertion / X.509
Cloud Connector → SAP backend   ← SAP sees the real user, applies their roles
```

### Destination `Authentication` types — when each applies

| Destination `Authentication` | Identity at SAP | Notes |
|---|---|---|
| `BasicAuthentication` | Technical user | Simplest; credentials stored in destination |
| `OAuth2SAMLBearerAssertion` | End user (cloud→cloud) | For S/4HANA Cloud. Requires OAuth client + trust in the SAP tenant. |
| `PrincipalPropagation` | End user (via Cloud Connector) | For on-prem S/4HANA. Requires Cloud Connector system-certificate trust. |
| `OAuth2ClientCredentials` | Technical client | For AGW / service-to-service, no user context. |

> The three-step auth chain in Mode C assumes `BasicAuthentication` (pre-built Basic header from the destination). For principal propagation, Step 1 returns a destination configured for SAML/X.509 instead of a Basic header, and the user JWT must be forwarded — set the destination `Authentication` accordingly and forward the incoming token.

### `xs-security.json` — what the agent app needs

Bind an XSUAA instance so the agent can validate incoming JWTs and (optionally) exchange them:

```json
{
  "xsappname": "my-agent",
  "tenant-mode": "dedicated",
  "scopes": [
    { "name": "$XSAPPNAME.Invoke", "description": "Call this agent" }
  ],
  "role-templates": [
    { "name": "AgentUser", "scope-references": ["$XSAPPNAME.Invoke"] }
  ],
  "oauth2-configuration": {
    "redirect-uris": ["https://my-agent.cfapps.<region>.hana.ondemand.com/**"]
  }
}
```

```yaml
# manifest.yml — add the xsuaa service binding
services:
  - my-agent-xsuaa   # cf create-service xsuaa application my-agent-xsuaa -c xs-security.json
```

> Role-collection assignment *policy* (who gets `AgentUser`, approval flow) is governed by `guidelines.md` — follow it there; this section covers only the technical wiring.

### Validate the incoming JWT at the A2A boundary

```python
# [illustrative] agent_executor.py — reject unauthenticated calls before any tool runs
# In mock mode (IBD_TESTING=1), skip validation so offline tests/demos still work.
if os.environ.get("IBD_TESTING") != "1":
    token = _bearer_from_headers(request.headers)          # Authorization: Bearer <jwt>
    claims = validate_xsuaa_jwt(token)                     # verify signature, audience, scope
    # carry user identity into tool calls for principal propagation
    request_ctx.user_token = token
```

> ⚠️ Never trust `metadata.user` or any client-supplied identity field — always derive identity from the validated JWT. Client metadata (`mock`, `sap_mode`) controls *behavior*, never *authorization*.

---

## 3b. Error Handling & Resilience Contract
1b says to *alert* on 403/404 tool failures. This section defines what the agent actually **returns** when a tool fails — because an advisory agent that silently hallucinates around a failed SAP call is worse than one that says "I couldn't reach the data."

### Error taxonomy → agent behavior

| Condition | Likely cause | Agent behavior | Retry? |
|---|---|---|---|
| **401 Unauthorized** | Expired/invalid token | Refresh token once, retry. If still 401 → surface auth error, stop. | Once, after refresh |
| **403 Forbidden** | Missing role/authorization on the entity | Do **not** retry. Tell user the data is not authorized for them; suggest contacting Basis. | No |
| **404 Not Found** | Wrong entity set / service alias / record absent | Do **not** retry. State the record/service was not found; never fabricate a substitute. | No |
| **429 Too Many Requests** | Backend/AI Core throttle | Exponential backoff, retry up to N. If exhausted → ask user to retry later. | Yes, backoff |
| **5xx / timeout** | Backend down, Cloud Connector down, proxy timeout | Retry idempotent GETs with backoff. If exhausted → partial answer + explicit gap note. | Yes (GET only) |
| **AI Core token-expiry** | OAuth token TTL elapsed mid-session | Transparently re-fetch AICORE token, retry. | Yes, transparent |

### Golden rules

1. **Never return a raw stack trace or SAP error payload to the end user.** Log the detail (with correlation id, see 1b Observability); return an advisory-safe message.
2. **A failed tool call is a data gap, not a reason to guess.** Combine with the existing system-prompt rule *"When data is missing, state this explicitly and continue with partial simulation + disclaimer"*.
3. **Retry only idempotent operations.** All SAP calls here are GETs (advisory-only), so retry is safe — but keep the guard explicit so a future writer of a non-GET tool must opt in.
4. **Circuit-break repeated failures.** After K consecutive failures to the same MCP server/tool, stop calling it for the request and report the outage rather than timing out repeatedly.

### Pattern

```python
# [illustrative] mcp_tools.py — wrap tool invocation with a resilience policy
async def call_tool_safely(tool, args):
    for attempt in range(MAX_RETRIES):
        try:
            return await tool.arun(args)
        except AuthExpired:
            refresh_tokens()                      # 401 / AI Core token-expiry
            continue
        except Throttled:                         # 429
            await backoff(attempt)
            continue
        except (BackendUnavailable, Timeout):     # 5xx / timeout — GET is idempotent
            await backoff(attempt)
            continue
        except Forbidden:                         # 403 — do not retry
            return ToolError("not_authorized", user_msg="You don't have access to this SAP data.")
        except NotFound:                          # 404 — do not retry
            return ToolError("not_found", user_msg="That record or service was not found in SAP.")
    return ToolError("unavailable", user_msg="SAP data is temporarily unavailable. Please retry shortly.")
```

> The agent then folds `ToolError.user_msg` into its answer and appends the standard disclaimer — never the raw exception.

---


## 4. System Prompt Engineering

### Core rules for every SAP agent

These rules apply regardless of domain (from `specification/guidelines-agent.md`):

```python
SYSTEM_PROMPT = """
You are a [domain] AI agent operating on SAP data.

MANDATORY RULES:
1. Never fabricate SAP document numbers, amounts, or statuses — always retrieve live data first
2. Set top=100 on every tool call that accepts it (prevents context overflow on large datasets)
3. Present both benefits AND costs before stating a net figure — never partial analysis
4. Never execute write or delete operations on SAP systems — advisory only
5. When data is missing, state this explicitly and continue with partial simulation + disclaimer
6. End every financial output with: "These are estimates based on available SAP data.
   Validate with your finance team before acting."
"""
```

### Using Claude Code CLI to draft domain-specific prompts

**For a new SAP agent, use this prompt with Claude Code:**

```
Given this SAP OData service metadata:
[paste EDMX service document or entity set list]

Write a system prompt for an AI agent that [describe agent purpose].
The agent must:
- Always retrieve live SAP data before answering (never fabricate)
- Set top=100 on every tool call
- Surface these specific fields from tool responses: [list key fields]
- Model at least two scenarios (e.g. today vs +30 days)
- Include go/no-go recommendation
- End with the standard SAP data disclaimer

The agent should route user queries about [topic A] to [tool name A],
and queries about [topic B] to [tool name B].
```

**For Destination-based metadata surfacing:**

When using Mode C (Direct), the agent can pull system metadata from the destination at startup and include it in reasoning. Prompt pattern:

```
You have access to SAP system [DEST_NAME] with client [sap-client].
When the user asks about [domain], query [entity set] filtering by [key field].
The financial fields to always include are: [list fields confirmed from entity probe].
```

> `<to be updated>` — Claude Code CLI prompt patterns for SAP-specific prompt generation are evolving. This section will be updated as patterns stabilise.

---

## 5. EDMX Download, Translation, and Registration

The same three-script pipeline applies whether you're working in Joule Studio or outside it. Joule Studio's `mcp-translation-file` skill wraps these same steps.

### Step 1: Download EDMX from SAP API Business Hub

```bash
# Get your API key: https://api.sap.com → log in → "Show API Key" (top right)
export SAP_API_HUB_KEY=<your-key>
python3 scripts/fetch_edmx.py
```

What it does: downloads `.edmx` files for each API to `specification/<agent>/api-specs/`. Uses `APIKey:` header authentication — no browser login needed.

To add a new API, add an entry to the `APIS` list in `scripts/fetch_edmx.py`.

### Step 2: Generate MCP translation files

```bash
python3 scripts/generate_mcp_translations.py
# Force regenerate: python3 scripts/generate_mcp_translations.py --force
```

What it does: parses each EDMX, extracts entity sets and property metadata, generates `mcp-translation-*.json` files. Each file tells Agent Gateway which entity sets to expose as tools and what their input/output schemas are.

The `API_CONFIGS` dict in the script controls which entity sets to expose and what query fields to require. **This is the only part requiring human judgement** — everything else is automated from the EDMX.

In Joule Studio: the `mcp-translation-file` skill performs the same parsing. If the skill is unavailable (Gate 0 check fails), run the script manually.

### Step 3: Register in Agent Gateway

```bash
export AGW_CREDENTIALS_JSON=<service key JSON>
python3 scripts/register_mcp_servers.py --destination <sap-system-destination>

# Verify:
python3 scripts/register_mcp_servers.py --list

# Dry run:
python3 scripts/register_mcp_servers.py --destination MY_SAP --dry-run
```

What it does: reads all `mcp-translation-*.json` files and calls the Agent Gateway REST API to register each as an MCP server, linked to a BTP Destination.

### On-premise service discovery

Before writing tools for an on-premise system, always probe what's actually accessible:

1. In SAP GUI: open transaction `/IWFND/MAINT_SERVICE`
2. Find your service → click **SAP Gateway Client**
3. Test the entity set URL with `?$top=1&$format=json&sap-client=<client>`
4. Check the response fields — on-prem field names differ from cloud

> If you get `/IWFND/MED/170: No service found` — the service has no System Alias configured. In `/IWFND/MAINT_SERVICE` → select service → Add System Alias → `LOCAL` (for co-hosted systems).

---

# Part B — Integrate into Joule Studio

## 6. Deploying to Cloud Foundry

### `manifest.yml` essentials

```yaml
applications:
  - name: my-agent
    memory: 512M        # 1G often exceeds space quota
    disk_quota: 1G
    instances: 1
    buildpacks: [python_buildpack]
    command: python3 app/main.py --host 0.0.0.0 --port $PORT
    health-check-type: http
    health-check-http-endpoint: /.well-known/agent.json   # A2A agent card
    timeout: 180
    env:
      AGENT_MODEL: sap/anthropic--claude-3.5-sonnet
      AICORE_RESOURCE_GROUP: default
      SAP_MODE: gateway    # or: cloud, onprem
      AGENT_PUBLIC_URL: https://my-agent.cfapps.<region>.hana.ondemand.com
    services:
      - AICore             # SAP AI Core for LLM
      - my-dest            # Destination Service (Mode C only)
      - my-conn            # Connectivity Service (Mode C only)
```

### Read VCAP_SERVICES in `app/main.py`

CF injects bound service credentials into `VCAP_SERVICES`. Map them before any imports:

```python
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

import json, os
vcap = os.environ.get("VCAP_SERVICES")
if vcap:
    services = json.loads(vcap)
    # AI Core
    for svc in services.get("aicore", []):
        c = svc["credentials"]
        os.environ.setdefault("AICORE_CLIENT_ID",     c["clientid"])
        os.environ.setdefault("AICORE_CLIENT_SECRET", c["clientsecret"])
        os.environ.setdefault("AICORE_AUTH_URL",      c["url"])
        os.environ.setdefault("AICORE_BASE_URL",      c["serviceurls"]["AI_API_URL"])
        break
    # Destination Service (Mode C)
    for svc in services.get("destination", []):
        c = svc["credentials"]
        os.environ.setdefault("DEST_CLIENT_ID",     c["clientid"])
        os.environ.setdefault("DEST_CLIENT_SECRET", c["clientsecret"])
        os.environ.setdefault("DEST_AUTH_URL",      c["url"])
        os.environ.setdefault("DEST_SERVICE_URI",   c["uri"])
        break
    # Connectivity Service (Mode C)
    for svc in services.get("connectivity", []):
        c = svc["credentials"]
        os.environ.setdefault("CONN_CLIENT_ID",     c["clientid"])
        os.environ.setdefault("CONN_CLIENT_SECRET", c["clientsecret"])
        os.environ.setdefault("CONN_AUTH_URL",      c["token_service_url"])
        os.environ.setdefault("CONN_PROXY_HOST",    c["onpremise_proxy_host"])
        os.environ.setdefault("CONN_PROXY_PORT",    str(c["onpremise_proxy_http_port"]))
        break
```

### Deploy

```bash
cf login -a https://api.cf.us10.hana.ondemand.com --sso   # ALWAYS --sso, never TOTP
cd assets/<agent-name>
cf push
curl https://my-agent.cfapps.<region>.hana.ondemand.com/.well-known/agent.json
```

### Add CORS for browser clients

```python
# app/main.py — after server.build()
from starlette.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["GET","POST","OPTIONS"], allow_headers=["*"])
```

---

## 6a. Alternative Runtime: Kyma

Cloud Foundry is the default above, but the same A2A agent runs unchanged on
**Kyma** (BTP's managed Kubernetes) — the container and code are identical; only
the deployment descriptor changes. Choose Kyma when the customer standardises on
Kubernetes, needs finer scaling/networking control, or CF isn't their runtime.

- **Packaging** — build the agent as a container image; deploy with a Helm chart (Deployment + Service + APIRule to expose the route) or Kustomize overlays per environment.
- **Config & secrets** — the same variables from [§1a](#1a-model-provider-isolation) / Mode C map to a ConfigMap (non-secret) and a Secret (credentials); mount them as env vars. Never bake secrets into the image.
- **Health check** — point the readiness/liveness probe at `/.well-known/agent.json`, same as the CF health check.
- **Route** — an APIRule (or Gateway/VirtualService) publishes the public agent URL that Joule and clients call.

Everything else in this blueprint — connectivity modes, auth, resilience,
observability, Joule registration — is identical on Kyma. The only hard hosting
requirement for any deployment is a subaccount with **Cloud Foundry or Kyma**.

---

## 7. Registering with Joule Studio

### BTP prerequisites

1. **JouleAdmin role collection** assigned to your user:
   - BTP Cockpit → Security → Role Collections → `JouleAdmin` → Users → Add

2. **das-ias IAS tenant account** — Joule uses its own IAS tenant, separate from BTP SSO:
   - Try **Forgot Password** on the Joule login page — if no email arrives, your account doesn't exist in das-ias
   - Ask the Joule admin (visible in BTP → Subscriptions → Joule → Changed By) to create your account

### Register the agent card

In the Joule admin UI:
1. Navigate to **Settings → External Skills** (or **Agents**)
2. Click **Register Agent** / **Add External Skill**
3. Enter agent card URL: `https://my-agent.cfapps.<region>.hana.ondemand.com/.well-known/agent.json`
4. Joule fetches the card, reads `skills[].description` and `tags`, registers automatically

### Joule intent routing

Joule routes user queries to your agent based on the skill description and tags in the agent card. Write these thoughtfully:

```python
# app/main.py
skill = AgentSkill(
    id="my-agent-skill",
    name="My SAP Agent",
    description="Detailed description of what this agent does and when Joule should route to it. "
                "Include domain keywords: procurement, engineering change, cost simulation, etc.",
    tags=["procurement", "engineering", "cost", "simulation", "s4hana"],
    examples=[
        "Simulate the cost impact of retiring process X",
        "What is the financial exposure on open POs for supplier Y?",
    ]
)
```

### `jouleautomation-srv` pattern (automated registration)

Some subaccounts have a `jouleautomation-srv` CF app that handles registration programmatically. If present:
- Start it: `cf start jouleautomation-srv` (requires space memory quota)
- It reads agent card URLs from config and registers them with Joule automatically
- Memory quota issues: stop unused apps or request quota increase from space admin

### CLI-driven capability deployment (Joule Studio CLI)

Beyond the admin UI, Joule Studio supports deploying the agent as a **capability
bundle** via the Joule Studio CLI plus a native BTP destination. This is the
scriptable, repeatable path (and what CI/CD uses).

**Prerequisites:** agent already deployed; BTP roles `extensibility_developer` +
`capabilityadmin`; the Joule Studio CLI (`npm install -g @sap/joule-studio-cli`
— note `@sap/joule-cli` 404s, use `@sap/joule-studio-cli`); `joule login`
succeeded (the App2App IAS flow must be configured on the subaccount); a BTP
Destination service available; tenant on a current Joule capability schema
(DTA schema **3.28.0+**).

**Two descriptors** (generated into `joule-capability/` by the scaffold's default
profile):
- `capability.sapdas.yaml` — capability metadata + system aliases. The destination `ALIAS_NAME` must match `system_aliases.<AliasName>.destination`.
- `da.sapdas.yaml` — the top-level deployment descriptor passed to `joule deploy`.

**Create the destination, then deploy:**

```bash
# 1. Create a native BTP HTTP destination pointing at the deployed agent route.
#    (NoAuthentication for the destination itself; the agent enforces its own auth.)

# 2. Compile + publish the capability bundle:
cd <agent-name>/joule-capability
joule deploy ./da.sapdas.yaml --compile -n "<assistant_name>"
```

**Verify:**

```bash
curl -s https://<agent-route>/.well-known/agent.json | jq .name
# Then send a matching prompt in the Joule UI and confirm the task arrived:
cf logs <agent-name> --recent | grep "task received"
```

**Troubleshooting (common):**
- `Schema version ... greater than the current schema version of Joule` → tenant DTA schema too old; request a Joule service update.
- `namespace validation error` → `metadata.namespace` must be `joule.ext`.
- `401` from Joule → re-run `joule login`; verify `extensibility_developer` + `capabilityadmin`.
- `joule login` fails → App2App IAS flow not configured for the CLI on the subaccount (a one-time IAS admin action).

**Cleanup:** `joule undeploy <capability-id>`.

---

## 8. Protocols and Endpoints

### `/.well-known/agent.json` — A2A agent discovery

```
GET /.well-known/agent.json
```

Returns the agent card. Used by Joule, other agents, and automated discovery tools. The health check in `manifest.yml` polls this endpoint.

### `POST /` — A2A request/response

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "<uuid-required>",
      "contextId": "<uuid-optional-for-multi-turn>",
      "role": "user",
      "parts": [{"kind": "text", "text": "Your query here"}],
      "metadata": {
        "mock": true,
        "sap_mode": "onprem"
      }
    }
  },
  "id": "1"
}
```

> ⚠️ `messageId` is required by the A2A protocol — requests without it return a validation error.

### `POST /` with `message/stream` — SSE streaming

Same payload, different method. Returns Server-Sent Events:

```
data: {"result": {"kind": "status-update", "status": {"state": "working",
       "message": {"parts": [{"text": "Retrieving PO data from SAP..."}]}}}}

data: {"result": {"kind": "artifact-update", "artifact": {"parts": [{"text": "## Simulation Report..."}]}}}

data: {"result": {"kind": "status-update", "status": {"state": "completed"}}}
```

Use streaming to show live progress — each SAP tool call emits a `working` status update via `astream_events()` in the agent:

```python
async for event in graph.astream_events(..., version="v2"):
    if event["event"] == "on_tool_start":
        yield _working(f"Retrieving {tool_name} from SAP...")
```

### `GET /ui` — Browser test interface

A self-contained HTML file served directly by the agent for human-readable testing. **Low priority** — build last, use primarily for demos and manual testing. The real interface is the A2A endpoint.

⚠️ Embedding the /ui HTML/JS in a Python string — avoid the silent-failure traps (any Python version):

> 1. Don't rely on Python's backslash handling in embedded JS. \n, \, \|, \s, \d in a normal string are invalid escape sequences — a DeprecationWarning on Python 3.6+, and silent mangling / hard error on 3.12→3.14 — so JS regex like s.replace(/\n/g,'
') arrives garbled and throws a silent parse error that kills the whole

### Future: `/v1/chat/completions` — OpenAI-compatible

For clients using the OpenAI SDK. Not currently exposed by the bootstrap. Add as a thin wrapper around the agent's `invoke()` method when needed.

### Future: `/mcp` — Expose as MCP tool server

For composability — other agents or LLM applications can call your agent as a tool. Not currently exposed. Add using `FastMCP` when your agent needs to be consumed by other orchestrators.

---

# Part C — Future Migration to Joule 2.0

## 9. Joule 2.0 Migration Path

### What changes in Joule 2.0

Joule 2.0 (roadmap) makes custom agents first-class Joule skills — no separate CF deployment required. The A2A protocol becomes the native communication layer, and `asset.yaml` ORD IDs become the standard registration format.

| Today (Joule Studio) | Joule 2.0 |
|---|---|
| Agent runs as separate CF app | Agent hosted natively or as CF app |
| Register via Joule admin UI | Automatic from `asset.yaml` ORD IDs |
| Agent Gateway optional | Agent Gateway standard — Destination path still valid |
| A2A via HTTP | A2A native in Joule runtime |

### What does NOT change

**Zero code changes required for migration:**
- System prompt (`app/agent.py`)
- Tool adapters (`app/tools/*.py`)
- Business logic (`app/logic/*.py`)
- Tests — all pass unchanged
- `asset.yaml` ORD ID format — identical

### Migration steps

```
Step 1 — Verify Agent Gateway registration
  All SAP APIs registered with correct ORD IDs
  (scripts/register_mcp_servers.py --list)

Step 2 — Confirm asset.yaml ORD IDs
  These are already the Joule 2.0 registration format
  No changes needed

Step 3 — Test in Joule 2.0 sandbox (when available)
  Point Joule 2.0 at the same CF app URL
  Same /.well-known/agent.json, same A2A endpoint

Step 4 — Remove Destination + Connectivity if not needed
  Once Agent Gateway handles all routing, mcp_tools.py
  and the 3-step auth chain are optional infrastructure
  Agent code unchanged — just stop binding the services

Step 5 — Re-register in Joule 2.0 catalog
  Point to same CF app URL or native hosting
  ORD IDs in asset.yaml are the registration key
```

### Keeping Destination mode in Joule 2.0

Even in Joule 2.0, the Direct (Destination + Connectivity) mode remains valid for:
- On-premise systems that aren't registered in Agent Gateway
- Custom SAP endpoints outside the standard ORD catalog
- Explicit control requirements

The `SAP_MODE` switch continues to work identically.

---

## 10. Event-Driven Triggers (optional)

Replace manual user queries with automated business event triggers.

### Architecture

```
SAP Backend → SAP Event Mesh → Listener App → POST to Agent A2A endpoint
```

### Setup

1. **Create a dedicated Event Mesh instance** (never update shared ones):
   ```bash
   cf create-service enterprise-messaging default my-agent-eventmesh -c '{
     "emname": "my-agent-events",
     "version": "1.1.0",
     "namespace": "sap/mycompany/myagent",
     "rules": {
       "queueRules": {"subscribeFilter": ["po/*"]},
       "topicRules": {
         "publishFilter": ["po/*"],
         "subscribeFilter": ["po/*"]
       }
     }
   }'
   ```
   - ⚠️ Never run `cf update-service` on a shared Event Mesh instance — it affects all bindings. Always create a dedicated instance.

2. **Create queue + topic subscription** in Event Mesh dashboard (BTP Cockpit)

3. **Deploy listener** (separate lightweight CF app):
   ```python
   # Polls queue, calls agent when event arrives
   def call_agent(event_payload):
       supplier = event_payload.get("SupplierID", "")
       query = f"A business change was detected for supplier {supplier}. Assess the financial impact."
       requests.post(AGENT_URL + "/", json={
           "jsonrpc": "2.0", "method": "message/send",
           "params": {"message": {
               "messageId": str(uuid.uuid4()), "role": "user",
               "parts": [{"kind": "text", "text": query}],
               "metadata": {"sap_mode": "onprem"}
           }},
           "id": "1"
       })
   ```

4. **Configure SAP backend** to publish events (SAP Basis task: `/IWXBE/CONFIG`)

---

## 11. Optional Capabilities

Extend the base agent with additional data sources and knowledge — each is
opt-in, added behind the same tool boundary, and never required to ship an MVP.

### Knowledge / semantic search (HANA Vector Store — "HVS")

When the agent must answer from documents or policies (not just live
transactional records), add a vector-search tool backed by SAP HANA Cloud's
vector engine: embed the source documents, store the vectors in HANA, and expose
a retrieval tool the agent calls to ground its answers.

```bash
HANA_HOST=<hana-host>
HANA_PORT=443
HANA_USER=<user>
HANA_PASSWORD=<secret>
```

Use it for policy Q&A, product/spec lookup, or any retrieval-augmented answer.
The retrieval tool follows the same interface/mock/live pattern as any other tool.

### SuccessFactors (SF)

Add HR data (e.g. leave balances, org data) by wiring an SF OData tool — same
pattern as the S/4HANA tool in [§3](#3-connect-sap-data--three-modes):

```bash
SF_BASE_URL=https://<api-host>/odata/v2
SF_API_KEY=<or the auth vars your tool needs>
```

### Other backends

Ariba, Concur, or any HTTP/OData API attach the same way — one tool per backend,
credentials behind the boundary, mock-first then live. Describe the backend and
its key entities, and the tool is generated to match.

---

## 12. Reference Agents (worked examples)

Two end-to-end examples show the full scaffold → connect → run shape:

- **Supply Chain Risk Agent** — full-stack agent that reads live S/4HANA data (purchase orders, business partners), fetches supplier news via an external API, and synthesises a risk briefing with Claude via AI Core. Thread-based UI with real-time tool-call progress, structured risk cards, and charts. A good pattern source for a live S/4HANA tool.
- **Service Technician Companion** — field-service agent for S/4HANA plant maintenance (equipment, maintenance orders, notifications). Uses the public SAP API Business Hub sandbox, so it runs without a customer tenant — ideal for a no-tenant demo.

Each is self-contained and documents its own run/deploy steps; use them as
templates when connecting a new domain in [§3](#3-connect-sap-data--three-modes).

---

## Quick Reference

### Which SAP connectivity mode should I use?

```
Is Agent Gateway entitled in this BTP subaccount?
  YES, and I want managed auth + standard routing → SAP_MODE=gateway
  NO, or I need explicit control → ↓

Is this S/4HANA Cloud?
  YES → SAP_MODE=cloud (CE_* and API_* OData v4 services)
  NO  → SAP_MODE=onprem (MM_*, PLM_* OData v2 services)
         Discover entity set names via /IWFND/MAINT_SERVICE first
```

### Which endpoint should I call?

```
Discover agent capabilities?    → GET /.well-known/agent.json
Single query, wait for result?  → POST / with message/send
Show live progress steps?       → POST / with message/stream
Human browser-based testing?    → GET /ui (deploy last, low priority)
Automated business trigger?     → Event Mesh listener → POST /
```

### Environment variable quick reference

| Variable | Values | Effect |
|---|---|---|
| `IBD_TESTING` | `1` / unset | `1` = mock mode everywhere |
| `SAP_MODE` | `gateway` / `cloud` / `onprem` | Primary connectivity choice |
| `AGENT_MODEL` | `sap/anthropic--claude-3.5-sonnet` | LLM model |
| `AICORE_*` | From AI Core service key | SAP AI Core auth |
| `DEST_*` | From Destination service key | Destination Service (Mode C) |
| `CONN_*` | From Connectivity service key | Connectivity proxy (Mode C) |
| `AGW_CREDENTIALS_JSON` | From Agent Gateway service key | Agent Gateway (Mode B) |

---

### Glossary

| Term | Meaning |
|---|---|
| **A2A** | Agent-to-Agent protocol — JSON-RPC over HTTP, the standard agent communication layer; native in Joule 2.0 |
| **AGW** | Agent Gateway — BTP service that proxies auth + routing to SAP APIs (Mode B) |
| **ORD** | Open Resource Discovery — the ID scheme (`sap.s4:apiResource:...`) used in `asset.yaml`; the Joule 2.0 registration key |
| **EDMX** | OData metadata document describing entity sets and properties; input to the MCP translation pipeline |
| **MCP** | Model Context Protocol — how tools are described and invoked by the agent |
| **IAS** | Identity Authentication Service — SAP's identity provider; Joule uses a separate `das-ias` tenant |
| **XSUAA** | SAP's OAuth/JWT authorization service on BTP; validates incoming tokens (3a) |
| **VCAP_SERVICES** | Env var CF injects with bound service credentials |
| **SCC** | SAP Cloud Connector — secure tunnel to on-prem SAP; used by the connectivity proxy (Mode C) |
| **GenAI Hub** | SAP AI Core's Generative AI Hub — provides LLM access (Claude/GPT) via LiteLLM |
| **CF** | Cloud Foundry — the BTP runtime the agent deploys to |

---

## Agent-PathToProd

One master checklist — from zero to Joule-registered production. Each item is tagged:

[code] — Claude Code validates this when generating the agent
[deploy] — Developer validates this when building/deploying

Each gate must pass before the next stage starts.

---

Stage 0 — Pre-build validation
[ ] [deploy] SAP API usage clause confirmed with product team
[ ] [deploy] Agent Gateway entitlement checked: cf marketplace | grep agent-gateway
[ ] [deploy] Joule IAS (das-ias) account exists
[ ] [deploy] JouleAdmin role collection assigned to your BTP user
[ ] [deploy] Space Developer CF role granted
[ ] [deploy] Memory quota confirmed ≥ 512M
[ ] [deploy] Identity model decided: technical user vs. principal propagation

Stage 1 — Scaffold & mock
[ ] [deploy] sap-agent-bootstrap run
[ ] [code] Exactly three mandatory decorators; @agent_config = temperature only
[ ] [code] No invented imports; [illustrative] samples reconciled against scaffold
[ ] [deploy] mcp-mock.json created; responses deterministic
[ ] [code] IBD_TESTING=1 honored everywhere — mock works fully offline
[ ] [deploy] Tests pass; coverage ≥ 70%; agent card returns valid JSON
[ ] [code] System prompt has all 6 MANDATORY RULES + disclaimer
[ ] [deploy] Prompt versioned + golden set eval passes

Stage 2 — SAP connectivity
[ ] [deploy] EDMX downloaded; MCP translation files generated
[ ] [deploy] Connectivity mode configured (A/B/C)
[ ] [deploy] On-prem entity set names verified via /IWFND/MAINT_SERVICE
[ ] [code] SAP_MODE switch + per-request metadata override wired
[ ] [code] asset.yaml present with correct ORD IDs

Stage 3 — Auth & resilience hardening
[ ] [deploy] XSUAA instance created + bound in manifest.yml
[ ] [code] JWT validated at A2A boundary; identity never from client metadata
[ ] [deploy] Destination Authentication type matches identity model
[ ] [code] Error taxonomy handled; no raw traces to users; retry GETs only
[ ] [code] Advisory-only: no POST/PATCH/DELETE; top=100; never fabricate
[ ] [code] Conversation state externally persisted, keyed by contextId + user identity
[ ] [code] Token-window cap + tool-payload summarization in place

Stage 4 — Observability & security
[ ] [deploy] application-logs bound; CF log drain + 403/404 alerts configured
[ ] [code] Structured logs: correlation_id, tool_name, sap_mode, tokens, latency
[ ] [code] PII redacted; prompt version stamped in logs
[ ] [code] No credentials committed; .env gitignored; VCAP bindings in prod
[ ] [deploy] CORS + rate limiting hardened for external exposure

Stage 5 — Cloud Foundry deployment
[ ] [code] manifest.yml: 512M, health-check on /.well-known/agent.json, SAP_MODE, AGENT_PUBLIC_URL
[ ] [code] VCAP_SERVICES mapped before imports; messageId required on inbound
[ ] [deploy] cf login --sso; cf push succeeds; agent card live on CF URL
[ ] [code] Agent card skills[].description + tags written for Joule intent routing

Stage 6 — Joule Studio registration
[ ] [deploy] Agent card URL registered in Joule admin UI
[ ] [deploy] Joule routes a test query; valid response received
[ ] [deploy] asset.yaml ORD IDs confirmed as Joule 2.0 registration keys

Stage 7 — Production readiness sign-off
[ ] [deploy] Data residency: AI Core region matches SAP system's requirements
[ ] [deploy] Human reviewer verified disclaimer present on all financial outputs
[ ] [deploy] Incident response contacts known (Basis for 403s, SCC admin for proxy)
[ ] [deploy] Event Mesh listener deployed if event-driven triggers needed

Stage 8 — Joule 2.0 migration readiness
[ ] [deploy] AGW registration verified: scripts/register_mcp_servers.py --list
[ ] [deploy] asset.yaml ORD IDs correct — no code changes needed for Joule 2.0
[ ] [deploy] Agent tested against Joule 2.0 sandbox when available
[ ] [deploy] Destination + Connectivity kept/removed based on AGW coverage

---
---
