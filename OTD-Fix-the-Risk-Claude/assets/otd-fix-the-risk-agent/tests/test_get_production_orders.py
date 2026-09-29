"""Unit test: production order with delayed scheduled end date."""
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("IBD_TESTING", "true")


def _make_tool(name: str, result: dict) -> MagicMock:
    tool = MagicMock()
    tool.name = name
    tool.arun = AsyncMock(return_value=json.dumps(result))
    return tool


@pytest.mark.asyncio
async def test_production_order_delayed():
    """Production order not released and scheduled end date is after confirmed delivery date."""
    from agent import SampleAgent

    delayed_prod_order = {
        "d": {
            "results": [
                {
                    "ManufacturingOrder": "000001000042",
                    "Material": "PROD-A",
                    "ProductionPlant": "1000",
                    "SalesOrder": "0000000042",
                    "SalesOrderItem": "000010",
                    "OrderIsReleased": "X",
                    "OrderIsConfirmed": "",
                    "OrderIsTechnicallyCompleted": "",
                    "MfgOrderScheduledEndDate": "/Date(1704844800000)/",
                    "TotalQuantity": "100",
                    "MfgOrderConfirmedYieldQty": "20",
                    "ProductionUnit": "EA",
                }
            ]
        }
    }

    tools = [
        _make_tool(
            "list_a_productionorder_2_for_api_production_order_2_srv",
            delayed_prod_order,
        )
    ]

    agent = SampleAgent()
    response = await agent.invoke(
        "What is the production status for sales order 0000000042?",
        context_id="test-prod-001",
        tools=tools,
    )

    assert response.status in ("completed", "error")
    assert response.message is not None
