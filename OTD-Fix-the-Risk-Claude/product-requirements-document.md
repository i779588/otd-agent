# Product Requirements Document (PRD)

**Title:** OTD-Fix-the-Risk: On-Time Delivery Advisory Agent
**Date:** 2026-09-28
**Owner:** Supply Chain Product Owner
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**
Supply Chain Planners spend hours manually cross-referencing SAP data to detect delivery risks. By the time a risk is identified, the mitigation window has often closed. OTD-Fix-the-Risk is an AI advisory agent that proactively identifies at-risk sales orders, diagnoses root causes, scores priorities, and delivers actionable recommendations — all in zero-write, human-in-the-loop mode.

**Business Need:**
There is no intelligent layer today that synthesizes cross-functional signals (orders, inventory, production, logistics) and surfaces prioritized, evidence-based recommendations proactively. Planners operate reactively, relying on manual triage across multiple SAP applications. This creates a systemic gap between risk detection and mitigation.

**Expected Value:**
- OTD rate improved from ~80% to 95% within 6 months
- Time-to-detect delays reduced from ~48 hours to under 4 hours within 3 months
- Planner manual triage time reduced from ~3 hrs/day to under 30 min/day within 6 months

**Product Objectives (Prioritized):**
1. Proactively detect and surface at-risk sales orders before the delivery window closes
2. Provide credible, evidence-based root-cause diagnosis with transparent confidence ratings
3. Deliver prioritized, actionable advisory dossiers that planners can act on without additional research
4. Generate executive-ready OTD risk summaries on demand
5. Maintain strict zero-write, advisory-only operation at all times

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| OTD Rate | ~80% (industry avg) | 95% | 6 months | Order Fulfillment / Delivery Risk Management | agent-derived |
| Time-to-Detect Delay | ~48 hours | < 4 hours | 3 months | Risk Detection & Alerting | agent-derived |
| Planner Time on Manual Risk Triage | ~3 hrs/day | < 30 min/day | 6 months | Supply Chain Planning Advisory | agent-derived |

---

## User Profiles & Personas

### Primary Persona: Marcus — Supply Chain Planner / Order Management Specialist

Marcus is a 34-year-old supply chain planner at a mid-to-large manufacturing company. He manages a portfolio of 200–400 active sales orders daily across multiple customer segments. His day starts by checking open delivery exceptions in SAP, which currently takes over an hour of manual cross-referencing across Manage Sales Orders, stock overview, and production reports. He is frustrated that by the time he identifies a risk, the expediting options are already limited. Marcus is technically proficient with SAP but is not a data scientist — he needs insights presented in plain language with clear next steps he can take in SAP. He judges the agent's value by how much time it saves him and whether the recommendations are actionable.

**Goals:**
- Know which orders are at risk before customers complain
- Understand the root cause quickly without digging through multiple SAP screens
- Get a prioritized list so he works on the highest-impact issues first
- Have clear, copy-ready next steps to take in SAP applications

**Key Tasks:**
- Review daily at-risk order list surfaced by the agent
- Query root cause and recommended actions for a specific order
- Validate priority scoring against customer tier and SLA exposure
- Copy recommended action steps into SAP (Manage Sales Orders, MRP, etc.)

### Secondary Persona: Diana — Supply Chain Director / Executive

Diana is a 47-year-old Supply Chain Director responsible for OTD KPI performance across the business. She reviews weekly performance reports and is accountable to the CFO for on-time delivery metrics and associated SLA penalty exposure. She does not operate SAP day-to-day but needs a reliable, jargon-free picture of current OTD risk exposure and what is being done about it. She uses the agent to generate on-demand executive summaries before leadership reviews.

**Goals:**
- Understand aggregate OTD risk exposure in minutes, not hours
- Forecast likely KPI impact without waiting for weekly reports
- Identify systemic bottleneck patterns across the order portfolio

**Key Tasks:**
- Request executive OTD risk summary before leadership meetings
- Review KPI impact forecast and identify top risk categories
- Ask follow-up questions about specific customer segments or risk drivers

---

## Product Principles

1. **Advisory-Only, Always:** The agent never modifies any data in any system. All execution is performed by authorized humans. This is non-negotiable.
2. **Confidence Transparency:** Every recommendation states its confidence level (High / Medium / Low) and discloses which signals were unavailable. No silent assumptions.
3. **Planner-First Design:** Outputs are structured for planners to act immediately — root cause, recommended action, copy-ready next steps — not for data exploration.
4. **Signal Completeness Over Speed:** If critical signals are missing, the agent flags the gap rather than speculating. Partial diagnoses are labelled as such.
5. **Human-in-the-Loop:** All business-impacting recommendations require explicit human review and manual execution. The agent proposes; the planner decides and acts.

