"""
Commune MCP — Streamable HTTP transport.

Deployed at https://mcp.commune.email for Smithery registry.
Pass your API key via query param or header:

  ?api_key=comm_...
  X-Commune-Api-Key: comm_...
  Authorization: Bearer comm_...
"""

from __future__ import annotations

import os

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from starlette.responses import PlainTextResponse
from starlette.routing import Route

from commune_mcp.server import _api_key_ctx, mcp


class _ApiKeyMiddleware(BaseHTTPMiddleware):
    """Extract per-request Commune API key and inject into ContextVar."""

    EXEMPT = {"/health", "/"}

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
                    "message": (
                        "Pass your Commune API key via ?api_key=comm_... "
                        "or X-Commune-Api-Key header. Get a key at commune.email"
                    ),
                },
                status_code=401,
            )

        token = _api_key_ctx.set(api_key)
        try:
            return await call_next(request)
        finally:
            _api_key_ctx.reset(token)


async def _health(request: Request):
    return PlainTextResponse("ok")


def create_app():
    """Build the Starlette ASGI app with API key middleware."""
    from starlette.applications import Starlette
    from starlette.routing import Mount

    mcp_app = mcp.streamable_http_app()
    mcp_app.add_middleware(_ApiKeyMiddleware)

    # Wrap with a top-level Starlette app so /health bypasses MCP routing
    return Starlette(
        routes=[
            Route("/health", _health),
            Mount("/", app=mcp_app),
        ]
    )


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
