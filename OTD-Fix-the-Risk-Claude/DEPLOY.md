# DEPLOY.md — OTD-Fix-the-Risk (Claude-backed, Joule-frontable)

> **Gated runbook.** Nothing here has been executed. Deploying to any runtime,
> registering with Joule, or calling a live SAP tenant happens **only on your
> explicit go-ahead**. Steps that leave your machine or incur cost are marked
> **[GATED]**.

## What this deployment is (and is not)

This packages the OTD agent to run its **LLM reasoning on the Anthropic API
directly** (off SAP AI Core / Gen AI Hub), while remaining a standard **A2A
agent that Joule can front** via its agent card.

Two LLM routing modes are available (selected via `OTD_LLM_ROUTE`):

| Mode | Value | LLM path | Governance |
|---|---|---|---|
| **Direct** (default) | `direct` | Anthropic API via LiteLLM + `ANTHROPIC_API_KEY` | ⚠️ Deviation — needs exception before production |
| **AI Core** (compliant) | `aicore` | SAP Gen AI Hub → AI Core → AWS Bedrock | ✅ Golden Path — set for production |

The `aicore` path targets deployment **`d009d0ca6a44ae29`** at
`https://api.ai.prod.us-east-1.aws.ml.hana.ondemand.com`.
Credentials come from `AICORE_*` env vars (service key from BTP cockpit).

**In scope for the Claude deployment:** the A2A server, LLM routing to Anthropic,
tools (mock now / read-only OData bridge later), identity propagation scaffold,
and — optionally, gated — registering the agent card with Joule.

**NOT in scope (these stay entirely on the Joule side and are untouched here):**

| Joule-platform concern | Handled here? |
|---|---|
| Joule Space configuration | No |
| Joule Project metadata | No |
| Joule UI artifacts | No |
| Private Environment settings | No |
| Generated test environment settings | No |

Running off SAP AI Core is a **governance deviation** (metering, Safety
Dashboard, Golden Path). See `agent-outcome-report.md` for the flagged controls
and required remediation (exception request + security review) before any
production use.

---

## 0. Prerequisites

- Python 3.11+
- **For `OTD_LLM_ROUTE=direct`:** an Anthropic API key (`ANTHROPIC_API_KEY`).
  Reasoning billed by Anthropic; governance deviation (see §4 and
  `agent-outcome-report.md`).
- **For `OTD_LLM_ROUTE=aicore` (recommended for production):** an AI Core
  service key from BTP → Instances and Subscriptions → your AI Core instance →
  Service Keys. Provides `clientid`, `clientsecret`, `url`, and the AI API URL.
- `cp .env.example .env` and fill it in. Secrets live in `.env` only.

## 1. Install

Windows note: install the venv at a **short path** (e.g. `C:\otdv`) — the deep
OneDrive path + litellm's nested files can exceed the 260-char limit.

```bash
python -m venv /c/otdv
/c/otdv/Scripts/python -m pip install -r assets/otd-fix-the-risk-agent/requirements.txt
```

## 2. Run locally — offline mock mode (no SAP, no credentials)

```bash
cd assets/otd-fix-the-risk-agent
IBD_TESTING=1 ANTHROPIC_API_KEY=sk-... python app/main.py --port 5000
```

- Tools come from `mcp-mock.json` (deterministic fixtures).
- `ANTHROPIC_API_KEY` is needed only for the reasoning step; tool loading and the
  agent card work without it.

Optional demo UI (second shell):

```bash
python demo/serve_demo.py           # → http://localhost:8000
```

## 3. Verify the build

```bash
# Offline test suite (from the agent folder)
cd assets/otd-fix-the-risk-agent
IBD_TESTING=1 /c/otdv/Scripts/python -m pytest        # coverage ≥70%, writes test_report.json

# Agent card is served (Joule discovers the agent via this document)
curl -s http://localhost:5000/.well-known/agent-card.json | head

# Confirm no write-capable tool is ever registered (expect only read/readByKey/metadata)
/c/otdv/Scripts/python -m bridge.odata_mcp_server --list-tools   # run from app/ dir
```

## 4. Run locally — live mode (read-only OData) **[GATED]**

Only once you have a tenant + credentials.

**4a. Configure `.env`** (secrets live here only).

*Default — `direct` mode (Anthropic API, fastest live test but governance deviation):*

