# -*- coding: utf-8 -*-
"""
Tests for status_transition_service
Covers: app/services/status_transition_service.py
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.status_transition_service import StatusTransitionService
from app.models.project import Project
from app.models.sales import Contract


@pytest.fixture
def status_transition_service(db_session: Session):
    """Create status_transition_service instance."""
    return StatusTransitionService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        stage="S2",
        status="ST05"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestStatusTransitionService:
    """Test suite for StatusTransitionService."""

    def test_init(self, db_session: Session):
        """Test service initialization."""
        service = StatusTransitionService(db_session)
        assert service.db is db_session
        # 验证 handler 已初始化
        assert service.contract_handler is not None
        assert service.material_handler is not None
        assert service.acceptance_handler is not None
        assert service.ecn_handler is not None

    def test_handle_contract_signed_not_found(self, status_transition_service):
        """测试处理合同签订 - 合同不存在"""
        with patch.object(status_transition_service.contract_handler, 'handle_contract_signed') as mock_handler:
            mock_handler.return_value = None
            result = status_transition_service.handle_contract_signed(99999)
            assert result is None

    def test_handle_contract_signed_success(self, status_transition_service, test_project):
        """测试处理合同签订 - 成功场景"""
        with patch.object(status_transition_service.contract_handler, 'handle_contract_signed') as mock_handler:
            mock_handler.return_value = test_project
            result = status_transition_service.handle_contract_signed(1, auto_create_project=True)
            assert result is not None
            mock_handler.assert_called_once()

    def test_handle_bom_published_success(self, status_transition_service, test_project):
        """测试处理BOM发布 - 成功场景"""
        with patch.object(status_transition_service.material_handler, 'handle_bom_published') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_bom_published(test_project.id)
            assert result is True
            mock_handler.assert_called_once()

    def test_handle_material_shortage_success(self, status_transition_service, test_project):
        """测试处理物料缺货 - 成功场景"""
        with patch.object(status_transition_service.material_handler, 'handle_material_shortage') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_material_shortage(test_project.id, is_critical=True)
            assert result is True
            mock_handler.assert_called_once()

    def test_handle_material_ready_success(self, status_transition_service, test_project):
        """测试处理物料齐套 - 成功场景"""
        with patch.object(status_transition_service.material_handler, 'handle_material_ready') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_material_ready(test_project.id)
            assert result is True
            mock_handler.assert_called_once()

    def test_handle_fat_passed_success(self, status_transition_service, test_project):
        """测试处理FAT通过 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_fat_passed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_fat_passed(test_project.id)
            assert result is True
            mock_handler.assert_called_once()

    def test_handle_fat_failed_success(self, status_transition_service, test_project):
        """测试处理FAT失败 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_fat_failed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_fat_failed(test_project.id)
            assert result is True
            mock_handler.assert_called_once()

    def test_handle_sat_passed_success(self, status_transition_service, test_project):
        """测试处理SAT通过 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_sat_passed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_sat_passed(test_project.id)
            assert result is True
            mock_handler.assert_called_once()

    def test_handle_ecn_approved_success(self, status_transition_service, test_project):
        """测试处理ECN批准 - 成功场景"""
        with patch.object(status_transition_service.ecn_handler, 'handle_ecn_approved') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_ecn_approved(1, test_project.id)
            assert result is True
            mock_handler.assert_called_once()

    def test_handle_project_stage_change(self, status_transition_service, test_project):
        """测试项目阶段变更处理"""
        with patch.object(status_transition_service, '_log_status_change') as mock_log:
            status_transition_service.handle_project_stage_change(
                project=test_project,
                old_stage="S2",
                new_stage="S3"
            )
            # 验证状态变更被记录
            mock_log.assert_called()

    def test_log_status_change(self, status_transition_service, test_project):
        """测试记录状态变更"""
        status_transition_service._log_status_change(
            project_id=test_project.id,
            old_status="ST05",
            new_status="ST08",
            reason="合同签订",
            triggered_by="system"
        )
        
        # 验证状态日志已创建
        from app.models.project import ProjectStatusLog
        logs = status_transition_service.db.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).all()
        
        assert len(logs) > 0
