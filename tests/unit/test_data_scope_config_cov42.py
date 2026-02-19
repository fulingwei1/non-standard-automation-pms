# -*- coding: utf-8 -*-
"""第四十二批：data_scope/config.py 单元测试"""
import pytest

pytest.importorskip("app.services.data_scope.config")

from app.services.data_scope.config import DataScopeConfig, DATA_SCOPE_CONFIGS


# ------------------------------------------------------------------ tests ---

def test_data_scope_config_defaults():
    cfg = DataScopeConfig()
    assert cfg.owner_field == "created_by"
    assert cfg.project_field == "project_id"
    assert cfg.dept_through_project is True
    assert cfg.custom_filter is None
    assert cfg.additional_owner_fields is None


def test_data_scope_config_custom():
    cfg = DataScopeConfig(
        owner_field="requester_id",
        additional_owner_fields=["created_by"],
        dept_field="dept_id",
        project_field="proj_id",
        dept_through_project=False,
    )
    assert cfg.owner_field == "requester_id"
    assert "created_by" in cfg.additional_owner_fields
    assert cfg.dept_field == "dept_id"
    assert cfg.dept_through_project is False


def test_predefined_configs_exist():
    assert "purchase_order" in DATA_SCOPE_CONFIGS
    assert "task" in DATA_SCOPE_CONFIGS
    assert "document" in DATA_SCOPE_CONFIGS


def test_purchase_order_config():
    cfg = DATA_SCOPE_CONFIGS["purchase_order"]
    assert cfg.owner_field == "requester_id"
    assert "created_by" in cfg.additional_owner_fields


def test_task_config():
    cfg = DATA_SCOPE_CONFIGS["task"]
    assert cfg.owner_field == "assignee_id"
    assert "created_by" in cfg.additional_owner_fields


def test_all_predefined_have_project_field():
    for name, cfg in DATA_SCOPE_CONFIGS.items():
        assert cfg.project_field is not None, f"{name} missing project_field"


def test_acceptance_order_has_inspector_as_additional_owner():
    cfg = DATA_SCOPE_CONFIGS["acceptance_order"]
    assert "inspector_id" in cfg.additional_owner_fields
