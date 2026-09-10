#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

__all__ = [
    "AuthenticationError",
    "InvalidRequestError",
    "MCPProtocolPlugin",
    "RateLimitExceeded",
    "deploy",
]
from silvaengine_daemon.errors import (
    AuthenticationError,
    InvalidRequestError,
    RateLimitExceeded,
)


def __getattr__(name):
    """
    Lazily import runtime entrypoints so metadata helpers remain available
    without reintroducing the old CLI main export.
    """
    if name in {"MCPProtocolPlugin", "deploy"}:
        from .main import MCPProtocolPlugin, deploy

        exports = {
            "MCPProtocolPlugin": MCPProtocolPlugin,
            "deploy": deploy,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
