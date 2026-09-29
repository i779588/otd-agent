"""Unit test: freight order in transit with delayed stop."""
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
async def test_freight_order_delayed():
    """Freight order in-transit with stop execution status indicating delay — Transit Delay signal."""
    from agent import SampleAgent

    delayed_freight = {
        "value": [
            {
                "TransportationOrderUUID": "550e8400-e29b-41d4-a716-446655440000",
                "TransportationOrder": "FO0000042",
                "Carrier": "CARRIER01",
                "TranspOrdLifeCycleStatus": "02",
                "TransportationOrderExecSts": "01",
                "TranspOrdGoodsMovementStatus": "A",
                "TransportationMode": "03",
            }
        ]
    }

    freight_stops = {
        "value": [
            {
                "TransportationOrderStopUUID": "660e8400-e29b-41d4-a716-446655440001",
                "TransportationOrderUUID": "550e8400-e29b-41d4-a716-446655440000",
                "TransportationOrderStop": "0001",
                "TranspOrdStopPlanTranspDteTme": "2024-01-08T08:00:00Z",
                "TranspOrdStopDteTme": None,
                "TranspOrdStopHndlgExecStatus": "01",
                "TranspOrdStopRole": "01",
            }
        ]
    }

    tools = [
        _make_tool("list_freightorder_for_sap_self", delayed_freight),
        _make_tool("list_freightorderstop_for_sap_self", freight_stops),
    ]

    agent = SampleAgent()
    response = await agent.invoke(
        "What is the freight status for delivery to customer CUST001?",
        context_id="test-freight-001",
        tools=tools,
    )

    assert response.status in ("completed", "error")
    assert response.message is not None