---

## Goals and Non-Goals

### Goals (In Scope)

- Detect sales orders at risk of missing confirmed delivery dates using live SAP S/4HANA signals
- Classify the primary root cause of each delay into one of four approved categories
- Score and rank at-risk orders using a multi-dimensional priority matrix (customer tier, SLA penalty, order value)
- Generate a per-order advisory dossier including root cause, confidence rating, recommended actions, and suggested revised promise date
- Generate on-demand executive summaries of aggregate OTD risk exposure
- Enforce strict read-only operation — no write-back tools registered at any layer
- Disclose missing signals and downgrade confidence ratings accordingly
- Respect the user's RBAC permissions — never surface data the active user is not authorized to view

### Non-Goals (Out of Scope)

- Directly updating any SAP transaction (sales orders, production orders, inventory records, delivery documents)
- Automatically changing promise dates or releasing blocked orders
- Sending emails or messages to customers, suppliers, or carriers
- Replacing the planner's judgment — the agent informs and advises, never decides
- Real-time external carrier tracking (Freight Order API provides internal logistics data only)

---

## Requirements

### Must-Have Requirements

**R1: At-Risk Order Detection**
- **Problem to Solve:** Planners have no automated way to identify which orders are at risk of missing delivery dates without manual cross-referencing across multiple SAP screens.
- **User Story:** As a Supply Chain Planner, I need the agent to identify and list all sales orders currently at risk of missing their confirmed delivery dates, so that I can focus my attention where it matters most.
- **Acceptance Criteria:**
  - Given a planner asks "Which orders are at risk today?", when the agent queries SAP S/4HANA signals (sales orders, inventory, production, outbound delivery), then it returns a prioritized list of at-risk orders with order ID, customer name, delivery date, and risk indicator.
  - Given signals are partially unavailable, when the agent detects missing data, then it includes a confidence flag on the affected orders.
- **Maps to Objective:** 1 — Proactive risk detection
- **Priority Rank:** 1

**R2: Root-Cause Classification**
- **Problem to Solve:** When an order is flagged as at risk, planners spend additional time diagnosing the cause, often without access to correlated cross-functional data.
- **User Story:** As a Supply Chain Planner, I need the agent to diagnose the most likely root cause of a delay for a specific order and assign it to an approved category, so that I can take targeted corrective action.
- **Acceptance Criteria:**
  - Given a planner asks about a specific order, when the agent analyzes available signals, then it returns a root-cause classification from: Material Shortage, Capacity/Production Constraint, Warehouse/Logistics Bottleneck, or Transit/Carrier Delay.
  - Given the classification is made, then a confidence rating (High / Medium / Low) and the supporting signals used are stated.
  - Given critical signals are missing, then the agent states: "Unable to determine root cause with high confidence due to missing [signal name]."
- **Maps to Objective:** 2 — Evidence-based root-cause diagnosis
- **Priority Rank:** 2

**R3: Multi-Dimensional Priority Scoring**
- **Problem to Solve:** Not all at-risk orders have equal business impact; planners need a way to triage by strategic importance, not just by delivery date.
- **User Story:** As a Supply Chain Planner, I need at-risk orders ranked by a priority score that accounts for customer tier, SLA penalty exposure, and order revenue value, so that I always work on the highest-impact issue first.
- **Acceptance Criteria:**
  - Given a list of at-risk orders, when the agent computes priority scores, then Tier 1 (strategic) customers with SLA penalty exposure rank above lower-tier orders of equal monetary value.
  - Given the priority list is returned, then each order displays its priority score components (customer tier weight, SLA risk, order value) for planner transparency.
- **Maps to Objective:** 3 — Prioritized, actionable advisory
- **Priority Rank:** 3

**R4: Advisory Dossier Generation**
- **Problem to Solve:** Planners must currently assemble remediation options manually from separate SAP applications, making response time slow and inconsistent.
- **User Story:** As a Supply Chain Planner, I need the agent to generate a complete advisory dossier per at-risk order, so that I can act immediately without additional research.
- **Acceptance Criteria:**
  - Given a planner requests details on a specific at-risk order, when the agent generates a dossier, then the dossier contains: root cause, confidence rating, 2–3 recommended mitigation actions, a suggested revised promise date, and copy-ready next steps referencing the relevant SAP application (e.g., "In Manage Sales Orders, navigate to order [ID] and…").
  - Given the dossier is generated, then no write-back action is triggered or suggested as automated.
