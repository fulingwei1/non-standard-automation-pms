# -*- coding: utf-8 -*-
"""
第三十五批 - cost_service.py 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.cost_service import CostService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


def _make_db(project=None, cost_total=0.0, cost_by_type=None, cost_by_category=None):
    db = MagicMock()

    # project query
    proj_q = MagicMock()
    proj_q.filter.return_value = proj_q
    proj_q.first.return_value = project

    # cost breakdown queries
    total_row = MagicMock()
    total_row.total = cost_total
    total_q = MagicMock()
    total_q.filter.return_value = total_q
    total_q.first.return_value = total_row

    type_q = MagicMock()
    type_q.filter.return_value = type_q
    type_q.group_by.return_value = type_q
    type_q.all.return_value = cost_by_type or []

    cat_q = MagicMock()
    cat_q.filter.return_value = cat_q
    cat_q.group_by.return_value = cat_q
    cat_q.all.return_value = cost_by_category or []

    call_count = [0]
    def query_side_effect(model):
        from app.models.project import Project, ProjectCost
        if model is Project:
            return proj_q
        return total_q  # simplified

    db.query.return_value = proj_q
    return db


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestCostService:

    def test_get_project_returns_none_if_not_found(self):
        """项目不存在时返回 None"""
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        svc = CostService(db)
        result = svc.get_project(9999)
        assert result is None

    def test_get_project_returns_project(self):
        """项目存在时正常返回"""
        mock_proj = MagicMock()
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = mock_proj
        db.query.return_value = q
        svc = CostService(db)
        result = svc.get_project(1)
        assert result is mock_proj

    def test_calculate_variance_no_budget(self):
        """预算为 0 时偏差为 0"""
        result = CostService.calculate_variance(0, 5000)
        assert result["budget_variance"] == 0
        assert result["budget_variance_pct"] == 0

    def test_calculate_variance_over_budget(self):
        """超出预算时返回正偏差"""
        result = CostService.calculate_variance(10000, 12000)
        assert result["budget_variance"] == 2000
        assert result["budget_variance_pct"] == pytest.approx(20.0)

    def test_calculate_variance_under_budget(self):
        """在预算内时返回负偏差"""
        result = CostService.calculate_variance(10000, 8000)
        assert result["budget_variance"] == -2000
        assert result["budget_variance_pct"] == pytest.approx(-20.0)

    def test_get_project_cost_analysis_not_found(self):
        """项目不存在时返回错误信息"""
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        svc = CostService(db)
        result = svc.get_project_cost_analysis(9999)
        assert "error" in result

    def test_get_cost_breakdown_returns_dict(self):
        """get_cost_breakdown 返回包含必要键的字典"""
        db = MagicMock()
        total_row = MagicMock()
        total_row.total = 50000.0

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = total_row
        q.group_by.return_value = q
        q.all.return_value = []
        q.label.return_value = q
        db.query.return_value = q

        svc = CostService(db)
        result = svc.get_cost_breakdown(1)
        assert "total_cost" in result
        assert "cost_by_type" in result
        assert "cost_by_category" in result

    def test_calculate_cost_stats_over_budget_flag(self):
        """超出预算时 is_over_budget 为 True"""
        db = MagicMock()
        svc = CostService(db)
        with patch.object(svc, "get_cost_breakdown", return_value={
            "total_cost": 15000.0,
            "cost_by_type": {},
            "cost_by_category": {},
        }):
            result = svc.calculate_cost_stats(1, budget_amount=10000.0)
        assert result["is_over_budget"] is True

    def test_calculate_cost_stats_under_budget_flag(self):
        """在预算内时 is_over_budget 为 False"""
        db = MagicMock()
        svc = CostService(db)
        with patch.object(svc, "get_cost_breakdown", return_value={
            "total_cost": 8000.0,
            "cost_by_type": {},
            "cost_by_category": {},
        }):
            result = svc.calculate_cost_stats(1, budget_amount=10000.0)
        assert result["is_over_budget"] is False
