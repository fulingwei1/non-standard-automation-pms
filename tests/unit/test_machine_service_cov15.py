# -*- coding: utf-8 -*-
"""第十五批: machine_service 单元测试"""
import pytest

pytest.importorskip("app.services.machine_service")

from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.services.machine_service import MachineService, ProjectAggregationService, VALID_STAGES, VALID_HEALTH


def make_db():
    return MagicMock()


def test_validate_stage_valid():
    svc = MachineService(make_db())
    assert svc.validate_stage("S1") is True
    assert svc.validate_stage("S9") is True


def test_validate_stage_invalid():
    svc = MachineService(make_db())
    assert svc.validate_stage("S99") is False
    assert svc.validate_stage("X1") is False


def test_validate_health_valid():
    svc = MachineService(make_db())
    assert svc.validate_health("H1") is True
    assert svc.validate_health("H3") is True


def test_validate_health_invalid():
    svc = MachineService(make_db())
    assert svc.validate_health("H5") is False


def test_generate_machine_code_project_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    svc = MachineService(db)
    with pytest.raises(ValueError, match="项目不存在"):
        svc.generate_machine_code(99)


def test_generate_machine_code_success():
    db = make_db()
    project = MagicMock()
    project.project_code = "PJ250101"

    def mock_query(model):
        q = MagicMock()
        from app.models.project import Project, Machine
        if model is Project:
            q.filter.return_value.first.return_value = project
        else:
            # func.max(Machine.machine_no) query
            q.filter.return_value.scalar.return_value = 2
        return q

    db.query.side_effect = mock_query
    svc = MachineService(db)
    code, no = svc.generate_machine_code(1)
    assert no == 3
    assert code == "PJ250101-PN003"


def test_get_project_machine_summary_no_machines():
    db = make_db()
    db.query.return_value.filter.return_value.all.return_value = []
    svc = ProjectAggregationService(db)
    summary = svc.get_project_machine_summary(1)
    assert summary["total_machines"] == 0
    assert summary["avg_progress"] == Decimal("0.00")


def test_get_project_machine_summary_with_machines():
    db = make_db()
    m1 = MagicMock()
    m1.stage = "S5"
    m1.health = "H1"
    m1.progress_pct = Decimal("50")
    m2 = MagicMock()
    m2.stage = "S9"
    m2.health = "H3"
    m2.progress_pct = Decimal("100")
    db.query.return_value.filter.return_value.all.return_value = [m1, m2]
    svc = ProjectAggregationService(db)
    summary = svc.get_project_machine_summary(1)
    assert summary["total_machines"] == 2
    assert summary["completed_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["avg_progress"] == Decimal("75.00")
