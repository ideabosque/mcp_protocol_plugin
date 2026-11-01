"""Re-installing with the module's existing setting as variables must not
pin the setting to the previous install target (which is then cleaned up)."""

import inspect

from mcp_protocol_plugin.handlers import mcp_git


def test_strip_git_metadata_keeps_business_settings_only():
    existing = {
        "graphql_modules": {"rfq_engine": {"auth": "forward"}},
        "installment_scheduled_day": "15",
        "install_target": "/tmp/packages/pkg/old",
        "resolved_commit": "a" * 40,
        "git_ref": "main",
        "installed_at": "2026-10-24T00:00:00Z",
    }
    assert mcp_git._strip_git_metadata(existing) == {
        "graphql_modules": {"rfq_engine": {"auth": "forward"}},
        "installment_scheduled_day": "15",
    }


def test_strip_git_metadata_passes_through_non_dicts():
    assert mcp_git._strip_git_metadata(None) is None
    assert mcp_git._strip_git_metadata({}) == {}


def test_install_applies_the_filter():
    source = inspect.getsource(mcp_git.install_mcp_package_from_git)
    assert "_strip_git_metadata(variables)" in source
