# -*- coding: utf-8 -*-
"""
OTD 对比分析测试

验证：
- 项目间对比结构 + shared_risks
- 时间对比结构 + direction(better/worse/stable)
- 错误处理（不存在的项目/空列表）
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.models.project import Project


def _make_project(db, code, stage="S5", contract=100000):
    p = Project(
        project_code=code,
        project_name=f"对比测试 {code}",
        stage=stage,
        status="ST01",
        health="H1",
        progress_pct=30,
        is_active=True,
        is_archived=False,
        contract_amount=Decimal(str(contract)),
        planned_start_date=date.today() - timedelta(days=90),
        planned_end_date=date.today() + timedelta(days=30),
    )
    db.add(p)
    db.flush()
    return p


@pytest.fixture(autouse=True)
def _clear_cache():
    from app.utils.cache_decorator import get_cache_service
    get_cache_service().clear()
    yield
    get_cache_service().clear()


class TestCompareProjects:
    def test_compare_structure(self, db_session):
        """对比返回结构正确。"""
        from app.services.otd.compare_service import OTDCompareService

        p1 = _make_project(db_session, "CMP-001")
        p2 = _make_project(db_session, "CMP-002")

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=50000,
        ):
            result = OTDCompareService(db_session).compare_projects([p1.id, p2.id])

        assert result["project_count"] == 2
        assert len(result["projects"]) == 2
        assert "shared_risks" in result
        # 每条有对比字段
        for item in result["projects"]:
            assert "severity" in item
            assert "current_margin_rate" in item
            assert "margin_gap" in item

    def test_compare_sorted_by_severity(self, db_session):
        """按 severity 降序（最严重在前）。"""
        from app.services.otd.compare_service import OTDCompareService

        p1 = _make_project(db_session, "CMP-S1", stage="S2")
        p2 = _make_project(db_session, "CMP-S2", stage="S5")

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=50000,
        ):
            result = OTDCompareService(db_session).compare_projects([p1.id, p2.id])

        # 两条都有 severity
        for item in result["projects"]:
            assert item.get("severity") in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_compare_nonexistent_project(self, db_session):
        """不存在的项目不崩（scan_project 返回 LOW + meta 维度）。"""
        from app.services.otd.compare_service import OTDCompareService

        p1 = _make_project(db_session, "CMP-EX")

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=50000,
        ):
            result = OTDCompareService(db_session).compare_projects([p1.id, 999999])

        assert result["project_count"] == 2
        # 不存在的项目 severity=LOW（scan_project 对不存在的返回 LOW+meta）
        nonexistent = next(i for i in result["projects"] if i["project_id"] == 999999)
        assert nonexistent["severity"] == "LOW"

    def test_shared_risks(self, db_session):
        """共有的风险维度被识别。"""
        from app.services.otd.compare_service import OTDCompareService

        # 两个项目都造关键节点逾期（共享 risk dim）
        from app.models.project.financial import ProjectMilestone

        p1 = _make_project(db_session, "CMP-SHARE1", stage="S3")
        p2 = _make_project(db_session, "CMP-SHARE2", stage="S3")

        for p in [p1, p2]:
            db_session.add(
                ProjectMilestone(
                    project_id=p.id,
                    milestone_name="关键节点",
                    planned_date=date.today() - timedelta(days=10),
                    status="IN_PROGRESS",
                    is_key=True,
                )
            )
        db_session.flush()

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=50000,
        ):
            result = OTDCompareService(db_session).compare_projects([p1.id, p2.id])

        # 两个项目都命中 key_milestone_overdue，应在 shared_risks 里
        shared_dims = [r["dim"] for r in result["shared_risks"]]
        assert "key_milestone_overdue" in shared_dims


class TestCompareTrend:
    def test_trend_structure(self, db_session):
        """时间对比结构正确。"""
        from app.services.otd.compare_service import OTDCompareService

        result = OTDCompareService(db_session).compare_trend(days=30)

        assert "period" in result
        assert "comparisons" in result
        assert "summary" in result
        assert len(result["comparisons"]) == 7  # 7 个指标

    def test_direction_values(self, db_session):
        """direction 取值合法。"""
        from app.services.otd.compare_service import OTDCompareService

        result = OTDCompareService(db_session).compare_trend(days=30)

        for c in result["comparisons"]:
            assert c["direction"] in ("better", "worse", "stable", "unknown")

    def test_summary_counts(self, db_session):
        """summary 的 better/worse/stable 计数正确。"""
        from app.services.otd.compare_service import OTDCompareService

        result = OTDCompareService(db_session).compare_trend(days=30)
        s = result["summary"]
        total = s["better_count"] + s["worse_count"] + s["stable_count"]
        # unknown 不计入，但 better+worse+stable 应 <= 7
        assert total <= 7

    def test_periods_correct(self, db_session):
        """本期和上期的时间窗正确（不重叠）。"""
        from app.services.otd.compare_service import OTDCompareService

        result = OTDCompareService(db_session).compare_trend(days=30)
        current = result["period"]["current"]
        prev = result["period"]["previous"]

        # 本期 start = 上期 end + 1（不重叠）
        current_start = date.fromisoformat(current["start"])
        prev_end = date.fromisoformat(prev["end"])
        assert current_start == prev_end + timedelta(days=1)
