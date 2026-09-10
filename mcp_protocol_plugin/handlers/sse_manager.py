# -*- coding: utf-8 -*-
"""SSE manager — re-exported from silvaengine_daemon.sse.

The gateway route manifest references:
  sse_manager: mcp_protocol_plugin.handlers.sse_manager:sse_manager
  on_shutdown: mcp_protocol_plugin.handlers.sse_manager:cleanup_sse

These are re-exported here so the gateway's importlib resolution works.
"""
from __future__ import print_function

__author__ = "bibow"

from silvaengine_daemon.sse import SSEManager, sse_manager, cleanup_sse

__all__ = ["SSEManager", "sse_manager", "cleanup_sse"]
