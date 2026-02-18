# -*- coding: utf-8 -*-
"""第十七批 - 合同状态处理器单元测试"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

pytest.importorskip("app.services.status_handlers.contract_handler")


def _make_handler(db=None):
    from app.services.status_handlers.contract_handler import ContractStatusHandler
    return ContractStatusHandler(db or MagicMock())


class TestContractStatusHandler:

    def test_handle_returns_none_when_contract_not_found(self):
        """合同不存在时返回 None"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        handler = _make_handler(db)
        result = handler.handle_contract_signed(999)
        assert result is None

    def test_handle_updates_existing_project(self):
        """合同已关联项目时更新项目状态"""
        db = MagicMock()
        contract = MagicMock()
        contract.project_id = 10
        contract.signed_date = datetime(2026, 1, 1)
        contract.contract_amount = 100000
        contract.customer_contract_no = "CC-001"

        project = MagicMock()
        project.stage = "S2"
        project.status = "ST05"

        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        handler = _make_handler(db)
        result = handler.handle_contract_signed(1)

        assert project.stage == "S3"
        assert project.status == "ST08"
        db.commit.assert_called_once()
        assert result is project

    def test_handle_no_auto_create_returns_none(self):
        """auto_create_project=False 且无关联项目时返回 None"""
        db = MagicMock()
        contract = MagicMock()
        contract.project_id = None
        db.query.return_value.filter.return_value.first.return_value = contract
        handler = _make_handler(db)
        result = handler.handle_contract_signed(1, auto_create_project=False)
        assert result is None

    def test_log_status_change_uses_callback_when_provided(self):
        """提供 log_status_change 回调时调用它"""
        db = MagicMock()
        handler = _make_handler(db)
        callback = MagicMock()

        handler._log_status_change(
            project_id=1,
            old_stage="S2",
            new_stage="S3",
            change_type="CONTRACT_SIGNED",
            log_status_change=callback
        )
        callback.assert_called_once()

    def test_log_status_change_creates_log_when_no_callback(self):
        """无回调时创建 ProjectStatusLog 记录"""
        db = MagicMock()
        handler = _make_handler(db)

        with patch("app.services.status_handlers.contract_handler.ProjectStatusLog") as MockLog:
            mock_log_instance = MagicMock()
            MockLog.return_value = mock_log_instance
            handler._log_status_change(project_id=1, change_type="AUTO")
            db.add.assert_called_with(mock_log_instance)

    def test_handle_creates_new_project_when_no_project_id(self):
        """合同无关联项目时自动创建项目"""
        db = MagicMock()
        contract = MagicMock()
        contract.project_id = None
        contract.customer_id = 5
        contract.contract_code = "CTR-001"
        contract.contract_amount = 50000
        contract.signed_date = datetime(2026, 2, 1)
        contract.opportunity_id = None

        # contract 查询
        db.query.return_value.filter.return_value.first.return_value = contract

        handler = _make_handler(db)

        with patch("app.services.status_handlers.contract_handler.generate_project_code", return_value="P-001"), \
             patch("app.services.status_handlers.contract_handler.init_project_stages"), \
             patch("app.services.status_handlers.contract_handler.Project") as MockProject:
            mock_project = MagicMock()
            MockProject.return_value = mock_project
            result = handler.handle_contract_signed(1, auto_create_project=True)

        db.add.assert_called()
        db.flush.assert_called()
        db.commit.assert_called()