- **Maps to Objective:** 3 — Actionable advisory dossiers
- **Priority Rank:** 4

**R5: Executive OTD Risk Summary**
- **Problem to Solve:** Supply Chain Directors have no quick way to get a narrative overview of OTD risk exposure before leadership meetings.
- **User Story:** As a Supply Chain Director, I need the agent to generate an executive-ready OTD risk summary on demand, so that I can present current risk exposure and expected KPI impact in leadership reviews without waiting for manual reports.
- **Acceptance Criteria:**
  - Given a director asks for an executive summary, when the agent aggregates at-risk order data, then it returns a plain-language summary covering: total orders at risk, breakdown by root-cause category, estimated OTD KPI impact, and top recommended actions.
  - Given the summary is generated, then it contains no technical jargon and is suitable for direct presentation to leadership.
- **Maps to Objective:** 4 — Executive-ready summaries
- **Priority Rank:** 5

**R6: Zero-Write Guardrail Enforcement**
- **Problem to Solve:** Any accidental or unauthorized write-back to SAP systems would be a compliance and operational risk.
- **User Story:** As a Compliance Officer, I need the agent to be technically incapable of modifying any data in any SAP system, so that advisory-only operation is guaranteed by design, not just policy.
- **Acceptance Criteria:**
  - Given any user interaction, when the agent processes a request, then no MCP tool with write, create, update, or delete capabilities is registered or invocable.
  - Given a user explicitly asks the agent to update an order, then the agent responds that it is advisory-only and provides the manual steps the user should take instead.
- **Maps to Objective:** 5 — Zero-write advisory operation
- **Priority Rank:** 1 (parallel constraint, not sequential)

**R7: RBAC-Compliant Data Access**
- **Problem to Solve:** Sensitive order, pricing, and customer data must not be surfaced to users who are not authorized to view it.
- **User Story:** As a Security Administrator, I need the agent to respect the active user's existing SAP data access permissions, so that the agent never exposes data beyond the user's authorized scope.
- **Acceptance Criteria:**
  - Given a user queries orders, when the agent fetches data via MCP tools, then only data accessible under the user's SAP credentials is returned and surfaced.
  - Given a user without Tier 1 customer access asks about a Tier 1 order, then the agent does not reveal that order's details.
- **Maps to Objective:** 5 — Governance and compliance
- **Priority Rank:** 2 (parallel constraint)

---

## Non-Functional Requirements

### Performance
- **Latency:** Risk detection queries should return results within 10 seconds for portfolios up to 500 active orders.
- **Advisory Dossier:** Per-order advisory dossier generation should complete within 15 seconds.

### Reliability
- **Availability:** Agent should be available during business hours with graceful degradation if one SAP API signal is temporarily unavailable.
- **Fallback:** If an API signal is unavailable, the agent continues with remaining signals and discloses the missing data clearly in its response.

### Explainability
- **Traceability:** Every recommendation must reference the specific SAP data signals used to reach the conclusion.
- **Uncertainty Communication:** Confidence ratings (High / Medium / Low) must be present on every diagnosis and recommendation. The basis for confidence downgrade must be stated explicitly.

---

## Solution Architecture

**Architecture Overview:**
A pro-code Python AI agent built on the A2A protocol, deployed on SAP BTP. The agent uses SAP Generative AI Hub as its reasoning engine and connects to SAP S/4HANA Cloud via five MCP tool wrappers generated from OData API specifications. All MCP tools are read-only. The agent maintains conversation context across multi-turn advisory sessions.

**Key Components:**
- **OTD Advisory Agent (Python, A2A):** Core reasoning agent hosted on SAP BTP; handles multi-turn conversations, tool orchestration, root-cause classification, priority scoring, and advisory dossier generation.
- **SAP Generative AI Hub:** LLM reasoning engine (e.g., GPT-4o or equivalent); used for natural language understanding, cross-signal synthesis, and executive summary generation.
- **MCP Tool Wrappers (×5):** Read-only MCP tools generated from SAP S/4HANA OData specs — Sales Order, Warehouse Available Stock, Production Order, Outbound Delivery, Freight Order.
- **SAP S/4HANA Cloud:** Source of all transactional data; accessed via OData APIs only.

