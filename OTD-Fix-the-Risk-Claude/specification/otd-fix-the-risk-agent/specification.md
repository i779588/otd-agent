# Specification: otd-fix-the-risk-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [ ] Read the project input (`product-requirements-document.md`, `intent.md`)
- [ ] Bootstrap agent code in `assets/otd-fix-the-risk-agent/` using instructions from the sap-agent-bootstrap section. (invoke from inside `assets/otd-fix-the-risk-agent/`, use copy commands — do NOT create files manually)
- [ ] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

> Read [guidelines-agent-skills.md](../guidelines-agent-skills.md) before deciding on skills.

The OTD agent has complex domain-specific advisory logic. The following runtime skills are required:

- [ ] Create `assets/otd-fix-the-risk-agent/app/skills/otd-risk-detection/SKILL.md` with:
  - YAML frontmatter: `name: otd-risk-detection`, `description: Guides the agent in detecting at-risk sales orders by correlating multi-signal SAP data`
  - Body: Step-by-step instructions to query sales orders, check confirmed delivery dates vs. today, cross-reference inventory/ATP, production order status, and outbound delivery status to flag orders at risk
  - Include zero-write guardrail reminders

- [ ] Create `assets/otd-fix-the-risk-agent/app/skills/root-cause-diagnosis/SKILL.md` with:
  - YAML frontmatter: `name: root-cause-diagnosis`, `description: Guides the agent to classify the root cause of a delivery delay into one of four approved categories`
  - Body: Decision tree for classifying delays as (1) Material Shortage, (2) Capacity/Production Constraint, (3) Warehouse/Logistics Bottleneck, or (4) Transit/Carrier Delay, with signal mapping and confidence rating logic
  - Include confidence downgrade rules for missing signals

- [ ] Create `assets/otd-fix-the-risk-agent/app/skills/priority-scoring/SKILL.md` with:
  - YAML frontmatter: `name: priority-scoring`, `description: Computes the multi-dimensional priority score for at-risk orders`
  - Body: Priority Score = (w1 × Customer Tier) + (w2 × SLA Financial Penalty) + (w3 × Order Revenue Value). Tier weights: Tier 1 = 3, Tier 2 = 2, Tier 3 = 1. Instructions for scoring and ranking output.

- [ ] Create `assets/otd-fix-the-risk-agent/app/skills/advisory-dossier/SKILL.md` with:
  - YAML frontmatter: `name: advisory-dossier`, `description: Generates a complete advisory dossier for a specific at-risk order`
  - Body: Template for dossier including root cause, confidence rating, 2–3 recommended mitigation actions, suggested revised promise date, copy-ready SAP next steps referencing specific applications (e.g. Manage Sales Orders)
  - Mandatory HITL reminder appended to every dossier

- [ ] Create `assets/otd-fix-the-risk-agent/app/skills/governance-guardrails/SKILL.md` with:
  - YAML frontmatter: `name: governance-guardrails`, `description: Enforces advisory-only guardrails and escalation rules`
  - Body: Rules from escalation_rules.md, governance_guidelines.md — no write-backs, no automated decisions, no direct communications, RBAC data access boundaries

---

## Project-Specific Tasks

### System Prompt

- [ ] Configure `assets/otd-fix-the-risk-agent/app/agent.py` with a `@prompt_section` that:
  - Declares the agent as a zero-write, advisory-only OTD risk copilot
  - States it serves Supply Chain Planners and Executives
  - Lists four root-cause categories: Material Shortage, Capacity/Production Constraint, Warehouse/Logistics Bottleneck, Transit/Carrier Delay
  - States the priority scoring formula: Priority Score = (w1 × Customer Tier) + (w2 × SLA Financial Penalty) + (w3 × Order Revenue Value)
  - Declares the HITL requirement: every recommendation must include "Requires manual review and execution by an authorized planner"
  - Declares confidence rating requirement (High / Medium / Low) on every diagnosis
  - Explicitly prohibits: updating any SAP system, changing promise dates automatically, sending communications to customers/suppliers/carriers
  - States that when signals conflict, the agent must flag the discrepancy rather than assuming

