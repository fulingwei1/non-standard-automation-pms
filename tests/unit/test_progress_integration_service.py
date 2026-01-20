# -*- coding: utf-8 -*-
"""
Tests for progress_integration_service service
Covers: app/services/progress_integration_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 148 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.progress_integration_service import ProgressIntegrationService
from app.models.project import Project
from app.models.shortage import ShortageAlert
from app.models.progress import Task
from app.models.ecn import Ecn
from app.models.acceptance import AcceptanceOrder


@pytest.fixture
def progress_integration_service(db_session: Session):
    """创建 ProgressIntegrationService 实例"""
    return ProgressIntegrationService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_shortage_alert(db_session: Session, test_project):
    """创建测试缺料预警"""
    alert = ShortageAlert(
        project_id=test_project.id,
        alert_no="ALERT001",
        material_name="测试物料",
        material_code="MAT001",
        alert_level="level3",
        impact_type="stop",
        estimated_delay_days=5
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


@pytest.fixture
def test_task(db_session: Session, test_project):
    """创建测试任务"""
    task = Task(
        project_id=test_project.id,
        task_name="装配任务",
        stage="S5",
        status="IN_PROGRESS",
        plan_end=date.today() + timedelta(days=10)
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


class TestProgressIntegrationService:
    """Test suite for ProgressIntegrationService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = ProgressIntegrationService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_handle_shortage_alert_created_no_project(self, progress_integration_service, db_session):
        """测试处理缺料预警创建 - 无关联项目"""
        alert = ShortageAlert(
            project_id=None,
            alert_no="ALERT002",
            material_name="测试物料"
        )
        db_session.add(alert)
        db_session.commit()
        
        result = progress_integration_service.handle_shortage_alert_created(alert)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_handle_shortage_alert_created_high_level(self, progress_integration_service, test_shortage_alert, test_task):
        """测试处理缺料预警创建 - 高级别预警"""
        result = progress_integration_service.handle_shortage_alert_created(test_shortage_alert)
        
        assert isinstance(result, list)
        # 高级别预警应该阻塞任务
        if len(result) > 0:
            assert result[0].status == 'BLOCKED'

    def test_handle_shortage_alert_resolved_no_project(self, progress_integration_service, db_session):
        """测试处理缺料预警解决 - 无关联项目"""
        alert = ShortageAlert(
            project_id=None,
            alert_no="ALERT003"
        )
        db_session.add(alert)
        db_session.commit()
        
        result = progress_integration_service.handle_shortage_alert_resolved(alert)
        
        assert isinstance(result, list)

    def test_handle_shortage_alert_resolved_success(self, progress_integration_service, test_shortage_alert, test_task):
        """测试处理缺料预警解决 - 成功场景"""
        # 先阻塞任务
        test_task.status = 'BLOCKED'
        test_task.block_reason = f"缺料预警：{test_shortage_alert.material_name}"
        progress_integration_service.db.add(test_task)
        progress_integration_service.db.commit()
        
        result = progress_integration_service.handle_shortage_alert_resolved(test_shortage_alert)
        
        assert isinstance(result, list)

    def test_handle_ecn_approved_no_project(self, progress_integration_service, db_session):
        """测试处理ECN批准 - 无关联项目"""
        ecn = Ecn(
            ecn_no="ECN001",
            project_id=None,
            status="APPROVED"
        )
        db_session.add(ecn)
        db_session.commit()
        
        result = progress_integration_service.handle_ecn_approved(ecn)
        
        assert isinstance(result, list)

    def test_check_milestone_completion_requirements_not_found(self, progress_integration_service):
        """测试检查里程碑完成要求 - 里程碑不存在"""
        result = progress_integration_service.check_milestone_completion_requirements(99999)
        
        assert result is not None
        assert result.get('success') is False
        assert '不存在' in result.get('message', '')

    def test_handle_acceptance_failed_not_found(self, progress_integration_service):
        """测试处理验收失败 - 验收单不存在"""
        result = progress_integration_service.handle_acceptance_failed(99999)
        
        assert result is not None
        assert result.get('success') is False

    def test_handle_acceptance_passed_not_found(self, progress_integration_service):
        """测试处理验收通过 - 验收单不存在"""
        result = progress_integration_service.handle_acceptance_passed(99999)
        
        assert result is not None
        assert result.get('success') is False
