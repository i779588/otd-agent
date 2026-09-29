---
name: otd-risk-detection
description: Guides the agent in detecting at-risk sales orders by correlating multi-signal SAP data
---

# OTD Risk Detection Skill

You are detecting sales orders that are at risk of missing their confirmed delivery date.

## Step-by-Step Instructions

1. **Fetch open sales orders**: Use `list_salesorder_for_sap_self` with filter `OverallDeliveryStatus ne 'C'` (not fully delivered), top=100.

2. **Identify the risk horizon**: Default risk window is orders with `ConfirmedDeliveryDate` within the next 7 days from today. Fetch items using `list_salesorderitem_for_sap_self` filtering by `ConfirmedDeliveryDate le <today+7days>`.

3. **Cross-reference signals**: For each flagged order item, check:
   - **Inventory/ATP**: Use `list_warehouseavailablestock_for_sap_self` filtering by `Product` and check `AvailableEWMStockQty`
   - **Production**: Use `list_a_productionorder_2_for_api_production_order_2_srv` filtering by `SalesOrder` and check `OrderIsReleased`, `MfgOrderScheduledEndDate`
   - **Outbound Delivery**: Use `list_a_outbdeliveryheader_for_api_outbound_delivery_srv` filtering by `SoldToParty` and check `OverallGoodsMovementStatus`, `OverallPickingStatus`
   - **Freight**: Use `list_freightorder_for_sap_self` and check `TransportationOrderExecSts`, `TranspOrdGoodsMovementStatus`

4. **Flag at-risk orders**: An order is at risk if ANY of these conditions are true:
   - Stock quantity is zero or insufficient
   - Production order not released or scheduled end date is after confirmed delivery date
   - Outbound delivery picking not completed (`OverallPickingStatus ne 'C'`) and delivery date is near
   - Freight order execution status indicates delay

5. **Return a prioritized list** with for each order:
   - SalesOrder, SoldToParty, CustomerGroup
   - RequestedDeliveryDate, ConfirmedDeliveryDate
   - DeliveryStatus, NetAmount
   - Risk indicator and signals triggered

## Zero-Write Guardrails
- NEVER call any create, update, or delete tool
- NEVER modify any SAP record
- NEVER send any communication on behalf of the user
- All output is advisory only — the planner must take manual action
