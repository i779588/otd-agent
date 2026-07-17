> Related guidelines: [guidelines-agent.md](guidelines-agent.md) | [guidelines.md](guidelines.md) | [AI Agent Runtime Cost Estimation Guide.md](AI%20Agent%20Runtime%20Cost%20Estimation%20Guide%20v7.md)

# SAP Custom Agent Blueprint: Joule Studio Build & Joule 2.0 Migration Guide

*A neutral, reusable blueprint for building SAP AI agents — from first scaffold to production integration and future migration. Two paths, starting with Joule 2.0 build to custom agent developement and productive deployment on Joule Studio, and then in future migrate back.*

---

## Who This Is For

SAP developers building custom AI agents that need to consume SAP data and integrate with SAP Joule. This guide covers:
- Starting from the Joule Studio scaffold
- Connecting to SAP APIs via three first-class modes
- Deploying to Cloud Foundry and registering in Joule Studio
- Future migration to Joule 2.0 when available

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

## 1b. Road to Production: Key Considerations

Before building, validate these conditions. Discovering them late is expensive.

### SAP API Access

| Checkpoint | How to verify | Comments |
|---|---|---|
| OData Service Usage Clause| `Product Team Gudiance` → [<Gudiance> ](https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf)| IMP: Verifiy with global api policy team |


> Have agreed way ahead with right stakeholders as emails save for reference.


**Recommended for production:**

- **Application Logging** (`application-logs` service) — bind in `manifest.yml` for CF log aggregation
- **Alert on 403/404 tool failures** — set up CF log drain to monitoring; tool access issues need Basis team response
- **Version the system prompt** — track prompt changes that affect simulation outputs

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

> ⚠️ `@agent_config` exposes values to the BTP admin UI. It is intentionally restricted to temperature. All other configuration must be plain Python constants.

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
export AGW_CREDENTIALS_JSON='<service key JSON>'
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

## 7. Registering with Joule Studio

### BTP prerequisites

1. **JouleAdmin role collection** assigned to your user:
   > BTP Cockpit → Security → Role Collections → `JouleAdmin` → Users → Add

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
  Once Agent Gateway handles all routing, m06_tools.py
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
   > ⚠️ Never run `cf update-service` on a shared Event Mesh instance — it affects all bindings. Always create a dedicated instance.

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

# Agent-PathToProd