```bash
OTD_LLM_ROUTE=direct
ANTHROPIC_API_KEY=sk-ant-...
OTD_TOKEN_EXCHANGE_MODE=basic
OTD_S4_USER=<S/4HANA Cloud communication user>
OTD_S4_PASSWORD=<its password>
OTD_SERVICE_BASE_URLS={"sap.s4:apiResource:CE_SALESORDER_0001:v1":"https://<s4-host>/sap/opu/odata4/sap/api_salesorder/srvd_a2x/sap/salesorder/0001","sap.s4:apiResource:WAREHOUSEAVAILABLESTOCK_0001:v1":"https://<s4-host>/sap/opu/odata4/sap/api_warehouse_available_stock/srvd_a2x/sap/warehouseavailablestock/0001","sap.s4:apiResource:API_PRODUCTION_ORDER_2_SRV:v1":"https://<s4-host>/sap/opu/odata/sap/API_PRODUCTION_ORDER_2_SRV","sap.s4:apiResource:API_OUTBOUND_DELIVERY_SRV_0002:v2":"https://<s4-host>/sap/opu/odata/sap/API_OUTBOUND_DELIVERY_SRV;v=0002","sap.s4:apiResource:CE_FREIGHTORDER_0001:v1":"https://<s4-host>/sap/opu/odata4/sap/api_freightorder/srvd_a2x/sap/freightorder/0001"}
```

*Recommended for production — `aicore` mode (SAP Gen AI Hub, Golden Path):*

```bash
OTD_LLM_ROUTE=aicore
AICORE_BASE_URL=https://api.ai.prod.us-east-1.aws.ml.hana.ondemand.com
AICORE_AUTH_URL=https://<subaccount>.authentication.<region>.hana.ondemand.com/oauth/token
AICORE_CLIENT_ID=<clientid from service key>
AICORE_CLIENT_SECRET=<clientsecret from service key>
AICORE_RESOURCE_GROUP=default
AICORE_DEPLOYMENT_ID=d009d0ca6a44ae29
OTD_TOKEN_EXCHANGE_MODE=basic
OTD_S4_USER=<S/4HANA Cloud communication user>
OTD_S4_PASSWORD=<its password>
OTD_SERVICE_BASE_URLS={...same map as above...}
```

The service key JSON fields map to env vars as: `clientid` → `AICORE_CLIENT_ID`,
`clientsecret` → `AICORE_CLIENT_SECRET`, `url` → `AICORE_AUTH_URL` (append
`/oauth/token`), the AI API URL → `AICORE_BASE_URL`.
Alternatively, paste the entire service key JSON as `AICORE_SERVICE_KEY`.

The communication user must be assigned (via a Communication Arrangement) to the
inbound services exposing these 5 OData APIs, else calls return `403`. Every call
acts as this one identity (no per-user RBAC) — a documented deviation from the
production principal-propagation model (see `agent-outcome-report.md` §4).

**4b. Smoke-test connectivity first (read-only — one `$metadata` GET per service):**

```bash
cd assets/otd-fix-the-risk-agent
set -a; . ../../.env; set +a          # load .env into the shell
PYTHONPATH=app /c/otdv/Scripts/python -m bridge.odata_mcp_server --smoke
# principal-propagation Destination? add: --token "<an-end-user-JWT>"
```

Expect `OK` for each of the 5 services and `5/5 services reachable`. This proves
the base URLs + Destination auth before you start the full agent.

**4c. Run the agent live** (note: **no** `IBD_TESTING`):

```bash
cd assets/otd-fix-the-risk-agent
set -a; . ../../.env; set +a
ANTHROPIC_API_KEY=sk-ant-... /c/otdv/Scripts/python app/main.py --port 5000
```

The bridge issues **GET only** and refuses any non-read operation — the zero-write
guarantee holds on the live path by construction.

## 5. Host the A2A agent **[GATED]**

Any runtime that can serve the Starlette/uvicorn app over HTTPS works (container,
BTP Cloud Foundry/Kyma, VM). Required env: `ANTHROPIC_API_KEY`, `AGENT_PUBLIC_URL`
(the externally reachable base URL), plus the live `OTD_SERVICE_*` / token-exchange
config. Expose:

- `GET /.well-known/agent-card.json` — the agent card
- `POST /` — the A2A JSON-RPC endpoint

## 6. Register with Joule **[GATED]**

Joule fronts external A2A agents by discovering their agent card. With the agent
hosted at a reachable HTTPS URL:

1. Confirm `AGENT_PUBLIC_URL` matches the public endpoint and the card resolves.
2. Register the agent card / ORD `kind: agent` metadata in your Joule tenant per
   your org's Joule onboarding process.
3. Smoke-test one of the card's example prompts through Joule.

This is the **only** Joule touchpoint — no Space, project, UI, or environment
configuration is created or modified by this port.

## 7. Rollback

- Mock mode: stop the process. Nothing persisted (in-memory task store + checkpointer).
- Live mode: stop the process; no SAP writes are ever made, so there is nothing to
  reverse in SAP.
- Joule: de-register the agent card in your Joule tenant.

