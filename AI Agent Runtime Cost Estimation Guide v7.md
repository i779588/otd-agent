# AI Agent Runtime Cost Estimation Guide
### SAP BTP Runtime Environment — Custom AI Agent Deployments

**Classification:** Internal Architecture Guidance  
**Role:** AI Technical Architect  
**Version:** 7.0  
**Date:** July 09, 2026  
**Incorporates:** SAP Note 3437766 — Availability of Generative AI Models, Version 153, released 07.07.2026  
**Changes from v6:** gpt-5-nano output rate corrected 0.00034 → **0.00029** (confirmed by calculator: 100K input + 300K output + 10K read-cached, 100 occurrences = 16.7729 raw CU → ROUND = 17 CU → EUR 17.68 ✓); Section 13.2 gpt-5-nano entry updated (GT 0.830→0.730, raw CU 1.580→1.390, billed CU 2→1, EUR 2.08→1.04); third verified example added (gpt-5-nano simulation, July 2026 calculator screenshots).

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [What Is a Custom AI Agent on BTP?](#2-what-is-a-custom-ai-agent-on-btp)
3. [Reference Architecture and Cost-Bearing Components](#3-reference-architecture-and-cost-bearing-components)
   - 3.1 [SAP AI Core Cost Calculation Tools (Three Calculators)](#31-sap-ai-core-cost-calculation-tools)
4. [Cost Dimension 1: LLM Inference via SAP AI Core and Generative AI Hub](#4-cost-dimension-1-llm-inference-via-sap-ai-core-and-generative-ai-hub)
   - 4.2 Token Metering, Capacity Units, and Rounding Rule
   - 4.4 SAP BTPEA EUR Billing
   - 4.5 [AI Core Standard Infrastructure Costs (Calculator 2)](#45-ai-core-standard-infrastructure-costs-calculator-2)
   - 4.6 [Orchestration and Prompt Optimization CU (Calculator 3)](#46-orchestration-and-prompt-optimization-cu-calculator-3)
5. [Cost Dimension 2: Compute Runtime](#5-cost-dimension-2-compute-runtime)
6. [Cost Dimension 3: Vector Store (SAP HANA Cloud)](#6-cost-dimension-3-vector-store-sap-hana-cloud)
7. [Cost Dimension 4: Embedding Model Calls](#7-cost-dimension-4-embedding-model-calls)
8. [Cost Dimension 5: Orchestration and Integration Services](#8-cost-dimension-5-orchestration-and-integration-services)
9. [Cost Dimension 6: Storage and Object Persistence](#9-cost-dimension-6-storage-and-object-persistence)
10. [Cost Dimension 7: Observability and Monitoring](#10-cost-dimension-7-observability-and-monitoring)
11. [Cost Dimension 8: Network and Data Transfer](#11-cost-dimension-8-network-and-data-transfer)
12. [Estimation Methodology: Step-by-Step](#12-estimation-methodology-step-by-step)
13. [Cost Estimation Worksheet](#13-cost-estimation-worksheet)
14. [Cost Sensitivity and Scaling Factors](#14-cost-sensitivity-and-scaling-factors)
15. [Cost Optimization Strategies](#15-cost-optimization-strategies)
16. [Governance and Cost Monitoring on BTP](#16-governance-and-cost-monitoring-on-btp)
17. [Key Assumptions and Limitations](#17-key-assumptions-and-limitations)
18. [Glossary](#18-glossary)
19. [Model Deprecation Risk and Migration Paths](#19-model-deprecation-risk-and-migration-paths)
20. [Special and Non-Standard Pricing Reference](#20-special-and-non-standard-pricing-reference)
21. [Rate Limit Risk and Design Implications](#21-rate-limit-risk-and-design-implications)

---

## 1. Purpose and Scope

This document provides a structured, repeatable framework for estimating the **monthly runtime cost** of a custom AI Agent deployed on the SAP Business Technology Platform (BTP). It is intended for use during project sizing, architecture reviews, and budget planning exercises.

**In scope:**
- Runtime and operational costs once the agent is deployed and in active use
- All BTP-native services consumed by the agent at runtime
- SAP AI Core (Generative AI Hub) LLM and embedding inference costs
- Supporting data, integration, compute, and observability services

**Out of scope:**
- One-time development and implementation costs
- SAP license costs for backend systems the agent connects to (e.g., S/4HANA)
- Fine-tuning or custom model training costs
- BTP Global Account setup fees

> **Important Notice on Pricing Data:**  
> All GenAI token conversion rates in this guide are taken from **SAP Note 3437766 — Availability of Generative AI Models, Version 153, released 07.07.2026**. This note is updated regularly; always verify its current version before finalising any cost estimate. SAP BTP Capacity Unit pricing and commercial model details must be obtained from the [SAP Discovery Center](https://discovery-center.cloud.sap) or your SAP Account Executive.

---

## 2. What Is a Custom AI Agent on BTP?

A custom AI Agent on BTP is an autonomous or semi-autonomous application that:

- **Perceives** input from users or systems (natural language, events, structured data)
- **Reasons** using one or more Large Language Models (LLMs) accessed via SAP AI Core's Generative AI Hub
- **Plans and acts** through an orchestration loop (ReAct, Plan-and-Execute, or custom agentic patterns)
- **Uses tools** such as APIs, SAP backend function calls, database lookups, and external services
- **Persists context** via vector stores (e.g., SAP HANA Cloud Vector Engine) or memory modules
- **Returns responses** to users or triggers downstream processes

### Agentic Loop Cost Amplification

Unlike a single-turn chatbot call, an AI Agent executes **multiple LLM calls per user request** — often 3–10 or more per interaction. This is the single most important factor in AI agent cost modeling.

```
User Request
    │
    ▼
[Agent Orchestrator]
    │
    ├──► LLM Call 1: Intent Analysis          ← Token cost
    ├──► Tool Call: SAP API / HANA Query       ← Compute + Integration cost
    ├──► LLM Call 2: Reasoning over results   ← Token cost
    ├──► Tool Call: External lookup            ← Network + Integration cost
    ├──► LLM Call 3: Response synthesis       ← Token cost
    │
    ▼
User Response
```

**Each LLM invocation carries a token cost. Tool calls carry compute and integration costs. Memory/retrieval carries vector query costs.**

---

## 3. Reference Architecture and Cost-Bearing Components

| # | Component | BTP Service | Cost Driver |
|---|-----------|-------------|-------------|
| 1 | Agent Orchestrator / Application | BTP Cloud Foundry or Kyma Runtime | GB-RAM hours / node hours |
| 2 | LLM Inference | SAP AI Core — Generative AI Hub | Input + Output + Cached tokens → Capacity Units |
| 3 | Embedding Model | SAP AI Core — Generative AI Hub | Input tokens → Capacity Units |
| 4 | Vector Store (RAG) | SAP HANA Cloud (Vector Engine) | Instance size + storage |
| 5 | Tool: SAP Backend APIs | SAP Integration Suite / API Management | API calls / messages |
| 6 | Memory / Session State | SAP HANA Cloud or Redis (via BTP) | Storage + queries |
| 7 | Artifact & Document Storage | SAP Object Store Service | Storage GB + operations |
| 8 | Observability | SAP Cloud Logging / Alert Notification | Log ingestion GB |
| 9 | Identity & Security | SAP Cloud Identity Services | Authentications |
| 10 | Network Egress | BTP Platform | GB transferred |

> **KG Source Note:** SAP AI Core, SAP AI Launchpad, SAP HANA Cloud Vector Engine, SAP BTP Cloud Foundry Runtime, SAP BTP Kyma Runtime, SAP Integration Suite, and agent orchestration are confirmed entities within the SAP Knowledge Graph. Service-level pricing figures are not stored in the KG and must be sourced from official SAP commercial documentation.

### 3.1 SAP AI Core Cost Calculation Tools

SAP provides three complementary calculators for estimating AI Core costs. Use all three together for a complete monthly cost estimate. Calculator outputs (Capacity Units) feed into Calculator 1 for the consolidated EUR/month bill.

| # | Calculator | URL | Covers | Notes |
|---|-----------|-----|--------|-------|
| 1 | **SAP BTP Service Estimator** | [discovery-center.cloud.sap/estimator](https://discovery-center.cloud.sap/protected/index.html#/estimator/539CA2A9-3973-47FC-80C1-EBCF5499099B/) | Full BTP portfolio — all services including AI Core | Starting point for consolidated EUR budget across all BTP services |
| 2 | **SAP AI Core Standard Cost Calculator** | [ai-core-calculator/core](https://ai-core-calculator.cfapps.eu10.hana.ondemand.com/uimodule/index.html#/core) | **Instances** (node hours/month) · **Storage** (GB hours/month) · **Baseline** (tenant hours/month) | **Run separately per subaccount.** Repeat for each subaccount using AI Core — separate regions, hyperscalers, or environments each require their own calculation. |
| 3 | **Generative AI Hub in SAP AI Core Calculator** | [ai-core-calculator/gen](https://ai-core-calculator.cfapps.eu10.hana.ondemand.com/uimodule/index.html#/gen) | **Requests** (LLM inference CU/month) · **Orchestration** (CU/month) · **Prompt Optimization** (CU/month) | Token-level metering — the primary cost driver for AI Agents. Covered in detail in Section 4. |

> **How the calculators interact:** Calculator 2 gives the fixed/semi-fixed infrastructure CU. Calculator 3 gives the variable inference CU. Both feed into Calculator 1 (BTP Service Estimator) for the total EUR/month figure under your commercial model (e.g., SAP BTPEA). **The guide's Sections 4–13 primarily address Calculator 3 (GenAI Hub inference).** Section 4.5 addresses Calculator 2 inputs.



---

## 4. Cost Dimension 1: LLM Inference via SAP AI Core and Generative AI Hub

This is typically the **dominant cost driver** for AI Agents. Every call to an LLM through the Generative AI Hub consumes tokens, metered as GenAI tokens and billed as SAP BTP Capacity Units.

### 4.1 SAP AI Core Service Plans

| Plan | Use Case | Key Constraint |
|------|----------|----------------|
| **Free Tier** | Development and prototyping | Rate-limited; not for production |
| **Standard** | Production workloads | Full throughput; per-token metering |
| **Extended** | High-throughput or reserved capacity | Higher limits; commitment-based |

> The free tier option for SAP AI Core is confirmed in the SAP Knowledge Graph (identifier: `42010AEF0E491EED81C1678B189B06EA`). Use it strictly for development.

### 4.2 Token Metering Model, Capacity Units, and Rounding Rule

Generative AI Hub meters usage in **GenAI tokens** (per 1,000 model tokens processed). GenAI tokens are then converted to **SAP BTP Capacity Units** — the unit that appears on your SAP bill.

> **Sources:** SAP Note 3437766 (Version 153, 07.07.2026) for GenAI token rates. SAP Note 3505347 for orchestration module conversion rates.

#### Token Types

| Token Type | Description | Availability |
|-----------|-------------|--------------|
| **Input tokens** | Prompt, system instructions, RAG context, history, tool outputs | All models |
| **Output tokens** | Model-generated response | All generative models |
| **Read Cached Input** | Input tokens served from provider-side prompt cache (discounted rate) | Select models — see Section 4.3 |
| **Write Cached Input** | Input tokens that populate the cache for the first time | Select models — see Section 4.3 |

#### Cost Formula — Per LLM Call

```
GenAI tokens per call =
    (Input_Tokens        / 1,000 × Input_Rate)
  + (Output_Tokens       / 1,000 × Output_Rate)
  + (Read_Cached_Tokens  / 1,000 × Read_Cached_Rate)   [where supported; else 0]
  + (Write_Cached_Tokens / 1,000 × Write_Cached_Rate)  [where supported; else 0]

Capacity Units per call = GenAI_tokens_per_call × 1.90385
```

> **Rounding Rule:** SAP AI Core does not accept fractional Capacity Units. Values are rounded to the **nearest whole integer** (`ROUND`). Example: 1.238 raw CU → ROUND → **1 CU**; 13.4926 raw CU → ROUND → **13 CU** (confirmed by BTP Service Estimator simulation). Note: values exactly at .5 round to the nearest even integer (standard rounding). At low volumes, rounding can slightly reduce or slightly increase the billed amount relative to raw CU; the maximum deviation is always ± 0.5 CU.

#### Monthly Cost Formula

```
Occurrences_per_Month = Monthly_User_Requests × LLM_Calls_per_User_Request

Total_GenAI_tokens_per_month = Occurrences_per_Month ×
  [
      (Avg_Input_Tokens        / 1,000 × Input_Rate)
    + (Avg_Output_Tokens       / 1,000 × Output_Rate)
    + (Avg_Read_Cached_Tokens  / 1,000 × Read_Cached_Rate)
    + (Avg_Write_Cached_Tokens / 1,000 × Write_Cached_Rate)
  ]

Total_Capacity_Units_per_month = Total_GenAI_tokens_per_month × 1.90385

-- Rounding rule (SAP AI Core does not accept fractional CU):
Billed_CU_per_month = ROUND(Total_Capacity_Units_per_month)

-- SAP BTPEA billing (EUR):
Monthly_EUR_Cost_BTPEA = Billed_CU_per_month × EUR_per_CU
```

> **Verified example 1 — gpt-4o 2024-05-13:**  
> Input: 1,000 tokens · Output: 1,000 tokens · 30 occurrences/month  
> GenAI tokens = 30 × (1×0.00312 + 1×0.00920) = **0.36960**  
> Raw CU = 0.36960 × 1.90385 = **0.7037**  
> Billed CU = ROUND(0.7037) = **1 CU**  
> EUR (BTPEA) = 1 × **EUR 1.04** = **EUR 1.04 / month** ✓ (confirmed: BTP estimator unit price EUR 1.04/CU)
>
> **Verified example 2 — gpt-realtime 2025-08-28 (from calculator simulation):**  
> 1,000 text in · 1,000 text out · 1,000 audio in · 1,000 audio out · 1,000 cached audio · 100 occurrences  
> Raw CU (from GenAI Hub Calculator) = **13.4926**  
> Billed CU = ROUND(13.4926) = **13 CU**  
> EUR (BTPEA) = 13 × **EUR 1.04** = **EUR 13.52 / month** ✓ (confirmed: BTP Service Estimator shows EUR 1.04 × 13 = EUR 13.52)

### 4.4 SAP BTPEA Billing — EUR Conversion

Under the **SAP BTPEA** (BTP Enterprise Agreement) commercial model, costs are billed in **EUR** based on Capacity Units consumed. This is the standard production commercial model for SAP BTP.

```
Monthly EUR Cost = ROUND(Total Capacity Units) × EUR_per_CU (BTPEA)
```

**Observed rate from the SAP BTP calculator (July 2026):**

| Commercial Model | Price per Capacity Unit | Currency | Billing Basis |
|-----------------|------------------------|----------|---------------|
| SAP BTPEA | **EUR 1.04** | EUR | Capacity Units consumed (unit price per CU per month) |

> **Source:** Confirmed from the **SAP BTP Service Estimator**: EUR 1.04 is the unit price per Capacity Unit per month for the Generative AI Hub in SAP AI Core service (Standard plan, Australia (Sydney) AWS — rates may vary by region and hyperscaler).  
> Verification 1: ROUND(0.7037 CU) = 1 CU × EUR 1.04 = **EUR 1.04** ✓  
> Verification 2: gpt-realtime simulation — ROUND(13.4926 CU) = 13 CU × EUR 1.04 = **EUR 13.52** ✓  
> Verification 3: gpt-5-nano simulation — 100K input + 300K output + 10K read-cached + 10K write-cached, 100 occurrences → **16.7729 raw CU** → ROUND = **17 CU** × EUR 1.04 = **EUR 17.68** ✓  
> Always confirm the applicable rate for your region, hyperscaler, and commercial contract with your SAP Account Executive.

**Key implication for budget planning:** All LLM inference costs in this guide are now expressible in EUR. The GenAI token amounts in Section 4.3 and the Capacity Unit amounts in Section 13.2 convert directly at this rate.

```
Example — gpt-5-mini, Base Case (1,000 monthly requests):
  GenAI tokens  = 6.420
  Capacity Units (raw) = 6.420 × 1.90385 = 12.223 CU
  Billed CU     = ROUND(12.223) = 12 CU
  EUR cost (BTPEA) = 12 × 1.04 = EUR 12.48 / month
```

### 4.3 Complete Model Pricing Reference

All rates are GenAI tokens per 1,000 model tokens. Source: SAP Note 3437766 Version 153, 07.07.2026.  
`—` = feature not supported. Rate Limit = requests per minute per AI Core tenant.

> **CRITICAL — IMMINENT RETIREMENTS (as of 2026-07-09):**  
> **o1 retires 2026-07-15 (6 days).** o3-mini retires 2026-08-02 (24 days). Do not start new projects on these models.

---

#### SAP-Hosted Mistral Models (`aicore-mistralai`)

| Model | Version | Input | Output | Read Cached | Write Cached | Status | Retirement | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|--------|------------|------------|
| mistralai--mistral-large-instruct | 2407 (latest) | 0.00112 | 0.00320 | — | — | Active | not earlier than 2026-09-30 | 100 |
| mistralai--mistral-small-instruct | 2503 | 0.00005 | 0.00015 | — | — | **Deprecated** → mistral-small 2603 | not earlier than 2026-09-30 | 100 |
| mistralai--mistral-medium-instruct | 2505 (latest) | 0.00036 | 0.00122 | — | — | Active | not earlier than 2026-09-30 | 240 |
| mistralai--mistral-small | 2603 (latest) | 0.00007 | 0.00028 | — | — | Active — replaces mistral-small-instruct | not earlier than 2026-12-31 | 100 |

---

#### SAP-Managed NVIDIA Model (`aicore-nvidia`)

| Model | Version | Input | Output | Notes | Retirement | Rate Limit |
|-------|---------|-------|--------|-------|------------|------------|
| nvidia--llama-3.2-nv-embedqa-1b | 2 (latest) | 0.00007 | — | Embedding only | not earlier than 2026-09-30 | 138 |

---

#### SAP-Hosted Cohere Models (`aicore-cohere`)

| Model | Version | Input | Output | Read Cached | Write Cached | Notes | Retirement | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|-------|------------|------------|
| cohere--command-a-reasoning | 2508 (latest) | 0.00063 | 0.00505 | — | — | — | not earlier than 2026-08-30 | 240 |
| cohere-reranker | 3.5 (latest) | *** | — | — | — | Per search_unit — see Section 20 | not earlier than 2026-09-30 | 100 |

---

#### SAP-Hosted SAP Models (`aicore-sap`)

| Model | Version | Input | Output | Notes | Retirement | Rate Limit |
|-------|---------|-------|--------|-------|------------|------------|
| sap-rpt-1-small | 1 (latest) | *** | — | Cells-based pricing — see Section 20 | not earlier than 2026-12-31 | 100 |
| sap-rpt-1-large | 1 (latest) | *** | — | Cells-based pricing — see Section 20 | not earlier than 2026-12-31 | 100 |
| sap-abap-1 | 1 (latest) | 0.00048 | 0.00170 | Orchestration service only | not earlier than 2026-08-30 | 100 |

---

#### Perplexity AI Models (`perplexity-ai`)

| Model | Version | Input | Output | Notes | Retirement | Rate Limit |
|-------|---------|-------|--------|-------|------------|------------|
| sonar | perplexity- | 0.00086 | 0.00086 | + web search fee per call (see Section 20) | No current plans | 100 |
| sonar-pro | perplexity-us | 0.00243 | 0.01185 | + web search fee per call (see Section 20) | No current plans | 100 |

---

#### AWS Bedrock Models (`aws-bedrock`)

| Model | Version | Input | Output | Read Cached | Write Cached | Status | Retirement | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|--------|------------|------------|
| amazon--nova-micro | 1 (latest) | 0.00003 | 0.00010 | — | — | Active | No current plans | **50** |
| amazon--nova-lite | 1 | 0.00004 | 0.00016 | — | — | Active | No current plans | **50** |
| amazon--nova-lite | 2 (latest) | — | — | — | — | Active — pricing TBD | No current plans | **50** |
| amazon--nova-pro | 1 (latest) | 0.00056 | 0.00213 | — | — | Active | No current plans | **50** |
| amazon--nova-premier | 1 (latest) | 0.00171 | 0.00825 | — | — | **Deprecated** → nova-lite 2 | **2026-09-10** | **50** |
| amazon--titan-embed-text | 1.2 | 0.00014 | — | — | — | Active — embedding | No current plans | 50 |
| amazon--titan-embed-text | 2 (latest) | 0.00014 | — | — | — | Active — embedding | No current plans | 138 |
| amazon--titan-embed-image | 1 (latest) | 0.00006 | — | — | — | Active — image embeddings | No current plans | 120 |
| anthropic--claude-3-haiku | 1 (latest) | 0.00024 | 0.00089 | — | — | **Deprecated** → claude-4.5-haiku | **2026-09-10** | 50 |
| anthropic--claude-4-sonnet | 1 (latest) | 0.00204 | 0.00988 | 0.00020 | 0.00254 | **Deprecated** → claude-4.5-sonnet | **2026-10-14** | 100 |
| anthropic--claude-4.5-haiku | 1 (latest) | 0.00079 | 0.00367 | 0.00008 | 0.00099 | Active | No current plans | 100 |
| anthropic--claude-4.5-sonnet | 1 (latest) | 0.00223 | 0.01087 | 0.00020 | 0.00254 | Active | No current plans | 100 |
| anthropic--claude-4.5-opus | 1 (latest) | 0.00367 | 0.01806 | 0.00037 | 0.00459 | Active | No current plans | 100 |
| anthropic--claude-4.6-sonnet | 1 | 0.00223 | 0.01087 | 0.00020 | 0.00254 | Active | No current plans | 100 |
| anthropic--claude-4.6-opus | 1 | 0.00367 | 0.01806 | 0.00037 | 0.00459 | Active | No current plans | 100 |
| anthropic--claude-4.7-opus | 1 | 0.00367 | 0.01806 | 0.00037 | 0.00459 | Active | No current plans | 100 |
| anthropic--claude-4.8-opus | 1 | 0.00367 | 0.01806 | 0.00037 | 0.00459 | Active | No current plans | 100 |

---

#### Azure OpenAI Models — Embedding Models (`azure-openai`)

| Model | Version | Input | Status | Retirement | Rate Limit |
|-------|---------|-------|--------|------------|------------|
| text-embedding-3-small | 1 (latest) | 0.00002 | Active | not earlier than 2027-04-15 | 138 |
| text-embedding-ada-002 | 2 (latest) | 0.00007 | **Deprecated** → 3-small / 3-large | not earlier than 2027-04-15 | 600 (EU10/US10); 138 elsewhere |
| text-embedding-3-large | 1 (latest) | 0.00009 | Active | not earlier than 2027-04-15 | 138 |

---

#### Azure OpenAI Models — GPT-4o Family

> All GPT-4o versions retire **2026-10-01**. Suggested replacement: gpt-5.  
> **Version 2024-05-13 has 2× higher input cost than 2024-08-06. Always confirm the deployed version.**

| Model | Version | Input | Output | Read Cached | Write Cached | Status | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|--------|------------|
| gpt-4o | **2024-05-13** | **0.00312** | **0.00920** | — | — | **Deprecated** | 78 |
| gpt-4o | 2024-08-06 (latest) | 0.00159 | 0.00616 | — | — | **Deprecated** | 78 |
| gpt-4o | 2024-11-20 | 0.00175 | 0.00677 | — | — | Retiring 2026-10-01 | 78 |
| gpt-4o-mini | 2024-07-18 (latest) | 0.00009 | 0.00039 | — | — | **Deprecated** → gpt-5-mini | 120 |

---

#### Azure OpenAI Models — GPT-4.1 Family

> All GPT-4.1 versions retire **2026-10-14**. Batch API pricing available — see Section 20.

| Model | Version | Input | Output | Read Cached | Write Cached | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|------------|
| gpt-4.1 | 2025-04-14 | 0.00129 | 0.00494 | 0.00032 | — | 78 |
| gpt-4.1-mini | 2025-04-14 | 0.00026 | 0.00099 | 0.00007 | — | 120 |
| gpt-4.1-nano | 2025-04-14 | 0.00008 | 0.00026 | — | — | 120 |

---

#### Azure OpenAI Models — GPT-5 Family

| Model | Version | Input | Output | Read Cached | Write Cached | Notes | Retirement | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|-------|------------|------------|
| gpt-5-nano | 2025-08-07 | 0.00001 | **0.00029** | 0.00001 | — | Cheapest GPT-5 | No current plans | 120 |
| gpt-5-mini | 2025-08-07 | 0.00024 | 0.00141 | 0.00002 | — | — | No current plans | 120 |
| gpt-5 | 2025-08-07 | 0.00091 | 0.00677 | 0.00009 | — | Batch API available (US only) | No current plans | 78 |
| gpt-5.1 | 2025-11-13 (latest) | 0.00090 | 0.00675 | — | — | — | No current plans | 100 |
| gpt-5.2 | 2025-12-11 | 0.00125 | 0.00944 | 0.00012 | — | — | No current plans | 100 |
| gpt-5.2-nano (alias: gpt-5.4-nano) | 2025-12-11 | 0.00008 | 0.00026 | — | — | — | No current plans | 120 |
| gpt-5.3-codex | 2026-02-24 | 0.00125 | 0.00944 | 0.00012 | — | Code-optimised | No current plans | 120 |
| gpt-5.4 | 2026-03-05 | 0.00159 | 0.00920 | 0.00016 | — | — | No current plans | 120 |
| gpt-5.4-nano | 2026-03-17 | 0.00014 | 0.00078 | 0.00001 | — | — | No current plans | 120 |
| gpt-5.5 | 2026-04-24 | 0.00342 | 0.02015 | 0.00034 | — | Latest OpenAI flagship | No current plans | 100 |

---

#### Azure OpenAI Models — Reasoning (o-series)

> **CRITICAL:** o1 retires **2026-07-15** — 6 days from today. o3-mini retires **2026-08-02** — 24 days from today.

| Model | Version | Input | Output | Read Cached | Write Cached | Retirement | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|------------|------------|
| o1 | 2024-12-17 | 0.00920 | 0.03658 | — | — | **2026-07-15** | 78 |
| o3-mini | 2025-01-31 | 0.00069 | 0.00270 | — | — | **2026-08-02** | 120 |
| o3 | 2025-04-16 | 0.00610 | 0.02430 | 0.00153 | — | 2026-10-16 | 78 |
| o4-mini | 2025-04-16 | 0.00069 | 0.00270 | 0.00017 | — | 2026-10-16 | 120 |

---

#### Azure OpenAI Models — Real-Time Audio/Text

| Model | Version | Input (text / audio) | Output (text / audio) | Notes | Rate Limit |
|-------|---------|----------------------|-----------------------|-------|------------|
| gpt-realtime | 2025-08-28 | 0.00251 / 0.01954 | 0.00981 / 0.03901 | Text and audio tokens priced separately. Audio ≈ 8× more expensive than text per token. | — |

---

#### Google Vertex AI Models — Text Models (`gcp-vertexai`)

| Model | Version | Input | Output | Read Cached | Write Cached | Status | Retirement | Rate Limit |
|-------|---------|-------|--------|-------------|--------------|--------|------------|------------|
| gemini-2.5-flash-lite | 001 (latest) | 0.00008 | 0.00028 | 0.00001 | — | Active | No current plans | 100 |
| gemini-2.5-flash | 001 (latest) | 0.00027 | 0.00167 | 0.00003 | — | Retiring | 2026-10-16 | 100 |
| gemini-2.5-pro | 001 (latest) | 0.00087 / 0.00167* | 0.00647 / 0.00966* | 0.00009 / 0.00017* | — | Retiring | 2026-10-16 | 100 |
| gemini-3.1-flash-lite | 001 | 0.00020 | 0.00108 | — | — | Active | No current plans | 100 |
| gemini-3.5-flash | 001 (latest) | 0.00169 | 0.00981 | — | — | Active | No current plans | 100 |
| gemini-embedding | 001 (latest) | 0.00011 | — | — | — | Active — embedding | No current plans | 100 |

> `*` **Gemini 2.5 Pro tiered pricing:** Lower rate for prompts < 200,000 tokens; higher rate for ≥ 200,000 tokens. Same tiers apply to read cached rates.

---

#### Google Vertex AI Models — Multimodal / Image Models

| Model | Version | Text Input | Image Input | Text Output | Image Output | Rate Limit |
|-------|---------|-----------|------------|------------|--------------|------------|
| gemini-2.5-flash-image | 001 | 0.00021 | 0.00021 | 0.00162 | 0.01920 | 10 |
| gemini-3-pro-image | 001 | 0.00204 | 0.00204 | 0.01187 | 0.11810 | 20 |
| gemini-3.1-flash-image | 001 | 0.00056 | 0.00056 | 0.00302 | 0.05909 | 20 |

> Image output tokens are significantly more expensive than text output (up to 12× for gemini-3-pro-image). Rate limits of 10–20 req/min make image models unsuitable for synchronous agent tool calls at meaningful scale.

### 4.4 Agentic Token Amplification — The Critical Factor

| Factor | Description | Typical Range |
|--------|-------------|---------------|
| **LLM calls per turn** | Number of distinct LLM invocations per user request | 3 – 10 |
| **System prompt size** | Static instructions repeated on every call | 200 – 2,000 tokens |
| **RAG context size** | Retrieved chunks appended to each call | 500 – 5,000 tokens |
| **Conversation history** | Prior turns included in context | 200 – 4,000 tokens |
| **Tool output size** | API response data fed back to model | 100 – 3,000 tokens |
| **Output per LLM call** | Generated response tokens per call | 100 – 1,000 tokens |

**Example:**
```
Input tokens/call = 800 + 1,500 + 1,000 + 500 + 100 = 3,900
Output tokens/call = 350
LLM calls/turn = 5

Total per user request: Input = 19,500 · Output = 1,750
```

### 4.5 AI Core Standard Infrastructure Costs (Calculator 2)

Beyond LLM inference token charges (Calculator 3), every active SAP AI Core tenant incurs **infrastructure-level costs** metered through the **AI Core Standard** service plan. These are calculated using **Calculator 2** and cover three components:

| Component | Billing Unit | Description |
|-----------|-------------|-------------|
| **Instances** | Node hours / month | Compute nodes backing AI Core workloads — model deployment pods, batch execution environments, and resource group nodes |
| **Storage** | GB hours / month | Persistent storage for model artifacts, pipeline outputs, training datasets, and execution logs |
| **Baseline** | Tenant hours / month | Base operational overhead per active AI Core tenant — incurred continuously regardless of request volume |

**Critical planning rules:**

- **Per-subaccount calculation:** Run Calculator 2 **separately for each BTP subaccount** with SAP AI Core enabled. Each subaccount in a different region, on a different hyperscaler, or serving a distinct environment (dev / test / prod) requires its own calculation. Calculator 2 results cannot be aggregated from a single run.
- **Baseline cost is always on:** The Tenant hours charge runs 24×7 while an AI Core tenant is active. For low-volume agents or development environments, this fixed cost can exceed the variable GenAI token costs.
- **Consolidation opportunity:** Where operationally feasible, consolidate multiple AI agents or use cases within a single BTP subaccount to pay the Baseline fee only once. Use AI Core **resource groups** to isolate workloads within the shared tenant.

> **Pricing data note:** Instance, Storage, and Baseline rates are not published in SAP Note 3437766 (which covers only GenAI model token rates). Use [Calculator 2](https://ai-core-calculator.cfapps.eu10.hana.ondemand.com/uimodule/index.html#/core) for current rates applicable to your region and hyperscaler, or request the price sheet from your SAP Account Executive.

Include Calculator 2 CU outputs in **Section 13.8 (Total Monthly Cost Summary)** alongside GenAI Hub inference CU from Calculator 3.

---

### 4.6 Orchestration and Prompt Optimization CU (Calculator 3)

Calculator 3 tracks two CU categories beyond direct LLM inference Requests:

| Service | Calculator 3 Category | Billing Unit | Description | Rate Reference |
|---------|-----------------------|-------------|-------------|----------------|
| **SAP AI Core Orchestration** | Orchestration | CU / month | CU overhead when requests are routed through the SAP AI Core Orchestration module — an SAP-native layer providing grounding, content filtering, and tool-use management on top of model calls | SAP Note 3505347 |
| **Prompt Optimization** | Prompt Optimization | CU / month | CU consumed when the AI Core Prompt Optimization service automatically refines and evaluates prompts at runtime | SAP Note 3437766 |

**When Orchestration CU applies:**
- Your agent routes requests through the SAP AI Core **Orchestration service endpoint** rather than calling model endpoints directly.
- Orchestration adds a small per-request CU overhead on top of the underlying model's token cost.
- Direct model endpoint calls (bypassing the Orchestration module) do not incur Orchestration CU.
- The Orchestration module is the recommended approach for production agents using SAP AI Core natively; account for its CU contribution in your total estimate.

**When Prompt Optimization CU applies:**
- Only when the **Prompt Optimization** feature is explicitly enabled on a deployment. Most standard inference workloads do not use this feature.

> Add Orchestration and Prompt Optimization CU outputs from Calculator 3 to the **Total Billed CU** in Section 13.8 before applying the ROUND rounding rule (see Section 4.2).

---

### 4.7 Model Selection Decision Matrix

| Task Type | Recommended Tier | Suggested Active Models (v153) |
|-----------|-----------------|-------------------------------|
| Classification, routing, intent detection | Economy | nova-micro, mistral-small 2603, gpt-5-nano |
| Tool call planning, structured extraction | Standard | gpt-5-mini, gpt-5.1, nova-pro, gemini-2.5-flash-lite |
| Multi-step reasoning, complex analysis | Standard–Premium | gpt-5, claude-4.5-haiku, gemini-3.5-flash |
| SAP ABAP code generation | SAP-specific | sap-abap-1 (Orchestration service only) |
| Long-context document analysis | Premium | claude-4.5-sonnet/opus, gpt-5.5, gemini-2.5-pro |
| Advanced chain-of-thought / reasoning | Reasoning | o3, o4-mini (**avoid o1/o3-mini — retiring within weeks**) |
| Batch / offline pipeline | Any via Batch API | gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-5 — see Section 20 |
| Web-augmented search | Search | sonar, sonar-pro (+ web search fee per call) |
| Multimodal / image generation | Multimodal | gemini-2.5-flash-image, gemini-3.1-flash-image |

### 4.6 Inputs Required

- [ ] Expected monthly request volume (DAU × requests/user/day × working days)
- [ ] Average LLM calls per agent turn (measure during prototyping)
- [ ] System prompt length (tokens)
- [ ] Max RAG context chunks and chunk size
- [ ] Conversation history window (in tokens)
- [ ] **Exact model name AND version** — confirm in AI Core resource group configuration
- [ ] Expected output length (tokens)
- [ ] Whether prompt caching is used (read cached / write cached token volumes)
- [ ] Whether multi-model routing is used

---

## 5. Cost Dimension 2: Compute Runtime

The agent orchestrator, API server, and microservices run on BTP compute infrastructure.

### 5.1 SAP BTP, Cloud Foundry Runtime

```
Monthly CF Cost = Instances × Memory_per_Instance_GB × Hours_per_Month × Price_per_GB-Hour
```

| Input | Guidance |
|-------|----------|
| **Instance count** | Minimum 2 for HA in production |
| **Memory per instance** | Typical agent app: 512 MB – 2 GB |
| **Burst vs. steady-state** | CF supports auto-scaling |
| **Disk quota** | Ephemeral; usually negligible |

### 5.2 SAP BTP, Kyma Runtime

```
Monthly Kyma Cost = Node_Count × Node_Type_Price × Hours_per_Month
```

| Input | Guidance |
|-------|----------|
| **Node sizing** | Fit pod resource requests + overhead |
| **Scaling** | Use HPA; set min/max replicas |
| **System node pools** | Baseline node consumed even when idle |

### 5.3 Runtime Selection Guidance

| Criterion | Cloud Foundry | Kyma |
|-----------|---------------|------|
| Billing granularity | Per GB-RAM hour | Per node hour |
| Cost at low scale | Lower | Higher |
| Cost at high scale | Predictable | Flexible with HPA |
| Best fit | Simple stateless agents | Complex multi-service agents |

---

## 6. Cost Dimension 3: Vector Store (SAP HANA Cloud)

> SAP HANA Cloud Vector Engine is a confirmed KG entity (identifier: `42010AEF4E231EEEA7B2327E7CCE862F`).

### 6.1 Sizing Drivers

| Driver | Description |
|--------|-------------|
| **vCPUs** | Minimum 2; scale for query concurrency |
| **Memory (RAM)** | HANA is in-memory; vector data loaded into RAM |
| **Storage** | Disk for persistence; index adds overhead |
| **Number of vectors** | Each vector (1,536 dims) ≈ 6 KB RAM |
| **Query rate (QPS)** | Determines vCPU requirement |

### 6.2 Vector Store Sizing Formula

```
RAM Required ≈
  Number_of_Vectors × Vector_Dimension × 4 bytes × Safety_Factor (1.5–2.0)
  + Base_HANA_RAM (typically 32 GB minimum)

Example: 500,000 × 1,536 × 4 × 1.8 = ~5.5 GB + 32 GB base = ~38 GB
```

### 6.3 Cost Estimation Inputs

- [ ] Number of documents/chunks to embed and store
- [ ] Embedding dimension (model-dependent — see Section 7)
- [ ] Expected vector query rate at peak
- [ ] HANA Cloud instance size (S/M/L/XL)
- [ ] Whether HANA is shared with other workloads

---

## 7. Cost Dimension 4: Embedding Model Calls

### 7.1 Two Embedding Phases

| Phase | Trigger | Frequency |
|-------|---------|-----------|
| **Indexing (batch)** | Document ingestion pipeline | One-time + incremental updates |
| **Query-time** | Each user message requiring RAG | Every agent request with retrieval |

### 7.2 Available Embedding Models and Pricing

All rates from SAP Note 3437766 Version 153. Embedding models are input-only (no output tokens).

| Model | Provider / Hosting | Input / 1K tokens | Status | Retirement | Rate Limit |
|-------|--------------------|-------------------|--------|------------|------------|
| text-embedding-3-small v1 | Azure OpenAI | 0.00002 | Active | not earlier than 2027-04-15 | 138 |
| amazon--titan-embed-image v1 | AWS Bedrock | 0.00006 | Active — image embeddings | No current plans | 120 |
| nvidia--llama-3.2-nv-embedqa-1b v2 | SAP-managed | 0.00007 | Active | not earlier than 2026-09-30 | 138 |
| text-embedding-ada-002 v2 | Azure OpenAI | 0.00007 | **Deprecated** → 3-small / 3-large | not earlier than 2027-04-15 | 600 (EU10/US10); 138 elsewhere |
| text-embedding-3-large v1 | Azure OpenAI | 0.00009 | Active | not earlier than 2027-04-15 | 138 |
| gemini-embedding v001 | Google Vertex | 0.00011 | Active | No current plans | 100 |
| amazon--titan-embed-text v1.2 | AWS Bedrock | 0.00014 | Active | No current plans | 50 |
| amazon--titan-embed-text v2 | AWS Bedrock | 0.00014 | Active | No current plans | 138 |

**Selection guidance:**
- **text-embedding-3-small** (0.00002) is the cheapest text embedding on GenAI Hub.
- **text-embedding-3-large** (0.00009) produces higher-quality embeddings for complex semantic search.
- **nvidia--llama-3.2-nv-embedqa-1b** (0.00007) offers SAP-hosted infrastructure with no hyperscaler dependency.
- Do **not** start new deployments on **text-embedding-ada-002** — it is deprecated.
- Do not mix embedding models within a single vector store.

### 7.3 Embedding Cost Formula

```
Monthly Embedding GenAI Tokens =
  (Indexing: Total_Docs × Avg_Chunk_Tokens × Price_per_1K / 1,000) / Amortization_Months
  + (Query: Monthly_Requests × Avg_Query_Tokens × Price_per_1K / 1,000)

Monthly Embedding Capacity Units = GenAI_Tokens × 1.90385
```

**Example — 50,000 docs, 500 tokens/chunk, text-embedding-3-large, 12-month amortisation, 10,000 requests/month at 100 tokens/query:**
```
Indexing: 50,000 × 500 × 0.00009 / 1,000 / 12 = 0.1875 GenAI tokens/month
Query:    10,000 × 100 × 0.00009 / 1,000       = 0.0900 GenAI tokens/month
Total:                                          = 0.2775 GenAI tokens/month
CU:       0.2775 × 1.90385                      ≈ 0.528 CU/month
```

---

## 8. Cost Dimension 5: Orchestration and Integration Services

### 8.1 SAP Integration Suite

| Component | Cost Driver |
|-----------|-------------|
| **Cloud Integration** | Messages processed per month |
| **API Management** | API calls per month |
| **Advanced Event Mesh** | Messages / GB transferred |

### 8.2 Direct API Calls

Cost is embedded in the target service plan (SAP backends) or is customer-direct (external APIs).

### 8.3 SAP AI Launchpad

SAP AI Launchpad (KG identifier: `73555000100800003283`) is typically included with SAP AI Core and does not incur a separate runtime charge for basic usage.

### 8.4 Orchestration Module Costs

Using the SAP AI Core Orchestration service may incur additional GenAI token costs. Refer to **SAP Note 3505347** for orchestration module conversion rates.

### 8.5 Integration Cost Formula

```
Monthly Integration Cost =
  API_Calls_Per_Request × Monthly_Requests × Price_per_API_Call
  + Event_Messages_per_Month × Price_per_Message
```

---

## 9. Cost Dimension 6: Storage and Object Persistence

| Storage Type | Service | Cost Driver |
|--------------|---------|-------------|
| Documents / RAG corpus | SAP Object Store Service | GB stored per month |
| Vector index (on-disk) | SAP HANA Cloud storage | GB per month (included in HANA) |
| Conversation history | SAP HANA Cloud or Redis | GB stored + read/write ops |
| AI Core artifacts | SAP AI Core (included) | Workflow output artifacts |
| Application logs | SAP Cloud Logging | GB ingested |

| Input | Typical Range |
|-------|---------------|
| RAG document corpus size | 1 – 100 GB |
| Conversation history per user (30 days) | < 1 MB |
| Log volume per 1,000 requests | 50 – 500 MB |
| Model artifact storage | 1 – 10 GB |

---

## 10. Cost Dimension 7: Observability and Monitoring

| Service | Cost Driver | Estimated Volume |
|---------|-------------|------------------|
| SAP Cloud Logging | GB ingested and retained | 1–5 GB/month per 10K requests |
| SAP Alert Notification Service | Notifications sent | Low volume typically |
| SAP Cloud ALM | Included in enterprise subscriptions | — |

> Enable structured JSON logging from day one. It reduces log volume and enables cost-efficient querying.

---

## 11. Cost Dimension 8: Network and Data Transfer

| Traffic Pattern | Typical Cost Trigger |
|-----------------|---------------------|
| BTP → External Internet | LLM API responses, external tool calls |
| BTP ↔ BTP (same region) | Usually free or very low |
| BTP ↔ On-Premise (Cloud Connector) | Low per-GB cost |
| BTP ↔ External (cross-region) | Standard cloud egress rates |

At typical agent usage (< 1 million requests/month), network costs are usually < 5% of total cost.

---

## 12. Estimation Methodology: Step-by-Step

### Step 1: Define Usage Profile

```
Monthly_Requests  = DAU × Requests_per_User_per_Day × Working_Days_per_Month
Occurrences/Month = Monthly_Requests × LLM_Calls_per_User_Request
```

Define three scenarios: **Conservative (P10), Base Case (P50), Peak (P90)**.

### Step 2: Profile the Agentic Loop

Planning defaults (use until prototyping data is available):

| Parameter | Conservative | Base | Peak |
|-----------|-------------|------|------|
| LLM calls per turn | 3 | 5 | 8 |
| Input tokens per LLM call | 1,500 | 3,000 | 6,000 |
| Output tokens per LLM call | 200 | 400 | 800 |
| Read Cached tokens per call | 0 | 0 | 0 |
| Write Cached tokens per call | 0 | 0 | 0 |
| Embedding calls per turn | 1 | 2 | 3 |
| Query tokens per embedding | 50 | 100 | 200 |

### Step 3: Calculate GenAI Tokens, Capacity Units (Raw and Billed), and EUR Cost

Worked examples — Base Case defaults — **1,000 monthly user requests** (Occurrences = 5,000; Input K = 15,000; Output K = 2,000):  
EUR cost = ROUND(Raw CU) × EUR 1.04. The SAP BTP calculator displays raw (unrounded) CU; the billed amount is the nearest whole integer.

#### Example A — Economy: amazon--nova-micro (Input 0.00003 / Output 0.00010)

| Scenario | Occurrences | GenAI Tokens | Raw CU | Billed CU | EUR/month (BTPEA) |
|----------|------------|-------------|--------|-----------|-------------------|
| Conservative | 3,000 | (4,500×0.00003)+(600×0.00010) = 0.195 | 0.371 | **0** | **EUR 0.00** |
| Base Case | 5,000 | (15,000×0.00003)+(2,000×0.00010) = 0.650 | 1.238 | **1** | **EUR 1.04** |
| Peak | 8,000 | (48,000×0.00003)+(6,400×0.00010) = 2.080 | 3.960 | **4** | **EUR 4.16** |

#### Example B — Standard: gpt-5-mini (Input 0.00024 / Output 0.00141)

| Scenario | Occurrences | GenAI Tokens | Raw CU | Billed CU | EUR/month (BTPEA) |
|----------|------------|-------------|--------|-----------|-------------------|
| Conservative | 3,000 | (4,500×0.00024)+(600×0.00141) = 1.926 | 3.668 | **4** | **EUR 4.16** |
| Base Case | 5,000 | (15,000×0.00024)+(2,000×0.00141) = 6.420 | 12.223 | **12** | **EUR 12.48** |
| Peak | 8,000 | (48,000×0.00024)+(6,400×0.00141) = 20.544 | 39.113 | **39** | **EUR 40.56** |

#### Example C — Premium: anthropic--claude-4.5-sonnet (Input 0.00223 / Output 0.01087)

| Scenario | Occurrences | GenAI Tokens | Raw CU | Billed CU | EUR/month (BTPEA) |
|----------|------------|-------------|--------|-----------|-------------------|
| Conservative | 3,000 | (4,500×0.00223)+(600×0.01087) = 16.557 | 31.522 | **32** | **EUR 33.28** |
| Base Case | 5,000 | (15,000×0.00223)+(2,000×0.01087) = 55.190 | 105.073 | **105** | **EUR 109.20** |
| Peak | 8,000 | (48,000×0.00223)+(6,400×0.01087) = 176.608 | 336.235 | **336** | **EUR 349.44** |

**Cross-model comparison — Base Case, 1,000 monthly requests:**

| Model | Raw CU | Billed CU | EUR/month (BTPEA) | vs. claude-4.5-sonnet |
|-------|--------|-----------|-------------------|----------------------|
| amazon--nova-micro 1 | 1.238 | 1 | **EUR 1.04** | ~1% |
| gpt-5-mini 2025-08-07 | 12.223 | 12 | **EUR 12.48** | ~11% |
| gpt-5 2025-08-07 | 51.766 | 52 | **EUR 54.08** | ~50% |
| anthropic--claude-4.5-sonnet 1 | 105.073 | 105 | **EUR 109.20** | 100% (baseline) |
| gpt-5.5 2026-04-24 | 174.393 | 174 | **EUR 180.96** | ~166% |

> Scale linearly: multiply by actual monthly requests ÷ 1,000.

### Steps 4–8

4. **Size Compute Runtime** — Section 5
5. **Size the Vector Store** — Section 6.2
6. **Calculate Supporting Service Costs** — Sections 7–11
7. **Sum all dimensions:**
```
Total CU/month = LLM_CU + Embedding_CU + [other services] + 15% contingency
```
8. **Sensitivity check:** Vary top 3 cost drivers ±50%; identify inputs requiring validation.

---

## 13. Cost Estimation Worksheet

> All LLM costs expressed in both GenAI tokens and Capacity Units. CU = GenAI tokens × 1.90385.

### 13.1 Usage Profile

| Parameter | Value | Unit |
|-----------|-------|------|
| Daily Active Users (DAU) | ___ | users |
| Requests per user per day | ___ | requests |
| Working days per month | 22 | days |
| **Monthly Request Volume** | `DAU × Req/user × Days` | requests/month |
| LLM calls per user request | ___ | calls |
| **Monthly Occurrences** | `Monthly Requests × LLM Calls` | occurrences/month |

### 13.2 LLM Inference Reference Table (Base Case, 1,000 monthly requests)

Defaults: 5 LLM calls/turn · 3,000 input/call · 400 output/call · no caching  
→ Input K = 15,000 · Output K = 2,000 · Occurrences = 5,000  
**Raw CU** = GenAI tokens × 1.90385 (calculator display value).  
**Billed CU** = ROUND(Raw CU) — nearest whole integer (SAP AI Core does not accept fractional CU).  
**EUR/month** = Billed CU × **EUR 1.04** (SAP BTPEA unit price per CU per month — Section 4.4). Scale linearly by actual monthly requests ÷ 1,000.

| Model | Tier | Input/1K | Output/1K | GenAI Tokens | Raw CU | Billed CU | EUR/month (BTPEA) | Status |
|-------|------|---------|-----------|-------------|--------|-----------|-------------------|--------|
| amazon--nova-micro 1 | Economy | 0.00003 | 0.00010 | 0.650 | 1.238 | **1** | **EUR 1.04** | Active |
| gpt-5-nano 2025-08-07 | Economy | 0.00001 | **0.00029** | 0.730 | 1.390 | **1** | **EUR 1.04** | Active |
| amazon--nova-lite 1 | Economy | 0.00004 | 0.00016 | 0.920 | 1.752 | **2** | **EUR 2.08** | Active |
| mistralai--mistral-small 2603 | Economy | 0.00007 | 0.00028 | 1.610 | 3.065 | **3** | **EUR 3.12** | Active |
| gemini-2.5-flash-lite 001 | Economy | 0.00008 | 0.00028 | 1.760 | 3.351 | **3** | **EUR 3.12** | Active |
| gemini-3.1-flash-lite 001 | Standard | 0.00020 | 0.00108 | 5.160 | 9.824 | **10** | **EUR 10.40** | Active |
| gpt-5-mini 2025-08-07 | Standard | 0.00024 | 0.00141 | 6.420 | 12.223 | **12** | **EUR 12.48** | Active |
| gpt-4.1-mini 2025-04-14 _(retiring 2026-10-14)_ | Standard | 0.00026 | 0.00099 | 5.880 | 11.195 | **11** | **EUR 11.44** | Retiring |
| mistralai--mistral-medium-instruct 2505 | Standard | 0.00036 | 0.00122 | 7.840 | 14.926 | **15** | **EUR 15.60** | Active |
| amazon--nova-pro 1 | Standard | 0.00056 | 0.00213 | 12.660 | 24.103 | **24** | **EUR 24.96** | Active |
| gpt-5.1 2025-11-13 | Standard | 0.00090 | 0.00675 | 27.000 | 51.404 | **51** | **EUR 53.04** | Active |
| gpt-5 2025-08-07 | Standard | 0.00091 | 0.00677 | 27.190 | 51.766 | **52** | **EUR 54.08** | Active |
| anthropic--claude-4.5-haiku 1 | Premium | 0.00079 | 0.00367 | 19.190 | 36.535 | **37** | **EUR 38.48** | Active |
| gpt-4.1 2025-04-14 _(retiring 2026-10-14)_ | Premium | 0.00129 | 0.00494 | 29.230 | 55.650 | **56** | **EUR 58.24** | Retiring |
| gpt-4o 2024-08-06 _(retiring 2026-10-01)_ | Premium | 0.00159 | 0.00616 | 36.170 | 68.862 | **69** | **EUR 71.76** | Retiring |
| **gpt-4o 2024-05-13** _(retiring 2026-10-01)_ | Premium | **0.00312** | **0.00920** | **65.200** | **124.131** | **124** | **EUR 128.96** | Retiring — **2× cost of 2024-08-06** |
| anthropic--claude-4.5-sonnet 1 | Premium | 0.00223 | 0.01087 | 55.190 | 105.073 | **105** | **EUR 109.20** | Active |
| gpt-5.5 2026-04-24 | Premium | 0.00342 | 0.02015 | 91.600 | 174.393 | **174** | **EUR 180.96** | Active |
| anthropic--claude-4.5-opus 1 | Premium | 0.00367 | 0.01806 | 91.170 | 173.574 | **174** | **EUR 180.96** | Active |

> **Rounding note:** Billed CU = ROUND(Raw CU). The deviation from raw CU is always ≤ 0.5 CU. For very low usage (raw CU < 0.5), billed CU rounds to 0 — no LLM inference charge for that month; AI Core Baseline costs (Calculator 2) still apply. Scale: multiply EUR/month by actual monthly requests ÷ 1,000.

### 13.3 Your Project's LLM Inference Worksheet

| Parameter | Conservative | Base Case | Peak |
|-----------|-------------|-----------|------|
| Monthly requests | ___ | ___ | ___ |
| LLM calls per request | ___ | ___ | ___ |
| Avg input tokens/call | ___ | ___ | ___ |
| Avg output tokens/call | ___ | ___ | ___ |
| Avg read cached tokens/call | ___ | ___ | ___ |
| Avg write cached tokens/call | ___ | ___ | ___ |
| Input rate (Section 4.3) | ___ | ___ | ___ |
| Output rate (Section 4.3) | ___ | ___ | ___ |
| Read cached rate (Section 4.3) | ___ | ___ | ___ |
| Write cached rate (Section 4.3) | ___ | ___ | ___ |
| **Total GenAI Tokens / month** | **___** | **___** | **___** |
| **Raw Capacity Units / month (× 1.90385)** | **___** | **___** | **___** |
| **Billed CU / month (ROUND of Raw CU)** | **___** | **___** | **___** |
| **EUR / month BTPEA (Billed CU × EUR 1.04)** | **___** | **___** | **___** |

### 13.4 Compute Runtime Cost Worksheet

| Parameter | Value | Unit |
|-----------|-------|------|
| Runtime type | CF / Kyma | — |
| Instance / Node count | ___ | — |
| Memory per instance (CF) | ___ | GB |
| Hours per month | 730 | hours |
| Price per GB-hour (CF) or per node-hour (Kyma) | ___ | USD |
| **Monthly Compute Cost** | `Count × Mem × Hours × Price` | USD |

### 13.5 HANA Cloud Vector Store Cost Worksheet

| Parameter | Value | Unit |
|-----------|-------|------|
| Number of vectors | ___ | vectors |
| Vector dimension | ___ | dimensions |
| Estimated RAM required | `N × D × 4 bytes × 1.8 ÷ 1GB + 32` | GB |
| HANA Cloud instance size | ___ | S/M/L/XL |
| Price per instance-hour | ___ | USD |
| Shared with other workloads? | Yes / No | — |
| Cost allocation % | ___ | % |
| **Monthly HANA Cost** | `Price/hr × 730 × Allocation%` | USD |

### 13.6 Embedding Cost Worksheet

| Parameter | Value | Unit |
|-----------|-------|------|
| Monthly user requests (with RAG) | ___ | requests |
| Avg query tokens per embedding call | ___ | tokens |
| Embedding calls per request | ___ | calls |
| Embedding model price / 1K tokens (Section 7.2) | ___ | GenAI tokens |
| Monthly embedding GenAI tokens | `Requests × Calls × Tokens/1,000 × Rate` | GenAI tokens |
| **Monthly Embedding CU (raw)** | `GenAI tokens × 1.90385` | CU |
| **Monthly Embedding CU (billed)** | `ROUND(raw CU)` | CU |
| Indexing amortised monthly (CU) | ___ | CU |

### 13.7 Integration and Supporting Services

| Service | Monthly Volume | Unit Price | Monthly Cost |
|---------|---------------|------------|--------------|
| SAP Integration Suite — API calls | ___ calls | ___ /call | ___ USD |
| SAP Integration Suite — messages | ___ messages | ___ /msg | ___ USD |
| SAP Object Store | ___ GB | ___ /GB | ___ USD |
| SAP Cloud Logging | ___ GB | ___ /GB | ___ USD |
| Network Egress | ___ GB | ___ /GB | ___ USD |
| Perplexity Sonar (if used) | ___ API calls | token CU + 0.00393–0.00942/call × 1.90385 | ___ CU |
| Cohere Reranker (if used) | ___ search_units | 0.00114 × 1.90385 per unit | ___ CU |
| **Subtotal** | | | **___ USD/CU** |

### 13.8 Total Monthly Cost Summary

> LLM Inference and Embedding are billed in **EUR** under SAP BTPEA (Billed CU × **EUR 1.04**).  
> AI Core Standard (Instances, Storage, Baseline) CU must be sourced from Calculator 2 — run once **per active subaccount**.  
> Orchestration and Prompt Optimization CU from Calculator 3 should be added to LLM/Embedding CU before applying ROUND.  
> Compute, HANA, Integration, and other BTP services are listed in **EUR** or USD depending on your contract. Align currency to your commercial model.

| Cost Dimension | Source | Conservative | Base Case | Peak |
|----------------|--------|-------------|-----------|------|
| LLM Inference (EUR — BTPEA) | Calculator 3 — Requests | ___ | ___ | ___ |
| Embedding Calls (EUR — BTPEA) | Calculator 3 — Requests | ___ | ___ | ___ |
| Orchestration (EUR — BTPEA) | Calculator 3 — Orchestration | ___ | ___ | ___ |
| Prompt Optimization (EUR — BTPEA) | Calculator 3 — Prompt Opt | ___ | ___ | ___ |
| AI Core Standard — Baseline | Calculator 2 (per subaccount) | ___ | ___ | ___ |
| AI Core Standard — Instances | Calculator 2 (per subaccount) | ___ | ___ | ___ |
| AI Core Standard — Storage | Calculator 2 (per subaccount) | ___ | ___ | ___ |
| Compute Runtime | BTP Estimator / Cockpit | ___ | ___ | ___ |
| HANA Cloud / Vector Store | BTP Estimator / Cockpit | ___ | ___ | ___ |
| Integration Services | BTP Estimator / Cockpit | ___ | ___ | ___ |
| Storage | BTP Estimator / Cockpit | ___ | ___ | ___ |
| Observability | BTP Estimator / Cockpit | ___ | ___ | ___ |
| Network | BTP Estimator / Cockpit | ___ | ___ | ___ |
| **Subtotal** | | **___** | **___** | **___** |
| Contingency (+15%) | | ___ | ___ | ___ |
| **Total Monthly Cost** | | **___** | **___** | **___** |

---

## 14. Cost Sensitivity and Scaling Factors

### 14.1 Typical Cost Distribution

For a mid-scale RAG-enabled agent (1,000–10,000 requests/day, standard LLM):

| Dimension | Typical Share |
|-----------|--------------|
| LLM Inference (all calls) | 60% – 80% |
| HANA Cloud (Vector Store) | 10% – 20% |
| Compute Runtime | 5% – 15% |
| Embedding Calls | 2% – 5% |
| Integration + Storage + Other | 2% – 8% |

### 14.2 Scale Impact Table (gpt-5-mini reference)

| Monthly Request Volume | Raw LLM CU | Billed CU (ROUND) | Rounding Delta | Dominant Cost Driver |
|------------------------|------------|-------------------|----------------|----------------------|
| 100 | 1.2 | 1 | −0.2 CU (−17%) | AI Core Baseline + LLM inference |
| 500 | 6.1 | 6 | −0.1 CU (−2%) | AI Core Baseline |
| < 1,000 | < 12.2 | ≤12 | ±0.5 CU max | HANA Cloud (fixed baseline) |
| 1,000 – 10,000 | 12 – 122 | 12–122 | ±0.5 CU max | LLM Inference |
| 10,000 – 100,000 | 122 – 1,220 | 122–1,220 | ±0.5 CU max (<0.1%) | LLM Inference |
| > 100,000 | > 1,220 | >1,220 | ±0.5 CU max (<0.05%) | LLM Inference + Compute |

### 14.3 High-Impact Variables

| Variable | Impact | Action |
|----------|--------|--------|
| LLM model selection | Very High | Validate if smaller model meets quality bar |
| LLM calls per agent turn | Very High | Minimise unnecessary reasoning steps |
| Model version (e.g. gpt-4o 2024-05-13 vs 2024-08-06) | High | Confirm deployed version in AI Core config |
| Context window size per call | High | Limit RAG chunks; compress history |
| Request volume growth | High | Model monthly growth; review quarterly |
| HANA Cloud instance size | Medium | Right-size; stop non-production instances |

---

## 15. Cost Optimization Strategies

### 15.1 LLM Cost Reduction

| Strategy | Mechanism | Estimated Saving |
|----------|-----------|-----------------|
| **Semantic caching** | Cache LLM responses for similar queries | 15% – 40% |
| **Model tiering** | Economy models for simple tasks; premium for complex | 20% – 50% |
| **Prompt caching** | Read Cached for stable long system prompts | 10% – 30% |
| **Prompt compression** | Reduce system prompt verbosity | 10% – 25% |
| **RAG chunk optimisation** | Reduce chunk size and top-K | 10% – 30% |
| **Conversation history truncation** | Last N turns + summary | 10% – 20% |
| **Output length control** | Set max_tokens per call type | 5% – 15% |
| **Batch API for offline tasks** | ~50% saving on eligible workloads | ~50% |

### 15.2 Compute Cost Reduction

| Strategy | Guidance |
|----------|----------|
| **Auto-scaling** | CF App Autoscaler / Kyma HPA; scale to 1 during off-hours |
| **Right-sizing** | Profile actual memory before scaling up |
| **Shared infrastructure** | Share HANA Cloud and node pools across agents |
| **Stop non-prod** | Shut down dev/test instances outside business hours |

### 15.3 HANA Cloud Cost Reduction

| Strategy | Guidance |
|----------|----------|
| **Instance sharing** | Separate schemas per use case within one instance |
| **Scheduled stop/start** | Stop non-production instances automatically |
| **Index maintenance** | Periodically clean up stale embeddings |

### 15.4 Architecture-Level Optimisations

| Strategy | Description |
|----------|-------------|
| **Async processing** | Decouple long-running tasks from synchronous user response |
| **Tool result caching** | Cache frequent SAP API responses (product master, config) |
| **Pre-computed summaries** | Summarise at ingestion time to reduce per-query token load |
| **Agent specialisation** | Route simple queries to single-call flows; reserve loops for complex tasks |

---

## 16. Governance and Cost Monitoring on BTP

### 16.0 SAP AI Core Cost Calculators — Quick Reference

Use all three tools together for a complete cost estimate:

| Calculator | URL | What it Covers | Run Frequency |
|-----------|-----|---------------|---------------|
| **SAP BTP Service Estimator** | [discovery-center.cloud.sap/estimator](https://discovery-center.cloud.sap/protected/index.html#/estimator/539CA2A9-3973-47FC-80C1-EBCF5499099B/) | Full BTP portfolio; consolidated EUR bill | Monthly or at major scope changes |
| **AI Core Standard Calculator** | [ai-core-calculator/core](https://ai-core-calculator.cfapps.eu10.hana.ondemand.com/uimodule/index.html#/core) | Instances (node hours) · Storage (GB hours) · Baseline (tenant hours) | Per subaccount; revisit when adding regions or hyperscalers |
| **Generative AI Hub Calculator** | [ai-core-calculator/gen](https://ai-core-calculator.cfapps.eu10.hana.ondemand.com/uimodule/index.html#/gen) | Requests (CU) · Orchestration (CU) · Prompt Optimization (CU) | Per model change or usage volume change |

> **Multi-subaccount rule:** If your deployment spans multiple BTP subaccounts (separate regions, hyperscalers, or environments), run the AI Core Standard Calculator (above) independently for each subaccount. CU costs from each subaccount are billed separately.

### 16.1 BTP Cost Visibility

| Capability | Description |
|------------|-------------|
| **SAP BTP Cockpit — Usage Analytics** | View CU consumption per subaccount, directory, or global account |
| **Cost and Revenue Management API** | Programmatic usage data for FinOps dashboards |
| **Alerts on CPEA Credits** | Threshold alerts at 70%, 90%, 100% |
| **SAP AI Core Usage Metrics** | Token consumption per scenario, deployment, and resource group |

### 16.2 Cost Governance Recommendations

- Tag subaccounts by project and cost centre
- Separate dev / test / prod subaccounts
- Monthly cost review: compare actual vs. estimated CU; update worksheet monthly
- Instrument agent to log token counts per request for internal chargeback

### 16.3 AI Core Resource Group Governance

Use separate resource groups per:
- Deployment environment (dev / prod)
- Business unit or cost centre
- Agent use case

---

## 17. Key Assumptions and Limitations

| Assumption | Description |
|------------|-------------|
| **Commercial model** | LLM inference costs are validated against **SAP BTPEA** (BTP Enterprise Agreement), which bills in EUR. The unit price is **EUR 1.04 per Capacity Unit per month**, confirmed from the BTP Service Estimator. Other commercial models (CPEA, PAYG) may differ — verify with your SAP Account Executive. |
| **CU rounding** | SAP AI Core does not accept fractional Capacity Units. Raw CU values are **rounded to the nearest whole integer** (standard ROUND). The SAP BTP calculator displays raw values; the billed amount is the rounded integer. Maximum rounding deviation is ±0.5 CU regardless of volume. Confirmed: raw 13.4926 CU → ROUND → 13 CU (BTP estimator). |
| **Billing currency** | GenAI Hub / LLM inference under SAP BTPEA bills in **EUR** per Capacity Unit. Other BTP services (compute, storage) may be in EUR or USD. Align your total cost model to your contract currency. |
| **EUR/CU rate** | **EUR 1.04/CU** is the observed unit price from the SAP BTP Service Estimator (Standard plan, Australia (Sydney) AWS). Rates may vary by region, hyperscaler, contract tier, or change over time. Always verify the applicable rate with your SAP Account Executive. |
| **Single-region deployment** | Multi-region HA adds compute and egress costs |
| **No custom fine-tuning** | Training compute costs are out of scope |
| **Managed LLM models** | Assumes hosted endpoints via Generative AI Hub |
| **Price stability** | Token rates change frequently — review SAP Note 3437766 at minimum quarterly |
| **Agent framework neutral** | Applies regardless of framework (LangChain, SAP AI SDK, custom) |

---

## 18. Glossary

| Term | Definition |
|------|------------|
| **AI Agent** | Autonomous application that uses an LLM for reasoning and executes multi-step actions |
| **Agentic Loop** | Iterative cycle of perceive → reason → act per user request |
| **Batch API** | Asynchronous inference mode (~50% cost saving); results not returned in real time |
| **Capacity Unit (CU)** | SAP BTP billing unit for AI Core consumption. Raw CU = Total GenAI tokens × 1.90385. **Billed CU = ROUND(Raw CU)** — SAP AI Core accepts only whole integers; standard nearest-integer rounding applies. Unit price: **EUR 1.04 per CU per month** (SAP BTPEA). |
| **BTPEA** | BTP Enterprise Agreement — SAP commercial model for BTP under which GenAI Hub bills in EUR per Capacity Unit |
| **AI Core Standard Calculator** | SAP-provided tool for estimating AI Core infrastructure costs (Instances, Storage, Baseline). Must be run per subaccount. URL: https://ai-core-calculator.cfapps.eu10.hana.ondemand.com/uimodule/index.html#/core |
| **GenAI Hub Calculator** | SAP-provided tool for estimating Generative AI Hub usage costs (Requests, Orchestration, Prompt Optimization). URL: https://ai-core-calculator.cfapps.eu10.hana.ondemand.com/uimodule/index.html#/gen |
| **Orchestration (AI Core)** | SAP AI Core service layer providing grounding, content filtering, and tool-use management for LLM calls. Incurs a small per-request CU overhead in addition to model token costs (see SAP Note 3505347). |
| **Prompt Optimization** | Optional SAP AI Core feature that automatically refines prompts at runtime. Incurs CU charges only when explicitly enabled. |
| **CPEA** | Cloud Platform Enterprise Agreement — SAP's consumption-based BTP commercial model |
| **Embedding** | Numerical vector representation of text for semantic similarity search |
| **GenAI Token** | SAP's metering unit: GenAI tokens per 1,000 model tokens processed |
| **Generative AI Hub** | SAP AI Core capability providing access to hosted LLM models via a unified API |
| **RAG** | Retrieval-Augmented Generation — enhances LLM responses with retrieved context |
| **Rate Limit** | Maximum API requests per minute per AI Core tenant for a given model |
| **Read Cached Input** | Input tokens served from provider-side prompt cache at a discounted rate |
| **Resource Group** | Isolation boundary in SAP AI Core for workloads, tenants, or cost centres |
| **SAP Note 3437766** | Authoritative note listing all Generative AI Hub models, pricing, rate limits, and deprecation status |
| **SAP Note 3505347** | SAP Note covering Orchestration module GenAI token conversion rates |
| **search_unit** | Billing unit for Cohere Reranker calls |
| **Token** | Basic LLM text processing unit; approximately 0.75 English words |
| **Vector Engine** | SAP HANA Cloud capability for storing and querying embedding vectors |
| **Write Cached Input** | Input tokens that populate a provider-side prompt cache for the first time |
| **BTP** | SAP Business Technology Platform |
| **CF Runtime** | SAP BTP, Cloud Foundry Runtime |
| **Kyma Runtime** | SAP BTP, Kyma Runtime (Kubernetes-based) |
| **GB-hour** | 1 GB of RAM consumed for 1 hour (CF Runtime billing unit) |

---

## 19. Model Deprecation Risk and Migration Paths

> **Source:** SAP Note 3437766, Version 153, 07.07.2026. Retirement dates may be adjusted. Monitor the note.

### 19.1 URGENT — Retiring Within 90 Days (as of 2026-07-09)

| Model | Retirement Date | Days Remaining | Migration Target |
|-------|----------------|----------------|-----------------|
| **o1** 2024-12-17 | **2026-07-15** | **6 days** | o3 or o4-mini |
| **o3-mini** 2025-01-31 | **2026-08-02** | 24 days | o4-mini |
| **sap-abap-1** 1 | not earlier than 2026-08-30 | ~52 days | Monitor SAP Note 3437766 |
| **cohere--command-a-reasoning** 2508 | not earlier than 2026-08-30 | ~52 days | Monitor SAP Note 3437766 |
| **amazon--nova-premier** 1 | **2026-09-10** | ~63 days | amazon--nova-lite 2 |
| **anthropic--claude-3-haiku** 1 | **2026-09-10** | ~63 days | anthropic--claude-4.5-haiku |
| **mistralai--mistral-large-instruct** 2407 | not earlier than 2026-09-30 | ~83 days | mistral-medium-instruct 2505 or gpt-5 |
| **mistralai--mistral-small-instruct** 2503 | not earlier than 2026-09-30 | ~83 days | mistralai--mistral-small 2603 |
| **nvidia--llama-3.2-nv-embedqa-1b** v2 | not earlier than 2026-09-30 | ~83 days | Monitor SAP Note 3437766 |
| **cohere-reranker** 3.5 | not earlier than 2026-09-30 | ~83 days | Monitor SAP Note 3437766 |

### 19.2 Retiring Q4 2026

| Model | Retirement Date | Migration Target | Notes |
|-------|----------------|-----------------|-------|
| gpt-4o 2024-05-13 | 2026-10-01 | gpt-5 | **Input rate 0.00312 — 2× higher than 2024-08-06. Verify version before migrating.** |
| gpt-4o 2024-08-06 | 2026-10-01 | gpt-5 | — |
| gpt-4o 2024-11-20 | 2026-10-01 | gpt-5 | — |
| gpt-4o-mini 2024-07-18 | 2026-10-01 | gpt-5-mini | Pricing comparable |
| anthropic--claude-4-sonnet 1 | 2026-10-14 | anthropic--claude-4.5-sonnet | Write cached rate unchanged (0.00254) |
| gpt-4.1 2025-04-14 | 2026-10-14 | gpt-5 | Batch API available for both (gpt-5: US only) |
| gpt-4.1-mini 2025-04-14 | 2026-10-14 | gpt-5-mini | Batch API available for gpt-4.1-mini |
| gpt-4.1-nano 2025-04-14 | 2026-10-14 | gpt-5-nano | Batch API available for gpt-4.1-nano |
| gemini-2.5-flash 001 | 2026-10-16 | gemini-2.5-flash-lite or gemini-3.1-flash-lite | Verify region availability |
| gemini-2.5-pro 001 | 2026-10-16 | gemini-3.5-flash | Replacement pricing significantly higher |
| o3 2025-04-16 | 2026-10-16 | Monitor SAP Note 3437766 | — |
| o4-mini 2025-04-16 | 2026-10-16 | Monitor SAP Note 3437766 | — |

### 19.3 Migration Cost Impact Assessment

When migrating from any retiring model:

1. **Re-run Section 13.2** with replacement model prices.
2. **Test prompt compatibility:** System prompt changes affect token counts and cost.
3. **Update model selector strings** in code and AI Core configuration before the retirement date.
4. **Budget for parallel-running period** (2–4 weeks) — temporarily increases inference cost.
5. **Verify the gpt-4o version:** If your deployment inadvertently uses 2024-05-13, actual cost is 2× estimates based on 2024-08-06. Check the AI Core resource group configuration.

### 19.4 Deprecation Monitoring Governance

- Subscribe to SAP Note 3437766 change notifications in SAP for Me.
- Include exact model name, version, and retirement date in every architecture decision record.
- Review SAP Note 3437766 at the start of each project phase and at minimum once per quarter.

---

## 20. Special and Non-Standard Pricing Reference

> **Source:** SAP Note 3437766, Version 153, 07.07.2026.

### 20.1 Batch API (Asynchronous Inference)

Reduces cost by approximately 50% by processing requests offline. Available in **EU and US regions only**, except prod-euonly and sovereign cloud deployments.

| Model | Batch Input / 1K | Batch Output / 1K | Standard Input | Standard Output | Region |
|-------|-----------------|------------------|----------------|-----------------|--------|
| gpt-4.1 2025-04-14 | 0.00064 | 0.00247 | 0.00129 | 0.00494 | EU, US |
| gpt-4.1-mini 2025-04-14 | 0.00013 | 0.00049 | 0.00026 | 0.00099 | EU, US |
| gpt-4.1-nano 2025-04-14 | 0.00004 | 0.00013 | 0.00008 | 0.00026 | EU, US |
| gpt-5 2025-08-07 | 0.00045 | 0.00338 | 0.00091 | 0.00677 | **US only** |

**When to use Batch API:** Overnight document analysis, bulk summarisation, non-interactive report generation, entity extraction.  
**When NOT to use:** User-facing interactive calls; tool-call loops requiring sequential LLM responses.

**Capacity Units comparison — Base Case, 1,000 monthly requests:**

| Model | Standard CU | Batch CU | Saving |
|-------|-------------|----------|--------|
| gpt-4.1 | 55.641 | 27.820 | ~50% |
| gpt-4.1-mini | 11.195 | 5.598 | ~50% |
| gpt-5 | 51.773 | 25.886 | ~50% |

### 20.2 SAP RPT Models — Cells-Based Pricing

`sap-rpt-1` models use a **cells-based** pricing unit, not tokens.

| Model | Input / 1,000 cells | Predict / 1,000 cells |
|-------|--------------------|-----------------------|
| sap-rpt-1-small | 0.00020 | 0.02054 |
| sap-rpt-1-large | 0.00055 | 0.07630 |

> Prediction cost is approximately 100× the input cost.

**Example — 10,000-cell report, sap-rpt-1-large:**
```
Input GenAI tokens:   10 × 0.00055 = 0.00550
Predict GenAI tokens: 10 × 0.07630 = 0.76300
Total GenAI tokens:                = 0.76850
Capacity Units:       0.76850 × 1.90385 ≈ 1.463 CU per report
At 1,000 reports/month:            ≈ 1,463 CU/month
```

### 20.3 Perplexity Sonar / Sonar Pro — Token Rates and Web Search Fee

Perplexity models incur **both** token-based GenAI charges **and** a flat per-call web search fee.

**Token rates (GenAI tokens per 1,000 model tokens):**

| Model | Input | Output |
|-------|-------|--------|
| sonar | 0.00086 | 0.00086 |
| sonar-pro | 0.00243 | 0.01185 |

**Web search request fee (per API call, in addition to token rates):**

| Search Context Size | Fee per API Call (GenAI tokens) |
|--------------------|---------------------------------|
| low | 0.00393 |
| medium | 0.00628 |
| high | 0.00942 |

**Example — sonar-pro, medium search context, 500 input + 500 output tokens, 1,000 requests/month:**
```
Token GenAI tokens:  1,000 × (0.5×0.00243 + 0.5×0.01185) = 7.140
Search fee GenAI:    1,000 × 0.00628                      = 6.280
Total GenAI tokens:                                        = 13.420
Capacity Units:      13.420 × 1.90385                      ≈ 25.550 CU/month
```

### 20.4 Cohere Reranker — Per search_unit Pricing

| Model | Price per search_unit (GenAI tokens) |
|-------|--------------------------------------|
| cohere-reranker 3.5 | 0.00114 |

**Example — top-20 chunk reranking, 10,000 requests/month:**
```
search_units:    10,000 × 20 = 200,000
GenAI tokens:    200,000 × 0.00114 = 228.000
Capacity Units:  228.000 × 1.90385 ≈ 434.1 CU/month
```

---

## 21. Rate Limit Risk and Design Implications

> **Source:** SAP Note 3437766, Version 153, 07.07.2026.  
> Limits are applied per AI Core tenant (BTP subaccount). Multiple deployments of the same model under the same tenant share the published limit.

### 21.1 Complete Rate Limit Reference

| Provider | Model | Rate Limit (req/min/tenant) |
|----------|-------|-----------------------------|
| Mistral (SAP-hosted) | mistral-large-instruct 2407 | 100 |
| Mistral (SAP-hosted) | mistral-small-instruct 2503 | 100 |
| Mistral (SAP-hosted) | mistral-medium-instruct 2505 | 240 |
| Mistral (SAP-hosted) | mistral-small 2603 | 100 |
| NVIDIA (SAP-managed) | nvidia--llama-3.2-nv-embedqa-1b v2 | 138 |
| Cohere (SAP-hosted) | cohere--command-a-reasoning 2508 | 240 |
| Cohere (SAP-hosted) | cohere-reranker 3.5 | 100 |
| SAP (SAP-hosted) | sap-abap-1, sap-rpt-1-small, sap-rpt-1-large | 100 |
| Perplexity | sonar, sonar-pro | 100 |
| AWS Bedrock | amazon--nova-micro/lite/pro/premier | **50** |
| AWS Bedrock | amazon--titan-embed-text v1.2, nova models | **50** |
| AWS Bedrock | amazon--titan-embed-text v2 | 138 |
| AWS Bedrock | amazon--titan-embed-image v1 | 120 |
| AWS Bedrock | anthropic--claude-3-haiku | 50 |
| AWS Bedrock | anthropic--claude-4-sonnet, claude-4.5/4.6/4.7/4.8 | 100 |
| Azure OpenAI | text-embedding-3-small, text-embedding-3-large | 138 |
| Azure OpenAI | text-embedding-ada-002 | 600 (EU10/US10); 138 elsewhere |
| Azure OpenAI | gpt-4o (all versions) | 78 |
| Azure OpenAI | gpt-4o-mini | 120 |
| Azure OpenAI | gpt-4.1 | 78 |
| Azure OpenAI | gpt-4.1-mini, gpt-4.1-nano | 120 |
| Azure OpenAI | gpt-5 | 78 |
| Azure OpenAI | gpt-5.1, gpt-5.2, gpt-5.5 | 100 |
| Azure OpenAI | gpt-5-mini, gpt-5-nano, gpt-5.2-nano, gpt-5.3-codex, gpt-5.4, gpt-5.4-nano | 120 |
| Azure OpenAI | o1 | 78 |
| Azure OpenAI | o3-mini | 120 |
| Azure OpenAI | o3 | 78 |
| Azure OpenAI | o4-mini | 120 |
| Google Vertex | All gemini text/embedding models | 100 |
| Google Vertex | gemini-2.5-flash-image | 10 |
| Google Vertex | gemini-3-pro-image, gemini-3.1-flash-image | 20 |

> **Correction from v2:** AWS Bedrock nova models (nova-micro, nova-lite, nova-pro) rate limit is **50 req/min**, not 138.

### 21.2 Throughput Ceiling Formula

```
Max sustained user requests/min =
  Rate_Limit_per_Min / LLM_Calls_per_User_Request

Example (gpt-5, 78 req/min, 5 LLM calls/turn):
  78 / 5 = 15.6 user requests/minute maximum
```

For burst traffic above this ceiling:
- **Request queuing** via SAP Advanced Event Mesh or Redis
- **Exponential backoff with jitter** on all LLM client calls
- **Multi-model routing** — simple calls to higher-limit economy tier models

### 21.3 Multi-Tenant Considerations

Rate limits are per tenant (BTP subaccount). Multiple agents or teams sharing one AI Core instance compete against the same limit. Use **separate resource groups per environment** to isolate limits.

### 21.4 Cost Implication of 429 Errors

A 429 response is not billed — no tokens are consumed. However, poor retry logic triggers retry storms that compound the problem. Design retry policy with exponential backoff and jitter from the start.

### 21.5 Rate Limit Governance Checklist

- [ ] Confirm rate limit for your primary model in SAP Note 3437766 before finalising architecture
- [ ] Calculate max sustained throughput ceiling and compare to peak demand forecast
- [ ] Implement exponential backoff with jitter on all LLM client calls
- [ ] Use separate resource groups per environment
- [ ] Monitor 429 response rates via SAP Cloud Logging; alert if rate > 1% of requests
- [ ] Evaluate multi-model routing for economy tier calls to distribute load

---

*This document is maintained by the AI Technical Architecture practice. Version 3.0 is fully aligned with SAP Note 3437766 (Availability of Generative AI Models, Version 153, released 07.07.2026). Review and update the cost worksheet at the start of each project phase and at minimum quarterly in production. Subscribe to SAP Note 3437766 change notifications in SAP for Me to stay current on model pricing, rate limits, and deprecation status.*

*For current BTP Capacity Unit pricing and commercial model details, refer to the [SAP Discovery Center](https://discovery-center.cloud.sap) or contact your SAP Account Executive.*
