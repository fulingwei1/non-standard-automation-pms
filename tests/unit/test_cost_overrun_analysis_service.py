# -*- coding: utf-8 -*-
"""Tests for cost_overrun_analysis_service"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session


class TestCostOverrunAnalysisService:
    """Test suite for CostOverrunAnalysisService"""

    @pytest.fixture
    def service(self, db_session: Session):
        from app.services.cost.cost_overrun_analysis_service import CostOverrunAnalysisService

        return CostOverrunAnalysisService(db_session)

    def test_analyze_reasons(self, service):
        """Test analyzing cost overrun reasons"""
        result = service.analyze_reasons()
        assert result is not None
        assert isinstance(result, dict)
        assert "analysis_period" in result
        assert "total_overrun_projects" in result
        assert "reasons" in result

    def test_labor_cost_and_hours_only_include_approved_timesheets(self, db_session: Session):
        """Draft/submitted timesheets must not affect labor cost or actual hours."""
        from datetime import date
        from decimal import Decimal
        import uuid

        from app.models.project import Project
        from app.models.timesheet import Timesheet
        from app.models.user import User
        from app.services.cost.cost_overrun_analysis_service import CostOverrunAnalysisService

        suffix = uuid.uuid4().hex[:8]
        approved_user = User(
            username=f"proj13-labor-user-{suffix}",
            password_hash="test_hash_123",
            real_name="已审批工时用户",
            is_active=True,
        )
        db_session.add(approved_user)
        db_session.flush()

        project = Project(
            project_code=f"PROJ13-LABOR-{suffix}",
            project_name="PROJ13 工时过滤项目",
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=approved_user.id,
        )
        db_session.add(project)
        db_session.flush()

        db_session.add_all(
            [
                Timesheet(
                    user_id=approved_user.id,
                    project_id=project.id,
                    work_date=date(2026, 6, 1),
                    hours=Decimal("2.00"),
                    status="APPROVED",
                    work_content="已审批工时",
                    created_by=approved_user.id,
                ),
                Timesheet(
                    user_id=approved_user.id,
                    project_id=project.id,
                    work_date=date(2026, 6, 2),
                    hours=Decimal("10.00"),
                    status="DRAFT",
                    work_content="草稿工时",
                    created_by=approved_user.id,
                ),
                Timesheet(
                    user_id=approved_user.id,
                    project_id=project.id,
                    work_date=date(2026, 6, 3),
                    hours=Decimal("8.00"),
                    status="PENDING",
                    work_content="待审工时",
                    created_by=approved_user.id,
                ),
            ]
        )
        db_session.flush()

        service = CostOverrunAnalysisService(db_session)
        service.hourly_rate_service.get_user_hourly_rate = MagicMock(
            return_value=Decimal("123.00")
        )

        assert service._calculate_labor_cost(project.id) == Decimal("246.0000")
        assert service._calculate_actual_hours(project.id) == 2.0
        service.hourly_rate_service.get_user_hourly_rate.assert_called_once_with(
            db_session, approved_user.id, date(2026, 6, 1)
        )

    def test_accountability_ignores_unapproved_timesheets(self, db_session: Session):
        """Cost accountability should not blame users for unapproved drafts."""
        from datetime import date
        from decimal import Decimal
        import uuid

        from app.models.project import Project
        from app.models.timesheet import Timesheet
        from app.models.user import User
        from app.services.cost.cost_overrun_analysis_service import CostOverrunAnalysisService

        suffix = uuid.uuid4().hex[:8]
        approved_user = User(
            username=f"proj13-acct-approved-{suffix}",
            password_hash="test_hash_123",
            real_name="已审批工时用户",
            is_active=True,
        )
        draft_user = User(
            username=f"proj13-acct-draft-{suffix}",
            password_hash="test_hash_123",
            real_name="未审批工时用户",
            is_active=True,
        )
        db_session.add_all([approved_user, draft_user])
        db_session.flush()

        project = Project(
            project_code=f"PROJ13-ACCT-{suffix}",
            project_name="PROJ13 归责过滤项目",
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=approved_user.id,
        )
        db_session.add(project)
        db_session.flush()

        db_session.add_all(
            [
                Timesheet(
                    user_id=approved_user.id,
                    project_id=project.id,
                    work_date=date(2026, 6, 1),
                    hours=Decimal("2.00"),
                    status="APPROVED",
                    work_content="已审批工时",
                    created_by=approved_user.id,
                ),
                Timesheet(
                    user_id=draft_user.id,
                    project_id=project.id,
                    work_date=date(2026, 6, 2),
                    hours=Decimal("10.00"),
                    status="PENDING",
                    work_content="待审工时",
                    created_by=approved_user.id,
                ),
            ]
        )
        db_session.flush()

        service = CostOverrunAnalysisService(db_session)
        service.hourly_rate_service.get_user_hourly_rate = MagicMock(
            return_value=Decimal("100.00")
        )
        with patch.object(
            service,
            "analyze_reasons",
            return_value={
                "projects": [{"project_id": project.id, "overrun_amount": 1000.0}],
                "total_overrun_projects": 1,
                "reasons": [],
            },
        ):
            result = service.analyze_accountability()

        by_person = {row["person_id"]: row for row in result["by_person"]}
        assert approved_user.id in by_person
        assert draft_user.id not in by_person
        assert by_person[approved_user.id]["total_overrun"] == 200.0


# ──────────────────────────────────────────────────────────────────────────────
# G4 补充测试（MagicMock，不依赖真实数据库）
# ──────────────────────────────────────────────────────────────────────────────

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestCostOverrunAnalysisServiceG4:
    """G4 补充：CostOverrunAnalysisService 深度覆盖"""

    def _make_service(self):
        from app.services.cost.cost_overrun_analysis_service import CostOverrunAnalysisService

        db = MagicMock()
        service = CostOverrunAnalysisService(db)
        return service, db

    # ---- analyze_reasons: 无项目时返回结构正确 ----

    def test_analyze_reasons_no_projects(self):
        """无项目时返回空原因列表"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_reasons()

        assert result["total_overrun_projects"] == 0
        assert result["reasons"] == []
        assert isinstance(result, dict)

    # ---- analyze_reasons: 有超支项目 ----

    def test_analyze_reasons_with_overrun_project(self):
        """有超支项目时 total_overrun_projects >= 1"""
        service, db = self._make_service()

        project = MagicMock()
        project.id = 1
        project.project_code = "PJ-001"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("150000")

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [project]
        db.query.return_value = q

        # patch _analyze_project_overrun 返回确定的超支结果
        with patch.object(
            service,
            "_analyze_project_overrun",
            return_value={
                "has_overrun": True,
                "overrun_amount": 50000,
                "project_id": 1,
                "project_code": "PJ-001",
                "reasons": ["scope_change"],
            },
        ):
            result = service.analyze_reasons()

        assert result["total_overrun_projects"] == 1
        assert len(result["reasons"]) == 1
        assert result["reasons"][0]["reason"] == "scope_change"

    # ---- analyze_reasons: date 过滤参数传入 ----

    def test_analyze_reasons_with_date_filter(self):
        """传入 start_date/end_date 时 analysis_period 正确"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_reasons(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
        assert result["analysis_period"]["start_date"] == "2024-01-01"
        assert result["analysis_period"]["end_date"] == "2024-12-31"

    # ---- analyze_reasons: project_id 过滤 ----

    def test_analyze_reasons_with_project_id(self):
        """传入 project_id 时，结果只包含该项目"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_reasons(project_id=42)
        assert result["total_overrun_projects"] == 0

    # ---- analyze_accountability ----

    def test_analyze_accountability_no_data(self):
        """无超支项目时 accountability 返回空"""
        service, db = self._make_service()
        with patch.object(
            service,
            "analyze_reasons",
            return_value={"projects": [], "total_overrun_projects": 0, "reasons": []},
        ):
            result = service.analyze_accountability()
        assert isinstance(result, dict)

    # ---- _analyze_project_overrun: 无超支 ----

    def test_analyze_project_overrun_no_overrun(self):
        """预算 >= 实际成本时，has_overrun=False"""
        service, db = self._make_service()
        project = MagicMock()
        project.id = 1
        project.project_code = "PJ-002"
        project.budget_amount = Decimal("200000")
        project.budget = Decimal("200000")
        project.actual_cost = Decimal("100000")
        project.project_name = "项目2"

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = project
        db.query.return_value = q

        with patch.object(service, "_calculate_actual_cost", return_value=Decimal("100000")):
            result = service._analyze_project_overrun(project)
        assert result["has_overrun"] is False
