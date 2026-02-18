# -*- coding: utf-8 -*-
"""第二十八批 - decomposition_tree 单元测试（分解树与追溯）"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.strategy.decomposition.decomposition_tree")

from app.services.strategy.decomposition.decomposition_tree import (
    get_decomposition_tree,
    trace_to_strategy,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_strategy(strategy_id=1, name="战略2024"):
    s = MagicMock()
    s.id = strategy_id
    s.name = name
    s.is_active = True
    return s


def _make_csf(csf_id=10, code="CSF-01", name="客户满意", dimension="客户", sort_order=1):
    c = MagicMock()
    c.id = csf_id
    c.code = code
    c.name = name
    c.dimension = dimension
    c.sort_order = sort_order
    return c


def _make_kpi(kpi_id=100, csf_id=10, code="KPI-01", name="客户满意度"):
    k = MagicMock()
    k.id = kpi_id
    k.csf_id = csf_id
    k.code = code
    k.name = name
    k.is_active = True
    return k


def _make_dept_obj(obj_id=200, kpi_id=100, department_id=5):
    o = MagicMock()
    o.id = obj_id
    o.kpi_id = kpi_id
    o.department_id = department_id
    o.is_active = True
    return o


def _make_personal_kpi(pkpi_id=300, user_id=7, code="PKPI-01",
                        name="个人KPI", dept_objective_id=200, source_kpi_id=None):
    p = MagicMock()
    p.id = pkpi_id
    p.user_id = user_id
    p.code = code
    p.name = name
    p.dept_objective_id = dept_objective_id
    p.source_kpi_id = source_kpi_id
    p.is_active = True
    return p


# ─── get_decomposition_tree ──────────────────────────────────

class TestGetDecompositionTree:

    def _setup_db_empty(self, strategy):
        """返回 strategy 不存在的 db mock"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = strategy
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        return db

    def test_returns_empty_when_strategy_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_decomposition_tree(db, strategy_id=99)

        assert result.strategy_id == 99
        assert result.strategy_name == ""
        assert result.nodes == []

    def test_returns_strategy_name_when_found(self):
        strategy = _make_strategy(name="战略2025")
        db = self._setup_db_empty(strategy)

        result = get_decomposition_tree(db, strategy_id=1)
        assert result.strategy_name == "战略2025"

    def test_empty_csfs_returns_empty_nodes(self):
        strategy = _make_strategy()
        db = self._setup_db_empty(strategy)

        result = get_decomposition_tree(db, strategy_id=1)
        assert result.nodes == []

    def test_builds_csf_nodes(self):
        strategy = _make_strategy()
        csf = _make_csf()

        db = MagicMock()
        # strategy query
        db.query.return_value.filter.return_value.first.return_value = strategy
        # csf list
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [csf]
        # kpi list (empty)
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_decomposition_tree(db, strategy_id=1)
        assert len(result.nodes) == 1
        assert result.nodes[0].type == "CSF"
        assert result.nodes[0].name == "客户满意"

    def test_csf_node_id_format(self):
        strategy = _make_strategy()
        csf = _make_csf(csf_id=10)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = strategy
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [csf]
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_decomposition_tree(db, strategy_id=1)
        assert result.nodes[0].id == "csf-10"

    def test_kpi_dimension_stored_in_csf_node(self):
        strategy = _make_strategy()
        csf = _make_csf(dimension="内部运营")

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = strategy
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [csf]
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_decomposition_tree(db, strategy_id=1)
        assert result.nodes[0].dimension == "内部运营"


# ─── trace_to_strategy ───────────────────────────────────────

class TestTraceToStrategy:

    @patch("app.services.strategy.decomposition.decomposition_tree.get_personal_kpi")
    def test_returns_none_when_pkpi_not_found(self, mock_get):
        mock_get.return_value = None
        db = MagicMock()
        result = trace_to_strategy(db, personal_kpi_id=999)
        assert result is None

    @patch("app.services.strategy.decomposition.decomposition_tree.get_personal_kpi")
    def test_returns_response_with_user_name(self, mock_get):
        pkpi = _make_personal_kpi(user_id=7)
        mock_get.return_value = pkpi

        db = MagicMock()
        user = MagicMock()
        user.name = "李四"
        # chain: User / DeptObj / KPI / CSF / Strategy all query through first()
        db.query.return_value.filter.return_value.first.side_effect = [
            user,   # User query
            None,   # DepartmentObjective
            None,   # KPI
            None,   # CSF
            None,   # Strategy
        ]

        result = trace_to_strategy(db, personal_kpi_id=1)
        assert result is not None
        assert result.user_name == "李四"

    @patch("app.services.strategy.decomposition.decomposition_tree.get_personal_kpi")
    def test_traces_full_chain_to_strategy(self, mock_get):
        pkpi = _make_personal_kpi(dept_objective_id=200, source_kpi_id=None)
        mock_get.return_value = pkpi

        db = MagicMock()
        user = MagicMock()
        user.name = "王五"

        dept_obj = _make_dept_obj(kpi_id=100, department_id=5)
        dept = MagicMock()
        dept.name = "研发部"

        company_kpi = _make_kpi(kpi_id=100, csf_id=10)
        csf = _make_csf(csf_id=10)
        strategy = _make_strategy(strategy_id=1, name="战略主线")

        db.query.return_value.filter.return_value.first.side_effect = [
            user,
            dept_obj,
            dept,
            company_kpi,
            csf,
            strategy,
        ]

        result = trace_to_strategy(db, personal_kpi_id=1)
        assert result.strategy_name == "战略主线"
        assert result.csf_name == "客户满意"
        assert result.department_name == "研发部"

    @patch("app.services.strategy.decomposition.decomposition_tree.get_personal_kpi")
    def test_handles_missing_user(self, mock_get):
        pkpi = _make_personal_kpi(user_id=999)
        mock_get.return_value = pkpi

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            None,  # User not found
            None,  # DeptObj
            None,  # KPI
            None,  # CSF
            None,  # Strategy
        ]

        result = trace_to_strategy(db, personal_kpi_id=1)
        assert result.user_name is None

    @patch("app.services.strategy.decomposition.decomposition_tree.get_personal_kpi")
    def test_fields_are_none_when_no_csf(self, mock_get):
        pkpi = _make_personal_kpi()
        mock_get.return_value = pkpi

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(name="User"),  # user
            None,   # dept_obj
            None,   # kpi
            None,   # csf
            None,   # strategy
        ]

        result = trace_to_strategy(db, personal_kpi_id=1)
        assert result.csf_id is None
        assert result.strategy_id is None
