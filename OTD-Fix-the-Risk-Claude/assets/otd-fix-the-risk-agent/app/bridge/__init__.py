"""Live-ready OData->MCP bridge (read-only) for the Claude-backed OTD agent.

This package is the live-path replacement for SAP Agent Gateway. It is imported
lazily by the ``sap_cloud_sdk.agentgateway`` shim and is exercised only when
``IBD_TESTING`` is unset. See :mod:`bridge.odata_mcp_server` and
:mod:`bridge.token_exchange`.
"""
