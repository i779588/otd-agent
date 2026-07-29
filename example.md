# Example: Build a Custom SAP Agent with the Cookbook — Guided, No-Code

> **What this file is.** A single, self-contained recipe you can drop into an
> **empty folder** and hand to Claude Code (or any supported coding harness).
> The agent reads this file, **interviews you with a few plain questions**, tells
> you exactly which values to paste into a `.env` file, then scaffolds, tests,
> and launches a working SAP agent for you.
>
> **You do not need to write code.** You answer questions and paste API values
> when asked.
>
> **Companion reference:** the full engineering blueprint is
> [`README.md`](README.md) — the "boilerplate cookbook." This `example.md`
> is the *fast, guided path* that applies that blueprint's best practices
> (auth, resilience, observability, advisory-only governance) for you. You do
> not have to read README-3 to use this file; the agent consults it.

---

## 0. How to use this file (30 seconds)

1. Create a **new empty folder**, e.g. `my-agent/`.
2. Copy these files into that folder: **`example.md`**, **`CLAUDE.md`**, and (if
   you have it) **`README-3.md`**.
3. Open the folder in Claude Code.
4. **Kick it off — two ways, pick either:**
   - **Easiest:** just type **`start`** (or "hi"). The included `CLAUDE.md` is
     auto-loaded by Claude Code and tells the agent to read `example.md` and
     begin the interview. You don't have to copy anything.
   - **Manual:** open this file, copy the **kickoff prompt** in Section 1, and
     paste it as your first message. (Use this if there's no `CLAUDE.md`, or in a
     harness that doesn't auto-load it.)
5. Answer the questions the agent asks. Paste API values into `.env` when asked.
6. When every check is green, tell the agent to **launch**.

That's it.

> **Where do I "pass my intent"?** You barely type anything up front — you say
> `start`, and the agent's **interview questions (Section 2)** pull your intent
> out of you one question at a time (what the agent does, who uses it, your
> domain, your data). No long prompt to write. The full kickoff prompt in
> Section 1 is just the manual alternative to typing `start`.

---

## 1. Kickoff prompt (copy this to the agent)

> **You only need this if you're NOT using the auto-start.** If `CLAUDE.md` is in
> the folder, just type `start` instead (see Section 0). Otherwise, copy
> everything in the box and send it as your first message.

```
You are my SAP agent build assistant. Read example.md and README-3.md in this
folder and follow them exactly.

Rules you MUST obey:
- Work ONLY inside this folder. Create a new sub-folder for the agent you build.
- Do NOT edit, move, rename, or delete example.md, README-3.md, or ANY file
  outside the new sub-folder you create. They are read-only references.
- Do NOT touch or modify any other project or repository on this machine.
- Never put secrets in code or in these markdown files. All API keys, URLs, and
  credentials go into a .env file that I fill in — you only tell me what to add.
- Follow the best-practice rules from README-3 (advisory-only: no writes to SAP;
  never fabricate data; financial disclaimer; validate identity; structured logs).

Start by running the INTERVIEW in Section 2 of example.md. Ask me the questions
one group at a time, wait for my answers, and do not scaffold anything until the
interview is complete and I have confirmed the summary.
```

---

## 2. The interview — questions the agent asks you (before any build)

The agent asks these **before** creating anything. Nothing is hardcoded — your
answers drive the whole build. Answer in plain language.

> ℹ️ **Illustrative example used throughout this file: a Retail agent** (store
> inventory / sales orders). This is only to show what good answers look like —
> the agent still asks *you* for *your* domain and uses that. Retail, Finance,
> HR, Procurement, or anything else all work the same way.

### Group A — What is the agent for?
1. **What should the agent do?** (one sentence)
   - *Retail example:* "Answer store staff questions about stock levels and open sales orders."
2. **Who uses it?** (e.g. store associates, finance analysts)
3. **What domain / industry?** (Retail, Finance, HR, …) — *drives naming, prompt, and tags, not hardcoded.*
4. **Do you have any files to share?** (optional but helpful) — an OData/EDMX
   spec, an API doc, a sample data file, or a policy PDF. If yes, the agent tells
   you how to attach them (see Section 7) and uses them to build better tools.

### Group B — Where does the data come from?
5. **Do you have a live SAP system yet, or start with mock data?**
   - `mock` — demo works offline, no backend needed (recommended first).
   - `live` — connect a real backend now.
6. **If live:** which system/API? (e.g. S/4HANA Sales Orders `API_SALES_ORDER_SRV`)
7. **No SAP tenant?** The agent can wire the **free public sandbox** at
   `api.sap.com` (real OData shape, mock data) so you can try `live` without a tenant.

### Group C — Which model (LLM)?
8. **AI Core, or an OpenAI-compatible endpoint?**
   - `aicore` — SAP AI Core / GenAI Hub (if you have it).
   - `openai-compatible` — any hosted model gateway (also the **sovereign-region** path).

### Group D — Where will it run (later)?
9. **Just localhost for now, or deploy to BTP later?** (Cloud Foundry or Kyma)
   - You can start local and decide deployment afterward. No BTP account needed for local.

### Group E — Optional capabilities (ask, don't assume)
10. **Add a knowledge/semantic search capability (HANA Vector Store — "HVS")?** yes/no
    - Use when the agent should answer from documents/policies, not just live records.
11. **Add SuccessFactors (SF) data?** yes/no *(e.g. leave balances, org data)*
12. **Any other backend?** (Ariba, a custom HTTP API, …) — describe it.

> The agent presents a **one-screen summary** of your answers and asks you to
> confirm before it builds anything. If you say "change X," it re-asks only that.

---

## 3. The `.env` file — what the agent asks you to fill in

The agent **creates a `.env.example`** listing exactly the variables your choices
need, and tells you to copy it to `.env` and paste your values. **You never put
secrets in code or in this file.** The agent's tools read them at runtime.

> The agent only lists the variables relevant to *your* answers. Below is the
> full menu it draws from (from README-3's env reference).

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

## 4. Build flow — the gates (each must go green before the next)

The agent runs this sequence. It reports ✅/❌ at each gate and **stops on ❌**
with the exact fix, so a no-code user is never stuck guessing.

```
Interview (Section 2)  →  confirm summary
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

### Gate 5 — Best-practice checks (from README-3, automatic)
The agent confirms, per README-3:
- Advisory-only — **no** POST/PATCH/DELETE to SAP.
- Never fabricates document numbers/amounts; `top=100` on list calls.
- Financial outputs end with the standard disclaimer.
- Incoming identity validated at the A2A boundary (not from client metadata).
- Structured logs with correlation IDs; no secrets/PII in logs.

### Gate 6 — Domain test run (uses YOUR domain, not hardcoded)
The agent asks you for **one or two real questions from your domain** and runs
them end-to-end:
- *Retail:* "How many units of SKU 12345 are in store 0002?"
- *Finance:* "What's the open AR exposure for customer 100200?"

---

## 5. Launch (only when everything is green)

When Gates 1–6 are ✅, tell the agent:

```
All gates are green. Launch the agent locally and give me the exact command to
start it again myself, plus one sample question I can ask it.
```

If you also chose to deploy to BTP, the agent then walks you through the
deploy + (optional) Joule steps from README-3 — but **only after** you confirm,
and it tells you which additional `.env`/service values are needed first. It will
not deploy or register anything without your explicit go-ahead.

---

## 6. Guardrails (what the agent will and won't do)

**Will:**
- Work only inside the new sub-folder it creates in this folder.
- Ask before every non-local or irreversible action (deploy, register, teardown).
- Tell you the exact `.env` line to add whenever a credential is missing.
- Keep all secrets out of code and out of these markdown files.

**Won't:**
- Edit `example.md`, `README-3.md`, `CLAUDE.md`, or anything outside its sub-folder.
- Touch any other project/repository on your machine.
- Write to SAP systems (advisory-only), fabricate data, or invent credentials.
- Deploy, register in Joule, or spend on paid services without your confirmation.

> If the agent is ever unsure, it should ask you rather than assume — that's the
> intended behavior.

---

## 7. Attaching files (optional, makes the build better)

You don't need any files to start — but if you have them, they make the agent's
tools far more accurate. Useful things to attach:

- An **OData / EDMX spec** (`.edmx` / `.xml`) for your SAP service → the agent
  generates precise tool schemas instead of guessing entity/field names.
- An **API doc or Postman/OpenAPI file** for a custom backend.
- A **sample data file** (`.json` / `.csv`) → better mock data and field mapping.
- **Policy / knowledge documents** (`.pdf` / `.md`) → source material if you
  enabled **HVS** (knowledge search) in Group E.

**How to attach in Claude Code (any of these work):**

1. **Drag and drop** the file into the chat input box (you can also paste a
   screenshot/image directly).
2. **`@`-mention** the file by path once it's in the folder — e.g.
   `@specs/sales_order.edmx` — to pull it into the agent's context.
3. **Drop the file into the folder** (or a sub-folder like `specs/`) and just
   **tell the agent the filename**; since the folder is already open, it can read it.

> The agent will **ask** whether you have such files during the interview
> (Group A, question 4). Share them then, or say "none" to proceed with the
> guided defaults. Attaching a spec is the single biggest accuracy boost for
> `live` data — but everything still works without it.

### Prompt: attach a spec file at any time

If you decide to add a spec **after** the interview has started (or want to add
another one), attach the file (drag-drop / `@`-mention / drop-in-folder) and send
this:

```
I'm attaching a spec file: <filename> (e.g. an OData/EDMX or API spec).
Read it, and use it to build or refine the agent's tools — match the real
entity/field names from the spec instead of guessing. Keep everything inside the
agent sub-folder, don't touch the reference files, and after wiring it, re-run
the relevant gate (mock or live) and show me the result before moving on.
```

---

## 8. Quick FAQ

- **Do I have to copy a prompt?** No — if `CLAUDE.md` is in the folder, just type
  `start`. The copy-paste prompt (Section 1) is only the manual fallback.
- **Where do I give my requirements?** Through the agent's interview questions
  (Section 2). You answer in plain language; you don't write a spec.
- **I have no SAP system.** Choose `mock` (Gate 1 alone gives a working demo), or
  `live` with the **free api.sap.com sandbox** — same OData shape, no tenant.
- **I'm in a sovereign region (China / NS2 / KSA).** Choose `openai-compatible`
  in Group C and set the `MODEL_GATEWAY_*` vars; the data path is region-agnostic.
  See README-3 §D.3.
- **Where do I get API keys?** api.sap.com → log in → "Show API Key" (sandbox);
  AI Core / gateway keys come from your BTP service keys or secret store. The
  agent tells you which, per your choices.
- **Can I add capabilities later?** Yes — re-run this file and answer `yes` to
  HVS / SF / other in Group E; the agent extends the same sub-folder without
  breaking what works.

---

*This example applies the principles in [`README-3.md`](README-3.md). If any
step here and README-3 disagree on an engineering detail, README-3 is the source
of truth and the agent should follow it.*
