"""Live-ready identity propagation for the OData bridge — SCAFFOLD.

Turns the A2A caller's bearer token (captured per-request by ``JWTContextMiddleware``
in ``app/main.py`` and read from context by the bridge) into an SAP-bound
authorization header, so the planner's own identity — not a shared technical
user — is what S/4HANA authorizes. This preserves the agent's RBAC pass-through
requirement (only data the active user may see is ever returned).

Design rules
------------
* **Identity comes from the request context only** — the ``user_token`` argument
  originates from ``JWTContextMiddleware`` / the per-request context var. It is
  never taken from tool arguments the model can influence.
* **Secrets come from the environment / .env only** — never hard-coded, never
  logged.
* **Read-only** — this module only obtains credentials; it performs no SAP writes.

Modes (env ``OTD_TOKEN_EXCHANGE_MODE``)
---------------------------------------
* ``passthrough`` (default) — forward the incoming bearer token unchanged. Correct
  when S/4HANA trusts the same identity provider that issued the A2A token.
* ``basic`` — fixed technical user (``OTD_S4_USER`` + ``OTD_S4_PASSWORD``), e.g. an
  S/4HANA Cloud communication user. No SAML, no destination service, no per-user
  RBAC — every call acts as this one identity. Simplest path for a dev/demo live
  test; not for production. Read-only still holds (the bridge issues GET only).
* ``xsuaa`` — OAuth2 **jwt-bearer** grant against XSUAA: exchange the incoming
  user assertion for an S/4-audience access token (true principal propagation).
  Env: ``XSUAA_TOKEN_URL``, ``XSUAA_CLIENT_ID``, ``XSUAA_CLIENT_SECRET``.
* ``destination`` — resolve a BTP **Destination** (``OAuth2SAMLBearerAssertion`` /
  ``PrincipalPropagation``) and use the token it returns. Two credential sources,
  auto-detected:
    - **On CF (preferred):** a bound ``destination`` service. Its credentials come
      from ``VCAP_SERVICES``; only ``BTP_DESTINATION_NAME`` need be set. The module
      mints a client-credentials token for the destination service, then reads the
      destination. This is the idiomatic Cloud Foundry pattern.
    - **Local / off-CF:** set ``BTP_DESTINATION_URL`` + ``BTP_DESTINATION_TOKEN``
      (a pre-obtained bearer for the Destination service) + ``BTP_DESTINATION_NAME``.


All network routes are guarded: an unconfigured mode raises a clear error, and
this module is only reached on the live path (``IBD_TESTING`` unset).
"""

from __future__ import annotations

import base64
import json
import logging
import os

logger = logging.getLogger(__name__)

_JWT_BEARER_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"


async def get_sap_authorization_header(user_token: str | None) -> str | None:
    """Return the ``Authorization`` header value for an SAP OData call.

    Args:
        user_token: the active user's bearer token from request context (never
            from tool arguments). May be ``None`` if no token was presented.

    Returns:
        A full header value (``"Bearer <token>"``) or ``None`` when no identity
        is available and none is required.
    """
    mode = os.environ.get("OTD_TOKEN_EXCHANGE_MODE", "passthrough").lower()

    # Modes that do not need a per-request user identity: 'destination' (may carry
    # a SystemUser or its own technical auth) and 'basic' (fixed technical user).
    if not user_token and mode not in ("destination", "basic"):
        # No caller identity to propagate. Return None so the bridge issues an
        # unauthenticated call (which SAP will reject if it requires auth) rather
        # than fabricating credentials.
        logger.warning("No user token in context; proceeding without Authorization header.")
        return None

    if mode == "passthrough":
        return f"Bearer {user_token}"
    if mode == "basic":
        # Fixed technical user (e.g. an S/4HANA Cloud communication user). No SAML,
        # no destination service, no per-user RBAC — every call acts as this one
        # identity. Read-only still holds (the bridge issues GET only).
        return _basic_auth_header()
    if mode == "xsuaa":
        token = await _exchange_via_xsuaa(user_token)
        return f"Bearer {token}"
    if mode == "destination":
        # _resolve_via_destination returns a full Authorization header value: the
        # destination service tells us the scheme (Bearer for OAuth2/SAML, Basic
        # for BasicAuthentication destinations), so return it unchanged.
        return await _resolve_via_destination(user_token)

    raise ValueError(f"Unknown OTD_TOKEN_EXCHANGE_MODE '{mode}'.")


def _basic_auth_header() -> str:
    """Build a ``Basic`` header from a fixed technical user's credentials.

    Credentials come from the environment / .env only (never from tool args and
    never logged): ``OTD_S4_USER`` + ``OTD_S4_PASSWORD``. Intended for dev/demo
    live tests against S/4HANA Cloud communication users, where a full
    principal-propagation pipeline is not yet in place.
    """
    user = _require_env("OTD_S4_USER")
    password = _require_env("OTD_S4_PASSWORD")
    encoded = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"


