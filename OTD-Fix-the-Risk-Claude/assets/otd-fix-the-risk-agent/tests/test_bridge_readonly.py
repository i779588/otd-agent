"""Offline unit tests for the read-only OData->MCP bridge.

These exercise the live-path bridge without any network or SAP tenant:
* zero-write enforcement (the agent's R6 guarantee) — non-read ops are refused;
* discovery registers only read/readByKey/metadata tools from the real specs;
* OData URL/query building for read, readByKey, and metadata;
* the token-exchange dispatch (passthrough / unknown mode).
"""

import pytest

from bridge.odata_mcp_server import ODataMcpBridge, ToolRouting
from bridge.token_exchange import get_sap_authorization_header


# ---- zero-write enforcement -------------------------------------------------

@pytest.mark.asyncio
async def test_non_read_operation_is_refused():
    """A write op must never reach HTTP — call_read_tool refuses it outright."""
    bridge = ODataMcpBridge(tools=[])
    write_routing = ToolRouting(
        kind="create",  # anything not read/readByKey/metadata
        service_id="svc",
        service_base_url="https://example/svc",
        entity_set="SalesOrder",
    )
    with pytest.raises(PermissionError):
        await bridge.call_read_tool(routing=write_routing, params={}, user_token=None)


@pytest.mark.asyncio
async def test_read_without_base_url_raises_before_network():
    bridge = ODataMcpBridge(tools=[])
    routing = ToolRouting(kind="read", service_id="svc", service_base_url="", entity_set="SalesOrder")
    with pytest.raises(RuntimeError):
        await bridge.call_read_tool(routing=routing, params={}, user_token=None)


def test_discovery_registers_only_read_tools():
    """Discovered tools from the shipped specs are all read-only."""
    bridge = ODataMcpBridge.from_env()
    descriptors = bridge.discover_tools()
    assert descriptors, "expected tools discovered from translation specs"
    kinds = {d["routing"].kind for d in descriptors}
    assert kinds <= {"read", "readByKey", "metadata"}, f"non-read op registered: {kinds}"
    # The known scenario ships 19 read-only tools across 5 services.
    assert len(descriptors) == 19


# ---- OData URL / query building --------------------------------------------

def test_build_read_request_maps_query_options():
    bridge = ODataMcpBridge(tools=[])
    routing = ToolRouting(
        kind="read",
        service_id="svc",
        service_base_url="https://example/svc/",
        entity_set="SalesOrder",
        query_params=["filter", "top", "count"],
    )
    url, query = bridge._build_request(
        routing, {"filter": "x eq 1", "top": 50, "count": True, "ignored": "nope"}
    )
    assert url == "https://example/svc/SalesOrder"
    assert query == {"$filter": "x eq 1", "$top": "50", "$count": "true"}


def test_build_readbykey_request_builds_predicate():
    bridge = ODataMcpBridge(tools=[])
    routing = ToolRouting(
        kind="readByKey",
        service_id="svc",
        service_base_url="https://example/svc",
        entity_set="SalesOrder",
        key_params=[("salesorder", "SalesOrder")],
    )
    url, query = bridge._build_request(routing, {"salesorder": "4500001", "select": "SalesOrder"})
    assert url == "https://example/svc/SalesOrder(SalesOrder='4500001')"
    assert query == {"$select": "SalesOrder"}


def test_build_metadata_request():
    bridge = ODataMcpBridge(tools=[])
    routing = ToolRouting(kind="metadata", service_id="svc", service_base_url="https://example/svc")
    url, query = bridge._build_request(routing, {})
    assert url == "https://example/svc/$metadata"
    assert query == {}


def test_readbykey_missing_key_raises():
    bridge = ODataMcpBridge(tools=[])
    routing = ToolRouting(
        kind="readByKey",
        service_id="svc",
        service_base_url="https://example/svc",
        entity_set="SalesOrder",
        key_params=[("salesorder", "SalesOrder")],
    )
    with pytest.raises(ValueError):
        bridge._build_request(routing, {})


# ---- token exchange ---------------------------------------------------------

@pytest.mark.asyncio
async def test_passthrough_returns_bearer(monkeypatch):
    monkeypatch.delenv("OTD_TOKEN_EXCHANGE_MODE", raising=False)
    header = await get_sap_authorization_header("abc.def.ghi")
    assert header == "Bearer abc.def.ghi"


@pytest.mark.asyncio
async def test_passthrough_without_token_returns_none(monkeypatch):
    monkeypatch.setenv("OTD_TOKEN_EXCHANGE_MODE", "passthrough")
    assert await get_sap_authorization_header(None) is None


@pytest.mark.asyncio
async def test_unknown_mode_raises(monkeypatch):
    monkeypatch.setenv("OTD_TOKEN_EXCHANGE_MODE", "bogus")
    with pytest.raises(ValueError):
        await get_sap_authorization_header("abc.def.ghi")


@pytest.mark.asyncio
async def test_destination_mode_requires_config_before_network(monkeypatch):
    """Destination mode must fail with a clear error before any HTTP call when
    its env is unset — no fabricated credentials, no accidental live traffic."""
    monkeypatch.setenv("OTD_TOKEN_EXCHANGE_MODE", "destination")
    for var in ("BTP_DESTINATION_URL", "BTP_DESTINATION_NAME", "BTP_DESTINATION_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError):
        await get_sap_authorization_header("user.jwt.here")
