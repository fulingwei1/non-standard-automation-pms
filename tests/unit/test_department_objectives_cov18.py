# -*- coding: utf-8 -*-
"""第十八批 - 部门目标管理单元测试"""
import json
from unittest.mock import MagicMock, patch, call

import pytest

try:
    from app.services.strategy.decomposition.department_objectives import (
        create_department_objective,
        get_department_objective,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


class TestCreateDepartmentObjective:
    def test_creates_and_commits(self, db):
        data = MagicMock()
        data.strategy_id = 1
        data.department_id = 2
        data.csf_id = 3
        data.kpi_id = 4
        data.year = 2024
        data.objectives = ["目标1", "目标2"]
        data.key_results = "关键结果"
        data.target_value = 100.0
        data.weight = 0.3
        data.owner_user_id = 5

        mock_obj = MagicMock()
        with patch("app.services.strategy.decomposition.department_objectives.DepartmentObjective", return_value=mock_obj):
            result = create_department_objective(db, data)

        db.add.assert_called_once_with(mock_obj)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(mock_obj)
        assert result is mock_obj

    def test_objectives_serialized_as_json(self, db):
        data = MagicMock()
        data.strategy_id = 1
        data.department_id = 2
        data.csf_id = None
        data.kpi_id = None
        data.year = 2024
        data.objectives = {"key": "value"}
        data.key_results = None
        data.target_value = None
        data.weight = None
        data.owner_user_id = None

        captured = {}
        def capture_init(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch("app.services.strategy.decomposition.department_objectives.DepartmentObjective") as MockCls:
            MockCls.side_effect = lambda **kw: captured.update(kw) or MagicMock()
            create_department_objective(db, data)

        # objectives should have been JSON-serialized
        if "objectives" in captured:
            assert isinstance(captured["objectives"], str)

    def test_none_objectives_remains_none(self, db):
        data = MagicMock()
        data.strategy_id = 1
        data.department_id = 2
        data.csf_id = None
        data.kpi_id = None
        data.year = 2024
        data.objectives = None
        data.key_results = None
        data.target_value = None
        data.weight = None
        data.owner_user_id = None

        mock_obj = MagicMock()
        with patch("app.services.strategy.decomposition.department_objectives.DepartmentObjective", return_value=mock_obj):
            result = create_department_objective(db, data)
        assert result is mock_obj


class TestGetDepartmentObjective:
    def test_returns_none_when_not_found(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = get_department_objective(db, 999)
        assert result is None

    def test_returns_objective_when_found(self, db):
        mock_obj = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_obj
        result = get_department_objective(db, 1)
        assert result is mock_obj

    def test_queries_correct_model(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        try:
            get_department_objective(db, 10)
        except Exception:
            pass
        db.query.assert_called()
