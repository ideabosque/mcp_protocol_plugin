# -*- coding: utf-8 -*-
"""PostgreSQL SQLAlchemy base metadata — re-exported from silvaengine_daemon.

This module re-exports ``Base`` and ``normalize_row`` from
``silvaengine_daemon.repositories.postgresql.base`` so that plugin model
modules importing ``from .base import Base`` continue to work.

Only imported when ``DB_BACKEND=postgresql``.
"""
from __future__ import print_function

__author__ = "bibow"

from silvaengine_daemon.repositories.postgresql.base import Base, normalize_row

__all__ = ["Base", "normalize_row"]
