# -*- coding: utf-8 -*-
"""第二十八批 - detail_stats 单元测试（年度重点工作详情与统计）"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.strategy.annual_work_service.detail_stats")

from unittest.mock import patch as _patch

from app.services.strategy.annual_work_service.detail_stats import (
    get_annual_work_detail,
    get_annual_work_stats,
)

# AnnualKeyWorkProjectLink.is_active 在此模型中不存在，需要在模块级别打补丁
import app.models.strategy as _strategy_models
if not hasattr(_strategy_models.AnnualKeyWorkProjectLink, "is_active"):
    _strategy_models.AnnualKeyWorkProjectLink.is_active = MagicMock()


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_work(
    work_id=1,
    csf_id=10,
    name="重点工作A",
    status="IN_PROGRESS",
    priority=1,
    progress_percent=Decimal("60"),
    owner_user_id=None,
    owner_dept_id=None,
):
    w = MagicMock()
    w.id = work_id
    w.csf_id = csf_id
    w.code = f"W-{work_id:04d}"
    w.name = name
    w.description = "描述"
    w.voc_source = None
    w.pain_point = None
    w.solution = None
    w.year = 2024
    w.priority = priority
    w.status = status
    w.start_date = None
    w.end_date = None
    w.progress_percent = progress_percent
    w.progress_description = None
    w.owner_dept_id = owner_dept_id
    w.owner_user_id = owner_user_id
    w.is_active = True
    w.created_at = None
    w.updated_at = None
    return w


def _make_csf(csf_id=10, name="战略重点", dimension="客户"):
    csf = MagicMock()
    csf.id = csf_id
    csf.name = name
    csf.dimension = dimension
    csf.strategy_id = 1
    csf.is_active = True
    return csf


# ─── get_annual_work_detail ──────────────────────────────────

class TestGetAnnualWorkDetail:

    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_returns_none_when_work_not_found(self, mock_get):
        mock_get.return_value = None
        db = MagicMock()
        result = get_annual_work_detail(db, work_id=99)
        assert result is None

    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_returns_detail_without_owner(self, mock_get):
        """没有 owner_user_id / owner_dept_id 时应正常返回"""
        work = _make_work(owner_user_id=None, owner_dept_id=None)
        mock_get.return_value = work

        db = MagicMock()
        # CSF query
        csf = _make_csf()
        # 控制 db.query 链
        db.query.return_value.filter.return_value.first.return_value = csf
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_annual_work_detail(db, work_id=1)
        assert result is not None
        assert result.owner_name is None
        assert result.owner_dept_name is None

    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_returns_owner_name_when_present(self, mock_get):
        work = _make_work(owner_user_id=5)
        mock_get.return_value = work

        db = MagicMock()
        user = MagicMock()
        user.name = "张三"

        csf = _make_csf()

        call_results = [user, csf]
        db.query.return_value.filter.return_value.first.side_effect = call_results
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_annual_work_detail(db, work_id=1)
        assert result.owner_name == "张三"

    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_returns_csf_name_and_dimension(self, mock_get):
        work = _make_work(csf_id=10, owner_user_id=None, owner_dept_id=None)
        mock_get.return_value = work

        db = MagicMock()
        csf = _make_csf(csf_id=10, name="质量提升", dimension="内部运营")

        db.query.return_value.filter.return_value.first.return_value = csf
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_annual_work_detail(db, work_id=1)
        assert result.csf_name == "质量提升"
        assert result.csf_dimension == "内部运营"

    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_linked_projects_count(self, mock_get):
        work = _make_work(owner_user_id=None, owner_dept_id=None)
        mock_get.return_value = work

        db = MagicMock()
        csf = _make_csf()

        link1 = MagicMock()
        link1.project_id = 100
        link1.contribution_weight = Decimal("0.5")

        link2 = MagicMock()
        link2.project_id = 101
        link2.contribution_weight = Decimal("0.5")

        project1 = MagicMock()
        project1.id = 100
        project1.code = "P100"
        project1.name = "项目A"

        project2 = MagicMock()
        project2.id = 101
        project2.code = "P101"
        project2.name = "项目B"

        # first calls: csf; then project queries
        first_side = [csf, project1, project2]
        db.query.return_value.filter.return_value.first.side_effect = first_side
        db.query.return_value.filter.return_value.all.return_value = [link1, link2]

        result = get_annual_work_detail(db, work_id=1)
        assert result.linked_project_count == 2

    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_no_csf_returns_none_names(self, mock_get):
        work = _make_work(csf_id=999, owner_user_id=None, owner_dept_id=None)
        mock_get.return_value = work

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_annual_work_detail(db, work_id=1)
        assert result.csf_name is None
        assert result.csf_dimension is None


# ─── get_annual_work_stats ───────────────────────────────────

class TestGetAnnualWorkStats:

    def test_returns_zero_stats_when_no_works(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = get_annual_work_stats(db, strategy_id=1, year=2024)
        assert result["total"] == 0
        assert result["avg_progress"] == 0
        assert result["completed"] == 0

    def test_counts_by_status(self):
        db = MagicMock()
        works = [
            _make_work(status="COMPLETED", progress_percent=Decimal("100")),
            _make_work(work_id=2, status="IN_PROGRESS", progress_percent=Decimal("50")),
            _make_work(work_id=3, status="NOT_STARTED", progress_percent=Decimal("0")),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = works
        # csf query for dimension
        csf = _make_csf(csf_id=10, dimension="客户")
        db.query.return_value.filter.return_value.first.return_value = csf

        result = get_annual_work_stats(db, strategy_id=1, year=2024)
        assert result["total"] == 3
        assert result["completed"] == 1
        assert result["in_progress"] == 1
        assert result["not_started"] == 1

    def test_average_progress_calculated_correctly(self):
        db = MagicMock()
        works = [
            _make_work(status="IN_PROGRESS", progress_percent=Decimal("60")),
            _make_work(work_id=2, status="IN_PROGRESS", progress_percent=Decimal("40")),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = works
        csf = _make_csf()
        db.query.return_value.filter.return_value.first.return_value = csf

        result = get_annual_work_stats(db, strategy_id=1, year=2024)
        assert abs(result["avg_progress"] - 50.0) < 0.01

    def test_default_year_uses_current_year(self):
        """不传 year 时应使用当前年份"""
        import datetime
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = get_annual_work_stats(db, strategy_id=1)
        assert result["year"] == datetime.date.today().year

    def test_by_priority_aggregation(self):
        db = MagicMock()
        works = [
            _make_work(priority=1, status="IN_PROGRESS", progress_percent=Decimal("50")),
            _make_work(work_id=2, priority=1, status="COMPLETED", progress_percent=Decimal("100")),
            _make_work(work_id=3, priority=2, status="NOT_STARTED", progress_percent=Decimal("0")),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = works
        csf = _make_csf()
        db.query.return_value.filter.return_value.first.return_value = csf

        result = get_annual_work_stats(db, strategy_id=1, year=2024)
        assert result["by_priority"][1] == 2
        assert result["by_priority"][2] == 1

    def test_dimension_progress_computed(self):
        db = MagicMock()
        works = [
            _make_work(csf_id=10, status="IN_PROGRESS", progress_percent=Decimal("80")),
            _make_work(work_id=2, csf_id=10, status="COMPLETED", progress_percent=Decimal("100")),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = works
        csf = _make_csf(csf_id=10, dimension="客户")
        db.query.return_value.filter.return_value.first.return_value = csf

        result = get_annual_work_stats(db, strategy_id=1, year=2024)
        dim_progress = result["dimension_progress"]
        assert "客户" in dim_progress
        assert abs(dim_progress["客户"] - 90.0) < 0.01
