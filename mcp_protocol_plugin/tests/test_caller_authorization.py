"""Per-call caller credential for hosted MCP modules (forward auth)."""

import asyncio
import threading

from mcp_protocol_plugin.handlers.caller_context import (
    CALLER_AUTHORIZATION,
    bearer_from_headers,
    with_caller_authorization,
)


def test_bearer_from_headers():
    assert bearer_from_headers({"authorization": "Bearer abc"}) == "abc"
    assert bearer_from_headers({"Authorization": "bearer  xyz "}) == "xyz"
    assert bearer_from_headers({"authorization": "Basic abc"}) is None
    assert bearer_from_headers({"authorization": "Bearer "}) is None
    assert bearer_from_headers(None) is None


def test_token_visible_inside_call_and_reset_after():
    async def inner():
        return CALLER_AUTHORIZATION.get()

    assert asyncio.run(with_caller_authorization("tok", inner())) == "tok"
    assert CALLER_AUTHORIZATION.get() is None


def test_token_survives_loop_on_fresh_thread():
    """Invoker.sync_call_async_compatible runs the loop on a new thread when a
    loop is already running; the wrapper sets the token inside the coroutine."""
    seen = {}

    async def inner():
        seen["token"] = CALLER_AUTHORIZATION.get()

    def run():
        asyncio.run(with_caller_authorization("tok", inner()))

    worker = threading.Thread(target=run)
    worker.start()
    worker.join()
    assert seen["token"] == "tok"


def test_concurrent_calls_do_not_leak_tokens():
    results = {}

    async def inner(name):
        await asyncio.sleep(0.01)
        results[name] = CALLER_AUTHORIZATION.get()

    async def both():
        await asyncio.gather(
            with_caller_authorization("tok-a", inner("a")),
            with_caller_authorization("tok-b", inner("b")),
        )

    asyncio.run(both())
    assert results == {"a": "tok-a", "b": "tok-b"}
