# -*- coding: utf-8 -*-
"""
健康趋势服务测试
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4


class TestHealthTrendService:
    """健康趋势服务测试"""

    def test_get_health_trend(self):
        """测试获取健康趋势"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        # Mock project exists
        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.get_health_trend(project_id=1)
        assert isinstance(result, dict)

    def test_get_health_trend_no_project(self):
        """测试项目不存在"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = HealthTrendService(mock_db)

        with pytest.raises(ValueError):
            service.get_health_trend(project_id=999)

    def test_get_risk_breakdown(self):
        """测试获取风险分解"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.health = "H1"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service._calc_schedule_score = MagicMock(return_value=80)
        service._calc_cost_score = MagicMock(return_value=75)
        service._calc_resource_score = MagicMock(return_value=90)
        service._calc_quality_score = MagicMock(return_value=85)

        result = service.get_risk_breakdown(project_id=1)
        assert isinstance(result, dict)

    def test_get_improvement_suggestions(self):
        """测试获取改进建议"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service.get_risk_breakdown = MagicMock(
            return_value={
                "overall_score": 85,
                "weak_factors": [],
            }
        )
        service._get_success_cases = MagicMock(return_value=[])

        result = service.get_improvement_suggestions(project_id=1)
        assert isinstance(result, dict)

    def test_calc_schedule_score(self):
        """测试计算进度评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_project.planned_start_date = None
        mock_project.planned_end_date = None
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        result = service._calc_schedule_score(mock_project)
        assert isinstance(result, int)

    def test_calc_cost_score(self):
        """测试计算成本评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        result = service._calc_cost_score(mock_project)
        assert isinstance(result, int)

    def test_calc_cost_score_uses_project_actual_cost_against_budget(self, db_session):
        """成本评分应从 Project.actual_cost / budget_amount 推算，而不是幽灵字段。"""
        from app.models.project import Project
        from app.services.health_trend_service import HealthTrendService

        project = Project(
            project_code=f"HT-COST-{uuid4().hex[:8]}",
            project_name="健康趋势成本评分项目",
            stage="S5",
            status="ST01",
            health="H2",
            budget_amount=Decimal("100.00"),
            actual_cost=Decimal("150.00"),
            progress_pct=Decimal("50.00"),
        )
        db_session.add(project)
        db_session.flush()

        score = HealthTrendService(db_session)._calc_cost_score(project)

        assert score < 100

    def test_calc_cost_score_counts_cost_overrun_alerts(self, db_session):
        """成本评分应识别真实 COST_OVERRUN 规则类型的待处理告警。"""
        from app.models.alert import AlertRecord, AlertRule
        from app.models.enums import AlertRuleTypeEnum
        from app.models.project import Project
        from app.services.health_trend_service import HealthTrendService

        suffix = uuid4().hex[:8]
        project = Project(
            project_code=f"HT-ALERT-{suffix}",
            project_name="健康趋势成本告警项目",
            stage="S5",
            status="ST01",
            health="H1",
            budget_amount=Decimal("0.00"),
            actual_cost=Decimal("0.00"),
            progress_pct=Decimal("0.00"),
        )
        rule = AlertRule(
            rule_code=f"HT-COST-OVERRUN-{suffix}",
            rule_name="成本超支",
            rule_type=AlertRuleTypeEnum.COST_OVERRUN.value,
            target_type="project",
            condition_type="THRESHOLD",
            alert_level="WARNING",
            is_enabled=True,
        )
        db_session.add_all([project, rule])
        db_session.flush()

        db_session.add(
            AlertRecord(
                alert_no=f"HT-COST-ALERT-{suffix}",
                rule_id=rule.id,
                target_type="project",
                target_id=project.id,
                project_id=project.id,
                alert_level="WARNING",
                alert_title="成本超支",
                alert_content="项目成本超支",
                triggered_at=datetime.now(),
                status="PENDING",
            )
        )
        db_session.flush()

        score = HealthTrendService(db_session)._calc_cost_score(project)

        assert score == 90

    def test_calc_resource_score(self):
        """测试计算资源评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        result = service._calc_resource_score(mock_project)
        assert isinstance(result, int)

    def test_calc_quality_score(self):
        """测试计算质量评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        result = service._calc_quality_score(mock_project)
        assert isinstance(result, int)

    def test_get_project(self):
        """测试获取项目"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service._get_project(project_id=1)
        assert result == mock_project
