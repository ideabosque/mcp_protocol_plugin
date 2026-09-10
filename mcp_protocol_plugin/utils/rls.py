# -*- coding: utf-8 -*-
"""Row-Level Security (RLS) helpers for the PostgreSQL backend.

Re-exports ``set_rls_context`` and ``create_rls_policies`` from
``silvaengine_daemon.rls``, binding the MCP protocol plugin's table names.
"""
from __future__ import print_function

__author__ = "bibow"

from silvaengine_daemon.rls import set_rls_context, create_rls_policies as _create_policies

_RLS_TABLES = [
    "mcp_functions",
    "mcp_modules",
    "mcp_settings",
    "mcp_function_calls",
]


def create_rls_policies(engine):
    """Enable RLS and create tenant-isolation policies on all MCP tables."""
    return _create_policies(engine, _RLS_TABLES)


__all__ = ["set_rls_context", "create_rls_policies", "_RLS_TABLES"]
