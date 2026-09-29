---
name: advisory-dossier
description: Generates a complete advisory dossier for a specific at-risk order
---

# Advisory Dossier Skill

Generate a structured advisory dossier for a specific at-risk sales order.

## Dossier Template

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OTD ADVISORY DOSSIER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Order ID:              {SalesOrder}
Customer:              {SoldToParty} (Group: {CustomerGroup})
Requested Delivery:    {RequestedDeliveryDate}
Confirmed Delivery:    {ConfirmedDeliveryDate}
Days Remaining:        {N days}
Net Order Value:       {NetAmount} {Currency}
Priority Score:        {Score} / 9

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROOT CAUSE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Primary Root Cause:    {Category}
Confidence Rating:     {High / Medium / Low}

Supporting Evidence:
  • {Signal 1}: {value and interpretation}
  • {Signal 2}: {value and interpretation}
  • {Signal 3 if available}

Missing Signals (if any):
  • {List any data that was unavailable}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. {Action 1 — specific, actionable, references SAP app where applicable}
2. {Action 2 — specific, actionable}
3. {Action 3 — specific, actionable}

Suggested Revised Promise Date: {Date or "Insufficient data to estimate"}

SAP Next Steps:
  • Use "Manage Sales Orders" app to review order status
  • Use "Monitor Production Orders" app to expedite production
  • Use "Monitor Outbound Deliveries" app to accelerate picking
  • Use "Track Freight Orders" app to contact carrier

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  HUMAN-IN-THE-LOOP REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All recommendations require manual review and execution by an authorized planner.
This dossier is advisory only. No changes have been made to any SAP system.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Rules
- Always include the HITL disclaimer at the end of every dossier
- Always include confidence rating — never omit it
- Always list missing signals explicitly
- Never suggest or imply that the agent will take action
- Recommended actions must be plain-language and reference the correct SAP application
