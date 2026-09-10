#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import sys
import types

from mcp_protocol_plugin.handlers.config import Config
from mcp_protocol_plugin.handlers.mcp_utility import _get_module


def test_get_module_prefers_extracted_package_over_stale_sys_modules(tmp_path):
    module_name = "demo_runtime_package"
    package_dir = tmp_path / module_name
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("VALUE = 'fresh'\n", encoding="utf-8")

    stale = types.ModuleType(module_name)
    stale.VALUE = "stale"
    sys.modules[module_name] = stale

    original_extract_path = Config.funct_extract_path
    original_zip_path = Config.funct_zip_path
    original_logger = Config.logger
    try:
        Config.funct_extract_path = str(tmp_path)
        Config.funct_zip_path = str(tmp_path)
        Config.logger = logging.getLogger("test_mcp_package_import")

        module = _get_module(module_name, module_name, source="s3")

        assert module.VALUE == "fresh"
        assert sys.modules[module_name] is module
        assert sys.modules[module_name].VALUE == "fresh"
    finally:
        sys.modules.pop(module_name, None)
        Config.funct_extract_path = original_extract_path
        Config.funct_zip_path = original_zip_path
        Config.logger = original_logger
