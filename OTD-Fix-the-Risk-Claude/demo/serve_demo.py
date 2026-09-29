"""Tiny offline demo server for the Claude-backed OTD agent — DEMO ONLY.

Serves demo/index.html and proxies the browser's questions to the running A2A
agent using the standard A2A JSON-RPC ``message/send`` method. The proxy exists
so the static page never makes a cross-origin request (no CORS changes to the
agent server, and app/main.py stays byte-identical to the ported original).

Run order (all offline, mock tools via IBD_TESTING=1):

    # 1. Start the agent (mock tools; ANTHROPIC_API_KEY needed only for the LLM reasoning step)
    cd assets/otd-fix-the-risk-agent
    IBD_TESTING=1 ANTHROPIC_API_KEY=sk-... python app/main.py --port 5000

    # 2. In a second shell, start this demo server and open http://localhost:8000
    python demo/serve_demo.py

Environment:
    OTD_AGENT_URL   Base URL of the running A2A agent (default http://localhost:5000/)
    DEMO_PORT       Port for this demo server (default 8000)

This server is for local demonstration only. It is not part of the deployable
agent and performs no SAP calls of its own.
"""

from __future__ import annotations

import json
import os
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AGENT_URL = os.environ.get("OTD_AGENT_URL", "http://localhost:5000/")
DEMO_PORT = int(os.environ.get("DEMO_PORT", "8000"))
_INDEX = Path(__file__).parent / "index.html"

# Reflect the run mode in the UI. The demo server is started alongside the agent,
# so its own IBD_TESTING env mirrors the agent's: "1" => offline mock fixtures,
# anything else => LIVE (real S/4HANA via the read-only OData bridge).
_MODE = "mock" if os.environ.get("IBD_TESTING") == "1" else "live"

# A syntactically valid but UNSIGNED demo JWT (header.payload.sig) carrying a
# 'sub' claim, so the agent's get_user_sub()/thread-id logic has an identity to
# key on. It authorizes nothing — in mock mode no SAP call is ever made. Never
# use an unsigned token like this against a real backend.
_DEMO_JWT = (
    "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0."
    "eyJzdWIiOiJkZW1vLXBsYW5uZXIiLCJuYW1lIjoiRGVtbyBQbGFubmVyIn0."
    "demo-not-a-real-signature"
)


def _ask_agent(query: str) -> dict:
    """Send one question to the agent via A2A message/send and return the result."""
    rpc = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": query}],
                "messageId": str(uuid.uuid4()),
                "kind": "message",
            }
        },
    }
    req = urllib.request.Request(
        AGENT_URL,
        data=json.dumps(rpc).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_DEMO_JWT}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload


def _extract_text(payload: dict) -> tuple[str, str]:
    """Pull the advisory text + task state out of the JSON-RPC result."""
    if "error" in payload:
        err = payload["error"]
        return f"Agent error: {err.get('message', err)}", "error"

    result = payload.get("result", {})
    state = (result.get("status") or {}).get("state", "unknown")

    # The executor returns the final answer as an artifact named 'agent_result'.
    for artifact in result.get("artifacts", []) or []:
        for part in artifact.get("parts", []) or []:
            text = part.get("text") or (part.get("root") or {}).get("text")
            if text:
                return text, state

    # Fallback: a status message (e.g. input_required).
    status_msg = (result.get("status") or {}).get("message") or {}
    for part in status_msg.get("parts", []) or []:
        text = part.get("text") or (part.get("root") or {}).get("text")
        if text:
            return text, state

    return "(No text returned by the agent.)", state


class DemoHandler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if self.path in ("/", "/index.html"):
            self._send(200, _INDEX.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/mode":
            out = json.dumps({"mode": _MODE, "agent_url": AGENT_URL}).encode("utf-8")
            self._send(200, out, "application/json")
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        if self.path != "/api/ask":
            self._send(404, b"Not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            query = (body.get("query") or "").strip()
            if not query:
                raise ValueError("Empty query")
            text, state = _extract_text(_ask_agent(query))
            out = json.dumps({"text": text, "state": state}).encode("utf-8")
            self._send(200, out, "application/json")
        except Exception as exc:  # surface a readable message to the demo UI
            out = json.dumps(
                {
                    "text": (
                        f"Could not reach the agent at {AGENT_URL}. Is it running "
                        f"with IBD_TESTING=1?\n\nDetail: {exc}"
                    ),
                    "state": "error",
                }
            ).encode("utf-8")
            self._send(200, out, "application/json")

    def log_message(self, *_args) -> None:  # quieter console
        pass


if __name__ == "__main__":
    print(f"OTD demo UI:   http://localhost:{DEMO_PORT}   [mode: {_MODE.upper()}]")
    print(f"Proxying to agent at: {AGENT_URL}")
    ThreadingHTTPServer(("127.0.0.1", DEMO_PORT), DemoHandler).serve_forever()
