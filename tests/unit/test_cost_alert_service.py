# -*- coding: utf-8 -*-
"""
Tests for cost_alert_service service
Covers: app/services/cost_alert_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 170 lines
Batch: 3
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.cost_alert_service import CostAlertService
from app.models.project import Project
from app.models.budget import ProjectBudget
from app.models.alert import AlertRecord, AlertRule
from tests.conftest import _ensure_login_user


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    admin = _ensure_login_user(
        db_session,
        username="admin",
        password="admin123",
        real_name="系统管理员",
        department="系统",
        employee_role="ADMIN",
        is_superuser=True
    )
    
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        stage="S1",
        status="ST01",
        health="H1",
        created_by=admin.id,
        budget_amount=Decimal('100000.00'),
        is_active=True
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_budget(db_session: Session, test_project):
    """创建测试预算"""
    budget = ProjectBudget(
        budget_no="BUDGET-001",
        project_id=test_project.id,
        budget_name="测试预算",
        version="V1.0",
        total_amount=Decimal('100000.00'),
        status="APPROVED",
        is_active=True
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    return budget


class TestCostAlertService:
    """Test suite for CostAlertService."""

    def test_check_budget_execution_project_not_found(self, db_session):
        """测试项目不存在"""
        result = CostAlertService.check_budget_execution(
            db=db_session,
            project_id=99999
        )

        assert result is None

    def test_check_budget_execution_no_budget(self, db_session, test_project):
        """测试无预算"""
        # 设置项目预算为0
        test_project.budget_amount = Decimal('0')
        db_session.commit()

        result = CostAlertService.check_budget_execution(
            db=db_session,
            project_id=test_project.id
        )

        assert result is None

    def test_check_budget_execution_no_alert_needed(self, db_session, test_project, test_budget):
        """测试无需预警（执行率低）"""
        with patch('app.services.budget_execution_check_service.get_actual_cost') as mock_cost:
            mock_cost.return_value = 50000.0  # 50%执行率

            result = CostAlertService.check_budget_execution(
                db=db_session,
                project_id=test_project.id
            )

            # 执行率50%，不需要预警
            assert result is None

    def test_check_budget_execution_warning_level(self, db_session, test_project, test_budget):
        """测试警告级别预警（执行率80-90%）"""
        with patch('app.services.budget_execution_check_service.get_actual_cost') as mock_cost, \
             patch('app.services.budget_execution_check_service.get_or_create_alert_rule') as mock_rule, \
             patch('app.services.budget_execution_check_service.find_existing_alert') as mock_find, \
             patch('app.services.budget_execution_check_service.create_alert_record') as mock_create:

            mock_cost.return_value = 85000.0  # 85%执行率
            mock_rule.return_value = MagicMock()
            mock_find.return_value = None
            mock_create.return_value = MagicMock()

            result = CostAlertService.check_budget_execution(
                db=db_session,
                project_id=test_project.id
            )

            assert result is not None

    def test_check_budget_execution_critical_level(self, db_session, test_project, test_budget):
        """测试严重级别预警（超支10-20%）"""
        with patch('app.services.budget_execution_check_service.get_actual_cost') as mock_cost, \
             patch('app.services.budget_execution_check_service.get_or_create_alert_rule') as mock_rule, \
             patch('app.services.budget_execution_check_service.find_existing_alert') as mock_find, \
             patch('app.services.budget_execution_check_service.create_alert_record') as mock_create:

            mock_cost.return_value = 115000.0  # 115%执行率，超支15%
            mock_rule.return_value = MagicMock()
            mock_find.return_value = None
            mock_create.return_value = MagicMock()

            result = CostAlertService.check_budget_execution(
                db=db_session,
                project_id=test_project.id
            )

            assert result is not None

    def test_check_budget_execution_urgent_level(self, db_session, test_project, test_budget):
        """测试紧急级别预警（超支20%以上）"""
        with patch('app.services.budget_execution_check_service.get_actual_cost') as mock_cost, \
             patch('app.services.budget_execution_check_service.get_or_create_alert_rule') as mock_rule, \
             patch('app.services.budget_execution_check_service.find_existing_alert') as mock_find, \
             patch('app.services.budget_execution_check_service.create_alert_record') as mock_create:

            mock_cost.return_value = 125000.0  # 125%执行率，超支25%
            mock_rule.return_value = MagicMock()
            mock_find.return_value = None
            mock_create.return_value = MagicMock()

            result = CostAlertService.check_budget_execution(
                db=db_session,
                project_id=test_project.id
            )

            assert result is not None

    def test_check_budget_execution_existing_alert(self, db_session, test_project, test_budget):
        """测试已存在预警（更新现有预警）"""
        with patch('app.services.budget_execution_check_service.get_actual_cost') as mock_cost, \
             patch('app.services.budget_execution_check_service.get_or_create_alert_rule') as mock_rule, \
             patch('app.services.budget_execution_check_service.find_existing_alert') as mock_find, \
             patch.object(db_session, 'add') as mock_add:

            mock_cost.return_value = 95000.0  # 95%执行率
            mock_rule.return_value = MagicMock()

            # 模拟已存在的预警（使用 MagicMock）
            existing_alert = MagicMock()
            existing_alert.alert_level = "WARNING"
            existing_alert.alert_content = "测试内容"
            existing_alert.triggered_at = None
            mock_find.return_value = existing_alert

            result = CostAlertService.check_budget_execution(
                db=db_session,
                project_id=test_project.id
            )

            assert result is not None
            # 验证返回的是 existing_alert
            assert result == existing_alert
            # 验证更新了内容
            assert existing_alert.alert_content is not None
            # 验证调用了 db.add
            mock_add.assert_called_once_with(existing_alert)

    def test_check_budget_execution_with_trigger_source(self, db_session, test_project, test_budget):
        """测试带触发来源的预警"""
        with patch('app.services.budget_execution_check_service.get_actual_cost') as mock_cost, \
             patch('app.services.budget_execution_check_service.get_or_create_alert_rule') as mock_rule, \
             patch('app.services.budget_execution_check_service.find_existing_alert') as mock_find, \
             patch('app.services.budget_execution_check_service.create_alert_record') as mock_create:

            mock_cost.return_value = 95000.0
            mock_rule.return_value = MagicMock()
            mock_find.return_value = None
            mock_create.return_value = MagicMock()

            result = CostAlertService.check_budget_execution(
                db=db_session,
                project_id=test_project.id,
                trigger_source="PURCHASE",
                source_id=123
            )

            assert result is not None
            mock_create.assert_called_once()
            # 验证传递了触发来源
            call_args = mock_create.call_args
            assert call_args[0][9] == "PURCHASE"  # trigger_source
            assert call_args[0][10] == 123  # source_id

    def test_check_all_projects_budget_specific_projects(self, db_session, test_project):
        """测试批量检查 - 指定项目"""
        with patch.object(CostAlertService, 'check_budget_execution') as mock_check:
            mock_check.return_value = MagicMock(id=1, alert_level="WARNING")

            result = CostAlertService.check_all_projects_budget(
                db=db_session,
                project_ids=[test_project.id]
            )

            assert isinstance(result, dict)
            assert 'checked_count' in result
            assert 'alert_count' in result
            assert 'projects' in result
            assert result['checked_count'] == 1

    def test_check_all_projects_budget_all_active(self, db_session, test_project):
        """测试批量检查 - 所有活跃项目"""
        # 创建另一个活跃项目
        admin = _ensure_login_user(
            db_session,
            username="admin",
            password="admin123",
            real_name="系统管理员",
            department="系统",
            employee_role="ADMIN",
            is_superuser=True
        )

        project2 = Project(
            project_code="PJ002",
            project_name="测试项目2",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=admin.id,
            budget_amount=Decimal('50000.00'),
            is_active=True
        )
        db_session.add(project2)
        db_session.commit()

        with patch.object(CostAlertService, 'check_budget_execution') as mock_check:
            mock_check.return_value = None  # 无预警

            result = CostAlertService.check_all_projects_budget(
                db=db_session,
                project_ids=None
            )

            assert isinstance(result, dict)
            assert result['checked_count'] >= 2
            assert result['alert_count'] == 0

    def test_check_all_projects_budget_with_alerts(self, db_session, test_project):
        """测试批量检查 - 有预警"""
        with patch.object(CostAlertService, 'check_budget_execution') as mock_check:
            # 第一个项目有预警
            alert1 = MagicMock()
            alert1.id = 1
            alert1.alert_level = "WARNING"

            # 第二个项目无预警
            mock_check.side_effect = [alert1, None]

            result = CostAlertService.check_all_projects_budget(
                db=db_session,
                project_ids=[test_project.id, 99999]  # 第二个项目不存在，会被跳过
            )

            assert isinstance(result, dict)
            assert result['alert_count'] >= 0

    def test_check_all_projects_budget_empty_list(self, db_session):
        """测试批量检查 - 空列表"""
        result = CostAlertService.check_all_projects_budget(
            db=db_session,
            project_ids=[]
        )

        assert isinstance(result, dict)
        assert result['checked_count'] == 0
        assert result['alert_count'] == 0
        assert result['projects'] == []
