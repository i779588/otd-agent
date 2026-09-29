"""Live-ready OData -> MCP bridge (read-only) — SCAFFOLD.

This is the live-path replacement for SAP Agent Gateway. It is exercised only
when ``IBD_TESTING`` is unset; offline runs (tests, demo) never reach it because
``app/mcp_providers/agw.py`` short-circuits to mcp-mock.json first.

What it does
------------
* Loads the declarative ``translation.json`` specs shipped under the sibling
  ``sap-s4-*-mcp-server/`` asset folders (the same specs the Joule build used).
* Turns each declared tool into an MCP-tool descriptor (name / description /
  input_schema / routing) that the ``sap_cloud_sdk.agentgateway`` shim adapts
  into LangChain tools.
* Issues plain OData ``GET`` requests against the backing S/4HANA services and
  returns the JSON payload as a string.

Zero-write guarantee (agent requirement R6)
-------------------------------------------
Only ``read``, ``readByKey`` and metadata operations are ever registered or
executed. ``call_read_tool`` re-checks the operation kind at call time and
raises ``PermissionError`` for anything else, and only ever issues HTTP GET.
There is no code path here that can POST/PUT/PATCH/DELETE to SAP.

Configuration (all via environment / .env — never hard-coded secrets)
---------------------------------------------------------------------
* ``OTD_MCP_TRANSLATION_ROOT`` — directory containing the ``sap-s4-*-mcp-server``
  folders. Defaults to the ``assets/`` directory that holds this agent folder
  (three levels above this file: ``app/bridge/`` -> ``app/`` -> agent -> assets).
* ``OTD_SERVICE_BASE_URLS`` — JSON object mapping a translation ``ordId`` (or the
  server folder name) to the OData service base URL, e.g.
  ``{"sap.s4:apiResource:API_PRODUCTION_ORDER_2_SRV:v1": "https://my-s4.example/sap/opu/odata/sap/API_PRODUCTION_ORDER_2_SRV"}``.
* ``OTD_HTTP_TIMEOUT_SECONDS`` — per-request timeout (default 30).

Identity propagation is delegated to :mod:`bridge.token_exchange`, which reads
the per-request user token from context and never from tool arguments.

Standalone MCP server
---------------------
``build_mcp_server()`` returns a ``FastMCP`` instance exposing the same read
tools, so a single service can also be run as its own MCP server process
(``python -m bridge.odata_mcp_server --serve``).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Operations this bridge is permitted to perform. Anything not in this set is a
# write and is refused — this is the enforcement point for the zero-write rule.
_READ_ONLY_OPERATIONS = frozenset({"read", "readByKey", "metadata"})

# JSON-schema type per known OData query option.
_QUERY_PARAM_TYPES: dict[str, str] = {
    "filter": "string",
    "select": "string",
    "orderby": "string",
    "top": "integer",
    "skip": "integer",
    "expand": "string",
    "count": "boolean",
    "inlinecount": "string",
}


@dataclass
class ToolRouting:
    """Everything needed to execute one tool against OData, minus identity."""

    kind: str  # "read" | "readByKey" | "metadata"
    service_id: str
    service_base_url: str
    entity_set: str | None = None
    # readByKey: ordered [(arg_name, odata_property_name)] for the key predicate.
    key_params: list[tuple[str, str]] = field(default_factory=list)
    # read: allowed OData query option names (filter/select/top/...).
    query_params: list[str] = field(default_factory=list)


@dataclass
class ToolDescriptor:
    """MCP-tool descriptor consumed by the agentgateway shim."""

    name: str
    description: str
    server_name: str
    fragment_name: str
    input_schema: dict[str, Any]
    routing: ToolRouting


class ODataMcpBridge:
    """Read-only OData bridge that discovers and invokes declarative MCP tools."""

    def __init__(self, tools: list[ToolDescriptor], *, timeout_seconds: float = 30.0):
        self._tools = tools
        self._timeout_seconds = timeout_seconds
        self._by_name = {t.name: t for t in tools}

    # ---- construction -----------------------------------------------------

    @classmethod
    def from_env(cls) -> "ODataMcpBridge":
        """Build a bridge from the translation specs + env configuration."""
        root = os.environ.get("OTD_MCP_TRANSLATION_ROOT")
        # app/bridge/ -> app/ -> <agent folder> -> assets/ (holds sap-s4-*-mcp-server).
        translation_root = Path(root) if root else Path(__file__).resolve().parents[3]

        try:
            base_urls: dict[str, str] = json.loads(
                os.environ.get("OTD_SERVICE_BASE_URLS", "{}")
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "OTD_SERVICE_BASE_URLS must be a JSON object mapping ordId/folder "
                f"-> base URL: {exc}"
            ) from exc

        timeout = float(os.environ.get("OTD_HTTP_TIMEOUT_SECONDS", "30"))

        tools: list[ToolDescriptor] = []
        for spec_file in sorted(translation_root.glob("*-mcp-server/mcp-translation/translation.json")):
            server_folder = spec_file.parents[1].name
            spec = json.loads(spec_file.read_text(encoding="utf-8"))
            service_id = spec.get("target", {}).get("ordId", server_folder)
            server_name = spec.get("serverInfo", {}).get("name", server_folder)

            base_url = base_urls.get(service_id) or base_urls.get(server_folder)
            if not base_url:
                # No URL configured yet — register the tools anyway so discovery
                # is complete; a live call without a URL fails loudly (below).
                logger.warning(
                    "No base URL configured for service '%s' (folder '%s'); set "
                    "OTD_SERVICE_BASE_URLS before live calls.",
                    service_id,
                    server_folder,
                )

            for tool_spec in spec.get("tools", []):
                descriptor = cls._descriptor_from_spec(
                    tool_spec, service_id, server_name, server_folder, base_url or ""
                )
                if descriptor is not None:
                    tools.append(descriptor)

        logger.info("ODataMcpBridge discovered %d read-only tool(s).", len(tools))
        return cls(tools, timeout_seconds=timeout)

    @staticmethod
    def _descriptor_from_spec(
        tool_spec: dict[str, Any],
        service_id: str,
        server_name: str,
        server_folder: str,
        base_url: str,
    ) -> ToolDescriptor | None:
        name = tool_spec["name"]
        description = tool_spec.get("description", "")
        odata = tool_spec.get("odataType", {})

        properties: dict[str, Any] = {}
        required: list[str] = []

        if "metadataRequest" in odata:
            routing = ToolRouting(
                kind="metadata", service_id=service_id, service_base_url=base_url
            )
        elif "entitySet" in odata:
            entity = odata["entitySet"]
            crud = entity.get("crudOperation", "")
            if crud not in _READ_ONLY_OPERATIONS:
                # Defensive: a write op in a spec is dropped, never registered.
                logger.warning(
                    "Skipping non-read tool '%s' (crudOperation=%s).", name, crud
                )
                return None

            key_params: list[tuple[str, str]] = []
            query_params: list[str] = []
            for param in entity.get("parameters", []):
                odata_name = param["name"]
                arg_name = param.get("newParameterName", odata_name)
                if odata_name in _QUERY_PARAM_TYPES:
                    query_params.append(odata_name)
                    properties[odata_name] = {
                        "type": _QUERY_PARAM_TYPES[odata_name],
                        "description": _query_param_description(odata_name),
                    }
                else:
                    # A non-query-option parameter on a readByKey op is a key field.
                    key_params.append((arg_name, odata_name))
                    properties[arg_name] = {
                        "type": "string",
                        "description": f"Key field '{odata_name}'.",
                    }

            # For readByKey, the key fields are required to address a record.
            if crud == "readByKey":
                required = [arg for arg, _ in key_params]

            routing = ToolRouting(
                kind=crud,
                service_id=service_id,
                service_base_url=base_url,
                entity_set=entity.get("name"),
                key_params=key_params,
                query_params=query_params,
            )
        else:
            logger.warning("Skipping tool '%s': unrecognized odataType.", name)
            return None

        input_schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            input_schema["required"] = required

        return ToolDescriptor(
            name=name,
            description=description,
            server_name=server_name,
            fragment_name=server_folder,
            input_schema=input_schema,
            routing=routing,
        )

    # ---- discovery / invocation (agentgateway shim contract) --------------

    def discover_tools(self) -> list[dict[str, Any]]:
        """Return tool descriptors as plain dicts for the agentgateway shim."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "server_name": t.server_name,
                "fragment_name": t.fragment_name,
                "input_schema": t.input_schema,
                "routing": t.routing,
            }
            for t in self._tools
        ]

    async def call_read_tool(
        self,
        *,
        routing: ToolRouting,
        params: dict[str, Any],
        user_token: str | None = None,
    ) -> str:
        """Execute one read/metadata operation and return the JSON body as text.

        Raises:
            PermissionError: if ``routing.kind`` is anything but a read/metadata
                operation (zero-write enforcement).
        """
        if routing.kind not in _READ_ONLY_OPERATIONS:
            raise PermissionError(
                f"Refusing non-read operation '{routing.kind}'. This bridge is "
                "read-only (agent zero-write guarantee)."
            )
        if not routing.service_base_url:
            raise RuntimeError(
                f"No base URL configured for service '{routing.service_id}'. "
                "Set OTD_SERVICE_BASE_URLS before making live calls."
            )

        url, query = self._build_request(routing, params or {})
        headers = {"Accept": "application/json"}

        # Identity propagation: resolve the SAP-bound authorization header from
        # the per-request user token via the token-exchange bridge. Never taken
        # from tool arguments.
        from bridge.token_exchange import get_sap_authorization_header

        auth_header = await get_sap_authorization_header(user_token)
        if auth_header:
            headers["Authorization"] = auth_header

        import httpx

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            # GET only — there is deliberately no other verb in this bridge.
            response = await client.get(url, params=query, headers=headers)
            response.raise_for_status()
            return response.text

    # ---- URL building -----------------------------------------------------

    def _build_request(
        self, routing: ToolRouting, params: dict[str, Any]
    ) -> tuple[str, dict[str, str]]:
        base = routing.service_base_url.rstrip("/")

        if routing.kind == "metadata":
            return f"{base}/$metadata", {}

        entity = routing.entity_set or ""

        if routing.kind == "readByKey":
            key_predicate = self._key_predicate(routing, params)
            url = f"{base}/{entity}({key_predicate})"
            query = self._odata_query(
                {k: v for k, v in params.items() if k in ("select", "expand")}
            )
            return url, query

        # kind == "read"
        allowed = {k: v for k, v in params.items() if k in routing.query_params}
        return f"{base}/{entity}", self._odata_query(allowed)

    @staticmethod
    def _key_predicate(routing: ToolRouting, params: dict[str, Any]) -> str:
        """Build the OData key predicate, e.g. ``SalesOrder='4500001'``."""
        parts: list[str] = []
        for arg_name, odata_name in routing.key_params:
            if arg_name not in params or params[arg_name] is None:
                continue
            value = str(params[arg_name])
            parts.append(f"{odata_name}='{quote(value, safe='')}'")
        if not parts:
            raise ValueError("readByKey call is missing its key field(s).")
        return ",".join(parts)

    @staticmethod
    def _odata_query(params: dict[str, Any]) -> dict[str, str]:
        """Map friendly param names to OData ``$`` query options, dropping Nones."""
        mapping = {
            "filter": "$filter",
            "select": "$select",
            "orderby": "$orderby",
            "top": "$top",
            "skip": "$skip",
            "expand": "$expand",
            "count": "$count",
            "inlinecount": "$inlinecount",
        }
        out: dict[str, str] = {}
        for key, value in params.items():
            if value is None:
                continue
            odata_key = mapping.get(key)
            if not odata_key:
                continue
            if isinstance(value, bool):
                out[odata_key] = "true" if value else "false"
            else:
                out[odata_key] = str(value)
        return out


