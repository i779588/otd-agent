"""Shim for `sap_cloud_sdk.aicore`.

On the SAP runtime, `set_aicore_config()` wired LiteLLM to route `sap/…`-prefixed
model names through SAP AI Core (Gen AI Hub). For the Claude-direct deployment the
LLM is reached through LiteLLM's native `anthropic/` provider using the
`ANTHROPIC_API_KEY` environment variable, which LiteLLM reads automatically — so no
global configuration is required and this is a no-op.

Model routing itself is repointed in app/agent.py (env-driven `anthropic/…` model
ids) and app/prompt_injection_detector.py, not here.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def set_aicore_config() -> None:
    """No-op: Anthropic credentials come from ANTHROPIC_API_KEY in the environment.

    Emits a single explicit warning if the key is absent so misconfiguration is
    obvious at startup (mock mode, IBD_TESTING=1, does not need it).
    """
    if os.environ.get("IBD_TESTING") == "1":
        logger.info("aicore shim: IBD_TESTING=1 — offline mock mode, no LLM credentials required")
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning(
            "aicore shim: ANTHROPIC_API_KEY is not set — live LLM calls will fail. "
            "Set it in your .env (see .env.example)."
        )
    else:
        logger.info("aicore shim: using Anthropic API directly via LiteLLM (anthropic/ provider)")


__all__ = ["set_aicore_config"]
