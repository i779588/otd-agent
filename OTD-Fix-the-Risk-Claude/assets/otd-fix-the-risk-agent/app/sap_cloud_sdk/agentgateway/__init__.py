"""Shim for `sap_cloud_sdk.agentgateway` — live, read-only OData→MCP tool client.

On the SAP runtime, `create_client()` returned a SAP Agent Gateway client that
discovered MCP tools from registered MCP servers and invoked them with principal
propagation. Off-platform, this shim provides a drop-in client backed by the local
read-only OData→MCP bridge (see ../../bridge/odata_mcp_server.py), which translates
the declarative `mcp-translation/translation.json` specs (shipped alongside the
agent) into OData GET calls against an SAP S/4HANA system.

Contract required by the application code (app/mcp_providers/agw.py + app/util.py):
  * `create_client()` -> object with
        async list_mcp_tools(user_token=<callable|str|None>) -> list[_BridgeMcpTool]
        async call_mcp_tool(tool=<_BridgeMcpTool>, user_token=<str|None>, **kwargs) -> str
  * `converters.mcp_tool_to_langchain(tool, caller, token_getter)` -> StructuredTool

This path is exercised only when IBD_TESTING != "1" (i.e. live mode). It is
strictly read-only by construction: the bridge refuses any non-read OData
operation, preserving the agent's zero-write guarantee.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class _BridgeMcpTool:
    """Minimal MCP-tool descriptor, duck-compatible with the SAP SDK tool object.

    Exposes the attributes app/util.py reads (`name`, `description`, `server_name`,
    `fragment_name`) plus the input schema used to build the LangChain args model.
    """

    name: str
    description: str
    server_name: str
    fragment_name: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    # Internal routing metadata (service base path + entity/operation), used by the
    # bridge to build the OData request. Not part of the public SAP contract.
    _routing: dict[str, Any] = field(default_factory=dict)


class AgentGatewayBridgeClient:
    """Read-only OData→MCP client that mimics the SAP Agent Gateway SDK surface."""

    def __init__(self) -> None:
        # Import the bridge lazily so merely importing this package never requires
        # the live OData configuration or optional deps to be present.
        from bridge.odata_mcp_server import ODataMcpBridge

        self._bridge = ODataMcpBridge.from_env()

    async def list_mcp_tools(self, user_token: Any = None) -> list[_BridgeMcpTool]:
        """Discover read-only tools from the configured translation specs.

        `user_token` is accepted for signature compatibility (the SAP client varied
        the tool listing per user); the OData bridge exposes the same read tools to
        every caller and enforces RBAC at the SAP backend via the propagated token.
        """
        descriptors = self._bridge.discover_tools()
        tools = [
            _BridgeMcpTool(
                name=d["name"],
                description=d["description"],
                server_name=d["server_name"],
                fragment_name=d.get("fragment_name", d["server_name"]),
                input_schema=d.get("input_schema", {}),
                _routing=d.get("routing", {}),
            )
            for d in descriptors
        ]
        logger.info("agentgateway shim: discovered %d read-only OData tool(s)", len(tools))
        return tools

    async def call_mcp_tool(
        self, tool: _BridgeMcpTool, user_token: str | None = None, **kwargs: Any
    ) -> str:
        """Invoke a read-only OData tool, propagating the user's identity.

        The identity comes from `user_token` (derived from the A2A request context,
        never from tool arguments). The bridge performs the token exchange and the
        OData GET, and refuses any non-read operation.
        """
        return await self._bridge.call_read_tool(
            routing=tool._routing,
            params=kwargs,
            user_token=user_token,
        )


def create_client() -> AgentGatewayBridgeClient:
    """Return a read-only OData→MCP bridge client (SAP Agent Gateway replacement)."""
    return AgentGatewayBridgeClient()


__all__ = ["create_client", "AgentGatewayBridgeClient", "_BridgeMcpTool"]
