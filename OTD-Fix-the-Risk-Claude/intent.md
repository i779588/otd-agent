# OTD-Fix-the-Risk: On-Time Delivery Advisory Agent

AI advisory copilot for proactive OTD risk detection, root-cause diagnosis, and mitigation recommendation — strictly read-only, no write-backs to any source system.

## Business challenge

Supply Chain Planners and Executives need a specialized advisory agent that proactively identifies sales orders at risk of missing their On-Time Delivery (OTD) targets, diagnoses the most likely root causes of delay (material shortage, capacity constraint, warehouse/logistics bottleneck, transit/carrier disruption), prioritizes them by customer tier and business value, and recommends optimal mitigation strategies. The agent operates in zero-write advisory-only mode — all execution remains with authorized human planners.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| OTD Rate | ~80% (industry avg) | 95% | 6 months | Order Fulfillment / Delivery Risk Management | agent-derived |
| Time-to-Detect Delay | ~48 hours | < 4 hours | 3 months | Risk Detection & Alerting | agent-derived |
| Planner Time on Manual Risk Triage | ~3 hrs/day | < 30 min/day | 6 months | Supply Chain Planning Advisory | agent-derived |

## Key Milestones

1. **Risk Detection Active** — Agent successfully identifies at-risk sales orders from live SAP S/4HANA data signals (inventory, ATP, production, delivery).
2. **Root-Cause Classification** — Agent correctly categorizes each delay into one of the four approved root-cause categories with a stated confidence level.
3. **Priority Scoring Operational** — Multi-dimensional priority score (customer tier × SLA penalty × order value) ranks orders correctly for planners.
4. **Advisory Dossier Delivery** — Agent generates complete advisory dossier (root cause, recommended actions, revised promise date suggestion, confidence rating) per at-risk order.
5. **Executive Summary Generation** — Agent produces leadership-ready OTD risk summary on demand, free of technical jargon.

## Business Architecture (RBA)

### End-to-End Process

Plan to Fulfill (Supply Chain)

### Process Hierarchy

```
Plan to Fulfill (E2E)
└── Plan to Optimize Fulfillment
    └── Develop supply chain strategy (BPS-335)
        └── Implement supply chain strategy
└── Manage Fulfillment
    └── Manage supply chain data and operations (BPS-342)
        └── Operate supply chain collaboration platform
└── Deliver Service to Fulfill
    └── Fulfill service (BPS-357)
        └── Execute service delivery
        └── Complete service delivery
```

### Summary

The OTD-Fix-the-Risk challenge maps primarily to Plan to Fulfill, covering supply chain strategy implementation and operational management. Order-level monitoring and fulfillment risk trace to Manage Fulfillment and Order to Fulfill sub-processes, with GRC-style risk controls underpinning the advisory guardrails.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ---- | ------------------- |
| Read sales order data & confirmed delivery dates | SAP S/4HANA Cloud (Public/Private) | `sap.s4:apiResource:CE_SALESORDER_0001:v1` | — | — | No | OData API available; no MCP server found — custom MCP translation required |
| Check inventory & ATP availability | SAP S/4HANA Cloud — Inventory Analytics | `sap.s4:apiResource:WAREHOUSEAVAILABLESTOCK_0001:v1` | — | — | No | Warehouse Available Stock API available |
| Monitor production order status & schedule | SAP S/4HANA Cloud — Production | `sap.s4:apiResource:API_PRODUCTION_ORDER_2_SRV:v1` | — | — | No | Production Order V2 API available |
| Track outbound delivery & shipment status | SAP S/4HANA Cloud — Logistics | `sap.s4:apiResource:API_OUTBOUND_DELIVERY_SRV_0002:v2` | — | — | No | Outbound Delivery API available |
| Monitor freight order / carrier tracking | SAP S/4HANA Cloud — TM | `sap.s4:apiResource:CE_FREIGHTORDER_0001:v1` | — | — | Maybe | Freight Order API available; real-time carrier tracking may need external enrichment |
| AI-driven root-cause diagnosis & advisory | SAP AI Core + custom agent | — | — | — | Yes | No standard SAP product covers advisory reasoning — custom Python A2A agent required |
| Executive summary generation | SAP Analytics Cloud (optional) | — | — | — | Yes | Standard reporting covers dashboards; narrative executive summaries require AI agent |
| Priority scoring by customer tier & business value | Custom logic in agent | — | — | — | Yes | No standard SAP capability for multi-dimensional OTD priority scoring |

### Key findings

- All required transactional data signals (sales orders, inventory, production, delivery, freight) are available via SAP S/4HANA OData APIs — no data access gaps.
- No MCP servers were found for any of the identified APIs; MCP translation files must be generated from the OData specs to expose them as agent tools.
- The core advisory, reasoning, root-cause diagnosis, and executive summary capabilities are genuine gaps not covered by standard SAP products — these require a custom AI agent.
- SAP Integrated Business Planning (IBP) and SAP Analytics Cloud cover supply chain strategy and analytics, but do not provide the conversational advisory layer needed.
- The agent must operate in strict read-only mode; no write-back tools should be registered or exposed.
- SAP Business Network for Logistics covers supply chain network operations but does not close the AI advisory gap.

## Recommendations

### OTD-Fix-the-Risk: AI Advisory Agent on SAP BTP

#### Executive Summary

Custom Python AI agent (A2A) on SAP BTP providing read-only OTD risk advisory.

#### Recommended Solution

Build a pro-code Python AI agent following the A2A protocol, deployed on SAP BTP. The agent integrates with SAP S/4HANA Cloud via OData APIs (Sales Order, Inventory, Production Order, Outbound Delivery, Freight Order) through generated MCP tool wrappers. It reasons over multi-signal data to detect at-risk orders, classify root causes, score priorities, and generate advisory dossiers — all in zero-write mode. Human planners execute any approved actions manually in SAP.

#### Problem Statement

Planners currently spend hours manually cross-referencing sales order data, inventory levels, production schedules, and delivery status to identify OTD risks. By the time a risk is detected, the mitigation window has often closed. There is no intelligent layer that synthesizes cross-functional signals, reasons over them, and surfaces prioritized, actionable recommendations proactively.

#### Affected User Roles

- Supply Chain Planners / Order Management Specialists (primary — daily operational use)
- Supply Chain Directors / Executives (secondary — on-demand executive summaries and KPI trends)

#### Important factors

##### Strict Advisory-Only Guardrails
The agent must enforce zero-write-back at every layer — no tool registrations that allow data mutation in any SAP system. This is a hard business and compliance requirement.

##### Multi-Signal Data Synthesis
The agent must correlate signals from at least four data domains (orders, inventory/ATP, production, logistics) to produce credible root-cause diagnoses. Missing signals degrade confidence and must be disclosed.

##### Confidence Transparency
Every recommendation must carry a confidence rating (High / Medium / Low) and state which data signals were unavailable if confidence is reduced.

#### Potential risks

##### MCP Translation Coverage
No MCP servers exist yet for the required APIs. Custom MCP translation files must be generated from OData specs. Incomplete coverage of API operations could limit the agent's diagnostic depth.

##### Real-Time Carrier Tracking Gap
The Freight Order API provides internal logistics data but may not include real-time external carrier tracking. External data enrichment (e.g., carrier APIs) may be needed for full transit visibility.

#### Recommended solution category

AI Agent

#### Intent fit
92%
