"""Shim for `sap_cloud_sdk.agent_memory.factory.langgraph_checkpoint`.

On the SAP runtime this returned a platform-managed LangGraph checkpointer (backed
by a managed store with TTL-based thread eviction). Off-platform we use LangGraph's
in-process checkpointer, which keeps conversation threads in memory for the life of
the server process — sufficient for a single-instance A2A deployment and for the
offline demo.

The `ttl_seconds` argument is accepted for signature compatibility. The in-process
checkpointer does not evict by TTL; for a horizontally-scaled or long-lived
deployment, swap this for a persistent checkpointer (e.g. langgraph's Postgres or
Redis saver) — that is the single, documented extension point for durable memory.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:  # langgraph 1.x
    from langgraph.checkpoint.memory import InMemorySaver as _MemorySaver
except ImportError:  # pragma: no cover - older langgraph fallback
    from langgraph.checkpoint.memory import MemorySaver as _MemorySaver


def create_checkpointer(ttl_seconds: int | None = None, **_kwargs: Any):
    """Return an in-process LangGraph checkpointer.

    Args:
        ttl_seconds: Accepted for compatibility with the SAP factory signature;
            the in-process saver does not evict by TTL (noted for durability).
    """
    if ttl_seconds:
        logger.info(
            "checkpointer shim: in-process InMemorySaver (ttl_seconds=%s is not enforced "
            "off-platform; use a persistent saver for durable/TTL memory)",
            ttl_seconds,
        )
    else:
        logger.info("checkpointer shim: in-process InMemorySaver")
    return _MemorySaver()


__all__ = ["create_checkpointer"]
