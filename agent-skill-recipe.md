# Build & Publish a Joule Skill

> **What this covers.** How to build a **Joule skill** and publish it so it is callable from the Joule consumer experience — the piece the rest of this blueprint referenced but did not spell out. Two supported paths: **low-code** (Joule Studio Skill Builder) and **pro-code** (a `.sapdas.yaml` capability bundle wired to an A2A agent).
>
> **Where this sits.** A *skill* is a single capability Joule can route to. A *full agent* (the subject of [`README.md`](README.md)) can expose one or more skills. If your task is "add one skill to Joule," start here. If it is "build a production agent," build the agent per `README.md` first, then use the **pro-code** path below to surface its skills in Joule.
>
> Grounded in the SAP CoE cookbook's `sap-joule-capability` skill and its `recipes/03-joule` (`wire an A2A agent into Joule`). Follow those canonical sources for the newest schema; this recipe is the followable walkthrough.

---

## 0. Which path?

| Path | Use when | Build surface | Output |
|---|---|---|---|
| **Low-code — Joule Studio Skill Builder** | Business/functional skill that maps to a backend API; no custom runtime; fastest | Joule Studio → Skill Builder (UI) | A published skill, auto-registered in the Skills Governance catalogue (L0-6.2 / L0-6.4) |
| **Pro-code — capability bundle** | The skill is served by a custom A2A agent (custom logic, tools, grounding) | `.sapdas.yaml` files + `joule` CLI | A deployed Joule **capability** that routes intents to your agent's A2A skill |

> Both paths satisfy checklist control **L0-6.2 Skill Builder in Joule Studio**. The pro-code path additionally consumes the agent you built in `README.md` Parts A–B.

---

## 1. Prerequisites (both paths)

- **Region check.** Joule is not GA everywhere (GA in `eu10`; rolling out; **not GA** in `cn40` / NS2 / KSA non-regulated — see [`README.md` §1c](README.md)). Run the region preflight before promising a customer. Where Joule isn't GA, surface the skill via a UI5 chat shell instead.
- **BTP roles:** `extensibility_developer` + `capabilityadmin` (pro-code); Skill Builder access in Joule Studio (low-code).
- **`das-ias` account** — Joule uses its own IAS tenant (see [`README.md` §7](README.md)).
- **Joule Studio CLI** (pro-code): `npm install -g @sap/joule-studio-cli` — note `@sap/joule-cli` 404s; use `@sap/joule-studio-cli`. Then `joule login` (the App2App IAS flow must be configured on the subaccount).
- **Joule capability schema:** tenant on **DTA schema 3.28.0+**.

---

## 2. Low-code path — Joule Studio Skill Builder

For a skill that maps directly to a backend API, with no custom runtime.

1. **Open Joule Studio → Skill Builder** and create a new skill.
2. **Declare the skill contract** — each skill maps to backend API(s) with a **declared scope**. Provide:
   - **Input schema** — the parameters the skill accepts (name, type, required, description).
   - **Output schema** — the shape of the response the skill returns.
   - **Error handling** — expected error states and user-facing messages.
   - **Latency SLA** — the response-time budget (used later by L0-8 performance gates).
3. **Bind the backend** — point the skill at its API/destination; least-privilege scope only.
4. **Add example utterances** — the natural-language phrases that should route to this skill (Joule uses these for intent routing — write them the way a user actually asks).
5. **Test in Skill Builder** — exercise happy path + at least one error path against the declared schemas.
6. **Publish** — the skill is registered and appears in the **Skills Governance** catalogue (L0-6.4, feature **J2259**) with version control and access policy.

> Governance: a skill built **outside** Joule Studio needs an exception + security review (L0-6.1). The Skill Builder path is the default because registration/governance is automatic.

---

## 3. Pro-code path — capability bundle for an A2A agent

Use this when the skill is served by a custom agent you built per [`README.md`](README.md). You ship a `joule-capability/` directory of four `.sapdas.yaml` files; Joule consumes them via `joule deploy`.

### 3.1 Bundle layout

```
joule-capability/
├── capability.sapdas.yaml         # who the agent is, where its Agent Card lives
├── _da.sapdas.yaml                # which Joule surfaces it appears in
├── scenarios/
│   └── default.sapdas.yaml        # intents → functions
└── functions/
    └── <name>.sapdas.yaml         # each function maps to one A2A skill id
```

The scaffold's default `genai-hub` profile generates this folder for you.

### 3.2 `capability.sapdas.yaml`

