"""Shim for `sap_cloud_sdk.agentgateway.converters`.

Provides `mcp_tool_to_langchain`, which turns a bridge MCP-tool descriptor into a
LangChain `StructuredTool` whose async implementation delegates to the caller
supplied by app/mcp_providers/agw.py (which in turn calls
`util.call_mcp_tool_with_retry`). Tool names are kept plain (unnamespaced) so the
live tool set matches the offline mock tool set the system prompt is written for.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import Field, create_model

logger = logging.getLogger(__name__)

_JSON_TO_PY: dict[str, type] = {
    "integer": int,
    "number": float,
    "boolean": bool,
    "string": str,
}


def _args_model(tool_name: str, input_schema: dict[str, Any]):
    """Build a pydantic args model from a JSON-schema-ish input spec."""
    props = (input_schema or {}).get("properties", {})
    required = set((input_schema or {}).get("required", []))
    fields: dict[str, Any] = {}
    for field_name, info in props.items():
        py_type = _JSON_TO_PY.get(info.get("type", "string"), str)
        description = info.get("description", "")
        if field_name in required:
            fields[field_name] = (py_type, Field(description=description))
        else:
            fields[field_name] = (py_type, Field(default=None, description=description))
    if fields:
        return create_model(f"{tool_name}_args", **fields)
    return create_model(f"{tool_name}_args")


def mcp_tool_to_langchain(
    mcp_tool: Any,
    caller: Callable[..., Any],
    token_getter: Callable[[], Any] | None = None,
) -> BaseTool:
    """Convert a bridge MCP-tool descriptor into a LangChain StructuredTool.

    Args:
        mcp_tool: descriptor with `.name`, `.description`, `.input_schema`.
        caller: async callable invoked with the tool's arguments as kwargs; it
            owns identity propagation (reads the per-request user token itself).
        token_getter: accepted for signature compatibility with the SAP converter.
    """
    args_schema = _args_model(mcp_tool.name, getattr(mcp_tool, "input_schema", {}))

    async def _coroutine(**kwargs: Any) -> str:
        return await caller(**kwargs)

    return StructuredTool(
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        args_schema=args_schema,
        coroutine=_coroutine,
        handle_tool_error=True,
    )


__all__ = ["mcp_tool_to_langchain"]
