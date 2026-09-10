# -*- coding: utf-8 -*-
"""Repository abstraction boundary for dual-backend persistence.

Re-exports the shared repository API from ``silvaengine_daemon.repositories``
and registers plugin-specific entity specs for lazy initialization.
"""
from __future__ import print_function

__author__ = "bibow"

from silvaengine_daemon.repositories import (
    DependencyExistsError,
    EntityNotFoundError,
    EntityRepository,
    RepositoryError,
    get_loaders,
    get_repo,
    register_repo,
    clear_registry,
    set_backend_resolver,
    register_entities,
)

__all__ = [
    "EntityRepository",
    "RepositoryError",
    "EntityNotFoundError",
    "DependencyExistsError",
    "get_repo",
    "get_loaders",
    "register_repo",
    "clear_registry",
    "set_backend_resolver",
    "register_entities",
]