```yaml
apiVersion: joule.ext/v1
kind: Capability
metadata:
  name: my-first-agent
  namespace: joule.ext          # must be joule.ext, or you get a namespace validation error
spec:
  agentCardUrl: https://my-first-agent.<your-cf-domain>/.well-known/agent.json
  authMode: oauth2-client-credentials      # OR `ias` for prod
  scenarios: [default]
```

### 3.3 `_da.sapdas.yaml` (Digital Assistant binding)

```yaml
apiVersion: joule.ext/v1
kind: DigitalAssistant
metadata: { name: my-first-agent-da }
spec:
  surfaces: [joule-code-editor, joule-sidebar-erp]
  capabilityRef: my-first-agent
```

### 3.4 `scenarios/default.sapdas.yaml`

```yaml
apiVersion: joule.ext/v1
kind: Scenario
metadata: { name: default }
spec:
  intents: ["@my-first-agent *"]
  fallback: true
  functions: [echo]
```

### 3.5 `functions/<name>.sapdas.yaml` — the skill

Each **function** is a Joule-callable skill mapped to an A2A skill id on your agent.

```yaml
apiVersion: joule.ext/v1
kind: Function
metadata: { name: echo }
spec:
  description: "Echo what the user said"      # Joule uses this + examples for routing
  examples: ["say PONG"]
  a2aSkillId: echo            # MUST match AgentSkill(id="echo") in app/agent_card.py
```

> **The critical link:** `a2aSkillId` must equal the `id` of an `AgentSkill(...)` in your agent's `app/agent_card.py` (see [`README.md` §7 intent routing](README.md)). A mismatch registers the function but returns **404** on invocation.

### 3.6 Deploy & publish

```bash
joule login
# From the agent folder:
cd my-first-agent/joule-capability
joule deploy ./da.sapdas.yaml --compile -n "<assistant_name>"
# or, deploying the whole bundle directory:
joule deploy ./joule-capability
```

### 3.7 Verify

```bash
# Agent Card must be publicly reachable (Joule discovers it):
curl -s https://<agent-route>/.well-known/agent.json | jq .name

joule list capabilities | grep -E "my-first-agent.+ACTIVE"
joule invoke --capability my-first-agent --text "say PONG"     # expect: response containing PONG

# In the Joule UI, send a matching prompt and confirm the task arrived:
cf logs <agent-name> --recent | grep "task received"
```

**Cleanup:** `joule undeploy <capability-id>`.

---

## 4. Integration paths (pro-code)

| Path | When | How |
|---|---|---|
| **1 · Direct A2A** | one agent, synchronous, < 60s | `authMode: oauth2-client-credentials`, agent on CF/Kyma |
| **2 · BPA-async** | long-running work | capability targets a Business Process Automation process; agent works, callback to BPA |
| **3 · Multi-agent front-door (proxy)** | many agents, central IAS | capability targets a proxy URL; proxy fans out to agents |

---

## 5. Pitfalls (from the CoE skill — check these first when routing fails)

- **`agentCardUrl` behind auth** → Joule can't discover the agent. Keep `/.well-known/agent.json` **public** (the agent still enforces its own auth on `POST /`).
- **`a2aSkillId` mismatch** → function registers but invocation returns **404**. Compare against `AgentSkill(id=...)`.
- **Missing `scenarios` / empty `intents`** → capability registers but Joule won't route to it.
- **`namespace` not `joule.ext`** → namespace validation error at deploy.
- **`Schema version ... greater than current`** → tenant DTA schema too old; request a Joule service update (need 3.28.0+).
- **`401` from Joule** → re-run `joule login`; verify `extensibility_developer` + `capabilityadmin`.

---

## 6. Checklist hooks

- **L0-6.2 Skill Builder in Joule Studio** — satisfied by either path; include I/O schema, error handling, latency SLA.
- **L0-6.1 Agent Builder in Joule Studio** — a skill served by an agent built outside Joule Studio needs an exception + security review.
- **L0-6.4 Skills Governance Agent (J2259)** — published skills are cataloged with version control + access policy.
- **README Stage 6 — Joule Studio registration** — the pro-code path is the scriptable, CI/CD version of that stage.

---

*Canonical sources: CoE cookbook `skills/sap-joule-capability/SKILL.md` and `recipes/03-joule/` (`github.tools.sap/business-ai-platform/Custom-Agentic-solutions-CoE`). See [`references.md`](references.md) for all external pointers.*
