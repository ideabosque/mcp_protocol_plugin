# -*- coding: utf-8 -*-
"""Repository base classes — re-exported from silvaengine_daemon.

Plugin repo files import ``from ..base import EntityRepository``; this module
re-exports the shared classes so those imports resolve without duplicating
the abstract base.
"""
from __future__ import print_function

__author__ = "bibow"

from silvaengine_daemon.repositories.base import (
    EntityRepository,
    RepositoryError,
    EntityNotFoundError,
    DependencyExistsError,
)

__all__ = [
    "EntityRepository",
    "RepositoryError",
    "EntityNotFoundError",
    "DependencyExistsError",
]
