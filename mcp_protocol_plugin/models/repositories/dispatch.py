# -*- coding: utf-8 -*-
"""Backend dispatch boundary for repository and loader selection.

This module wires the plugin's ``Config.DB_BACKEND`` into the shared
``silvaengine_daemon.repositories.dispatch`` backend resolver and registers
plugin-specific entity specs for lazy initialization.

``get_repo(entity_type)`` is re-exported from ``silvaengine_daemon`` — the
backend is resolved via the resolver set here.
"""
from __future__ import print_function

__author__ = "bibow"

import logging

from silvaengine_daemon.repositories import (
    get_repo,
    register_repo,
    get_loaders,
    clear_registry,
    set_backend_resolver,
    register_entities,
)

logger = logging.getLogger(__name__)


def _register_plugin_entities():
    """Register plugin-specific entity specs for lazy initialization.

    Called once at import time (below) to declare the 4 DynamoDB and 4
    PostgreSQL repository classes to the shared dispatch layer.
    """
    register_entities("dynamodb", [
        ("mcp_protocol_plugin.models.repositories.dynamodb.mcp_function_repo",
         "MCPFunctionRepository"),
        ("mcp_protocol_plugin.models.repositories.dynamodb.mcp_module_repo",
         "MCPModuleRepository"),
        ("mcp_protocol_plugin.models.repositories.dynamodb.mcp_setting_repo",
         "MCPSettingRepository"),
        ("mcp_protocol_plugin.models.repositories.dynamodb.mcp_function_call_repo",
         "MCPFunctionCallRepository"),
    ])
    register_entities("postgresql", [
        ("mcp_protocol_plugin.models.repositories.postgresql.mcp_function_repo",
         "MCPFunctionPGRepository"),
        ("mcp_protocol_plugin.models.repositories.postgresql.mcp_module_repo",
         "MCPModulePGRepository"),
        ("mcp_protocol_plugin.models.repositories.postgresql.mcp_setting_repo",
         "MCPSettingPGRepository"),
        ("mcp_protocol_plugin.models.repositories.postgresql.mcp_function_call_repo",
         "MCPFunctionCallPGRepository"),
    ])


def _set_backend():
    """Set the backend resolver to use the plugin's Config.DB_BACKEND."""
    from ..handlers.config import Config
    set_backend_resolver(lambda: Config.DB_BACKEND)


# Register entities at import time so they are available before first get_repo() call.
_register_plugin_entities()


__all__ = [
    "get_repo",
    "register_repo",
    "get_loaders",
    "clear_registry",
    "set_backend_resolver",
    "register_entities",
]
