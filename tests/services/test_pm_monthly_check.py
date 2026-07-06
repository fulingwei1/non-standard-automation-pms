# -*- coding: utf-8 -*-
"""
PM 月度自检服务测试（对应手册 Sheet8）

验证：
- 健康度表结构 + 按健康度排序
- 8项动作的自动判定（4项能判 + 4项manual）
- 汇总统计正确
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.models.project import Project


def _make_project(db, code="PMCHECK-001", contract=100000, stage="S5", **kw):
    from decimal import Decimal

    defaults = dict(
        project_code=code,
        project_name=f"月检测试 {code}",
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
    defaults.update(kw)
    p = Project(**defaults)
    db.add(p)
    db.flush()
    return p


@pytest.fixture(autouse=True)
def _clear_cache():
    from app.utils.cache_decorator import get_cache_service

    get_cache_service().clear()
    yield
    get_cache_service().clear()


class TestPmMonthlyCheck:
    def test_check_structure(self, db_session):
        """返回 summary/health_table/actions 三块。"""
        from app.services.dashboard.pm_monthly_check_service import (
            PmMonthlyCheckService,
        )

        _make_project(db_session, "PMCHECK-STRUCT")
        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=50000,
        ):
            result = PmMonthlyCheckService(db_session).get_check()

        assert "summary" in result
        assert "health_table" in result
        assert "actions" in result
        assert "period" in result
        assert len(result["actions"]) == 8  # 8项动作

    def test_health_table_sorted_by_severity(self, db_session):
        """健康度表 critical 在前。"""
        from app.services.dashboard.pm_monthly_check_service import (
            PmMonthlyCheckService,
        )

        _make_project(db_session, "PMCHECK-H1")
        _make_project(db_session, "PMCHECK-H2")
        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.batch_margin_analysis",
            return_value=[
                {
                    "project_id": 1,
                    "project_code": "PMCHECK-H1",
                    "project_name": "p1",
                    "project_level": None,
                    "contract_amount": 100000,
                    "current_margin_rate": 30.0,
                    "target_margin_rate": 25.0,
                    "margin_gap": 5.0,
                    "health": "healthy",
                },
                {
                    "project_id": 2,
                    "project_code": "PMCHECK-H2",
                    "project_name": "p2",
                    "project_level": None,
                    "contract_amount": 100000,
                    "current_margin_rate": 10.0,
                    "target_margin_rate": 25.0,
                    "margin_gap": -15.0,
                    "health": "critical",
                },
            ],
        ):
            result = PmMonthlyCheckService(db_session).get_check()

        table = result["health_table"]
        # critical 应排在前面
        assert table[0]["health"] == "critical"
        assert table[1]["health"] == "healthy"

    def test_summary_counts(self, db_session):
        """summary 的 healthy/warning/critical 计数正确。"""
        from app.services.dashboard.pm_monthly_check_service import (
            PmMonthlyCheckService,
        )

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.batch_margin_analysis",
            return_value=[
                {"project_id": 1, "project_code": "A", "project_name": "a",
                 "project_level": None, "contract_amount": 100,
                 "current_margin_rate": 30, "target_margin_rate": 25,
                 "margin_gap": 5, "health": "healthy"},
                {"project_id": 2, "project_code": "B", "project_name": "b",
                 "project_level": None, "contract_amount": 100,
                 "current_margin_rate": 18, "target_margin_rate": 25,
                 "margin_gap": -7, "health": "warning"},
                {"project_id": 3, "project_code": "C", "project_name": "c",
                 "project_level": None, "contract_amount": 100,
                 "current_margin_rate": 5, "target_margin_rate": 25,
                 "margin_gap": -20, "health": "critical"},
            ],
        ):
            result = PmMonthlyCheckService(db_session).get_check()

        s = result["summary"]
        assert s["total_projects"] == 3
        assert s["healthy"] == 1
        assert s["warning"] == 1
        assert s["critical"] == 1

    def test_action_unregistered_changes_auto_failed(self, db_session):
        """动作4：有未关闭变更 → auto_failed。"""
        from datetime import datetime

        from app.models.change_request import ChangeRequest
        from app.models.user import User
        from app.services.dashboard.pm_monthly_check_service import (
            PmMonthlyCheckService,
        )

        project = _make_project(db_session, "PMCHECK-CHG")
        user = User(
            username="pmcheck-submitter",
            password_hash="x",
            real_name="x",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
        db_session.add(
            ChangeRequest(
                change_code="CR-PMC-001",
                project_id=project.id,
                title="变更",
                change_type="REQUIREMENT",
                change_source="CUSTOMER",
                submitter_id=user.id,
                status="PENDING",  # 未关闭
            )
        )
        db_session.commit()

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.batch_margin_analysis",
            return_value=[
                {"project_id": project.id, "project_code": "PMCHECK-CHG",
                 "project_name": "p", "project_level": None,
                 "contract_amount": 100000, "current_margin_rate": 30,
                 "target_margin_rate": 25, "margin_gap": 5, "health": "healthy"},
            ],
        ):
            result = PmMonthlyCheckService(db_session).get_check()

        action4 = next(a for a in result["actions"] if a["id"] == 4)
        assert action4["status"] == "auto_failed"
        assert "未关闭" in action4["detail"]

    def test_action_delayed_projects_auto_failed(self, db_session):
        """动作6：有延期项目 → auto_failed。"""
        from app.services.dashboard.pm_monthly_check_service import (
            PmMonthlyCheckService,
        )

        # 造一个在途超期项目
        _make_project(
            db_session,
            "PMCHECK-LATE",
            planned_end_date=date.today() - timedelta(days=10),  # 已逾期
        )
        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=50000,
        ):
            result = PmMonthlyCheckService(db_session).get_check()

        action6 = next(a for a in result["actions"] if a["id"] == 6)
        assert action6["status"] == "auto_failed"

    def test_manual_actions_present(self, db_session):
        """动作1/3/8 是 manual（系统无法判）。"""
        from app.services.dashboard.pm_monthly_check_service import (
            PmMonthlyCheckService,
        )

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.batch_margin_analysis",
            return_value=[],
        ):
            result = PmMonthlyCheckService(db_session).get_check()

        for action_id in (1, 3, 8):
            action = next(a for a in result["actions"] if a["id"] == action_id)
            assert action["status"] == "manual"

    def test_pm_id_filter(self, db_session):
        """pm_id 过滤：只返回该 PM 的项目。"""
        from app.services.dashboard.pm_monthly_check_service import (
            PmMonthlyCheckService,
        )

        # pm_id=999 不存在，应返回空健康度表
        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.batch_margin_analysis",
            return_value=[
                {"project_id": 1, "project_code": "X", "project_name": "x",
                 "project_level": None, "contract_amount": 100,
                 "current_margin_rate": 30, "target_margin_rate": 25,
                 "margin_gap": 5, "health": "healthy"},
            ],
        ):
            result = PmMonthlyCheckService(db_session).get_check(pm_id=999)
        # project_id=1 的 pm_id 不是 999，被过滤
        assert result["summary"]["total_projects"] == 0
