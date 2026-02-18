# -*- coding: utf-8 -*-
"""第二十四批 - excel_template_service 单元测试"""

import pytest

pytest.importorskip("app.services.excel_template_service")

from app.services.excel_template_service import (
    TEMPLATE_CONFIGS,
    get_template_config,
)


class TestGetTemplateConfig:
    def test_get_project_config(self):
        cfg = get_template_config("PROJECT")
        assert cfg is not None
        assert "template_data" in cfg
        assert "sheet_name" in cfg

    def test_get_task_config(self):
        cfg = get_template_config("TASK")
        assert cfg is not None
        assert cfg["filename_prefix"] == "任务导入模板"

    def test_get_user_config(self):
        cfg = get_template_config("USER")
        assert cfg is not None
        assert "column_widths" in cfg

    def test_case_insensitive(self):
        assert get_template_config("project") == get_template_config("PROJECT")

    def test_unknown_type_returns_none(self):
        assert get_template_config("NONEXISTENT") is None

    def test_all_known_types(self):
        for key in TEMPLATE_CONFIGS:
            cfg = get_template_config(key)
            assert cfg is not None, f"Config for {key} should not be None"


class TestTemplatConfigStructure:
    def test_required_keys_exist(self):
        for key, cfg in TEMPLATE_CONFIGS.items():
            for req in ("template_data", "sheet_name", "column_widths", "instructions", "filename_prefix"):
                assert req in cfg, f"Config {key} missing key: {req}"

    def test_template_data_not_empty(self):
        for key, cfg in TEMPLATE_CONFIGS.items():
            assert len(cfg["template_data"]) > 0, f"{key} template_data is empty"

    def test_bom_config_has_required_columns(self):
        cfg = get_template_config("BOM")
        td = cfg["template_data"]
        required = ["BOM编码*", "项目编码*", "物料编码*", "用量*"]
        for col in required:
            assert col in td