**Integration Points:**
- Sales Order API (`CE_SALESORDER_0001`): Read sales order headers and confirmed delivery dates — inbound, on-demand.
- Warehouse Available Stock API (`WAREHOUSEAVAILABLESTOCK_0001`): Read current inventory and ATP status — inbound, on-demand.
- Production Order API (`API_PRODUCTION_ORDER_2_SRV`): Read production order status and scheduled completion — inbound, on-demand.
- Outbound Delivery API (`API_OUTBOUND_DELIVERY_SRV_0002`): Read delivery document status and shipment tracking — inbound, on-demand.
- Freight Order API (`CE_FREIGHTORDER_0001`): Read freight order and carrier assignment status — inbound, on-demand.

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
The agent is designed with extension points to support future capability additions without re-architecting the core:
- **Skill extension:** New advisory domains (e.g., procurement risk, production capacity advisory) can be added as discrete skill modules without modifying existing agent logic.
- **Tool extension:** Additional MCP tools (e.g., external carrier tracking APIs, IBP planning signals) can be registered and activated independently.
- **Confidence model extension:** The confidence scoring logic is modular and can be updated or replaced as data completeness improves.

**Business Step Instrumentation:**
All five key business milestones are instrumented with structured log statements for OpenTelemetry observability. Log statements follow the pattern: `[MILESTONE_ID].[achieved|missed]: [description]`.

---

### Automation & Agent Behaviour

**Automation Level:** Autonomous AI Agent (advisory outputs only; no automated execution)

**Actions the system performs without human approval:**
- Querying SAP S/4HANA APIs to read order, inventory, production, delivery, and freight data
- Classifying root causes and computing priority scores
- Generating advisory dossiers and executive summaries

**Actions that require human review or approval:**
- All recommended mitigation actions (expediting, inventory reallocation, promise date revision, carrier escalation)
- All actions that result in changes to any SAP system

**Model or engine used:** SAP Generative AI Hub (GPT-4o or equivalent large language model)

**Knowledge & data sources accessed:**
- SAP S/4HANA Cloud — Sales Orders: confirmed delivery dates, customer tier, order value
- SAP S/4HANA Cloud — Inventory/ATP: available stock and ATP check results
- SAP S/4HANA Cloud — Production Orders: scheduled completion, status, confirmations
- SAP S/4HANA Cloud — Outbound Delivery: delivery document status, goods issue date
- SAP S/4HANA Cloud — Freight Orders: carrier assignment, planned departure/arrival
- Business knowledge documents (skill resources): `business_process.md`, `otd_kpis.md`, `challenges.md`, `outcomes.md`, `escalation_rules.md`, `improvement_actions.md`, `governance_guidelines.md`, `data_dictionary.md`

**Tools or connectors invoked:**
- `get_sales_orders` (Sales Order MCP tool): Read at-risk orders and delivery schedule — read-only
- `get_warehouse_stock` (Warehouse Available Stock MCP tool): Check inventory and ATP status — read-only
- `get_production_orders` (Production Order MCP tool): Check production schedule and status — read-only
- `get_outbound_deliveries` (Outbound Delivery MCP tool): Check delivery and shipment status — read-only
- `get_freight_orders` (Freight Order MCP tool): Check freight and carrier status — read-only

**Guardrails & fail-safes:**
- No MCP tool with write, create, update, or delete capability is registered or invocable — enforced at tool registration level
- Agent must never send direct communications to customers, suppliers, or carriers
- If confidence falls below the "Low" threshold due to missing signals, the agent must explicitly state the limitation before providing a diagnosis
- If production and inventory signals conflict, the agent must flag the discrepancy to the user rather than making an assumption
- All recommendations must include a mandatory HITL advisory note: "This recommendation requires manual review and execution by an authorized planner"

---

## Milestones

### M1: Risk Detection Active

- **Description:** Agent successfully identifies and returns at-risk sales orders from live SAP S/4HANA signals.
- **Achieved when:** The agent returns a non-empty, prioritized list of at-risk orders with supporting signal data for a given portfolio query.
- **Log on achievement:** `M1.achieved: at-risk order detection completed — [N] orders identified from [M] signals`
- **Log on miss:** `M1.missed: at-risk order detection did not complete — signal query failed or returned no data`

### M2: Root-Cause Classification