### OTD Risk Detection (R1)

- [ ] Implement risk detection logic in `assets/otd-fix-the-risk-agent/app/agent.py`:
  - When user asks about at-risk orders: use `get_sales_orders` MCP tool to fetch open sales orders with `OverallDeliveryStatus` not fully delivered
  - Filter orders where `ConfirmedDeliveryDate` (at item or schedule line level) is within the risk horizon (configurable, default: 7 days)
  - Cross-reference with inventory, production, and delivery signals for each flagged order
  - Return a prioritized list with: SalesOrder, SoldToParty, CustomerGroup, RequestedDeliveryDate, ConfirmedDeliveryDate, DeliveryStatus, NetAmount, risk indicator

### Root-Cause Classification (R2)

- [ ] Implement root-cause classification:
  - Use `get_warehouse_stock` to check `AvailableEWMStockQty` for the order's product and plant
  - Use `get_production_orders` to check `OrderIsReleased`, `MfgOrderScheduledEndDate` vs. required date
  - Use `get_outbound_deliveries` to check `OverallGoodsMovementStatus`, `OverallPickingStatus`
  - Use `get_freight_orders` to check `TransportationOrderExecSts`, `TranspOrdGoodsMovementStatus`, stop timestamps
  - Apply root-cause decision tree from the `root-cause-diagnosis` skill
  - Output: root-cause category + confidence rating (High/Medium/Low) + supporting evidence signals
  - If any critical signal is missing, downgrade confidence and state the gap explicitly

### Priority Scoring (R3)

- [ ] Implement priority scoring:
  - Map `CustomerGroup` to customer tier weight (configurable mapping, default: Group "01" = Tier 1 weight 3, "02" = Tier 2 weight 2, others = Tier 3 weight 1)
  - SLA penalty risk derived from proximity to `ConfirmedDeliveryDate` (days remaining score: 0–3 days = 3, 4–7 days = 2, >7 days = 1)
  - Order revenue value score from `NetAmount` (configurable thresholds, default: >100K = 3, 10K–100K = 2, <10K = 1)
  - Compute and display final priority score alongside component breakdown

### Advisory Dossier Generation (R4)

- [ ] Implement advisory dossier generation:
  - Load `advisory-dossier` skill on dossier requests
  - Dossier must include: order ID, root cause, confidence rating, evidence signals used, 2–3 recommended mitigation actions, suggested revised promise date, copy-ready SAP next steps
  - Append HITL advisory: "All recommendations require manual review and execution by an authorized planner"
  - Never trigger any write-back actions

### Executive Summary (R5)

- [ ] Implement executive OTD risk summary:
  - On demand: aggregate all at-risk order data
  - Summary must include: total orders at risk, breakdown by root-cause category (with counts), estimated OTD impact (% of portfolio at risk), top 3 recommended actions by category
  - All output must be in plain language, free of SAP technical codes or jargon
  - Suitable for direct presentation to leadership

### Zero-Write Guardrail Enforcement (R6)

- [ ] Verify no MCP tool with write/create/update/delete capability is registered:
  - Audit all MCP tool registrations in `asset.yaml` — only read operations permitted
  - Add explicit system prompt instruction declining any write-back requests and providing manual steps instead
  - Add guardrail check in `agent.py`: if user asks to update/change any SAP record, respond with advisory-only message and manual steps

### RBAC-Compliant Data Access (R7)

- [ ] Wire user credential pass-through to MCP tools (handled by SAP BTP runtime)
- [ ] Add system prompt instruction stating the agent must only surface data accessible to the active user
- [ ] Document assumption: RBAC is enforced at SAP S/4HANA API authorization layer

---

## Business Instrumentation

