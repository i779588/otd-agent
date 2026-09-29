"""Compatibility shim for `sap_cloud_sdk` — Claude / open-source deployment.

The original agent was generated for the SAP CoE pro-code runtime and imported a
proprietary, SAP-internal package (`sap-cloud-sdk`, not on public PyPI) at five
sites across three files. That single dependency was the only thing binding the
agent to SAP AI Core (LLM routing), SAP Agent Gateway (tool discovery), and the
SAP agent-config/bootstrap machinery.

This shim provides the same public symbols with open, self-contained
implementations so the *application code is unchanged* while the agent runs:

  * LLM reasoning on the Anthropic API directly (via LiteLLM `anthropic/` routing;
    see app/agent.py) instead of `sap/…` AI Core routing — `aicore.set_aicore_config`
    becomes a no-op because credentials come from ANTHROPIC_API_KEY in the env.
  * Tools via a local, read-only OData→MCP bridge (see bridge/) instead of SAP
    Agent Gateway — `agentgateway.create_client` / `converters.mcp_tool_to_langchain`.
  * Config decorators (`agent_decorators`) as transparent pass-throughs.
  * Conversation memory via LangGraph's in-process checkpointer
    (`agent_memory.factory.langgraph_checkpoint.create_checkpointer`).
  * `bootstrap` as a no-op (the A2A Starlette app runs standalone).

Nothing here writes to SAP. The live tool path is read-only by construction.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def bootstrap(app=None):
    """No-op stand-in for the SAP platform bootstrap.

    The SAP runtime used this to attach platform middleware/telemetry. The A2A
    Starlette application is fully functional without it, so this simply returns
    the app unchanged.
    """
    logger.debug("sap_cloud_sdk.bootstrap shim: no-op (running off-platform)")
    return app


__all__ = ["bootstrap"]
