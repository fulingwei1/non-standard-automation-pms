# -*- coding: utf-8 -*-
"""第四十六批 - 分解统计单元测试"""
import pytest

pytest.importorskip("app.services.strategy.decomposition.stats",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock
from app.services.strategy.decomposition.stats import get_decomposition_stats


def _make_db_with_counts(csf=2, kpi=4, dept_obj=3, personal_kpi=6, dept_objs=None):
    db = MagicMock()
    call_count = [0]

    # We simulate multiple db.query(...) calls
    # The function calls in order: CSF count, KPI count, DeptObj count, PersonalKPI count, DeptObj list
    csf_q = MagicMock()
    csf_q.filter.return_value.count.return_value = csf

    kpi_q = MagicMock()
    kpi_q.join.return_value.filter.return_value.count.return_value = kpi

    dept_q = MagicMock()
    dept_q.filter.return_value.count.return_value = dept_obj

    pkpi_q = MagicMock()
    pkpi_q.join.return_value.filter.return_value.count.return_value = personal_kpi

    dept_list_q = MagicMock()
    objs = dept_objs or []
    dept_list_q.filter.return_value.all.return_value = objs

    # For per-dept PersonalKPI count
    per_dept_q = MagicMock()
    per_dept_q.filter.return_value.count.return_value = 0

    queries = [csf_q, kpi_q, dept_q, pkpi_q, dept_list_q]

    def side_effect(model):
        call_count[0] += 1
        idx = call_count[0] - 1
        if idx < len(queries):
            return queries[idx]
        return per_dept_q

    db.query.side_effect = side_effect
    return db


class TestGetDecompositionStats:
    def test_returns_dict_with_all_keys(self):
        db = _make_db_with_counts()
        result = get_decomposition_stats(db, strategy_id=1, year=2024)

        assert "csf_count" in result
        assert "kpi_count" in result
        assert "dept_objective_count" in result
        assert "personal_kpi_count" in result
        assert "decomposition_rate" in result
        assert "department_stats" in result
        assert result["year"] == 2024

    def test_decomposition_rate_calculated_correctly(self):
        db = _make_db_with_counts(kpi=4, personal_kpi=6)
        result = get_decomposition_stats(db, strategy_id=1, year=2024)
        assert result["decomposition_rate"] == pytest.approx(150.0)

    def test_decomposition_rate_zero_when_no_kpis(self):
        db = _make_db_with_counts(kpi=0, personal_kpi=0)
        result = get_decomposition_stats(db, strategy_id=1, year=2024)
        assert result["decomposition_rate"] == 0

    def test_uses_current_year_when_year_not_specified(self):
        db = _make_db_with_counts()
        from datetime import date
        result = get_decomposition_stats(db, strategy_id=1)
        assert result["year"] == date.today().year

    def test_dept_stats_empty_when_no_dept_objs(self):
        db = _make_db_with_counts(dept_objs=[])
        result = get_decomposition_stats(db, strategy_id=1, year=2024)
        assert result["department_stats"] == {}

    def test_dept_stats_populated_with_objectives(self):
        dept_obj = MagicMock()
        dept_obj.id = 10
        dept_obj.department_id = 42

        db = _make_db_with_counts(dept_objs=[dept_obj])
        result = get_decomposition_stats(db, strategy_id=1, year=2024)
        assert 42 in result["department_stats"]
        assert result["department_stats"][42]["objectives"] == 1
