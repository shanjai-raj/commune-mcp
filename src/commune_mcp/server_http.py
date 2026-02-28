"""
Commune MCP — Streamable HTTP transport.

Deployed at https://mcp.commune.email for Smithery registry.
MCP endpoint: POST https://mcp.commune.email/?api_key=comm_...

Smithery appends the api_key as a query parameter automatically.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import anyio
import uvicorn
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

from commune_mcp.server import _api_key_ctx, mcp

# ── Well-known server card (Smithery discovery) ───────────────────────────────

_SERVER_CARD = {
    "name": "Commune Email & SMS",
    "description": (
        "Email and SMS infrastructure for AI agents. "
        "Create inboxes, send email, read threads, provision phone numbers, send SMS."
    ),
    "vendor": "Commune",
    "version": "0.1.2",
    "homepage": "https://commune.email",
    "license": "MIT",
    "capabilities": {
        "tools": True,
        "resources": False,
        "prompts": False,
    },
}


# ── Middleware ────────────────────────────────────────────────────────────────

class _ApiKeyMiddleware(BaseHTTPMiddleware):
    """Extract per-request Commune API key from query param or header."""

    EXEMPT = {"/health", "/.well-known/mcp/server-card.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT:
            return await call_next(request)

        api_key = (
            request.query_params.get("api_key")
            or request.headers.get("x-commune-api-key")
            or request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        )

        if not api_key:
            return JSONResponse(
                {
                    "error": "api_key_required",
                    "message": "Pass your Commune API key via ?api_key=comm_... or X-Commune-Api-Key header.",
                },
                status_code=401,
            )

        token = _api_key_ctx.set(api_key)
        try:
            return await call_next(request)
        finally:
            _api_key_ctx.reset(token)


# ── Route handlers ────────────────────────────────────────────────────────────

async def _health(request: Request):
    return PlainTextResponse("ok")


async def _server_card(request: Request):
    return JSONResponse(_SERVER_CARD)


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> Starlette:
    """
    Build the ASGI app.

    Mounts the MCP session manager at / so Smithery can POST to /?api_key=...
    Uses FastMCP's internal session manager directly so the lifespan (task group)
    is owned by this app — avoids the 'Task group is not initialized' error.
    """
    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        event_store=None,
        json_response=False,
        stateless=False,
    )

    async def _handle_mcp(scope, receive, send):
        await session_manager.handle_request(scope, receive, send)

    @asynccontextmanager
    async def _lifespan(app: Starlette) -> AsyncIterator[None]:
        async with anyio.create_task_group() as tg:
            session_manager.task_group = tg
            yield

    app = Starlette(
        lifespan=_lifespan,
        routes=[
            Route("/health", _health),
            Route("/.well-known/mcp/server-card.json", _server_card),
            Mount("/", app=_handle_mcp),  # MCP at / — Smithery POSTs to /?api_key=...
        ],
    )
    app.add_middleware(_ApiKeyMiddleware)
    return app


def main():
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(
        create_app(),
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
