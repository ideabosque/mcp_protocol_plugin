#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the runtime (tool-dispatch-triggered) Git module auto-install/
auto-refresh path — ``ensure_git_module_current`` and its wiring into
``mcp_utility._import_git_module`` via ``Config.git_refresh_policy``.

Before this, a Git-installed module whose ``install_target`` went missing
(fresh container, GIT_INSTALL_PATH cleared, ...) could only be recovered by
an admin calling ``refreshMcpGitPackage``/``installMcpPackageFromGit`` by
hand — the runtime tool-dispatch path had no ``ResolveInfo`` to drive that
same install/refresh logic with, so it just raised ImportError. Likewise,
nothing ever detected that the upstream repo had a new commit unless an
admin explicitly asked via ``checkMcpGitPackageVersion``.

These tests mock the network/DB-touching pieces (``_read_existing_module_setting``,
``check_mcp_git_package_version``, ``refresh_mcp_git_package``) so they run
without a real git remote or database.
"""
from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock

import pytest

from mcp_protocol_plugin.handlers import mcp_git
from mcp_protocol_plugin.handlers.config import Config


@pytest.fixture
def logger():
    return logging.getLogger("test_mcp_git_runtime_refresh")


# ---------------------------------------------------------------------------
# ensure_git_module_current
# ---------------------------------------------------------------------------


def test_ensure_git_module_current_returns_none_without_git_metadata(monkeypatch, logger):
    """A module with no git_url at all (never installed from Git) is left
    alone entirely — there's nothing to install/refresh from."""
    monkeypatch.setattr(mcp_git, "_read_existing_module_setting", lambda *a, **k: {})

    result = mcp_git.ensure_git_module_current("some_module", "gpt#nestaging", logger)

    assert result is None


def test_ensure_git_module_current_skips_refresh_when_up_to_date(monkeypatch, logger, tmp_path):
    """A *present* install_target with needs_refresh=False (within TTL, or
    checked and unchanged) must not trigger a reinstall — just return the
    current setting as-is. install_target must actually exist on disk here,
    or this would exercise the target-missing branch instead (see below)."""
    tmp_path.mkdir(exist_ok=True)
    local_state = {"git_url": "git@github.com:org/repo.git", "install_target": str(tmp_path)}
    monkeypatch.setattr(
        mcp_git, "_read_existing_module_setting", lambda *a, **k: local_state
    )
    check_mock = MagicMock(return_value={"needs_refresh": False})
    monkeypatch.setattr(mcp_git, "check_mcp_git_package_version", check_mock)
    refresh_mock = MagicMock()
    monkeypatch.setattr(mcp_git, "refresh_mcp_git_package", refresh_mock)

    result = mcp_git.ensure_git_module_current("some_module", "gpt#nestaging", logger)

    check_mock.assert_called_once()
    refresh_mock.assert_not_called()
    assert result == local_state


def test_ensure_git_module_current_refreshes_when_repo_changed(monkeypatch, logger, tmp_path):
    """A present install_target with needs_refresh=True (remote has a new
    commit) must call refresh_mcp_git_package, then return the freshly
    re-read setting (which may have a new install_target)."""
    tmp_path.mkdir(exist_ok=True)
    old_state = {"git_url": "git@github.com:org/repo.git", "install_target": str(tmp_path)}
    new_state = {"git_url": "git@github.com:org/repo.git", "install_target": "/x/new-commit"}
    read_calls = {"n": 0}

    def fake_read(*a, **k):
        read_calls["n"] += 1
        return old_state if read_calls["n"] == 1 else new_state

    monkeypatch.setattr(mcp_git, "_read_existing_module_setting", fake_read)
    monkeypatch.setattr(
        mcp_git,
        "check_mcp_git_package_version",
        lambda info, **kw: {"needs_refresh": True},
    )
    refresh_mock = MagicMock()
    monkeypatch.setattr(mcp_git, "refresh_mcp_git_package", refresh_mock)

    result = mcp_git.ensure_git_module_current("some_module", "gpt#nestaging", logger)

    refresh_mock.assert_called_once()
    call_kwargs = refresh_mock.call_args.kwargs
    assert call_kwargs["module_name"] == "some_module"
    assert call_kwargs["force_refresh"] is False
    assert result == new_state