- **Description:** Agent correctly categorizes the primary bottleneck driving a delivery risk into one of the four approved root-cause categories.
- **Achieved when:** The agent returns a root-cause classification (Material Shortage / Capacity Constraint / Warehouse Bottleneck / Transit Delay) with a stated confidence rating and supporting evidence.
- **Log on achievement:** `M2.achieved: root cause classified as [category] with [confidence] confidence for order [order_id]`
- **Log on miss:** `M2.missed: root cause classification could not be completed for order [order_id] — missing signals: [list]`

### M3: Priority Scoring Operational

- **Description:** Agent computes and applies the multi-dimensional priority score to rank at-risk orders.
- **Achieved when:** The at-risk order list is returned with a computed priority score per order reflecting customer tier, SLA penalty, and order value weights.
- **Log on achievement:** `M3.achieved: priority scoring applied to [N] at-risk orders — top priority: order [order_id]`
- **Log on miss:** `M3.missed: priority scoring incomplete — missing customer tier or SLA data for [N] orders`

### M4: Advisory Dossier Delivery

- **Description:** Agent generates a complete advisory dossier for a specific at-risk order.
- **Achieved when:** The dossier contains root cause, confidence rating, recommended mitigation actions, suggested revised promise date, and copy-ready SAP next steps.
- **Log on achievement:** `M4.achieved: advisory dossier generated for order [order_id] — [N] recommendations provided`
- **Log on miss:** `M4.missed: advisory dossier could not be generated for order [order_id] — insufficient signal data`

### M5: Executive Summary Generation

- **Description:** Agent produces a leadership-ready aggregate OTD risk summary on demand.
- **Achieved when:** The summary covers total at-risk orders, root-cause breakdown, estimated OTD KPI impact, and top recommended actions in plain language without technical jargon.
- **Log on achievement:** `M5.achieved: executive summary generated — [N] orders at risk, estimated OTD impact: [X]%`
- **Log on miss:** `M5.missed: executive summary generation failed — insufficient aggregated data`

---

## Risks, Assumptions, and Dependencies

### Risks
- **MCP Translation Coverage:** No MCP servers exist yet for any of the five required APIs. Custom translation files must be generated from OData specs. Incomplete operation coverage could limit diagnostic depth.
- **Carrier Tracking Gap:** The Freight Order API provides internal logistics data but may not include real-time external carrier tracking events. This could limit Transit/Carrier Delay root-cause confidence.
- **LLM Reasoning Quality:** Root-cause diagnosis and dossier quality depend on LLM accuracy. Edge cases with conflicting signals may produce lower-confidence or ambiguous outputs.

### Assumptions
- The SAP S/4HANA instance exposes all five OData APIs and the deploying organization has the necessary licenses.
- RBAC enforcement is handled by SAP S/4HANA API authorization; the agent passes the user's credentials through without elevation.
- Business knowledge documents (`business_process.md`, `otd_kpis.md`, etc.) will be provided and maintained by the business team.

### Dependencies
- SAP BTP account with SAP Generative AI Hub access
- SAP S/4HANA Cloud (Public or Private Edition) with the five OData APIs enabled
- MCP translation files generated from OData specs (prerequisite for agent tool registration)

---

## Appendix

### Glossary

- **OTD (On-Time Delivery):** The percentage of sales orders delivered on or before the customer-confirmed delivery date.
- **ATP (Available-to-Promise):** A check confirming whether requested goods can be delivered by a requested date based on current stock and planned receipts.
- **A2A Protocol:** Agent-to-Agent communication protocol used to build interoperable AI agents on SAP BTP.
- **MCP (Model Context Protocol):** A protocol for exposing API tools to AI agents in a structured, discoverable format.
- **Advisory Dossier:** A per-order output from the agent containing root cause, confidence rating, recommended actions, and suggested revised promise date.
- **HITL (Human-in-the-Loop):** A design pattern requiring explicit human review and approval before any business-impacting action is executed.

### References
- SAP S/4HANA Sales Order API: `sap.s4:apiResource:CE_SALESORDER_0001:v1`
- SAP S/4HANA Warehouse Available Stock API: `sap.s4:apiResource:WAREHOUSEAVAILABLESTOCK_0001:v1`
- SAP S/4HANA Production Order API: `sap.s4:apiResource:API_PRODUCTION_ORDER_2_SRV:v1`
- SAP S/4HANA Outbound Delivery API: `sap.s4:apiResource:API_OUTBOUND_DELIVERY_SRV_0002:v2`
- SAP S/4HANA Freight Order API: `sap.s4:apiResource:CE_FREIGHTORDER_0001:v1`
- SAP BTP AI Agent development guidelines (A2A protocol)
- SAP Generative AI Hub documentation
