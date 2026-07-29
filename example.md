# Example: Build a Custom SAP Agent with the Cookbook — Declarative, No-Code

> **What this file is.** A single, self-contained recipe you can drop into an
> **empty folder** and hand to Claude Code (or any supported coding harness).
> You **declare what you want in an `intent.md` file** (even one line is enough),
> the agent reads it, tells you exactly which values to place in a `.env` file,
> then scaffolds, tests, and launches a working SAP agent for you.
>
> **You do not need to write code, and there is no back-and-forth interview.**
> You state your intent once; the agent captures the details, fills sensible
> defaults, and only comes back to you if something essential is genuinely
> unclear.
>
> **Companion reference:** the full engineering blueprint is
> [`README.md`](README.md) — the "boilerplate cookbook." This `example.md`
> is the *fast, declarative path* that applies that blueprint's best practices
> (auth, resilience, observability, advisory-only governance) for you. You do
> not have to read README.md to use this file; the agent consults it.

---

## 0. How to use this file (60 seconds)

1. Create a **new empty folder**, e.g. `my-agent/`.
2. Copy these files into that folder: **`example.md`**, **`CLAUDE.md`**, and (if
   you have it) **`README.md`**.
3. **Write an `intent.md`** in that folder describing the agent you want (see
   Section 1 for what to put in it — a single sentence is a valid start).
4. Open the folder in Claude Code and say, in your own words:
   *"Read my intent.md and build the agent."*
5. If anything essential is missing, the agent asks — otherwise it tells you
   which values to place in `.env`, then builds.
6. When every check is green, tell the agent to **launch**.

That's it. No step-by-step interview, no special command — you declare intent in
a file, the agent acts on it.

---

## 1. Declare your intent — `intent.md`

Create a file named **`intent.md`** in the folder and describe the agent you
want. **The agent captures the details even from a single line** — the fields
below just help it get more right the first time. Anything you leave out, it
fills with a sensible default (and lists what it assumed).

> ℹ️ **Illustrative example used throughout this file: a Retail agent** (store
> inventory / sales orders). This is only to show what a good intent looks like —
> the agent uses *your* domain from *your* `intent.md`. Retail, Finance, HR,
> Procurement, or anything else all work the same way.

**Minimal `intent.md` (perfectly valid):**

```markdown
Answer store staff questions about stock levels and open sales orders. Start with mock data.
```

**Fuller `intent.md` template (copy, keep what you need, delete the rest):**

```markdown
# Agent intent

## What it's for
- Purpose: Answer store staff questions about stock levels and open sales orders.
- Users: store associates
- Domain / industry: Retail

## Data source
- Mode: mock            # mock | live
- System / API (if live): S/4HANA Sales Orders (API_SALES_ORDER_SRV)
- No tenant? use the free api.sap.com sandbox: yes | no

## Model (LLM)
- Provider: aicore      # aicore | openai-compatible (openai-compatible = sovereign-region path)

## Runtime (later)
- Target: localhost     # localhost | cloud-foundry | kyma  (localhost needs no BTP account)

## Optional capabilities (only if you want them)
- Knowledge / semantic search (HANA Vector Store, "HVS"): no
- SuccessFactors (SF) data: no
- Other backend (Ariba, custom HTTP API, …): none

## Attachments (optional, improves accuracy)
- OData/EDMX spec, API doc, sample data, or policy PDF — see Section 6 for how to attach.
```

**What each field drives:** *Purpose/Users/Domain* → naming, system prompt, and
Joule routing tags. *Data source* → whether tools are mock or wired to a live
backend. *Model* → the `LLM_PROVIDER` switch and which `.env` vars you'll fill.
*Runtime* → deployment target (you can stay local and decide later). *Optional
capabilities* → extra tools the agent adds behind the same boundary. Nothing is
hardcoded — your `intent.md` drives the whole build.

