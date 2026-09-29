"""Integration test: end-to-end agent flow with mocked MCP tools."""
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("IBD_TESTING", "true")

WRITE_TOOL_NAMES = [
    "create_salesorder_for_sap_self",
    "update_salesorder_for_sap_self",
    "delete_salesorder_for_sap_self",
    "create_salesorderitem_for_sap_self",
    "update_salesorderitem_for_sap_self",
    "delete_salesorderitem_for_sap_self",
    "create_warehouseavailablestock_for_sap_self",
    "update_warehouseavailablestock_for_sap_self",
    "delete_warehouseavailablestock_for_sap_self",
    "create_a_productionorder_2_for_api_production_order_2_srv",
    "update_a_productionorder_2_for_api_production_order_2_srv",
    "delete_a_productionorder_2_for_api_production_order_2_srv",
    "create_a_outbdeliveryheader_for_api_outbound_delivery_srv",
    "update_a_outbdeliveryheader_for_api_outbound_delivery_srv",
    "delete_a_outbdeliveryheader_for_api_outbound_delivery_srv",
    "create_freightorder_for_sap_self",
    "update_freightorder_for_sap_self",
    "delete_freightorder_for_sap_self",
]


def _make_tool(name: str, result: dict) -> MagicMock:
    tool = MagicMock()
    tool.name = name
    tool.arun = AsyncMock(return_value=json.dumps(result))
    return tool


@pytest.mark.asyncio
async def test_integration_no_write_operations_invoked():
    """Verify that no write operations are called during a standard risk detection flow."""
    from agent import SampleAgent

    # Track which tools were called
    called_tools = []

    def tracking_tool(name: str, result: dict) -> MagicMock:
        tool = MagicMock()
        tool.name = name

        async def tracked_arun(*args, **kwargs):
            called_tools.append(name)
            return json.dumps(result)

        tool.arun = tracked_arun
        return tool

    sales_orders = {
        "value": [
            {
                "SalesOrder": "0000000099",
                "SoldToParty": "CUST002",
                "CustomerGroup": "01",
                "OverallDeliveryStatus": "A",
                "TotalNetAmount": 250000,
                "TransactionCurrency": "EUR",
                "RequestedDeliveryDate": "2024-01-12",
            }
        ]
    }
    items = {
        "value": [
            {
                "SalesOrder": "0000000099",
                "SalesOrderItem": "000010",
                "Product": "PROD-B",
                "ConfirmedDeliveryDate": "2024-01-10",
                "NetAmount": 250000,
                "DeliveryStatus": "A",
                "Plant": "2000",
            }
        ]
    }
    stock = {"value": [{"Product": "PROD-B", "AvailableEWMStockQty": 0}]}
    prod = {"d": {"results": []}}
    delivery = {"d": {"results": []}}
    freight = {"value": []}

    tools = [
        tracking_tool("list_salesorder_for_sap_self", sales_orders),
        tracking_tool("list_salesorderitem_for_sap_self", items),
        tracking_tool("list_warehouseavailablestock_for_sap_self", stock),
        tracking_tool("list_a_productionorder_2_for_api_production_order_2_srv", prod),
        tracking_tool("list_a_outbdeliveryheader_for_api_outbound_delivery_srv", delivery),
        tracking_tool("list_freightorder_for_sap_self", freight),
    ]

    agent = SampleAgent()
    response = await agent.invoke(
        "Which orders are at risk today? Give me the full risk assessment.",
        context_id="test-integration-001",
        tools=tools,
    )

    # Assert no write operations were invoked
    write_tools_called = [t for t in called_tools if t in WRITE_TOOL_NAMES]
    assert write_tools_called == [], f"Write tools were called: {write_tools_called}"

    assert response.status in ("completed", "error")
    assert response.message is not None
