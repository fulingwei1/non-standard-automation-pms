# -*- coding: utf-8 -*-
"""
第三十五批 - resource_allocation_service/conflicts.py 单元测试
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.resource_allocation_service.conflicts import detect_resource_conflicts
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


def _make_db(machine=None, conflicting_projects=None):
    """创建 mock 数据库会话"""
    db = MagicMock()

    machine_query = MagicMock()
    machine_query.filter.return_value = machine_query
    machine_query.first.return_value = machine

    project_query = MagicMock()
    project_query.join.return_value = project_query
    project_query.filter.return_value = project_query
    project_query.all.return_value = conflicting_projects or []

    def side_effect(model):
        from app.models import Machine, Project
        if model is Machine:
            return machine_query
        return project_query

    db.query.side_effect = side_effect
    return db


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDetectResourceConflicts:

    def test_no_machine_id_returns_empty(self):
        """未指定机台时返回空列表"""
        db = MagicMock()
        result = detect_resource_conflicts(db, 1, None, date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    def test_machine_not_found_returns_empty(self):
        """机台不存在时返回空列表"""
        try:
            from app.models import Machine, Project
        except Exception:
            pytest.skip("模型导入失败")
        db = _make_db(machine=None)
        result = detect_resource_conflicts(db, 1, 99, date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    def test_no_conflicts_returns_empty(self):
        """无冲突时返回空列表"""
        try:
            from app.models import Machine, Project
        except Exception:
            pytest.skip("模型导入失败")
        mock_machine = MagicMock()
        mock_machine.id = 5
        mock_machine.machine_code = "MC001"
        db = _make_db(machine=mock_machine, conflicting_projects=[])
        result = detect_resource_conflicts(db, 1, 5, date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    def test_conflict_detected(self):
        """检测到冲突时返回冲突信息"""
        try:
            from app.models import Machine, Project
        except Exception:
            pytest.skip("模型导入失败")
        mock_machine = MagicMock()
        mock_machine.id = 5
        mock_machine.machine_code = "MC002"

        conflict_project = MagicMock()
        conflict_project.id = 10
        conflict_project.project_name = "冲突项目"
        conflict_project.planned_start_date = date(2024, 1, 5)
        conflict_project.planned_end_date = date(2024, 1, 20)

        db = _make_db(machine=mock_machine, conflicting_projects=[conflict_project])
        result = detect_resource_conflicts(db, 1, 5, date(2024, 1, 1), date(2024, 1, 31))
        assert len(result) == 1
        assert result[0]["type"] == "MACHINE"
        assert result[0]["resource_id"] == 5
        assert result[0]["severity"] == "HIGH"

    def test_conflict_contains_required_keys(self):
        """冲突信息包含所有必要字段"""
        try:
            from app.models import Machine, Project
        except Exception:
            pytest.skip("模型导入失败")
        mock_machine = MagicMock()
        mock_machine.id = 6
        mock_machine.machine_code = "MC003"

        conflict_project = MagicMock()
        conflict_project.id = 20
        conflict_project.project_name = "项目X"
        conflict_project.planned_start_date = None
        conflict_project.planned_end_date = None

        db = _make_db(machine=mock_machine, conflicting_projects=[conflict_project])
        result = detect_resource_conflicts(db, 2, 6, date(2024, 2, 1), date(2024, 2, 28))
        assert len(result) == 1
        keys = {"type", "resource_id", "resource_name", "conflict_project_id",
                "conflict_project_name", "conflict_period", "severity"}
        assert keys.issubset(result[0].keys())

    def test_multiple_conflicts(self):
        """多个冲突项目都返回"""
        try:
            from app.models import Machine, Project
        except Exception:
            pytest.skip("模型导入失败")
        mock_machine = MagicMock()
        mock_machine.id = 7
        mock_machine.machine_code = "MC004"

        conflicts = []
        for i in range(3):
            cp = MagicMock()
            cp.id = 100 + i
            cp.project_name = f"冲突项目{i}"
            cp.planned_start_date = date(2024, 3, 1)
            cp.planned_end_date = date(2024, 3, 31)
            conflicts.append(cp)

        db = _make_db(machine=mock_machine, conflicting_projects=conflicts)
        result = detect_resource_conflicts(db, 99, 7, date(2024, 3, 1), date(2024, 3, 31))
        assert len(result) == 3