async def _exchange_via_xsuaa(user_token: str) -> str:
    """XSUAA jwt-bearer grant: exchange the user assertion for an S/4 token."""
    token_url = _require_env("XSUAA_TOKEN_URL")
    client_id = _require_env("XSUAA_CLIENT_ID")
    client_secret = _require_env("XSUAA_CLIENT_SECRET")

    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": _JWT_BEARER_GRANT,
                "assertion": user_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "response_type": "token",
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        access_token = response.json().get("access_token")

    if not access_token:
        raise RuntimeError("XSUAA jwt-bearer exchange returned no access_token.")
    return access_token


async def _resolve_via_destination(user_token: str | None) -> str:
    """Resolve a BTP Destination and return its principal-propagation token.

    Prefers a bound ``destination`` service (VCAP_SERVICES) — the CF pattern —
    and falls back to a manually supplied BTP_DESTINATION_URL/TOKEN for local runs.
    """
    destination_name = _require_env("BTP_DESTINATION_NAME")

    if os.environ.get("VCAP_SERVICES"):
        return await _resolve_via_vcap(user_token, destination_name)

    destination_url = _require_env("BTP_DESTINATION_URL")
    destination_token = _require_env("BTP_DESTINATION_TOKEN")

    import httpx

    headers = {"Authorization": f"Bearer {destination_token}", "Accept": "application/json"}
    # Principal propagation destinations accept the user assertion via this header.
    if user_token:
        headers["X-user-token"] = user_token

    # Accept either the destination-service base (…/destination-configuration/v1)
    # or a URL that already includes the /destinations collection — so it works
    # whichever form is pasted into BTP_DESTINATION_URL.
    base = destination_url.rstrip("/")
    if base.endswith("/destinations"):
        request_url = f"{base}/{destination_name}"
    else:
        request_url = f"{base}/destinations/{destination_name}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(request_url, headers=headers)
        response.raise_for_status()
        payload = response.json()

    return _destination_header_from_payload(payload, destination_name)


async def _resolve_via_vcap(user_token: str | None, destination_name: str) -> str:
    """Read the destination via a CF-bound ``destination`` service (VCAP_SERVICES).

    Mints a client-credentials token for the destination service from its bound
    XSUAA credentials, then reads the named destination. No secrets are handled by
    the app itself — they come from the service binding the platform injects.
    """
    creds = _destination_credentials_from_vcap()
    uri = str(creds["uri"]).rstrip("/")
    token_base = str(creds.get("url") or creds.get("token_service_url") or "").rstrip("/")
    client_id = creds.get("clientid") or creds.get("client_id")
    client_secret = creds.get("clientsecret") or creds.get("client_secret")
    if not (token_base and client_id and client_secret):
        raise RuntimeError(
            "Bound destination service is missing url/clientid/clientsecret."
        )

    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        tok = await client.post(
            f"{token_base}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Accept": "application/json"},
        )
        tok.raise_for_status()
        service_token = tok.json().get("access_token")
        if not service_token:
            raise RuntimeError("Destination service token request returned no access_token.")

        headers = {"Authorization": f"Bearer {service_token}", "Accept": "application/json"}
        if user_token:
            headers["X-user-token"] = user_token
        response = await client.get(
            f"{uri}/destination-configuration/v1/destinations/{destination_name}",
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()

    return _destination_header_from_payload(payload, destination_name)


def _destination_credentials_from_vcap() -> dict:
    """Extract the destination service credentials from VCAP_SERVICES."""
    services = json.loads(os.environ.get("VCAP_SERVICES", "{}"))
    for binding in services.get("destination", []):
        creds = binding.get("credentials") or {}
        if creds.get("uri"):
            return creds
    raise RuntimeError(
        "OTD_TOKEN_EXCHANGE_MODE=destination with VCAP_SERVICES set, but no bound "
        "'destination' service was found. Bind one (cf bind-service) or use the "
        "local BTP_DESTINATION_URL/TOKEN form."
    )


def _destination_header_from_payload(payload: dict, destination_name: str) -> str:
    """Return a ready-to-use ``Authorization`` header from a destination response.

    The destination service resolves the target auth and returns each token with an
    ``http_header`` ({key, value}) that already carries the correct scheme (``Bearer``
    for OAuth2/SAML, ``Basic`` for BasicAuthentication). Prefer that header verbatim;
    fall back to ``Bearer <value>`` for older payload shapes. If the service could not
    mint a token it returns an ``error`` on the entry — surface it so misconfigured
    destinations (e.g. principal propagation with no user/SystemUser) fail loudly.
    """
    auth_tokens = payload.get("authTokens") or []
    if not auth_tokens:
        raise RuntimeError(
            f"Destination '{destination_name}' returned no authTokens."
        )
    first = auth_tokens[0]
    if first.get("error"):
        raise RuntimeError(
            f"Destination '{destination_name}' token retrieval failed: {first['error']}"
        )
    http_header = first.get("http_header") or {}
    if http_header.get("value"):
        return http_header["value"]
    if first.get("value"):
        return f"Bearer {first['value']}"
    raise RuntimeError(
        f"Destination '{destination_name}' returned no usable authTokens."
    )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' is required for the configured "
            "OTD_TOKEN_EXCHANGE_MODE but is not set (see .env.example)."
        )
    return value
