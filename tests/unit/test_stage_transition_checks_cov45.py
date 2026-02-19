# -*- coding: utf-8 -*-
"""
第四十五批覆盖：stage_transition_checks.py
"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.stage_transition_checks")

from app.services.stage_transition_checks import (
    check_s3_to_s4_transition,
    check_s4_to_s5_transition,
    check_s7_to_s8_transition,
    check_s8_to_s9_transition,
    get_stage_status_mapping,
    execute_stage_transition,
)


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_project(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.contract_no = kwargs.get("contract_no", None)
    p.contract_date = kwargs.get("contract_date", None)
    p.contract_amount = kwargs.get("contract_amount", None)
    p.stage = kwargs.get("stage", "S3")
    p.status = kwargs.get("status", "ST07")
    return p


class TestCheckS3ToS4Transition:
    def test_missing_contract_info(self, mock_db):
        project = _make_project()
        ok, target, missing = check_s3_to_s4_transition(mock_db, project)
        assert ok is False
        assert target is None
        assert len(missing) > 0

    def test_contract_info_present_but_not_signed(self, mock_db):
        project = _make_project(
            contract_no="C001",
            contract_date="2024-01-01",
            contract_amount=100000,
        )
        contract = MagicMock(status="DRAFT")
        mock_db.query.return_value.filter.return_value.first.return_value = contract
        ok, target, missing = check_s3_to_s4_transition(mock_db, project)
        assert ok is False

    def test_signed_contract_advances(self, mock_db):
        project = _make_project(
            contract_no="C001",
            contract_date="2024-01-01",
            contract_amount=100000,
        )
        contract = MagicMock(status="SIGNED")
        mock_db.query.return_value.filter.return_value.first.return_value = contract
        ok, target, missing = check_s3_to_s4_transition(mock_db, project)
        assert ok is True
        assert target == "S4"


class TestCheckS4ToS5Transition:
    def test_no_released_bom(self, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        ok, target, missing = check_s4_to_s5_transition(mock_db, 1)
        assert ok is False
        assert len(missing) > 0

    def test_has_released_bom(self, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        ok, target, missing = check_s4_to_s5_transition(mock_db, 1)
        assert ok is True
        assert target == "S5"


class TestCheckS7ToS8Transition:
    def test_no_fat_passed(self, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        ok, target, missing = check_s7_to_s8_transition(mock_db, 1)
        assert ok is False
        assert "FAT" in missing[0]

    def test_fat_passed(self, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        ok, target, missing = check_s7_to_s8_transition(mock_db, 1)
        assert ok is True
        assert target == "S8"


class TestGetStageStatusMapping:
    def test_contains_expected_stages(self):
        mapping = get_stage_status_mapping()
        assert "S4" in mapping
        assert "S9" in mapping
        assert isinstance(mapping["S4"], str)


class TestExecuteStageTransition:
    def test_gate_failed_returns_false(self, mock_db):
        project = _make_project()
        mock_check_gate = MagicMock(return_value=(False, ["缺少合同"]))
        with patch.dict("sys.modules", {
            "app.api.v1.endpoints.projects.utils": MagicMock(check_gate=mock_check_gate)
        }):
            ok, result = execute_stage_transition(mock_db, project, "S4", "测试")
        assert ok is False
        assert result["can_advance"] is False
        assert len(result["missing_items"]) > 0

    def test_gate_passed_updates_stage(self, mock_db):
        project = _make_project(stage="S3")
        mock_check_gate = MagicMock(return_value=(True, []))
        with patch.dict("sys.modules", {
            "app.api.v1.endpoints.projects.utils": MagicMock(check_gate=mock_check_gate)
        }):
            ok, result = execute_stage_transition(mock_db, project, "S4", "测试")
        assert ok is True
        assert project.stage == "S4"
        assert result["auto_advanced"] is True

    def test_exception_returns_false(self, mock_db):
        project = _make_project()
        mock_utils = MagicMock()
        mock_utils.check_gate.side_effect = RuntimeError("DB error")
        with patch.dict("sys.modules", {
            "app.api.v1.endpoints.projects.utils": mock_utils
        }):
            ok, result = execute_stage_transition(mock_db, project, "S5", "测试")
        assert ok is False
        assert "失败" in result["message"]
