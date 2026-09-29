"""Shim for `sap_cloud_sdk.aicore`.

Two routing modes are supported, selected via OTD_LLM_ROUTE:

* ``direct`` (default): LLM reasoning runs on the **Anthropic API** directly.
  LiteLLM's ``anthropic/`` provider reads ``ANTHROPIC_API_KEY`` automatically.
  No global AI Core configuration is needed; this function is a no-op.
  *Governance deviation* — see agent-outcome-report.md §4 for the flagged
  controls and the required exception + security review before any
  production/customer use.

* ``aicore``: LLM reasoning routes through the **SAP Generative AI Hub**
  (compliant Golden Path). The ``gen_ai_hub`` proxy client is initialised here
  from ``AICORE_*`` environment variables; agent.py's ``_build_aicore_llm()``
  then picks it up via ``get_proxy_client()``. Required env vars::

      AICORE_BASE_URL        https://api.ai.prod.<region>.aws.ml.hana.ondemand.com
      AICORE_AUTH_URL        https://<subaccount>.authentication.<region>.hana.ondemand.com/oauth/token
      AICORE_CLIENT_ID       <service-key clientid>
      AICORE_CLIENT_SECRET   <service-key clientsecret>  [SECRET — .env only]
      AICORE_RESOURCE_GROUP  default  (or the resource group holding the deployment)
      AICORE_DEPLOYMENT_ID   d009d0ca6a44ae29  (pre-provisioned Claude deployment)

  The whole service key JSON can also be passed as a single ``AICORE_SERVICE_KEY``
  variable if you prefer to paste it from the BTP cockpit.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Required vars for the aicore route (CLIENT_SECRET is a secret → only in .env)
_AICORE_REQUIRED_VARS = (
    "AICORE_BASE_URL",
    "AICORE_AUTH_URL",
    "AICORE_CLIENT_ID",
    "AICORE_CLIENT_SECRET",
)


def set_aicore_config() -> None:
    """Validate credentials at startup and log the active LLM routing mode.

    For ``OTD_LLM_ROUTE=direct`` this is a no-op (beyond a readiness check).
    For ``OTD_LLM_ROUTE=aicore`` the ``gen_ai_hub`` proxy client initialises
    lazily when ``_build_aicore_llm()`` first calls ``get_proxy_client()`` in
    agent.py; this function only checks that the required env vars are present
    so misconfiguration is obvious at startup rather than at first inference.
    """
    if os.environ.get("IBD_TESTING") == "1":
        logger.info(
            "aicore shim: IBD_TESTING=1 — offline mock mode, no LLM credentials required"
        )
        return

    route = os.environ.get("OTD_LLM_ROUTE", "direct").lower()

    if route == "aicore":
        # Credentials can come from individual AICORE_* vars OR from the
        # AICORE_SERVICE_KEY JSON blob (same precedence as ai-core-sdk).
        service_key = os.environ.get("AICORE_SERVICE_KEY", "")
        if service_key:
            logger.info(
                "aicore shim: OTD_LLM_ROUTE=aicore — credentials from AICORE_SERVICE_KEY"
            )
        else:
            missing = [v for v in _AICORE_REQUIRED_VARS if not os.environ.get(v)]
            if missing:
                logger.warning(
                    "aicore shim: OTD_LLM_ROUTE=aicore — missing env vars: %s. "
                    "Live LLM calls will fail. Set them in your .env (see .env.example).",
                    ", ".join(missing),
                )
            else:
                deployment_id = os.environ.get("AICORE_DEPLOYMENT_ID", "d009d0ca6a44ae29")
                resource_group = os.environ.get("AICORE_RESOURCE_GROUP", "default")
                logger.info(
                    "aicore shim: OTD_LLM_ROUTE=aicore — routing Claude via SAP Gen AI Hub "
                    "(deployment=%s, resource_group=%s)",
                    deployment_id,
                    resource_group,
                )
    else:
        # Direct Anthropic API path
        if not os.environ.get("ANTHROPIC_API_KEY"):
            logger.warning(
                "aicore shim: ANTHROPIC_API_KEY is not set — live LLM calls will fail. "
                "Set it in your .env (see .env.example)."
            )
        else:
            logger.info(
                "aicore shim: OTD_LLM_ROUTE=direct — Anthropic API via LiteLLM (anthropic/ provider)"
            )


__all__ = ["set_aicore_config"]