def test_ensure_git_module_current_swallows_check_failure(monkeypatch, logger, tmp_path):
    """A network blip during the version check (install_target present, so
    the TTL-gated remote-check path runs) must not raise — the caller falls
    back to whatever is already installed."""
    tmp_path.mkdir(exist_ok=True)
    local_state = {"git_url": "git@github.com:org/repo.git", "install_target": str(tmp_path)}
    monkeypatch.setattr(
        mcp_git, "_read_existing_module_setting", lambda *a, **k: local_state
    )

    def boom(info, **kw):
        raise RuntimeError("remote unreachable")

    monkeypatch.setattr(mcp_git, "check_mcp_git_package_version", boom)
    refresh_mock = MagicMock()
    monkeypatch.setattr(mcp_git, "refresh_mcp_git_package", refresh_mock)

    result = mcp_git.ensure_git_module_current("some_module", "gpt#nestaging", logger)

    refresh_mock.assert_not_called()
    assert result == local_state


def test_ensure_git_module_current_missing_target_bypasses_version_check(
    monkeypatch, logger, tmp_path
):
    """Regression test for a live bug: when install_target is missing on
    disk, ensure_git_module_current must go straight to
    refresh_mcp_git_package WITHOUT consulting check_mcp_git_package_version
    first. check_mcp_git_package_version only compares remote commits and is
    TTL-gated (git_refresh_ttl) — it has no notion of "the local files are
    just gone", so if the module was checked/refreshed recently (TTL still
    fresh) it reports needs_refresh=False regardless of whether
    install_target exists, which would silently skip recovery for exactly
    the on_runtime_miss scenario this function exists to handle."""
    missing_target = str(tmp_path / "does-not-exist")
    local_state = {"git_url": "git@github.com:org/repo.git", "install_target": missing_target}
    monkeypatch.setattr(
        mcp_git, "_read_existing_module_setting", lambda *a, **k: local_state
    )
    check_mock = MagicMock(return_value={"needs_refresh": False})
    monkeypatch.setattr(mcp_git, "check_mcp_git_package_version", check_mock)
    refresh_mock = MagicMock()
    monkeypatch.setattr(mcp_git, "refresh_mcp_git_package", refresh_mock)

    mcp_git.ensure_git_module_current("some_module", "gpt#nestaging", logger)

    check_mock.assert_not_called()
    refresh_mock.assert_called_once()
    call_kwargs = refresh_mock.call_args.kwargs
    assert call_kwargs["module_name"] == "some_module"


def test_ensure_git_module_current_swallows_refresh_failure(monkeypatch, logger):
    """A failed reinstall (bad credentials, pip failure, ...) must not raise —
    the caller falls back to whatever is already installed, if anything."""
    local_state = {"git_url": "git@github.com:org/repo.git", "install_target": "/x/repo"}
    monkeypatch.setattr(
        mcp_git, "_read_existing_module_setting", lambda *a, **k: local_state
    )
    monkeypatch.setattr(
        mcp_git,
        "check_mcp_git_package_version",
        lambda info, **kw: {"needs_refresh": True},
    )

    def boom(info, **kw):
        raise RuntimeError("pip install failed")

    monkeypatch.setattr(mcp_git, "refresh_mcp_git_package", boom)

    result = mcp_git.ensure_git_module_current("some_module", "gpt#nestaging", logger)

    assert result == local_state


# ---------------------------------------------------------------------------
# _import_git_module policy wiring
# ---------------------------------------------------------------------------


def _make_install_target(tmp_path, module_name: str) -> str:
    target = tmp_path / "install"
    package_dir = target / module_name
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("VALUE = 'ok'\n", encoding="utf-8")
    return str(target)


def test_import_git_module_manual_policy_never_calls_ensure(monkeypatch, tmp_path):
    """git_refresh_policy=manual (the default) must never trigger the
    runtime path — only the explicit GraphQL mutations do."""
    from mcp_protocol_plugin.handlers import mcp_utility

    module_name = "manual_policy_pkg"
    install_target = _make_install_target(tmp_path, module_name)

    original_policy = Config.git_refresh_policy
    ensure_mock = MagicMock()
    monkeypatch.setattr(mcp_git, "ensure_git_module_current", ensure_mock)
    try:
        Config.git_refresh_policy = "manual"
        module = mcp_utility._import_git_module(
            module_name,
            {"install_target": install_target},
            partition_key="gpt#nestaging",
        )
        assert module.VALUE == "ok"
        ensure_mock.assert_not_called()
    finally:
        Config.git_refresh_policy = original_policy
        mcp_utility.sys.modules.pop(module_name, None)