> After reading `intent.md`, the agent restates its understanding + any
> assumptions and defaults in **one short summary**, then proceeds. It only stops
> to ask you if an essential detail is missing or contradictory ("open
> questions"). If everything it needs is present, it just builds.

---

## 2. The `.env` file — what the agent asks you to fill in

The agent **creates a `.env.example`** listing exactly the variables your choices
need, and tells you to copy it to `.env` and paste your values. **You never put
secrets in code or in this file.** The agent's tools read them at runtime.

> The agent only lists the variables relevant to *your* answers. Below is the
> full menu it draws from (from README.md's env reference).

### Always (model access)

```bash
# If you chose AI Core:
AICORE_CLIENT_ID=<from AI Core service key>
AICORE_CLIENT_SECRET=<from AI Core service key>
AICORE_AUTH_URL=<from AI Core service key>
AICORE_BASE_URL=<from AI Core service key>
AGENT_MODEL=sap/anthropic--claude-3.5-sonnet     # or your deployed model

# If you chose OpenAI-compatible / sovereign gateway instead:
LLM_PROVIDER=openai-compatible
MODEL_GATEWAY_URL=https://model-gateway.example.com/v1
MODEL_GATEWAY_API_KEY=<from your secret store>
MODEL_NAME=<model-deployment-name>
```

### If you chose `live` data — S/4HANA (Retail example uses this)

```bash
# Real tenant (basic auth for the demo path):
S4_BASE_URL=https://<your-s4-host>
S4_USERNAME=<user>
S4_PASSWORD=<secret>            # never commit; use a secret store in deployment

# OR the free public sandbox instead (no tenant needed):
S4_BASE_URL=https://sandbox.api.sap.com/s4hanacloud
S4_APIKEY=<key from api.sap.com → "Show API Key">
```

### If you enabled HVS (HANA Vector Store)

```bash
HANA_HOST=<hana-host>
HANA_PORT=443
HANA_USER=<user>
HANA_PASSWORD=<secret>
# (The agent will tell you the exact vars its generated HVS tool expects.)
```

### If you enabled SuccessFactors (SF)

```bash
SF_BASE_URL=https://<api-host>/odata/v2
SF_API_KEY=<or the auth vars the agent specifies>
```

> ⚠️ The agent **must not** proceed to a `live`/HVS/SF test until the matching
> `.env` values are present. It checks, and if something's missing it tells you
> precisely which line to add — it does not guess or fake credentials.

---

## 3. Build flow — the gates (each must go green before the next)

The agent runs this sequence. It reports ✅/❌ at each gate and **stops on ❌**
with the exact fix, so a no-code user is never stuck guessing.

```
Read intent.md    →  restate understanding + assumptions (ask only if essential detail is open)
        ↓
[Gate 1] Scaffold + MOCK          → agent replies on localhost with mock data
        ↓
[Gate 2] .env ready               → required vars present for your choices
        ↓
[Gate 3] Connect data (if live)   → real backend answers a test question
        ↓
[Gate 4] Optional: HVS / SF       → each added capability answers a test question
        ↓
[Gate 5] Best-practice checks     → advisory-only, no-fabrication, disclaimer,
                                     identity validation, structured logs
        ↓
[Gate 6] Domain test run          → e.g. Retail: "stock for item X?" / Finance:
                                     "open AR for customer Y?"  (uses YOUR domain)
        ↓
   ALL GREEN → LAUNCH
```

### Gate 1 — Scaffold + Mock (always first)
The agent scaffolds into your **new sub-folder** with mock tools, so it demos
with no backend. Proof it works:

```bash
# Agent Card resolves:
curl -s http://localhost:8080/.well-known/agent.json | jq .name
```

### Gate 3 — Connect live data (only if you chose `live`)
The agent rewrites the mock tool bodies against your real backend **without
changing** the tool interfaces, system prompt, or Agent Card. Then it sends a
message that **must call the tool** and shows you the real reply.
*Retail proof:* "List open sales orders for store 0001."

### Gate 4 — Optional capabilities (only what you enabled)
- **HVS:** the agent adds a semantic-search tool and proves it with a document question.
- **SF:** the agent adds an SF tool and proves it (e.g. "leave balance for user Z").

### Gate 5 — Best-practice checks (from README.md, automatic)
The agent confirms, per README.md:
- Advisory-only — **no** POST/PATCH/DELETE to SAP.
- Never fabricates document numbers/amounts; `top=100` on list calls.
- Financial outputs end with the standard disclaimer.
- Incoming identity validated at the A2A boundary (not from client metadata).
- Structured logs with correlation IDs; no secrets/PII in logs.

### Gate 6 — Domain test run (uses YOUR domain, not hardcoded)
The agent runs **one or two real questions from your domain** end-to-end (it
takes example questions from your `intent.md` if you gave any, otherwise it
derives them from your purpose):
- *Retail:* "How many units of SKU 12345 are in store 0002?"
- *Finance:* "What's the open AR exposure for customer 100200?"

---

## 4. Launch (only when everything is green)

When Gates 1–6 are ✅, tell the agent:

```
All gates are green. Launch the agent locally and give me the exact command to
start it again myself, plus one sample question I can ask it.
```

If you also chose to deploy to BTP, the agent then walks you through the
deploy + (optional) Joule steps from README.md — but **only after** you confirm,
and it tells you which additional `.env`/service values are needed first. It will
not deploy or register anything without your explicit go-ahead.

---

## 5. Guardrails (what the agent will and won't do)

**Will:**
- Work only inside the new sub-folder it creates in this folder.
- Ask before every non-local or irreversible action (deploy, register, teardown).
- Tell you the exact `.env` line to add whenever a credential is missing.
- Keep all secrets out of code and out of these markdown files.

**Won't:**
- Edit `example.md`, `README.md`, `CLAUDE.md`, or anything outside its sub-folder.
- Touch any other project/repository on your machine.
- Write to SAP systems (advisory-only), fabricate data, or invent credentials.
- Deploy, register in Joule, or spend on paid services without your confirmation.

> If the agent is ever unsure, it should ask you rather than assume — that's the
> intended behavior.

---

## 6. Attaching files (optional, makes the build better)

You don't need any files to start — but if you have them, they make the agent's
tools far more accurate. Useful things to attach:

- An **OData / EDMX spec** (`.edmx` / `.xml`) for your SAP service → the agent
  generates precise tool schemas instead of guessing entity/field names.
- An **API doc or Postman/OpenAPI file** for a custom backend.
- A **sample data file** (`.json` / `.csv`) → better mock data and field mapping.
- **Policy / knowledge documents** (`.pdf` / `.md`) → source material if you
  enabled **HVS** (knowledge search) in your `intent.md`.

**How to attach in Claude Code (any of these work):**

1. **Drag and drop** the file into the chat input box (you can also paste a
   screenshot/image directly).
2. **`@`-mention** the file by path once it's in the folder — e.g.
   `@specs/sales_order.edmx` — to pull it into the agent's context.
3. **Drop the file into the folder** (or a sub-folder like `specs/`) and just
   **tell the agent the filename**; since the folder is already open, it can read it.

> List any such files in your `intent.md` (the **Attachments** field) and share
> them in the folder. Attaching a spec is the single biggest accuracy boost for
> `live` data — but everything still works without it.

### Prompt: attach a spec file at any time

If you want to add a spec **after** the build has started (or add another one),
attach the file (drag-drop / `@`-mention / drop-in-folder) and send this:

```
I'm attaching a spec file: <filename> (e.g. an OData/EDMX or API spec).
Read it, and use it to build or refine the agent's tools — match the real
entity/field names from the spec instead of guessing. Keep everything inside the
agent sub-folder, don't touch the reference files, and after wiring it, re-run
the relevant gate (mock or live) and show me the result before moving on.
```

---

## 7. Quick FAQ

- **How do I start?** Write an `intent.md` in the folder and tell the agent
  *"read my intent.md and build the agent."* No special command, no interview.
- **Where do I give my requirements?** In `intent.md` (Section 1). A single
  sentence works; the fields just help the agent get more right the first time.
- **What if I leave things out?** The agent fills sensible defaults and lists what
  it assumed. It only comes back to ask if an essential detail is missing or
  contradictory.
- **I have no SAP system.** Set `Mode: mock` (Gate 1 alone gives a working demo),
  or `live` with the **free api.sap.com sandbox** — same OData shape, no tenant.
- **I'm in a sovereign region (China / NS2 / KSA).** Set `Provider:
  openai-compatible` in `intent.md` and fill the `MODEL_GATEWAY_*` vars; the data
  path is region-agnostic. See README.md §1c.
- **Where do I get API keys?** api.sap.com → log in → "Show API Key" (sandbox);
  AI Core / gateway keys come from your BTP service keys or secret store. The
  agent tells you which, per your `intent.md`.
- **Can I add capabilities later?** Yes — update `intent.md` (set HVS / SF / other
  to `yes`) and ask again; the agent extends the same sub-folder without breaking
  what works.

---

*This example applies the principles in [`README.md`](README.md). If any
step here and README.md disagree on an engineering detail, README.md is the source
of truth and the agent should follow it.*
