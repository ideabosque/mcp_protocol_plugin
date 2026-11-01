"""Per-call caller credential for hosted MCP modules.

The gateway passes each request's headers to the plugin. For a tool call the
caller's ``Authorization`` bearer is held in a context variable for the
duration of that call only, so a hosted module can forward the caller's own
short-lived token to downstream engines instead of storing credentials. Modules
opt in by declaring a ``caller_authorization`` attribute (same pattern as
``endpoint_id`` / ``part_id``). The value is never persisted or logged.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Awaitable, Mapping, Optional, TypeVar

T = TypeVar("T")

CALLER_AUTHORIZATION: ContextVar[Optional[str]] = ContextVar(
    "mcp_caller_authorization", default=None
)


def bearer_from_headers(headers: Optional[Mapping[str, Any]]) -> Optional[str]:
    """Return the bearer token from a request's ``Authorization`` header."""
    for key, value in (headers or {}).items():
        if str(key).lower() == "authorization" and isinstance(value, str):
            scheme, _, token = value.strip().partition(" ")
            if scheme.lower() == "bearer" and token.strip():
                return token.strip()
    return None


async def with_caller_authorization(token: Optional[str], coroutine: Awaitable[T]) -> T:
    """Await ``coroutine`` with ``token`` as the caller credential.

    Set inside the coroutine so it survives ``Invoker.sync_call_async_compatible``
    running the loop on a fresh thread.
    """
    reset = CALLER_AUTHORIZATION.set(token)
    try:
        return await coroutine
    finally:
        CALLER_AUTHORIZATION.reset(reset)
