---
name: priority-scoring
description: Computes the multi-dimensional priority score for at-risk orders
---

# Priority Scoring Skill

Compute and rank at-risk orders by business impact using the OTD priority scoring formula.

## Priority Score Formula

```
Priority Score = (w1 × Customer Tier) + (w2 × SLA Penalty Score) + (w3 × Revenue Score)
```

Where weights are equal by default: w1 = w2 = w3 = 1.

## Scoring Components

### Customer Tier (from `CustomerGroup`)
| CustomerGroup | Tier | Weight |
|---------------|------|--------|
| "01"          | Tier 1 | 3 |
| "02"          | Tier 2 | 2 |
| Any other     | Tier 3 | 1 |

### SLA Penalty Score (from `ConfirmedDeliveryDate` vs today)
| Days Remaining | Score |
|----------------|-------|
| 0–3 days       | 3     |
| 4–7 days       | 2     |
| > 7 days       | 1     |

### Revenue Score (from `NetAmount`)
| Net Amount        | Score |
|-------------------|-------|
| > 100,000         | 3     |
| 10,000 – 100,000  | 2     |
| < 10,000          | 1     |

## Output Format

For each scored order, show:
- SalesOrder ID
- Customer Tier score (with CustomerGroup value)
- SLA Penalty score (with days remaining)
- Revenue score (with NetAmount)
- **Total Priority Score**
- Final ranked list from highest to lowest priority

## Notes
- If CustomerGroup is missing, default to Tier 3 score and note the assumption
- If NetAmount is missing, default to Revenue Score 1 and note the gap
- Always show the component breakdown so planners can validate the ranking
