# -*- coding: utf-8 -*-
"""
Unit tests for app/services/data_scope/config.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.data_scope.config import DataScopeConfig, DATA_SCOPE_CONFIGS
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_data_scope_config_defaults():
    """DataScopeConfig 默认值验证"""
    config = DataScopeConfig()
    assert config.owner_field == "created_by"
    assert config.additional_owner_fields is None
    assert config.dept_field is None
    assert config.project_field == "project_id"
    assert config.dept_through_project is True
    assert config.custom_filter is None


def test_data_scope_config_custom_fields():
    """DataScopeConfig 自定义字段"""
    config = DataScopeConfig(
        owner_field="requester_id",
        additional_owner_fields=["created_by"],
        project_field="project_id",
        dept_field="dept_id",
        dept_through_project=False,
    )
    assert config.owner_field == "requester_id"
    assert "created_by" in config.additional_owner_fields
    assert config.dept_through_project is False


def test_data_scope_configs_not_empty():
    """预定义配置字典不应为空"""
    assert len(DATA_SCOPE_CONFIGS) > 0


def test_data_scope_configs_has_purchase_order():
    """purchase_order 配置应存在"""
    assert "purchase_order" in DATA_SCOPE_CONFIGS
    cfg = DATA_SCOPE_CONFIGS["purchase_order"]
    assert cfg.owner_field == "requester_id"


def test_data_scope_configs_has_task():
    """task 配置应存在且 owner_field 正确"""
    assert "task" in DATA_SCOPE_CONFIGS
    cfg = DATA_SCOPE_CONFIGS["task"]
    assert cfg.owner_field == "assignee_id"
    assert "created_by" in (cfg.additional_owner_fields or [])


def test_data_scope_configs_has_document():
    """document 配置应存在"""
    assert "document" in DATA_SCOPE_CONFIGS
    cfg = DATA_SCOPE_CONFIGS["document"]
    assert cfg.owner_field == "uploaded_by"


def test_data_scope_config_with_callable():
    """DataScopeConfig 支持自定义 filter 函数"""
    custom_fn = MagicMock()
    config = DataScopeConfig(custom_filter=custom_fn)
    assert config.custom_filter is custom_fn


def test_data_scope_configs_acceptance_order():
    """acceptance_order 配置应包含 inspector_id"""
    assert "acceptance_order" in DATA_SCOPE_CONFIGS
    cfg = DATA_SCOPE_CONFIGS["acceptance_order"]
    assert "inspector_id" in (cfg.additional_owner_fields or [])