def build_mcp_server(bridge: ODataMcpBridge | None = None):
    """Build a standalone FastMCP server exposing the bridge's read tools.

    Lets a single service run as its own MCP server process for local testing
    against a live tenant, independent of the A2A agent.
    """
    from mcp.server.fastmcp import FastMCP

    bridge = bridge or ODataMcpBridge.from_env()
    server = FastMCP("otd-odata-bridge")

    for descriptor in bridge.discover_tools():
        routing: ToolRouting = descriptor["routing"]

        def _make_handler(_routing: ToolRouting):
            async def _handler(**kwargs: Any) -> str:
                # user_token is resolved from context inside call_read_tool.
                return await bridge.call_read_tool(routing=_routing, params=kwargs)

            return _handler

        server.add_tool(
            _make_handler(routing),
            name=descriptor["name"],
            description=descriptor["description"],
        )

    return server


def _query_param_description(name: str) -> str:
    return {
        "filter": "OData $filter expression",
        "select": "Comma-separated properties to return",
        "orderby": "OData $orderby expression",
        "top": "Max records to return (page size, keep <=100)",
        "skip": "Records to skip (paging offset)",
        "expand": "OData $expand navigation properties",
        "count": "Include total count",
        "inlinecount": "Set to 'allpages' to include total count",
    }.get(name, "")


