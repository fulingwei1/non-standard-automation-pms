# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 机台管理服务 (扩展)
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.machine_service import (
        MachineService, ProjectAggregationService,
        VALID_STAGES, VALID_HEALTH, STAGE_PRIORITY, HEALTH_PRIORITY,
    )
    HAS_MS = True
except Exception:
    HAS_MS = False

pytestmark = pytest.mark.skipif(not HAS_MS, reason="machine_service 导入失败")


def make_machine_service():
    db = MagicMock()
    svc = MachineService(db)
    return svc, db


def make_aggregation_service():
    db = MagicMock()
    svc = ProjectAggregationService(db)
    return svc, db


class TestMachineServiceConstants:
    def test_valid_stages_count(self):
        assert len(VALID_STAGES) == 9

    def test_valid_health_count(self):
        assert len(VALID_HEALTH) == 4

    def test_stage_priority_ordered(self):
        assert STAGE_PRIORITY["S1"] < STAGE_PRIORITY["S9"]

    def test_health_priority_h3_highest(self):
        assert HEALTH_PRIORITY["H3"] < HEALTH_PRIORITY["H1"]


class TestMachineServiceGenerateMachineCode:
    def test_generate_code_project_not_found(self):
        """项目不存在时抛出ValueError"""
        svc, db = make_machine_service()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            svc.generate_machine_code(999)

    def test_generate_code_first_machine(self):
        """项目第一台机台编码"""
        svc, db = make_machine_service()
        mock_project = MagicMock()
        mock_project.project_code = "PJ001"

        call_count = [0]

        def query_side(*args, **kwargs):
            call_count[0] += 1
            m = MagicMock()
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = mock_project
            else:
                m.filter.return_value.scalar.return_value = None  # 无已有机台
            return m

        db.query.side_effect = query_side

        code, no = svc.generate_machine_code(1)
        assert no == 1
        assert "PN001" in code
        assert "PJ001" in code

    def test_generate_code_increments_sequence(self):
        """机台序号递增"""
        svc, db = make_machine_service()
        mock_project = MagicMock()
        mock_project.project_code = "PJ002"

        call_count = [0]

        def query_side(*args, **kwargs):
            call_count[0] += 1
            m = MagicMock()
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = mock_project
            else:
                m.filter.return_value.scalar.return_value = 3  # 已有3台
            return m

        db.query.side_effect = query_side

        code, no = svc.generate_machine_code(1)
        assert no == 4
        assert "PN004" in code


class TestMachineServiceValidateStage:
    def test_valid_stages(self):
        svc, db = make_machine_service()
        for stage in VALID_STAGES:
            assert svc.validate_stage(stage) is True

    def test_invalid_stage(self):
        svc, db = make_machine_service()
        assert svc.validate_stage("S10") is False
        assert svc.validate_stage("") is False
        assert svc.validate_stage("X1") is False


class TestMachineServiceValidateHealth:
    def test_valid_health(self):
        svc, db = make_machine_service()
        for h in VALID_HEALTH:
            assert svc.validate_health(h) is True

    def test_invalid_health(self):
        svc, db = make_machine_service()
        assert svc.validate_health("H5") is False
        assert svc.validate_health("") is False


class TestMachineServiceValidateStageTransition:
    def test_forward_transition_valid(self):
        svc, db = make_machine_service()
        ok, msg = svc.validate_stage_transition("S1", "S2")
        assert ok is True
        assert msg == ""

    def test_backward_transition_invalid(self):
        svc, db = make_machine_service()
        ok, msg = svc.validate_stage_transition("S5", "S3")
        assert ok is False
        assert "回退" in msg

    def test_s9_is_terminal(self):
        svc, db = make_machine_service()
        ok, msg = svc.validate_stage_transition("S9", "S8")
        assert ok is False
        assert "S9" in msg

    def test_invalid_current_stage(self):
        svc, db = make_machine_service()
        ok, msg = svc.validate_stage_transition("X1", "S2")
        assert ok is False

    def test_invalid_new_stage(self):
        svc, db = make_machine_service()
        ok, msg = svc.validate_stage_transition("S2", "X5")
        assert ok is False

    def test_same_stage_transition(self):
        svc, db = make_machine_service()
        ok, msg = svc.validate_stage_transition("S3", "S3")
        assert ok is True  # 同阶段应该允许


class TestProjectAggregationService:
    def test_init(self):
        db = MagicMock()
        svc = ProjectAggregationService(db)
        assert svc.db is db

    def test_calculate_project_progress_no_machines(self):
        """无机台时进度为0 (scalar返回None)"""
        svc, db = make_aggregation_service()
        # calculate_project_progress uses .scalar()
        db.query.return_value.filter.return_value.scalar.return_value = None
        result = svc.calculate_project_progress(1)
        assert result == Decimal("0.00")

    def test_calculate_project_stage_no_machines(self):
        """无机台时阶段为S1"""
        svc, db = make_aggregation_service()
        # calculate_project_stage uses .all() on Machine.stage column
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.calculate_project_stage(1)
        assert result == "S1"

    def test_calculate_project_health_no_machines(self):
        """无机台时健康度为H1"""
        svc, db = make_aggregation_service()
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.calculate_project_health(1)
        assert result == "H1"