## 8. Deploy to Cloud Foundry (BTP) **[GATED]**

The app is CF-ready: it reads the injected `$PORT`, binds `0.0.0.0`, and ships a
`manifest.yml` + `Procfile` in `assets/otd-fix-the-risk-agent/`. Secrets are **not**
in the manifest — they go in via `cf set-env` / service bindings.

**8a. (Only for the `destination`/`xsuaa` upgrade paths) create + bind the platform
services.** The default `basic` mode needs **no** service bindings — skip to 8b.
With a bound `destination` service, `token_exchange` reads it from `VCAP_SERVICES`
and you only need `BTP_DESTINATION_NAME` — no pasted token.

```bash
cf create-service destination        lite   otd-destination
cf create-service connectivity       lite   otd-connectivity
cf create-service xsuaa  application         otd-xsuaa   -c xs-security.json
# then uncomment the `services:` block in manifest.yml
```

(If S/4 is on-premise, the `connectivity` service + a configured **Cloud Connector**
are what bridge the CF app to the on-prem system.)

**8b. Push** (from the agent directory):

```bash
cd assets/otd-fix-the-risk-agent
cf push -f manifest.yml
```

**8c. Set the secrets / env-specific values** (never in the manifest), then restage.
The manifest defaults `OTD_TOKEN_EXCHANGE_MODE=basic` and `OTD_LLM_ROUTE=direct`.

*For `OTD_LLM_ROUTE=direct` (Anthropic API, governance deviation):*

```bash
cf set-env otd-fix-the-risk-agent ANTHROPIC_API_KEY      "sk-ant-..."
cf set-env otd-fix-the-risk-agent OTD_S4_USER            "<communication user>"
cf set-env otd-fix-the-risk-agent OTD_S4_PASSWORD        "<its password>"
cf set-env otd-fix-the-risk-agent OTD_SERVICE_BASE_URLS  '{"sap.s4:apiResource:CE_SALESORDER_0001:v1":"https://<s4-host>/...", ...}'
cf set-env otd-fix-the-risk-agent AGENT_PUBLIC_URL        "https://<the-assigned-route>/"
cf restage otd-fix-the-risk-agent
```

*For `OTD_LLM_ROUTE=aicore` (SAP Gen AI Hub — Golden Path, recommended for production):*

```bash
cf set-env otd-fix-the-risk-agent OTD_LLM_ROUTE           "aicore"
cf set-env otd-fix-the-risk-agent AICORE_BASE_URL          "https://api.ai.prod.us-east-1.aws.ml.hana.ondemand.com"
cf set-env otd-fix-the-risk-agent AICORE_AUTH_URL          "https://<subaccount>.authentication.<region>.hana.ondemand.com/oauth/token"
cf set-env otd-fix-the-risk-agent AICORE_CLIENT_ID         "<clientid from service key>"
cf set-env otd-fix-the-risk-agent AICORE_CLIENT_SECRET     "<clientsecret from service key>"
cf set-env otd-fix-the-risk-agent AICORE_RESOURCE_GROUP    "default"
cf set-env otd-fix-the-risk-agent AICORE_DEPLOYMENT_ID     "d009d0ca6a44ae29"
cf set-env otd-fix-the-risk-agent OTD_S4_USER              "<communication user>"
cf set-env otd-fix-the-risk-agent OTD_S4_PASSWORD          "<its password>"
cf set-env otd-fix-the-risk-agent OTD_SERVICE_BASE_URLS    '{"sap.s4:apiResource:CE_SALESORDER_0001:v1":"https://<s4-host>/...", ...}'
cf set-env otd-fix-the-risk-agent AGENT_PUBLIC_URL          "https://<the-assigned-route>/"
cf restage otd-fix-the-risk-agent
```

Alternatively for `aicore`, paste the whole service key JSON as one variable instead
of the four individual vars: `cf set-env ... AICORE_SERVICE_KEY '{...}'`.

For the `destination` upgrade path instead, set `OTD_TOKEN_EXCHANGE_MODE=destination`
+ `BTP_DESTINATION_NAME` (with the bound service from 8a), or — off the bound
service — also `BTP_DESTINATION_URL` + `BTP_DESTINATION_TOKEN`; the module falls
back to those when `VCAP_SERVICES` has no `destination` binding.

**8d. Verify:**

```bash
cf app otd-fix-the-risk-agent                                   # running, health check green
curl -s https://<route>/.well-known/agent-card.json | head       # agent card served
```

The health check hits `/.well-known/agent-card.json`, which works without a live
tenant — so the app goes healthy even before S/4 connectivity is proven. Confirm
real data separately by asking a question end-to-end. Zero-write still holds: the
bridge issues GET only.
