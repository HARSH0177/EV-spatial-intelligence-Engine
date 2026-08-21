"""
middleware/auth.py  —  Improvement 4: Auth-ready API hardening.

What is implemented
--------------------
- `APIKeyMiddleware`: checks X-API-Key header on protected routes.
  Skips auth on PUBLIC_PATHS (/, /health, /ready, /docs, /openapi.json).
- When REQUIRE_AUTH=false (default) all routes are open — safe for
  portfolio/demo use.  Set REQUIRE_AUTH=true + API_KEYS=key1,key2
  in .env to harden without changing code.
- Role-ready: the middleware attaches a minimal `request.state.role`
  ("driver" | "operator" | "anonymous") based on the key prefix.
  Future: swap for Cloud IAP or Firebase Auth without touching agent code.

Cost note
---------
Full IAM / Firebase / Cloud IAP: free up to usage limits, may cost at scale.
This minimal API-key layer: free in code.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import cfg

logger = logging.getLogger(__name__)

# Key prefixes → roles  (extend as needed)
_ROLE_PREFIXES = {
    "drv-": "driver",
    "ops-": "operator",
    "adm-": "admin",
}


def _resolve_role(key: str) -> str:
    for prefix, role in _ROLE_PREFIXES.items():
        if key.startswith(prefix):
            return role
    return "driver"   # default role for unrecognised prefixes


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that validates X-API-Key on non-public routes.

    Attach to FastAPI with:
        app.add_middleware(APIKeyMiddleware)

    Configuration (via config.py → env):
        REQUIRE_AUTH=true      enable enforcement
        API_KEYS=drv-abc,ops-xyz   comma-separated valid keys
        CORS_ORIGINS=https://myapp.com
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Always allow public paths
        if any(path.startswith(p) for p in cfg.auth.public_paths):
            request.state.role = "anonymous"
            return await call_next(request)

        # Auth disabled — pass everything through
        if not cfg.auth.require_auth:
            request.state.role = "anonymous"
            return await call_next(request)

        # No keys configured → open (dev safety valve)
        if not cfg.auth.api_keys:
            logger.warning("REQUIRE_AUTH=true but no API_KEYS configured — allowing request")
            request.state.role = "anonymous"
            return await call_next(request)

        api_key = request.headers.get(cfg.auth.api_key_header, "").strip()
        if api_key not in cfg.auth.api_keys:
            logger.warning("Rejected request to %s — invalid API key", path)
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid or missing {cfg.auth.api_key_header} header."},
            )

        request.state.role = _resolve_role(api_key)
        return await call_next(request)


# ── Operator-only guard (decorator / dependency) ──────────────────────────────

from fastapi import HTTPException


def require_operator(request: Request) -> None:
    """
    FastAPI dependency for operator-only endpoints.
    Usage:
        @app.post("/company/plan-expansion", dependencies=[Depends(require_operator)])
    """
    role = getattr(request.state, "role", "anonymous")
    if cfg.auth.require_auth and role not in ("operator", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Operator role required for this endpoint.",
        )
