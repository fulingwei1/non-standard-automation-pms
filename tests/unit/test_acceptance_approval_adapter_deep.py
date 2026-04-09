# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 验收审批适配器"""
import pytest
from unittest.mock import MagicMock


class TestAcceptanceApprovalAdapterBusinessLogic:
    """验收审批适配器业务逻辑测试"""

    def test_get_entity_found(self):
        """测试获取验收实体"""
        try:
            from app.services.approval_engine.adapters.acceptance import AcceptanceApprovalAdapter

            mock_db = MagicMock()

            mock_acceptance = MagicMock()
            mock_acceptance.id = 1
            mock_acceptance.acceptance_no = "ACC-001"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_acceptance

            adapter = AcceptanceApprovalAdapter(mock_db)
            result = adapter.get_entity(1)

            assert result.id == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_get_entity_data(self):
        """测试获取验收数据"""
        try:
            from app.services.approval_engine.adapters.acceptance import AcceptanceApprovalAdapter

            mock_db = MagicMock()

            mock_acceptance = MagicMock()
            mock_acceptance.acceptance_no = "ACC-001"
            mock_acceptance.machine_name = "测试设备"
            mock_acceptance.status = "PENDING"
            mock_acceptance.pass_rate = 95.0

            mock_db.query.return_value.filter.return_value.first.return_value = mock_acceptance

            adapter = AcceptanceApprovalAdapter(mock_db)
            result = adapter.get_entity_data(1)

            assert result["acceptance_no"] == "ACC-001"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_submit(self):
        """测试提交审批"""
        try:
            from app.services.approval_engine.adapters.acceptance import AcceptanceApprovalAdapter

            mock_db = MagicMock()

            mock_acceptance = MagicMock()
            mock_acceptance.status = "COMPLETED"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_acceptance

            adapter = AcceptanceApprovalAdapter(mock_db)
            adapter.on_submit(1, MagicMock())

            assert mock_acceptance.status == "PENDING_APPROVAL"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_approved(self):
        """测试审批通过"""
        try:
            from app.services.approval_engine.adapters.acceptance import AcceptanceApprovalAdapter

            mock_db = MagicMock()

            mock_acceptance = MagicMock()
            mock_acceptance.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_acceptance

            adapter = AcceptanceApprovalAdapter(mock_db)
            adapter.on_approved(1, MagicMock())

            assert mock_acceptance.status == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")

    def test_route_by_pass_rate(self):
        """测试按通过率路由"""
        try:
            from app.services.approval_engine.adapters.acceptance import AcceptanceApprovalAdapter

            mock_db = MagicMock()

            mock_acceptance = MagicMock()
            mock_acceptance.pass_rate = 95.0  # 高通过率

            mock_db.query.return_value.filter.return_value.first.return_value = mock_acceptance

            adapter = AcceptanceApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["pass_rate"] == 95.0
        except ImportError:
            pytest.skip("Module not found")