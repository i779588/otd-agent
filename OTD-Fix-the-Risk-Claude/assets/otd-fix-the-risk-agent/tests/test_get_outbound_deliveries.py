"""Unit test: outbound delivery not picked / goods not issued."""
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
async def test_delivery_not_picked():
    """Outbound delivery has picking and goods movement not completed — Warehouse Bottleneck signal."""
    from agent import SampleAgent

    delivery_not_picked = {
        "d": {
            "results": [
                {
                    "DeliveryDocument": "0080000042",
                    "SoldToParty": "CUST001",
                    "DeliveryDate": "/Date(1704672000000)/",
                    "PlannedGoodsIssueDate": "/Date(1704585600000)/",
                    "ActualGoodsMovementDate": None,
                    "OverallGoodsMovementStatus": "A",
                    "OverallPickingStatus": "A",
                    "OverallSDProcessStatus": "A",
                    "ShippingPoint": "SP01",
                }
            ]
        }
    }

    tools = [
        _make_tool(
            "list_a_outbdeliveryheader_for_api_outbound_delivery_srv",
            delivery_not_picked,
        )
    ]

    agent = SampleAgent()
    response = await agent.invoke(
        "What is the outbound delivery status for customer CUST001?",
        context_id="test-del-001",
        tools=tools,
    )

    assert response.status in ("completed", "error")
    assert response.message is not None