def test_import_git_module_on_runtime_miss_skips_ensure_when_target_present(
    monkeypatch, tmp_path
):
    """on_runtime_miss must not do a remote check when install_target
    already exists and is valid — only recovers a *missing* target."""
    from mcp_protocol_plugin.handlers import mcp_utility

    module_name = "runtime_miss_present_pkg"
    install_target = _make_install_target(tmp_path, module_name)

    original_policy = Config.git_refresh_policy
    ensure_mock = MagicMock()
    monkeypatch.setattr(mcp_git, "ensure_git_module_current", ensure_mock)
    try:
        Config.git_refresh_policy = "on_runtime_miss"
        module = mcp_utility._import_git_module(
            module_name,
            {"install_target": install_target},
            partition_key="gpt#nestaging",
        )
        assert module.VALUE == "ok"
        ensure_mock.assert_not_called()
    finally:
        Config.git_refresh_policy = original_policy
        mcp_utility.sys.modules.pop(module_name, None)


def test_import_git_module_on_runtime_miss_reinstalls_when_target_missing(
    monkeypatch, tmp_path
):
    """on_runtime_miss: a missing install_target triggers ensure_git_module_current,
    and the freshly-installed target it returns is what actually gets imported."""
    from mcp_protocol_plugin.handlers import mcp_utility

    module_name = "runtime_miss_missing_pkg"
    fresh_target = _make_install_target(tmp_path, module_name)

    original_policy = Config.git_refresh_policy
    ensure_mock = MagicMock(return_value={"install_target": fresh_target})
    monkeypatch.setattr(mcp_git, "ensure_git_module_current", ensure_mock)
    try:
        Config.git_refresh_policy = "on_runtime_miss"
        module = mcp_utility._import_git_module(
            module_name,
            {"install_target": os.path.join(str(tmp_path), "does-not-exist")},
            partition_key="gpt#nestaging",
        )
        assert module.VALUE == "ok"
        ensure_mock.assert_called_once_with(
            module_name, "gpt#nestaging", Config.logger
        )
    finally:
        Config.git_refresh_policy = original_policy
        mcp_utility.sys.modules.pop(module_name, None)


def test_import_git_module_on_runtime_check_always_calls_ensure(monkeypatch, tmp_path):
    """on_runtime_check must call ensure_git_module_current even when the
    existing install_target is already valid — the TTL gating lives inside
    ensure_git_module_current/check_mcp_git_package_version, not here."""
    from mcp_protocol_plugin.handlers import mcp_utility

    module_name = "runtime_check_pkg"
    install_target = _make_install_target(tmp_path, module_name)

    original_policy = Config.git_refresh_policy
    ensure_mock = MagicMock(return_value={"install_target": install_target})
    monkeypatch.setattr(mcp_git, "ensure_git_module_current", ensure_mock)
    try:
        Config.git_refresh_policy = "on_runtime_check"
        module = mcp_utility._import_git_module(
            module_name,
            {"install_target": install_target},
            partition_key="gpt#nestaging",
        )
        assert module.VALUE == "ok"
        ensure_mock.assert_called_once()
    finally:
        Config.git_refresh_policy = original_policy
        mcp_utility.sys.modules.pop(module_name, None)


def test_import_git_module_without_partition_key_skips_runtime_check(monkeypatch, tmp_path):
    """No partition_key (a caller that hasn't been threaded through yet)
    must not attempt the runtime path at all, and fall back to the plain
    existing-install-target behavior."""
    from mcp_protocol_plugin.handlers import mcp_utility

    module_name = "no_partition_key_pkg"
    install_target = _make_install_target(tmp_path, module_name)

    original_policy = Config.git_refresh_policy
    ensure_mock = MagicMock()
    monkeypatch.setattr(mcp_git, "ensure_git_module_current", ensure_mock)
    try:
        Config.git_refresh_policy = "on_runtime_check"
        module = mcp_utility._import_git_module(
            module_name,
            {"install_target": install_target},
            partition_key=None,
        )
        assert module.VALUE == "ok"
        ensure_mock.assert_not_called()
    finally:
        Config.git_refresh_policy = original_policy
        mcp_utility.sys.modules.pop(module_name, None)


def test_import_git_module_raises_clear_error_when_still_missing(monkeypatch, tmp_path):
    """If ensure_git_module_current can't recover a usable install_target
    (e.g. remote unreachable and nothing was ever installed), the import
    still fails, but with a message pointing at how to fix it."""
    from mcp_protocol_plugin.handlers import mcp_utility

    module_name = "unrecoverable_pkg"
    original_policy = Config.git_refresh_policy
    monkeypatch.setattr(mcp_git, "ensure_git_module_current", lambda *a, **k: None)
    try:
        Config.git_refresh_policy = "on_runtime_miss"
        with pytest.raises(ImportError, match="install target missing"):
            mcp_utility._import_git_module(
                module_name,
                {"install_target": os.path.join(str(tmp_path), "does-not-exist")},
                partition_key="gpt#nestaging",
            )
    finally:
        Config.git_refresh_policy = original_policy
