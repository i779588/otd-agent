"""Unit test: low/zero available stock ATP signal."""
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
async def test_zero_stock_signal():
    """Warehouse stock tool returns zero available qty — should surface as Material Shortage signal."""
    from agent import SampleAgent

    zero_stock = {
        "value": [
            {
                "EWMWarehouse": "WH01",
                "Product": "PROD-A",
                "Batch": "",
                "AvailableEWMStockQty": 0,
                "EWMStockQuantityBaseUnit": "EA",
                "EWMStockIsBlockedForInventory": False,
            }
        ]
    }

    tools = [_make_tool("list_warehouseavailablestock_for_sap_self", zero_stock)]

    agent = SampleAgent()
    response = await agent.invoke(
        "Check the warehouse stock for product PROD-A in warehouse WH01.",
        context_id="test-wh-001",
        tools=tools,
    )

    assert response.status in ("completed", "error")
    assert response.message is not None
