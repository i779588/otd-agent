---
name: root-cause-diagnosis
description: Guides the agent to classify the root cause of a delivery delay into one of four approved categories
---

# Root Cause Diagnosis Skill

Classify the root cause of a delivery delay for a specific at-risk sales order.

## Four Approved Root-Cause Categories

| # | Category | Key Signals |
|---|----------|-------------|
| 1 | **Material Shortage** | `AvailableEWMStockQty` = 0 or insufficient; `ConfdOrderQtyByMatlAvailCheck` < `ScheduleLineOrderQuantity` |
| 2 | **Capacity/Production Constraint** | `OrderIsReleased` = false; `MfgOrderScheduledEndDate` > `ConfirmedDeliveryDate`; production yield below target |
| 3 | **Warehouse/Logistics Bottleneck** | `OverallPickingStatus` ≠ 'C'; `OverallGoodsMovementStatus` ≠ 'C'; `PlannedGoodsIssueDate` exceeded |
| 4 | **Transit/Carrier Delay** | `TransportationOrderExecSts` = delayed/not started; `TranspOrdStopDteTme` exceeded planned; `TranspOrdGoodsMovementStatus` ≠ 'C' |

## Decision Tree

1. Check stock signals first → if insufficient ATP stock → **Material Shortage**
2. Else check production signals → if order unreleased or end date overdue → **Capacity/Production Constraint**
3. Else check outbound delivery signals → if picking/goods movement incomplete → **Warehouse/Logistics Bottleneck**
4. Else check freight signals → if carrier execution delayed → **Transit/Carrier Delay**
5. If multiple signals fire → report all, assign primary root cause with highest evidence weight

## Confidence Rating Rules

- **High**: 2+ corroborating signals from the same category, no conflicting signals
- **Medium**: 1 clear signal from a category, or 2+ signals across categories
- **Low**: Only 1 weak signal available, or signals conflict between categories

## Confidence Downgrade Rules
- If a required data source returns no data or an error → downgrade confidence by one level
- If signals conflict (e.g. stock is available but production is delayed) → flag the discrepancy explicitly and explain both signals
- Always state which signals were checked and which were missing

## Zero-Write Guardrails
- Do NOT attempt to fix the root cause
- Do NOT update any SAP record
- All findings are advisory only