async def _smoke_check(token: str | None) -> int:
    """Read-only connectivity probe: one ``$metadata`` GET per configured service.

    Validates the base URL + Destination/token-exchange auth end-to-end without
    pulling any business data. Uses the current ``OTD_TOKEN_EXCHANGE_MODE`` and
    an optional ``--token`` (needed only for principal-propagation setups).
    Returns a process exit code (0 = all reachable).
    """
    bridge = ODataMcpBridge.from_env()

    # One probe per distinct service: prefer its metadata tool; else a read
    # tool capped at $top=1 so no meaningful business data is fetched.
    probes: dict[str, tuple[ToolRouting, dict[str, Any]]] = {}
    for descriptor in bridge.discover_tools():
        routing: ToolRouting = descriptor["routing"]
        if not routing.service_base_url:
            continue
        existing = probes.get(routing.service_id)
        if routing.kind == "metadata":
            probes[routing.service_id] = (routing, {})
        elif existing is None and routing.kind == "read":
            probes[routing.service_id] = (routing, {"top": 1})

    if not probes:
        print("No services have a base URL configured. Set OTD_SERVICE_BASE_URLS.")
        return 2

    failures = 0
    for service_id, (routing, params) in sorted(probes.items()):
        try:
            body = await bridge.call_read_tool(
                routing=routing, params=params, user_token=token
            )
            preview = body[:80].replace("\n", " ")
            print(f"OK    {service_id}  [{routing.kind}]  {preview}...")
        except Exception as exc:  # noqa: BLE001 - report every failure, keep going
            failures += 1
            print(f"FAIL  {service_id}  [{routing.kind}]  {type(exc).__name__}: {exc}")

    print(f"\n{len(probes) - failures}/{len(probes)} services reachable (read-only).")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OTD read-only OData->MCP bridge")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run as a standalone MCP server (stdio transport).",
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="Print the discovered read-only tools and exit.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Read-only connectivity probe: one $metadata GET per configured "
        "service (validates base URLs + Destination/token-exchange auth).",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional end-user JWT for principal-propagation setups (--smoke).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.list_tools:
        _bridge = ODataMcpBridge.from_env()
        for _t in _bridge.discover_tools():
            print(f"{_t['name']:60s} [{_t['routing'].kind}] {_t['server_name']}")
    elif args.smoke:
        import asyncio

        raise SystemExit(asyncio.run(_smoke_check(args.token)))
    elif args.serve:
        build_mcp_server().run()
    else:
        parser.print_help()
