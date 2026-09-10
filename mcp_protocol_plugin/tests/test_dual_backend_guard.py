# -*- coding: utf-8 -*-
"""Static adoption guard and backend-agnostic dispatch tests.

Verifies that the GraphQL layer, mutation layer, and handlers/mcp_handlers.py
route all metadata persistence through get_repo() — no direct models.dynamodb
imports or free-function insert_update_*/delete_* calls remain.

Also verifies that the dispatch boundary registers all 4 entities under the
DynamoDB backend.
"""
from __future__ import print_function

__author__ = "bibow"

import ast
import os
import unittest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Static adoption guard — no direct models.dynamodb imports above the boundary
# ---------------------------------------------------------------------------

_FILES_TO_GUARD = [
    "queries/mcp_function.py",
    "queries/mcp_module.py",
    "queries/mcp_setting.py",
    "queries/mcp_function_call.py",
    "mutations/mcp_function.py",
    "mutations/mcp_module.py",
    "mutations/mcp_setting.py",
    "mutations/mcp_function_call.py",
    "handlers/mcp_handlers.py",
]

_FORBIDDEN_IMPORT_PATTERNS = [
    "models.dynamodb",
    "models.mcp_function",
    "models.mcp_module",
    "models.mcp_setting",
    "models.mcp_function_call",
]

_FORBIDDEN_CALL_PATTERNS = [
    "insert_update_mcp_function(",
    "insert_update_mcp_module(",
    "insert_update_mcp_setting(",
    "insert_update_mcp_function_call(",
    "delete_mcp_function(",
    "delete_mcp_module(",
    "delete_mcp_setting(",
    "delete_mcp_function_call(",
]


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StaticAdoptionGuardTest(unittest.TestCase):
    """Ensure no GraphQL/handler file imports models.dynamodb directly."""

    def test_no_forbidden_imports(self) -> None:
        root = _project_root()
        violations = []
        for rel_path in _FILES_TO_GUARD:
            full_path = os.path.join(root, rel_path)
            if not os.path.isfile(full_path):
                continue
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
            for pattern in _FORBIDDEN_IMPORT_PATTERNS:
                if pattern in source:
                    violations.append(f"{rel_path}: contains '{pattern}'")
        self.assertEqual(
            violations,
            [],
            f"Forbidden direct model imports found:\n" + "\n".join(violations),
        )

    def test_no_forbidden_free_function_calls(self) -> None:
        """No direct insert_update_*/delete_* free-function calls."""
        root = _project_root()
        violations = []
        for rel_path in _FILES_TO_GUARD:
            full_path = os.path.join(root, rel_path)
            if not os.path.isfile(full_path):
                continue
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
            for pattern in _FORBIDDEN_CALL_PATTERNS:
                # Exclude matches that are part of get_repo(...).insert_update / .delete
                # We look for the bare function call pattern (not preceded by a dot)
                lines = source.split("\n")
                for line in lines:
                    stripped = line.strip()
                    if pattern in stripped and not stripped.startswith("#"):
                        # Check it's not a method call (preceded by .)
                        idx = stripped.find(pattern)
                        if idx > 0 and stripped[idx - 1] == ".":
                            continue
                        violations.append(
                            f"{rel_path}: calls '{pattern}' directly"
                        )
        self.assertEqual(
            violations,
            [],
            f"Forbidden free-function calls found:\n" + "\n".join(violations),
        )


# ---------------------------------------------------------------------------
# Backend-agnostic dispatch test (DynamoDB arm)
# ---------------------------------------------------------------------------

class DynamoDBDispatchTest(unittest.TestCase):
    """Verify dispatch registers all 4 entities under DynamoDB backend."""

    @classmethod
    def setUpClass(cls) -> None:
        # Set Config.DB_BACKEND to dynamodb before importing dispatch
        from mcp_protocol_plugin.handlers.config import Config

        Config.DB_BACKEND = "dynamodb"

    def setUp(self) -> None:
        from mcp_protocol_plugin.models.repositories.dispatch import clear_registry

        clear_registry()

    def test_dynamodb_repos_registered(self) -> None:
        from mcp_protocol_plugin.models.repositories.dispatch import get_repo

        expected_entities = [
            "mcp_function",
            "mcp_module",
            "mcp_setting",
            "mcp_function_call",
        ]
        for entity_type in expected_entities:
            repo = get_repo(entity_type)
            self.assertEqual(repo.entity_type, entity_type)

    def test_get_loaders_stub_returns_none(self) -> None:
        from mcp_protocol_plugin.models.repositories.dispatch import get_loaders

        result = get_loaders({})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()