- [ ] Implement business step instrumentation for all 5 milestones with structured logging and OpenTelemetry spans:

  ```python
  # M1: Risk Detection Active
  logger.info("M1.achieved: at-risk order detection completed — %d orders identified from %d signals", order_count, signal_count)
  # on failure:
  logger.warning("M1.missed: at-risk order detection did not complete — signal query failed or returned no data")

  # M2: Root-Cause Classification
  logger.info("M2.achieved: root cause classified as %s with %s confidence for order %s", category, confidence, order_id)
  # on failure:
  logger.warning("M2.missed: root cause classification could not be completed for order %s — missing signals: %s", order_id, missing_signals)

  # M3: Priority Scoring Operational
  logger.info("M3.achieved: priority scoring applied to %d at-risk orders — top priority: order %s", n, top_order)
  # on failure:
  logger.warning("M3.missed: priority scoring incomplete — missing customer tier or SLA data for %d orders", n)

  # M4: Advisory Dossier Delivery
  logger.info("M4.achieved: advisory dossier generated for order %s — %d recommendations provided", order_id, n_recs)
  # on failure:
  logger.warning("M4.missed: advisory dossier could not be generated for order %s — insufficient signal data", order_id)

  # M5: Executive Summary Generation
  logger.info("M5.achieved: executive summary generated — %d orders at risk, estimated OTD impact: %.1f%%", n_orders, impact_pct)
  # on failure:
  logger.warning("M5.missed: executive summary generation failed — insufficient aggregated data")
  ```

- [ ] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [ ] Verify `api-discovery-results.md` is not needed (API specs are already in `specification/otd-fix-the-risk-agent/api-specs/`)
- [ ] Invoke `mcp-translation-file` skill for each of the 5 API specs in `specification/otd-fix-the-risk-agent/api-specs/`:
  - `CE_SALESORDER_0001.edmx` → ORD ID: `sap.s4:apiResource:CE_SALESORDER_0001:v1` → type: `edmx`
  - `WAREHOUSEAVAILABLESTOCK_0001.edmx` → ORD ID: `sap.s4:apiResource:WAREHOUSEAVAILABLESTOCK_0001:v1` → type: `edmx`
  - `API_PRODUCTION_ORDER_2_SRV.edmx` → ORD ID: `sap.s4:apiResource:API_PRODUCTION_ORDER_2_SRV:v1` → type: `edmx`
  - `API_OUTBOUND_DELIVERY_SRV_0002.edmx` → ORD ID: `sap.s4:apiResource:API_OUTBOUND_DELIVERY_SRV_0002:v2` → type: `edmx`
  - `CE_FREIGHTORDER_0001.edmx` → ORD ID: `sap.s4:apiResource:CE_FREIGHTORDER_0001:v1` → type: `edmx`
- [ ] Then invoke `setup-solution` to register the generated MCP assets in `solution.yaml` and create `asset.yaml` for each
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — NEVER import directly from `sap_cloud_sdk.agentgateway`
- [ ] Add MCP server dependencies to `asset.yaml` under `requires` — one entry per generated MCP server ORD ID. Exclude only read-only tool operations. **EXCLUDE `dpca-mcp-server`**
- [ ] Generate `mcp-mock.json` using the `mcp-mock-config` skill after MCP translation is complete

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup.

- [ ] `conftest.py` only sets `IBD_TESTING=true`
- [ ] Write unit tests in `assets/otd-fix-the-risk-agent/tests/`:
  - `test_get_sales_orders.py` — mock at-risk order detection with overdue ConfirmedDeliveryDate
  - `test_get_warehouse_stock.py` — mock low/zero available stock ATP signal
  - `test_get_production_orders.py` — mock production order delayed end date
  - `test_get_outbound_deliveries.py` — mock delivery not picked/goods-issued
  - `test_get_freight_orders.py` — mock freight order in-transit with delayed stop
  - Run each test immediately after writing
- [ ] Write one integration test executing end-to-end agent flow:
  - Simulate user asking "Which orders are at risk today?" with mocked LLM and mocked MCP tools
  - Assert response contains: at-risk order list, root cause, priority score, confidence rating
  - Assert no write operations are invoked
- [ ] Run `pytest` from `assets/otd-fix-the-risk-agent/` (no args)
- [ ] Verify `assets/otd-fix-the-risk-agent/app/agent.py` has exactly 9 decorated functions — run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/otd-fix-the-risk-agent/app/agent.py` and confirm it returns 9
- [ ] Run `pytest` again from `assets/otd-fix-the-risk-agent/` to generate final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/otd-fix-the-risk-agent/`
