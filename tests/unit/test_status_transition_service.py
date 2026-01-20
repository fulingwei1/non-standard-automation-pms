# -*- coding: utf-8 -*-
"""
Tests for status_transition_service
Covers: app/services/status_transition_service.py
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.status_transition_service import StatusTransitionService


@pytest.fixture
def status_transition_service(db_session: Session):
    """Create status_transition_service instance."""
    return StatusTransitionService(db_session)


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

    def test_handle_project_stage_change(self, status_transition_service):
        """测试项目阶段变更处理。"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ25001"
        mock_project.stage = "S3"

        # 调用阶段变更处理
        with patch.object(status_transition_service, 'trigger_stage_actions') as mock_trigger:
            status_transition_service.handle_project_stage_change(
                project=mock_project,
                old_stage="S2",
                new_stage="S3"
            )
            # 验证触发器被调用
            mock_trigger.assert_called()

    def test_handle_contract_signed(self, status_transition_service):
        """测试合同签订状态处理。"""
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_code = "CT25001"
        mock_contract.status = "SIGNED"

        with patch.object(status_transition_service.contract_handler, 'on_signed') as mock_handler:
            status_transition_service.contract_handler.on_signed(mock_contract)
            mock_handler.assert_called_once()

    def test_handle_ecn_approved(self, status_transition_service):
        """测试 ECN 批准状态处理。"""
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN25001"
        mock_ecn.status = "APPROVED"

        with patch.object(status_transition_service.ecn_handler, 'on_approved') as mock_handler:
            status_transition_service.ecn_handler.on_approved(mock_ecn)
            mock_handler.assert_called_once()

    def test_handle_acceptance_completed(self, status_transition_service):
        """测试验收完成状态处理。"""
        mock_acceptance = MagicMock()
        mock_acceptance.id = 1
        mock_acceptance.order_no = "FAT-P25001-M01-001"
        mock_acceptance.status = "COMPLETED"
        mock_acceptance.overall_result = "PASSED"

        with patch.object(status_transition_service.acceptance_handler, 'on_completed') as mock_handler:
            status_transition_service.acceptance_handler.on_completed(mock_acceptance)
            mock_handler.assert_called_once()
